"""
GitHub service for creating repositories and pushing files.
Uses GitPython for local commits and the GitHub REST API for repo creation.
"""

import os
import hashlib
import tempfile
import logging
from typing import List, Dict, Tuple
from git import Repo
import requests

logger = logging.getLogger(__name__)

async def create_repo_and_push(task: str, files: List[Dict[str, str]]) -> Tuple[str, str, str]:
    """
    Creates a new public GitHub repository, pushes files using GitPython,
    and enables GitHub Pages.

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

    # Generate repo name
    short_hash = hashlib.md5(task.encode()).hexdigest()[:8]
    repo_name = f"{task}-{short_hash}"
    logger.info(f"Creating repository: {repo_name}")

    # 1️⃣ Create repo on GitHub using REST API
    response = requests.post(
        "https://api.github.com/user/repos",
        headers={
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github+json"
        },
        json={"name": repo_name, "private": False, "auto_init": False}
    )

    if response.status_code not in (200, 201):
        raise RuntimeError(f"Failed to create repo: {response.text}")

    repo_data = response.json()
    repo_url = repo_data["html_url"]
    clone_url = f"https://{github_user}:{github_token}@github.com/{github_user}/{repo_name}.git"

    # 2️⃣ Create local repo and push files
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Repo.init(tmpdir)
        for file_info in files:
            path = os.path.join(tmpdir, file_info["path"])
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(file_info["content"])
            repo.index.add([path])

        repo.index.commit("Initial commit")

        origin = repo.create_remote("origin", clone_url)
        origin.push(refspec="HEAD:refs/heads/main")

        commit_sha = repo.head.commit.hexsha

    # 3️⃣ Enable GitHub Pages
    enable_github_pages(f"{github_user}/{repo_name}", github_token)

    # 4️⃣ URLs
    pages_url = f"https://{github_user}.github.io/{repo_name}/"
    logger.info(f"Repository created: {repo_url}")
    logger.info(f"GitHub Pages URL: {pages_url}")

    return repo_url, commit_sha, pages_url


def enable_github_pages(repo_full_name: str, token: str):
    """
    Enables GitHub Pages for the given repository using the REST API.
    """
    url = f"https://api.github.com/repos/{repo_full_name}/pages"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }
    payload = {"source": {"branch": "main", "path": "/"}}

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code not in (201, 204):
        logger.warning(f"Failed to enable GitHub Pages: {response.text}")
    else:
        logger.info("GitHub Pages enabled successfully")
