from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import requests
import json
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

class URLRequest(BaseModel):
    url: str

class DeleteRequest(BaseModel):
    job_id: str

class PriorityRequest(BaseModel):
    job_id: str
    priority: int

def save_job_data(job_data):
    """Save job data to local text file database"""
    filename = "jobs_database.txt"
    with open(filename, "a", encoding="utf-8") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {json.dumps(job_data)}\n")

def get_all_jobs():
    """Get all jobs from the database"""
    filename = "jobs_database.txt"
    jobs = []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    # Parse the line: [timestamp] json_data
                    bracket_end = line.find('] ')
                    if bracket_end != -1:
                        json_part = line[bracket_end + 2:].strip()
                        try:
                            job_data = json.loads(json_part)
                            jobs.append(job_data)
                        except json.JSONDecodeError:
                            continue
    except FileNotFoundError:
        pass
    return jobs

def delete_job(job_url):
    """Delete a job from the database using URL as primary key"""
    filename = "jobs_database.txt"
    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # Filter out the job with the given URL
        filtered_lines = []
        deleted = False
        for line in lines:
            if line.strip():
                bracket_end = line.find('] ')
                if bracket_end != -1:
                    json_part = line[bracket_end + 2:].strip()
                    try:
                        job_data = json.loads(json_part)
                        if job_data.get("url") != job_url:
                            filtered_lines.append(line)
                        else:
                            deleted = True
                    except json.JSONDecodeError:
                        filtered_lines.append(line)
        
        # Write back the filtered lines
        with open(filename, "w", encoding="utf-8") as f:
            f.writelines(filtered_lines)
        
        return deleted
    except FileNotFoundError:
        return False

def update_job_priority(job_url, new_priority):
    """Update the priority of a job in the database using URL as primary key"""
    filename = "jobs_database.txt"
    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()
        updated = False
        new_lines = []
        for line in lines:
            if line.strip():
                bracket_end = line.find('] ')
                if bracket_end != -1:
                    json_part = line[bracket_end + 2:].strip()
                    try:
                        job_data = json.loads(json_part)
                        if job_data.get("url") == job_url:
                            job_data["priority"] = new_priority
                            line = line[:bracket_end+2] + json.dumps(job_data) + "\n"
                            updated = True
                    except json.JSONDecodeError:
                        pass
            new_lines.append(line)
        with open(filename, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        return updated
    except FileNotFoundError:
        return False

def analyze_job_posting(url):
    """Scrape job posting and use Claude API to analyze the content"""
    logger.info(f"Starting analysis for URL: {url}")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not set")
        return {"error": "ANTHROPIC_API_KEY not set"}
    
    logger.info(f"API Key loaded: {api_key[:10]}..." if api_key else "No API key")
    
    # First, scrape the job posting content
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        if response.status_code != 200:
            logger.error(f"Failed to fetch URL {url}: {response.status_code}")
            return {"error": f"Failed to fetch URL: {response.status_code}"}
        
        soup = BeautifulSoup(response.content, 'html.parser')
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        text_content = soup.get_text()
        # Clean up the text
        lines = (line.strip() for line in text_content.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text_content = ' '.join(chunk for chunk in chunks if chunk)
        
        # Limit text length to avoid token limits
        if len(text_content) > 8000:
            text_content = text_content[:8000]
            
    except Exception as e:
        logger.error(f"Failed to scrape URL {url}: {str(e)}")
        return {"error": f"Failed to scrape URL: {str(e)}"}
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }
    
    prompt = f"""Please analyze this job posting content and extract the following information:

Content: {text_content}

Extract and return ONLY a JSON object with these fields:
- company_name: The name of the company
- job_title: The job title/position
- location: The job location
- job_summary: A brief 2-3 sentence summary of the job

Return only valid JSON, no other text."""
    
    data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 1000,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data
        )
        
        logger.info(f"API Response Status: {response.status_code}")
        logger.debug(f"API Response Headers: {response.headers}")
        logger.debug(f"API Response Text: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            content = result["content"][0]["text"]
            
            # Parse the JSON response
            try:
                job_data = json.loads(content)
                job_data["url"] = url
                job_data["date_added"] = datetime.now().strftime("%Y-%m-%d")
                job_data["priority"] = 5
                logger.info(f"Successfully analyzed job: {job_data.get('company_name', 'N/A')} - {job_data.get('job_title', 'N/A')}")
                return job_data
            except json.JSONDecodeError:
                logger.error(f"Failed to parse Claude response as JSON: {content}")
                return {"error": "Failed to parse Claude response as JSON"}
        else:
            logger.error(f"API request failed: {response.status_code} - {response.text}")
            return {"error": f"API request failed: {response.status_code} - {response.text}"}
            
    except Exception as e:
        logger.error(f"Request failed: {str(e)}")
        return {"error": f"Request failed: {str(e)}"}

@app.get("/", response_class=HTMLResponse)
async def read_root():
    from fastapi import Request
    request = Request(scope={"type": "http", "method": "GET"})
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/jobs")
async def get_jobs():
    """Get all jobs from the database"""
    jobs = get_all_jobs()
    return {"jobs": jobs}

@app.delete("/jobs")
async def delete_job_endpoint(request: DeleteRequest):
    """Delete a job from the database"""
    print(f"Delete request received for URL: {request.job_id}")
    success = delete_job(request.job_id)
    print(f"Delete result: {success}")
    if success:
        return {"success": True, "message": "Job deleted successfully"}
    else:
        return {"success": False, "error": "Job not found or could not be deleted"}

@app.patch("/jobs")
async def update_priority_endpoint(request: PriorityRequest):
    """Update job priority in the database"""
    success = update_job_priority(request.job_id, request.priority)
    if success:
        return {"success": True, "message": "Priority updated successfully"}
    else:
        return {"success": False, "error": "Job not found or could not update priority"}

@app.post("/analyze")
async def analyze_job(request: URLRequest):
    if not request.url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    # Check if URL already exists in database
    existing_jobs = get_all_jobs()
    for job in existing_jobs:
        if job.get("url") == request.url:
            return {"success": False, "error": "Job URL already exists in database"}
    
    # Analyze the job posting
    job_data = analyze_job_posting(request.url)
    
    if "error" not in job_data:
        # Save to database
        save_job_data(job_data)
        return {"success": True, "data": job_data}
    else:
        return {"success": False, "error": job_data["error"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
