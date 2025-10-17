"""
GitHub service for creating repositories and pushing files.
Uses PyGithub to interact with GitHub API.
"""
import os
import hashlib
from github import Github, GithubException
from typing import List, Dict, Tuple
import logging
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)


def generate_mit_license(owner_name=None):
    """
    Generate MIT License text with current year and owner name.
    """
    year = datetime.utcnow().year
    github_user = os.getenv("GITHUB_USER")
    owner = owner_name or github_user or "Owner"
    
    return f"""MIT License

Copyright (c) {year} {owner}

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


def create_or_update_file(repo, path: str, content: str, message: str):
    """
    Create a file or update if it already exists.
    """
    try:
        # Try to get file to see if exists
        current = repo.get_contents(path)
        sha = current.sha
        repo.update_file(path, message, content, sha)
        logger.info(f"Updated {path} in {repo.full_name}")
    except GithubException as e:
        # If 404 (not found) then create
        if e.status == 404:
            repo.create_file(path, message, content)
            logger.info(f"Created {path} in {repo.full_name}")
        else:
            # some other error
            raise


async def create_repo_and_push(task: str, files: List[Dict[str, str]]) -> Tuple[str, str, str]:
    """
    Creates a new public GitHub repository, pushes files, and enables GitHub Pages.
    If repo exists, updates files instead.
    
    Args:
        task: Task identifier
        files: List of dicts with 'path' and 'content' keys
        
    Returns:
        Tuple of (repo_url, commit_sha, pages_url)
    """
    github_token = os.getenv("GITHUB_TOKEN")
    github_user = os.getenv("GITHUB_USER")
    
    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable not set")
    if not github_user:
        raise ValueError("GITHUB_USER environment variable not set")
    
    # Initialize GitHub client
    g = Github(github_token)
    user = g.get_user()
    username = user.login
    
    # Generate repo name with short hash
    short_hash = hashlib.md5(task.encode()).hexdigest()[:8]
    repo_name = f"{task}-{short_hash}"
    
    logger.info(f"Creating/updating repository: {repo_name}")
    
    # Try to get existing repo or create new one
    try:
        repo = user.get_repo(repo_name)
        logger.info(f"Repository already exists: {repo.full_name}")
    except GithubException:
        # Create new repository
        repo = user.create_repo(
            name=repo_name,
            description=f"Automated static site for task: {task}",
            private=False,
            auto_init=False
        )
        logger.info(f"Created new repository: {repo.full_name}")
    
    # Add/update files to repository
    for file_info in files:
        path = file_info["path"]
        content = file_info["content"]
        logger.info(f"Creating/updating file: {path}")
        create_or_update_file(repo, path, content, f"Add/update {path}")
    
    # Add MIT License
    license_content = generate_mit_license(github_user)
    create_or_update_file(repo, "LICENSE", license_content, "Add MIT License")
    
    # Get the latest commit SHA
    commits = repo.get_commits()
    commit_sha = commits[0].sha
    
    # Enable GitHub Pages via REST API
    enable_github_pages(repo_name, github_user, github_token)
    
    # Build URLs
    repo_url = f"https://github.com/{username}/{repo_name}"
    pages_url = f"https://{username}.github.io/{repo_name}/"
    
    logger.info(f"Repository URL: {repo_url}")
    logger.info(f"GitHub Pages URL: {pages_url}")
    logger.info(f"Commit SHA: {commit_sha}")
    
    return repo_url, commit_sha, pages_url


def enable_github_pages(repo_name: str, username: str, token: str):
    """
    Enable GitHub Pages via REST API for the specified repository.
    """
    url = f"https://api.github.com/repos/{username}/{repo_name}/pages"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }
    data = {"source": {"branch": "main", "path": "/"}}
    
    try:
        response = httpx.post(url, headers=headers, json=data, timeout=30.0)
        if response.status_code in (201, 204):
            logger.info(f"✅ GitHub Pages enabled for {repo_name}")
            return True
        elif response.status_code == 409:
            logger.info(f"GitHub Pages already enabled for {repo_name}")
            return True
        else:
            logger.warning(f"Pages API returned: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Failed to enable GitHub Pages: {e}")
        return False