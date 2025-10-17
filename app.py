"""
Main FastAPI application for the automated student responder.
Receives webhook payloads, generates static sites via LLM, and publishes to GitHub Pages.
"""
import os
import asyncio
from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List, Dict
from dotenv import load_dotenv
import logging

from github_service import create_repo_and_push
from llm_service import generate_static_site
from evaluation_service import submit_evaluation

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AutoApp - Automated Student Responder")

# Pydantic model for incoming payload
class WebhookPayload(BaseModel):
    email: str
    secret: str
    task: str
    round: int
    nonce: str
    brief: str
    evaluation_url: str
    attachments: Optional[List[Dict]] = None


async def process_assignment(payload: WebhookPayload):
    """
    Background task that:
    1. Generates a static site using LLM
    2. Creates GitHub repo and pushes files
    3. Submits evaluation back to evaluation_url
    """
    try:
        logger.info(f"Starting background processing for task: {payload.task}")
        
        # Step 1: Generate static site files using LLM
        logger.info("Generating static site with LLM...")
        files = await generate_static_site(payload.brief)
        
        # Step 2: Create GitHub repo and push files
        logger.info("Creating GitHub repo and pushing files...")
        repo_url, commit_sha, pages_url = await create_repo_and_push(
            task=payload.task,
            files=files
        )
        
        # Step 3: Submit evaluation
        logger.info("Submitting evaluation...")
        evaluation_data = {
            "email": payload.email,
            "task": payload.task,
            "round": payload.round,
            "nonce": payload.nonce,
            "repo_url": repo_url,
            "commit_sha": commit_sha,
            "pages_url": pages_url
        }
        
        await submit_evaluation(payload.evaluation_url, evaluation_data)
        logger.info(f"Successfully completed processing for task: {payload.task}")
        
    except Exception as e:
        logger.error(f"Error processing assignment: {str(e)}", exc_info=True)


@app.post("/api-endpoint")
async def webhook_endpoint(payload: WebhookPayload, background_tasks: BackgroundTasks):
    """
    Main webhook endpoint that receives assignment requests.
    Validates secret immediately and processes assignment in background.
    """
    # Step 1: Validate secret immediately
    expected_secret = os.getenv("SECRET_KEY")
    if not expected_secret:
        logger.error("SECRET_KEY not configured in environment")
        raise HTTPException(status_code=500, detail="Server configuration error")
    
    if payload.secret != expected_secret:
        logger.warning(f"Invalid secret attempt for email: {payload.email}")
        return {"status": "error", "reason": "invalid secret"}
    
    # Step 2: Add background task and return immediately
    background_tasks.add_task(process_assignment, payload)
    logger.info(f"Accepted request for task: {payload.task}, email: {payload.email}")
    
    return {"status": "ok"}


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "AutoApp - Automated Student Responder",
        "status": "running",
        "llm_provider": os.getenv("LLM_PROVIDER", "openai")
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "github_token_set": bool(os.getenv("GITHUB_TOKEN")),
        "secret_key_set": bool(os.getenv("SECRET_KEY")),
        "llm_provider": os.getenv("LLM_PROVIDER", "openai"),
        "llm_api_key_set": bool(
            os.getenv("OPENAI_API_KEY") if os.getenv("LLM_PROVIDER", "openai") == "openai" 
            else os.getenv("ANTHROPIC_API_KEY")
        )
    }