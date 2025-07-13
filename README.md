# JobsAnalyzer

*This project was written by [Claude Code](https://claude.ai/code)*

A web application that analyzes job postings using AI and stores them in a local database. Built with FastAPI, it scrapes job posting URLs, uses Claude AI to extract key information, and provides a clean interface to view and manage job listings.

## Features

- **AI-powered Analysis**: Uses Claude AI to extract company name, job title, location, and summary from job postings
- **Web Scraping**: Automatically scrapes job posting content from URLs
- **Local Database**: Stores job data in a simple text file database
- **Web Interface**: Clean, responsive UI for analyzing and viewing jobs
- **Duplicate Prevention**: Prevents adding the same job URL twice
- **Expandable Rows**: Click to expand job details and view full summaries
- **Delete Functionality**: Remove jobs from the database with confirmation
- **Hover Tooltips**: Quick summary preview on row hover

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd JobsAnalyzer
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your Anthropic API key:
   ```
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

5. Get your Anthropic API key from: https://console.anthropic.com/

## Usage

1. Start the server:
   ```bash
   python app.py
   ```
   Or use uvicorn directly:
   ```bash
   uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```

2. Open your browser to `http://localhost:8000`

3. Enter a job posting URL and click "Analyze" to add it to your database

4. View all jobs in the table below, with options to:
   - Click the arrow (▶) to expand job details
   - Click the × to delete a job
   - Hover over rows to see quick summaries

## Project Structure

```
├── app.py              # Main FastAPI application
├── templates/
│   └── index.html      # HTML template
├── static/
│   ├── style.css       # CSS styles
│   └── script.js       # JavaScript functionality
├── .env                # Environment variables (create this)
├── jobs_database.txt   # Local database file (auto-created)
└── README.md          # This file
```

## API Endpoints

- `GET /` - Main web interface
- `POST /analyze` - Analyze a job posting URL
- `GET /jobs` - Get all jobs from database
- `DELETE /jobs` - Delete a job by URL
- `PATCH /jobs` - Update a job's priority (0-5)

## Requirements

- Python 3.7+
- FastAPI
- Uvicorn
- Requests
- BeautifulSoup4
- Python-dotenv
- Jinja2
- Anthropic API key

## Database Format

Jobs are stored in `jobs_database.txt` with the following format:
```
[YYYY-MM-DD HH:MM:SS] {"company_name": "...", "job_title": "...", "location": "...", "url": "...", "date_added": "YYYY-MM-DD", "job_summary": "...", "technologies": ["..."], "priority": 0-5}
```

## Note

This application is for educational and personal use. Please respect robots.txt and terms of service when scraping job sites.
