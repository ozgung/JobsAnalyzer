// Data store and sort state
let jobsData = [];
const sortState = { priority: 'asc', date: 'asc' };

async function loadJobs() {
    try {
        const response = await fetch('/jobs');
        const data = await response.json();
        jobsData = data.jobs;
        renderJobs(jobsData);
    } catch (error) {
        console.error('Error loading jobs:', error);
    }
}

function renderJobs(jobs) {
    const tbody = document.getElementById('jobsTableBody');
    tbody.innerHTML = '';
    jobs.forEach((job, index) => {
        const row = document.createElement('tr');
        row.title = job.job_summary || 'No summary available';
        const currentPriority = job.priority !== undefined ? job.priority : 5;
        row.innerHTML = `
            <td><button class="expand-btn" onclick="toggleJobDetails(${index})">▶</button></td>
            <td>${job.company_name || 'N/A'}</td>
            <td>${job.job_title || 'N/A'}</td>
            <td>${job.location || 'N/A'}</td>
            <td>
                <select class="priority-select" onchange="updatePriority('${job.url}', this.value)">
                    <option value="0"${currentPriority == 0 ? ' selected' : ''}>0</option>
                    <option value="1"${currentPriority == 1 ? ' selected' : ''}>1</option>
                    <option value="2"${currentPriority == 2 ? ' selected' : ''}>2</option>
                    <option value="3"${currentPriority == 3 ? ' selected' : ''}>3</option>
                    <option value="4"${currentPriority == 4 ? ' selected' : ''}>4</option>
                    <option value="5"${currentPriority == 5 ? ' selected' : ''}>5</option>
                </select>
            </td>
            <td>${job.date_added || 'N/A'}</td>
            <td><button class="view-btn" onclick="window.open('${job.url}', '_blank')">View</button></td>
            <td>
                <button class="delete-btn" onclick="deleteJob('${job.url}')">✗</button>
            </td>
        `;
        tbody.appendChild(row);
        // details row
        const detailsRow = document.createElement('tr');
        detailsRow.innerHTML = `
            <td colspan="8">
                <div class="job-details" id="details-${index}">
                    <h4>Job Details:</h4>
                    <p><strong>Company:</strong> ${job.company_name || 'N/A'}</p>
                    <p><strong>Job Title:</strong> ${job.job_title || 'N/A'}</p>
                    <p><strong>Location:</strong> ${job.location || 'N/A'}</p>
                    <p><strong>URL:</strong> <a href="${job.url}" target="_blank">${job.url}</a></p>
                    <p><strong>Date Added:</strong> ${job.date_added || 'N/A'}</p>
                    <p><strong>Summary:</strong> ${job.job_summary || 'No summary available'}</p>
                    <p><strong>Technologies:</strong> ${
                        (job.technologies || []).map(tech =>
                            `<span class="tech-label">${tech}</span>`
                        ).join('')
                    }</p>
                </div>
            </td>
        `;
        tbody.appendChild(detailsRow);
    });
}

// Load jobs when page loads
window.addEventListener('load', loadJobs);

// Sorting handlers
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('sort-priority').addEventListener('click', () => {
        sortState.priority = sortState.priority === 'asc' ? 'desc' : 'asc';
        const sorted = [...jobsData].sort((a, b) =>
            sortState.priority === 'asc'
                ? a.priority - b.priority
                : b.priority - a.priority
        );
        renderJobs(sorted);
    });
    document.getElementById('sort-date').addEventListener('click', () => {
        sortState.date = sortState.date === 'asc' ? 'desc' : 'asc';
        const sorted = [...jobsData].sort((a, b) => {
            const da = new Date(a.date_added);
            const db = new Date(b.date_added);
            return sortState.date === 'asc' ? da - db : db - da;
        });
        renderJobs(sorted);
    });
});

function toggleJobDetails(index) {
    const detailsDiv = document.getElementById(`details-${index}`);
    const button = event.target;
    
    if (detailsDiv.style.display === 'block') {
        detailsDiv.style.display = 'none';
        button.textContent = '▶';
    } else {
        detailsDiv.style.display = 'block';
        button.textContent = '▼';
    }
}

async function deleteJob(jobUrl) {
    if (confirm('Are you sure you want to delete this job?')) {
        try {
            console.log('Deleting job with URL:', jobUrl);
            const response = await fetch('/jobs', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ job_id: jobUrl })
            });
            
            console.log('Response status:', response.status);
            const data = await response.json();
            console.log('Response data:', data);
            
            if (data.success) {
                console.log('Job deleted successfully, refreshing table');
                loadJobs(); // Refresh the table
            } else {
                alert('Error deleting job: ' + data.error);
            }
        } catch (error) {
            console.error('Error deleting job:', error);
            alert('Error deleting job: ' + error.message);
        }
    }
}

async function analyzeJob() {
    const url = document.getElementById('urlInput').value;
    const resultDiv = document.getElementById('result');
    
    if (!url) {
        resultDiv.innerHTML = '<div class="result error">Please enter a URL</div>';
        return;
    }
    
    resultDiv.innerHTML = '<div class="result">Analyzing...</div>';
    
    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: url })
        });
        
        const data = await response.json();
        
        if (data.success) {
            resultDiv.innerHTML = `
                <div class="result success">
                    <h3>Job Analysis Results:</h3>
                    <p><strong>Company:</strong> ${data.data.company_name}</p>
                    <p><strong>Job Title:</strong> ${data.data.job_title}</p>
                    <p><strong>Location:</strong> ${data.data.location}</p>
                    <p><strong>URL:</strong> ${data.data.url}</p>
                    <p><strong>Date Added:</strong> ${data.data.date_added}</p>
                    <p><strong>Summary:</strong> ${data.data.job_summary}</p>
                </div>
            `;
            // Refresh the jobs table
            loadJobs();
        } else {
            resultDiv.innerHTML = `<div class="result error">Error: ${data.error}</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div class="result error">Error: ${error.message}</div>`;
    }
}

// Update priority for a job
async function updatePriority(jobUrl, priority) {
    try {
        const response = await fetch('/jobs', {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ job_id: jobUrl, priority: parseInt(priority, 10) })
        });
        const data = await response.json();
        if (!data.success) {
            alert('Failed to update priority: ' + data.error);
        }
    } catch (error) {
        console.error('Error updating priority:', error);
        alert('Error updating priority: ' + error.message);
    }
}
