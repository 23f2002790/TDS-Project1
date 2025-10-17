# AutoApp - Automated Student Responder

A FastAPI application that automatically generates static websites using LLM (GPT/Claude), deploys them to GitHub Pages, and reports back to an evaluation endpoint.

## 🎯 Purpose

This service receives assignment requests via webhook, uses an LLM to generate a complete static website based on the brief, creates a GitHub repository, pushes the code, enables GitHub Pages, and submits the results to an evaluation endpoint.

## 📋 Features

- **Single API Endpoint**: POST to `/api-endpoint` with assignment details
- **Secret Validation**: Instant authentication check
- **Background Processing**: Async task handling for long-running operations
- **LLM Integration**: Uses LangChain to support OpenAI or Anthropic
- **GitHub Automation**: Creates repos, pushes code, enables Pages
- **Retry Logic**: Exponential backoff for evaluation submission
- **Health Checks**: Monitor service status and configuration

## 🚀 Setup Instructions

### 1. Clone the Repository
```bash
git clone [<your-repo-url>](https://github.com/23f2002790/TDS-Project1)
cd autoapp
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials:

- **SECRET_KEY**: Your chosen secret for webhook authentication
- **GITHUB_TOKEN**: Personal access token from [GitHub Settings](https://github.com/settings/tokens)
  - Required scopes: `repo`, `admin:repo_hook`
- **LLM_PROVIDER**: Set to `"openai"` or `"anthropic"`
- **OPENAI_API_KEY**: Your OpenAI API key (if using OpenAI)
- **ANTHROPIC_API_KEY**: Your Anthropic API key (if using Claude)

### 4. Run Locally
```bash
uvicorn app:app --reload
```

The server will start at `http://localhost:8000`

Visit `http://localhost:8000` to see the health check.

## 🧪 Testing Locally

### Using the Test Script

1. **Get a Webhook URL**:
   - Visit [webhook.site](https://webhook.site/)
   - Copy your unique URL (e.g., `https://webhook.site/abc-123-def`)

2. **Update test_api.py**:
```python
   WEBHOOK_URL = "https://webhook.site/your-unique-id-here"
```

3. **Run the test**:
```bash
   python test_api.py
```

4. **Check Results**:
   - Console shows immediate API response
   - Server logs show background processing
   - Webhook.site shows the evaluation submission
   - GitHub shows new repository created

### Manual Testing with curl
```bash
curl -X POST http://localhost:8000/api-endpoint \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "secret": "your-secret-key-here",
    "task": "landing-page",
    "round": 1,
    "nonce": "test-123",
    "brief": "Create a modern landing page with hero section",
    "evaluation_url": "https://webhook.site/your-id",
    "attachments": []
  }'
```

## 🌐 Deploying to Vercel

### 1. Install Vercel CLI
```bash
npm i -g vercel
```

### 2. Deploy
```bash
vercel
```

### 3. Set Environment Variables

In the Vercel dashboard or via CLI:
```bash
vercel env add SECRET_KEY
vercel env add GITHUB_TOKEN
vercel env add LLM_PROVIDER
vercel env add OPENAI_API_KEY
vercel env add ANTHROPIC_API_KEY
```

**Note**: Vercel has limitations with long-running background tasks. For production, consider using:
- Railway
- Render
- Digital Ocean App Platform
- AWS Lambda with SQS

## 🔄 Switching LLM Providers

Change the `LLM_PROVIDER` environment variable:

### Use OpenAI (GPT-4)
```bash
LLM_PROVIDER=openai
```
Requires `OPENAI_API_KEY` to be set.

### Use Anthropic (Claude)
```bash
LLM_PROVIDER=anthropic
```
Requires `ANTHROPIC_API_KEY` to be set.

The application will automatically use the appropriate LangChain wrapper.

## 📁 Project Structure
```
autoapp/
├── app.py                  # Main FastAPI application
├── github_service.py       # GitHub repo creation and pushing
├── llm_service.py          # LangChain LLM wrapper
├── evaluation_service.py   # Evaluation endpoint submission
├── test_api.py             # Local testing script
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables template
├── vercel.json             # Vercel deployment config
└── README.md               # This file
```

## 🔐 Security Best Practices

### ⚠️ NEVER Commit Secrets

**Critical**: Do NOT commit your `.env` file or any files containing secrets!

The `.env` file is gitignored by default. Always:
- Store secrets in environment variables
- Use `.env` locally only
- Use Vercel/hosting platform's secret management for production

### Scanning for Leaked Secrets

After setup, scan for potential leaks:

**Using gitleaks** (recommended):
```bash
# Install gitleaks
brew install gitleaks  # macOS
# or download from https://github.com/gitleaks/gitleaks

# Scan repository
gitleaks detect --source . --verbose
```

**Using BFG Repo-Cleaner** (if secrets were committed):
```bash
# Install BFG
brew install bfg  # macOS

# Remove secrets from history
bfg --replace-text passwords.txt
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

### GitHub Token Security

Your `GITHUB_TOKEN`:
- Should have minimal necessary scopes
- Can be revoked at any time from [GitHub Settings](https://github.com/settings/tokens)
- Should be rotated regularly
- Never share or commit to version control

## 🐛 Troubleshooting

### "SECRET_KEY not configured"
- Ensure `.env` file exists and has `SECRET_KEY` set
- Restart the server after changing `.env`

### "GITHUB_TOKEN not set"
- Get a token from [GitHub Settings](https://github.com/settings/tokens)
- Add to `.env`: `GITHUB_TOKEN=ghp_your_token`
- Ensure scopes: `repo`, `admin:repo_hook`

### "OPENAI_API_KEY not set"
- Get API key from [OpenAI Platform](https://platform.openai.com/api-keys)
- Add to `.env`: `OPENAI_API_KEY=sk-...`

### LLM not generating valid JSON
- The code includes fallback to generate a minimal site
- Check logs for LLM response details
- Try switching providers (`LLM_PROVIDER=anthropic`)

### GitHub Pages not enabling
- GitHub Pages API may require manual activation
- Go to repo Settings → Pages → Enable from main branch
- Wait 1-2 minutes for site to deploy

### Evaluation endpoint not receiving data
- Check webhook.site URL is correct
- View server logs for retry attempts
- Verify network connectivity

### Background task not running
- Check server logs with `--log-level debug`
- Ensure uvicorn isn't timing out
- Consider using Celery for production

## 📊 API Reference

### POST `/api-endpoint`

Receives assignment request and processes in background.

**Request Body**:
```json
{
  "email": "student@example.com",
  "secret": "your-secret-key",
  "task": "task-identifier",
  "round": 1,
  "nonce": "unique-nonce",
  "brief": "Create a landing page with...",
  "evaluation_url": "https://eval.example.com/submit",
  "attachments": []
}
```

**Success Response** (200):
```json
{
  "status": "ok"
}
```

**Error Response** (401):
```json
{
  "status": "error",
  "reason": "invalid secret"
}
```

### GET `/`

Health check endpoint.

**Response**:
```json
{
  "service": "AutoApp - Automated Student Responder",
  "status": "running",
  "llm_provider": "openai"
}
```

### GET `/health`

Detailed health check with configuration status.

## 📝 Example Workflow

1. **Webhook arrives** → Secret validated instantly → Returns `{"status": "ok"}`
2. **Background task starts** → LLM generates HTML/CSS/JS files
3. **GitHub repo created** → Files pushed → Pages enabled
4. **Evaluation submitted** → Results posted to evaluation_url with retry logic

## ✅ Local Testing Checklist

Before deploying, verify:

- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Create `.env` from `.env.example`
- [ ] Add all required API keys and tokens
- [ ] Start server: `uvicorn app:app --reload`
- [ ] Visit `http://localhost:8000` - should see health check
- [ ] Update `WEBHOOK_URL` in `test_api.py`
- [ ] Run test: `python test_api.py` - should return `{"status": "ok"}`
- [ ] Check server logs - should see "Starting background processing"
- [ ] Check webhook.site - should receive evaluation data
- [ ] Check GitHub - should see new repository created
- [ ] Visit Pages URL - should see generated site

## 📚 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangChain Documentation](https://python.langchain.com/)
- [PyGithub Documentation](https://pygithub.readthedocs.io/)
- [GitHub Pages Guide](https://docs.github.com/en/pages)
- [Webhook.site](https://webhook.site/) - For testing webhooks

## 🤝 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review server logs for detailed error messages
3. Verify all environment variables are set correctly
4. Ensure API keys have proper permissions

---

Built with FastAPI, LangChain, and GitHub API • Keep your secrets safe! 🔐
