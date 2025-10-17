# 🤖 LLM Code Deployment System

Automatically generate and deploy web applications using AI (GPT-4) and GitHub Pages.

## What It Does

Receives task → Generates code with AI → Creates GitHub repo → Deploys to GitHub Pages → Updates on request

## Quick Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
export GITHUB_TOKEN="ghp_your_github_token"
export GITHUB_USERNAME="your_username"
export OPENAI_API_KEY="sk-your_openai_key"
export SECRET="your_password"
```

Or create a `.env` file:
```bash
GITHUB_TOKEN=ghp_your_github_token
GITHUB_USERNAME=your_username
OPENAI_API_KEY=sk-your_openai_key
SECRET=your_password
```

**Get Your Tokens:**
- GitHub: Settings → Developer settings → [Personal tokens](https://github.com/settings/tokens) (needs `repo` scope)
- OpenAI: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

### 3. Run Server

```bash
python main.py
```

Server runs at: `http://localhost:8000`

## Usage

### Test Health

```bash
curl http://localhost:8000/
```

Response: `{"status":"ok","service":"LLM Code Deployment"}`

### Submit Task (Round 1)

```bash
curl -X POST http://localhost:8000/handle_task \
  -H "Content-Type: application/json" \
  -d '{
    "secret": "your_password",
    "email": "you@example.com",
    "task": "calculator",
    "round": 1,
    "nonce": "abc123",
    "brief": "Create a calculator with +, -, *, / operations",
    "checks": [
      "Has digit buttons 0-9",
      "Has operation buttons",
      "Shows result in #result element"
    ]
  }'
```

**What happens:**
1. AI generates calculator code
2. Creates repo: `github.com/your_username/calculator_abc123`
3. Deploys to: `your_username.github.io/calculator_abc123`
4. Returns repo URL and commit SHA

### Update App (Round 2)

```bash
curl -X POST http://localhost:8000/handle_task \
  -H "Content-Type: application/json" \
  -d '{
    "secret": "your_password",
    "task": "calculator",
    "round": 2,
    "nonce": "abc123",
    "brief": "Add memory functions (M+, M-, MR, MC)",
    "checks": ["Memory buttons work correctly"]
  }'
```

## API Reference

### POST /handle_task

**Required Fields:**
```json
{
  "secret": "string",        // Your password
  "email": "string",         // Your email
  "task": "string",          // Task ID (e.g., "calculator")
  "round": 1 or 2,          // 1 = create, 2 = update
  "nonce": "string",        // Unique ID (e.g., "abc123")
  "brief": "string",        // What to build
  "checks": ["string"]      // Requirements list
}
```

**Optional Fields:**
```json
{
  "evaluation_url": "string",   // Callback URL for results
  "attachments": [              // Files as data URIs
    {
      "name": "file.csv",
      "url": "data:text/csv;base64,..."
    }
  ]
}
```

**Success Response (200):**
```json
{
  "message": "Round 1 completed successfully",
  "result": {
    "email": "you@example.com",
    "task": "calculator",
    "round": 1,
    "nonce": "abc123",
    "repo_url": "https://github.com/user/calculator_abc123",
    "commit_sha": "a1b2c3d4e5f6...",
    "pages_url": "https://user.github.io/calculator_abc123/"
  }
}
```

**Error Responses:**
- `401` - Invalid secret
- `400` - Missing fields or invalid round
- `500` - Processing failed

## Examples

### Todo List App
```json
{
  "brief": "Todo list with add/delete/mark complete",
  "checks": [
    "Input field for new todos",
    "Add button creates items",
    "Checkbox marks complete",
    "Delete button removes items"
  ]
}
```

### Chart from CSV
```json
{
  "brief": "Display bar chart from sales data",
  "checks": [
    "Loads data.csv",
    "Shows bar chart using Chart.js",
    "Chart displays in #chart element"
  ],
  "attachments": [{
    "name": "data.csv",
    "url": "data:text/csv;base64,cHJvZHVjdCxzYWxlcw..."
  }]
}
```

### Weather Dashboard
```json
{
  "brief": "Weather app showing temperature and conditions",
  "checks": [
    "Input for city name",
    "Fetches weather data",
    "Displays temperature and icon",
    "Shows 5-day forecast"
  ]
}
```

## Features

✅ AI code generation (GPT-4o-mini)  
✅ Automatic GitHub repo creation  
✅ Auto-deploy to GitHub Pages  
✅ Professional README generation  
✅ MIT License included  
✅ Two-round system (create + update)  
✅ Exponential backoff retries  
✅ File attachment support  
✅ Error handling & validation  

## Troubleshooting

### "Invalid secret"
Check environment variable: `echo $SECRET`

### "Failed to create repository"
- Verify GitHub token has `repo` permission
- Check token isn't expired: [github.com/settings/tokens](https://github.com/settings/tokens)
- Repo might already exist (system handles this)

### "OpenAI API error"
- Verify API key: `echo $OPENAI_API_KEY`
- Check credits: [platform.openai.com/account/billing](https://platform.openai.com/account/billing)
- Wait if rate limited

### "Generated code is empty"
- Make brief more specific
- Check OpenAI API status
- Review error logs

### GitHub Pages not loading
- Wait 2-3 minutes for deployment
- Check repo Settings → Pages is enabled
- Verify index.html exists in repo

## How It Works

```
1. Validate request (secret, fields)
2. Generate HTML/CSS/JS code using GPT-4
3. Generate professional README
4. Create GitHub repository
5. Push files (index.html, README.md, LICENSE)
6. Enable GitHub Pages
7. Return repo URLs and commit SHA
8. Notify evaluation URL (if provided)
```

**Round 2** updates the existing repo with new requirements.

## Security Notes

⚠️ **CRITICAL:** The OpenAI API key in the code is exposed and should be removed immediately!

```python
# ❌ NEVER do this:
OPENAI_API_KEY = "sk-proj-..."

# ✅ Always use environment variables:
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
```

**Best Practices:**
- Never commit `.env` files
- Rotate tokens every 90 days
- Use strong passwords for SECRET
- Revoke exposed tokens immediately
- Add `.env` to `.gitignore`

```bash
# Create .gitignore
echo ".env" >> .gitignore
echo "*.key" >> .gitignore
```

## Deployment

### Local Development
```bash
python main.py
# or
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production (Railway)
```bash
npm i -g @railway/cli
railway login
railway init
railway variables set GITHUB_TOKEN=ghp_...
railway variables set OPENAI_API_KEY=sk-...
railway variables set SECRET=password
railway variables set GITHUB_USERNAME=username
railway up
```

### Docker
```bash
docker build -t llm-deploy .
docker run -p 8000:8000 \
  -e GITHUB_TOKEN=ghp_... \
  -e OPENAI_API_KEY=sk-... \
  -e SECRET=password \
  -e GITHUB_USERNAME=username \
  llm-deploy
```

## Requirements

See `requirements.txt`:
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
openai==1.3.7
requests==2.31.0
python-dotenv==1.0.0
```

## Files Generated

Each deployment creates:
- `index.html` - Main application (HTML/CSS/JS)
- `README.md` - Professional documentation
- `LICENSE` - MIT License

## Testing

```bash
# Health check
curl http://localhost:8000/

# Full test with sample task
curl -X POST http://localhost:8000/handle_task \
  -H "Content-Type: application/json" \
  -d @test_task.json

# Check created repo
open https://github.com/your_username/task_nonce

# View deployed site
open https://your_username.github.io/task_nonce/
```

## Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `GITHUB_TOKEN` | Yes | GitHub personal access token | `ghp_abc123...` |
| `GITHUB_USERNAME` | Yes | Your GitHub username | `johndoe` |
| `OPENAI_API_KEY` | Yes | OpenAI API key | `sk-proj-abc123...` |
| `SECRET` | Yes | Authentication password | `my_secure_password` |

## License

MIT License - Free to use and modify

---

**⚠️ SECURITY WARNING:** Remove the hardcoded OpenAI API key from line 9 of `main.py` before deploying!
