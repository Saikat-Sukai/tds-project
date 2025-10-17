import os
import base64
import requests
import time
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from openai import OpenAI
from typing import List, Dict, Optional

# Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "Saikat-Sukai")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SECRET = os.getenv("secret")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Validation
if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN environment variable is required")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")
if not SECRET:
    raise ValueError("SECRET environment variable is required")


def validate_secret(secret: str) -> bool:
    """Validate the provided secret against the stored secret."""
    return secret == SECRET


def write_code_with_llm(brief: str, checks: List[str], attachments: Optional[List[Dict]] = None) -> List[Dict]:
    """
    Uses an LLM (OpenAI) to generate minimal, working app code
    based on the brief and checks received from instructor.
    """
    attachments_text = ""
    if attachments:
        attachments_text = "\n--- ATTACHMENTS ---\n"
        for att in attachments:
            attachments_text += f"- {att.get('name')}: {att.get('url')[:100]}...\n"

    prompt = f"""
You are an expert web developer.
Create a minimal working app that satisfies this task:

--- BRIEF ---
{brief}

--- CHECKS / REQUIREMENTS ---
{chr(10).join('- ' + c for c in checks)}
{attachments_text}

--- RULES ---
- Generate a complete, self-contained index.html file with inline CSS and JavaScript
- The code must be simple, readable, and work as-is (no build steps or npm dependencies)
- Use CDN links for any external libraries (e.g., Bootstrap, marked.js, highlight.js from jsdelivr or cdnjs)
- Handle all checks specified above
- Do NOT use localStorage, sessionStorage, or any browser storage APIs unless explicitly required by the brief
- Avoid secrets, API keys, and any credentials in the code
- Make the app functional and production-ready
- Include proper error handling
- Respond with ONLY the HTML code, no explanations or markdown formatting
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a code generator that outputs production-ready HTML files with inline CSS and JavaScript."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )

        code_output = response.choices[0].message.content.strip()

        # Remove markdown code fences if present
        if code_output.startswith("```"):
            lines = code_output.split("\n")
            # Remove first line (```html or ```)
            lines = lines[1:]
            # Remove last line if it's ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            code_output = "\n".join(lines).strip()

        # Validate that we have actual HTML content
        if not code_output or len(code_output) < 50:
            raise Exception("Generated code is too short or empty")
        
        if not ("<!DOCTYPE" in code_output or "<html" in code_output):
            raise Exception("Generated code doesn't appear to be valid HTML")

        return [{"name": "index.html", "content": code_output}]
    
    except Exception as e:
        print(f"❌ Error in write_code_with_llm: {e}")
        raise


def generate_readme_with_llm(brief: str, checks: List[str], repo_name: str, round_num: int = 1) -> Dict:
    """Generate a professional README.md file."""
    prompt = f"""
Write a professional README.md for this project.

Project Name: {repo_name}
Round: {round_num}

--- BRIEF ---
{brief}

--- CHECKS ---
{chr(10).join('- ' + c for c in checks)}

The README should include:
1. Project title and brief description
2. Features (based on checks)
3. Setup & Usage Instructions (how to open/use the app)
4. File Structure (list key files and their purpose)
5. Technologies Used
6. License (MIT)

Make it professional, clear, and well-formatted in Markdown.
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        text = response.choices[0].message.content.strip()
        
        # Remove markdown code fences if present
        if text.startswith("```"):
            lines = text.split("\n")
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        
        return {"name": "README.md", "content": text}
    
    except Exception as e:
        print(f"❌ Error in generate_readme_with_llm: {e}")
        raise


def create_github_repo(repo_name: str) -> Dict:
    """Create a new GitHub repository."""
    payload = {
        "name": repo_name,
        "private": False,
        "auto_init": False,  # We'll push files ourselves
        "description": f"Auto-generated app: {repo_name}",
    }
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    
    response = requests.post(
        "https://api.github.com/user/repos",
        headers=headers,
        json=payload,
        timeout=30
    )
    
    if response.status_code == 201:
        print(f"✅ Repository created: {response.json().get('html_url')}")
        return response.json()
    elif response.status_code == 422:
        # Repository might already exist
        print(f"⚠️ Repository {repo_name} may already exist")
        return {"name": repo_name, "html_url": f"https://github.com/{GITHUB_USERNAME}/{repo_name}"}
    else:
        raise Exception(f"Failed to create repository: {response.status_code} {response.text}")


def create_license_file() -> Dict:
    """Create an MIT LICENSE file."""
    license_content = """MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
    return {"name": "LICENSE", "content": license_content}


def enable_github_pages(repo_name: str) -> Dict:
    """Enable GitHub Pages for the repository."""
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    payload = {
        "build_type": "legacy",
        "source": {
            "branch": "main",
            "path": "/"
        }
    }
    
    response = requests.post(
        f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/pages",
        headers=headers,
        json=payload,
        timeout=30
    )
    
    if response.status_code == 201:
        print("✅ GitHub Pages enabled successfully")
        return response.json()
    elif response.status_code == 409:
        # Pages already enabled
        print("⚠️ GitHub Pages already enabled")
        return {"html_url": f"https://{GITHUB_USERNAME.lower()}.github.io/{repo_name}/"}
    else:
        raise Exception(f"Failed to enable GitHub Pages: {response.status_code} {response.text}")


def get_file_sha(repo_name: str, file_path: str) -> Optional[str]:
    """Get the SHA of a file if it exists in the repository."""
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/contents/{file_path}"
    response = requests.get(url, headers=headers, timeout=30)
    
    if response.status_code == 200:
        return response.json().get("sha")
    return None


def push_files_to_repo(repo_name: str, files: List[Dict], round_num: int) -> str:
    """
    Push multiple files to a GitHub repository.
    Returns the latest commit SHA.
    """
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    for file_data in files:
        file_name = file_data.get("name")
        content = file_data.get("content")

        # Convert content to base64
        if isinstance(content, str):
            content_b64 = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        else:
            content_b64 = base64.b64encode(content).decode("utf-8")

        # Check if file exists to get SHA
        sha = get_file_sha(repo_name, file_name)

        # Prepare payload
        payload = {
            "message": f"Round {round_num}: Update {file_name}",
            "content": content_b64,
            "branch": "main"
        }
        
        if sha:
            payload["sha"] = sha

        # Push file
        url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/contents/{file_name}"
        response = requests.put(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code in (200, 201):
            print(f"✅ Successfully pushed {file_name}")
        else:
            raise Exception(f"Failed to push {file_name}: {response.status_code} {response.text}")

    # Get the latest commit SHA
    time.sleep(1)  # Brief delay to ensure commit is processed
    commits_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/commits/main"
    response = requests.get(commits_url, headers=headers, timeout=30)
    
    if response.status_code == 200:
        commit_sha = response.json().get("sha")
        print(f"✅ Latest commit SHA: {commit_sha}")
        return commit_sha
    else:
        raise Exception(f"Failed to get commit SHA: {response.status_code}")


def notify_evaluation_url(eval_url: str, payload: Dict, max_retries: int = 5) -> bool:
    """
    Notify the evaluation URL with exponential backoff.
    Retries with delays: 1s, 2s, 4s, 8s, 16s
    """
    headers = {"Content-Type": "application/json"}
    
    for attempt in range(max_retries):
        try:
            response = requests.post(eval_url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                print(f"✅ Evaluation URL notified successfully (attempt {attempt + 1})")
                return True
            else:
                print(f"⚠️ Evaluation URL returned {response.status_code}: {response.text}")
        
        except Exception as e:
            print(f"⚠️ Error notifying evaluation URL (attempt {attempt + 1}): {e}")
        
        # Exponential backoff
        if attempt < max_retries - 1:
            delay = 2 ** attempt
            print(f"⏳ Retrying in {delay} seconds...")
            time.sleep(delay)
    
    print(f"❌ Failed to notify evaluation URL after {max_retries} attempts")
    return False


def round_1(data: Dict) -> Dict:
    """
    Handles Round 1:
    - Generates code and README using LLM
    - Creates a new GitHub repository
    - Pushes generated files (including LICENSE)
    - Enables GitHub Pages
    - Returns detailed repo and pages info
    """
    repo_name = f"{data['task']}_{data['nonce']}"
    brief = data.get("brief", "")
    checks = data.get("checks", [])
    attachments = data.get("attachments", [])

    print(f"🔧 Starting Round 1 for: {repo_name}")

    try:
        # Step 1: Generate app code
        files = write_code_with_llm(brief, checks, attachments)
        print("✅ Code generated successfully")
        
        # Step 2: Generate README
        files.append(generate_readme_with_llm(brief, checks, repo_name, 1))
        print("✅ README generated successfully")
        
        # Step 3: Add LICENSE
        files.append(create_license_file())
        print("✅ LICENSE added")

        # Step 4: Create GitHub repository
        create_github_repo(repo_name)
        time.sleep(2)  # Wait for repo to be fully created

        # Step 5: Push files
        commit_sha = push_files_to_repo(repo_name, files, round_num=1)
        
        # Step 6: Enable GitHub Pages
        time.sleep(2)
        enable_github_pages(repo_name)

        # Step 7: Prepare response
        repo_url = f"https://github.com/{GITHUB_USERNAME}/{repo_name}"
        pages_url = f"https://{GITHUB_USERNAME.lower()}.github.io/{repo_name}/"

        result = {
            "email": data["email"],
            "task": data["task"],
            "round": 1,
            "nonce": data["nonce"],
            "repo_url": repo_url,
            "commit_sha": commit_sha,
            "pages_url": pages_url,
        }

        # Step 8: Notify evaluation URL
        eval_url = data.get("evaluation_url")
        if eval_url:
            notify_evaluation_url(eval_url, result)

        print("✅ Round 1 completed successfully")
        return result

    except Exception as e:
        error_msg = f"Round 1 failed: {str(e)}"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)


def round_2(data: Dict) -> Dict:
    """
    Handles Round 2:
    - Updates app code based on new instructions
    - Updates README
    - Pushes changes to GitHub
    - Notifies evaluation URL
    """
    repo_name = f"{data['task']}_{data['nonce']}"
    brief = data.get("brief", "")
    checks = data.get("checks", [])
    attachments = data.get("attachments", [])

    print(f"🔧 Starting Round 2 for: {repo_name}")

    try:
        # Step 1: Regenerate code based on new brief
        files = write_code_with_llm(brief, checks, attachments)
        print("✅ Code updated for Round 2")

        # Step 2: Regenerate README
        files.append(generate_readme_with_llm(brief, checks, repo_name, 2))
        print("✅ README updated for Round 2")

        # Step 3: Push files
        commit_sha = push_files_to_repo(repo_name, files, round_num=2)

        # Step 4: Prepare response
        repo_url = f"https://github.com/{GITHUB_USERNAME}/{repo_name}"
        pages_url = f"https://{GITHUB_USERNAME.lower()}.github.io/{repo_name}/"

        result = {
            "email": data["email"],
            "task": data["task"],
            "round": 2,
            "nonce": data["nonce"],
            "repo_url": repo_url,
            "commit_sha": commit_sha,
            "pages_url": pages_url
        }

        # Step 5: Notify evaluation URL
        eval_url = data.get("evaluation_url")
        if eval_url:
            notify_evaluation_url(eval_url, result)

        print("✅ Round 2 completed successfully")
        return result

    except Exception as e:
        error_msg = f"Round 2 failed: {str(e)}"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)


# FastAPI Application
app = FastAPI(title="LLM Code Deployment Service")


@app.get("/")
def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "LLM Code Deployment"}


@app.post("/handle_task")
def handle_task(data: Dict) -> JSONResponse:
    """
    Main endpoint to handle task requests.
    Validates secret and routes to appropriate round handler.
    """
    # Validate secret
    secret = data.get("secret", "")
    if not validate_secret(secret):
        return JSONResponse(
            status_code=401,
            content={"error": "Invalid secret"}
        )
    
    # Validate required fields
    required_fields = ["email", "task", "round", "nonce", "brief", "checks"]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return JSONResponse(
            status_code=400,
            content={"error": f"Missing required fields: {', '.join(missing_fields)}"}
        )
    
    # Route to appropriate round
    round_num = data.get("round")
    
    try:
        if round_num == 1:
            result = round_1(data)
            return JSONResponse(
                status_code=200,
                content={"message": "Round 1 completed successfully", "result": result}
            )
        elif round_num == 2:
            result = round_2(data)
            return JSONResponse(
                status_code=200,
                content={"message": "Round 2 completed successfully", "result": result}
            )
        else:
            return JSONResponse(
                status_code=400,
                content={"error": f"Invalid round: {round_num}. Must be 1 or 2"}
            )
    
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"error": e.detail}
        )
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "details": str(e)}
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
