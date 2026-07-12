from typing import Any
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, Field


class GitHubRepository(BaseModel):
    name: str
    full_name: str
    html_url: str
    description: str | None = None
    language: str | None = None
    stargazers_count: int = Field(ge=0)
    forks_count: int = Field(ge=0)
    archived: bool
    fork: bool
    pushed_at: str | None = None
    has_readme: bool = False
    has_tests: bool = False
    has_ci: bool = False


class GitHubProfile(BaseModel):
    username: str
    html_url: str
    name: str | None = None
    bio: str | None = None
    public_repos: int = Field(ge=0)
    followers: int = Field(ge=0)
    repositories: list[GitHubRepository] = Field(default_factory=list)


class GitHubClient:
    def __init__(self, token: str | None = None) -> None:
        self.token = token

    @property
    def headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "snipe-career-intelligence",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def fetch_public_profile(self, username_or_url: str) -> GitHubProfile:
        username = normalize_github_username(username_or_url)
        with httpx.Client(timeout=20, trust_env=False, headers=self.headers) as client:
            user_response = client.get(f"https://api.github.com/users/{username}")
            if user_response.status_code == 404:
                raise GitHubLookupError("GitHub user not found.")
            if user_response.status_code >= 400:
                raise GitHubLookupError("GitHub profile fetch failed.")

            repos_response = client.get(
                f"https://api.github.com/users/{username}/repos",
                params={"sort": "updated", "per_page": "12", "type": "owner"},
            )
            if repos_response.status_code >= 400:
                raise GitHubLookupError("GitHub repository fetch failed.")

            user = user_response.json()
            repos = [
                _repository_from_api(client, repo)
                for repo in repos_response.json()
                if isinstance(repo, dict)
            ]
        return GitHubProfile(
            username=username,
            html_url=user["html_url"],
            name=user.get("name"),
            bio=user.get("bio"),
            public_repos=user.get("public_repos") or 0,
            followers=user.get("followers") or 0,
            repositories=repos,
        )


class GitHubLookupError(RuntimeError):
    pass


def normalize_github_username(value: str) -> str:
    cleaned = value.strip().rstrip("/")
    if not cleaned:
        raise GitHubLookupError("GitHub username is required.")
    if "github.com" in cleaned:
        parsed = urlparse(cleaned if "://" in cleaned else f"https://{cleaned}")
        parts = [part for part in parsed.path.split("/") if part]
        if not parts:
            raise GitHubLookupError("GitHub profile URL is missing a username.")
        return parts[0]
    if "/" in cleaned or " " in cleaned:
        raise GitHubLookupError("Enter a GitHub username or profile URL.")
    return cleaned.lstrip("@")


def _repository_from_api(client: httpx.Client, repo: dict[str, Any]) -> GitHubRepository:
    owner = repo.get("owner") or {}
    owner_login = owner.get("login")
    name = repo.get("name")
    full_name = repo.get("full_name")
    has_readme = _path_exists(client, owner_login, name, "README.md")
    has_ci = _path_exists(client, owner_login, name, ".github/workflows")
    has_tests = any(
        _path_exists(client, owner_login, name, path)
        for path in ("tests", "test", "__tests__", "spec")
    )
    return GitHubRepository(
        name=name,
        full_name=full_name,
        html_url=repo.get("html_url"),
        description=repo.get("description"),
        language=repo.get("language"),
        stargazers_count=repo.get("stargazers_count") or 0,
        forks_count=repo.get("forks_count") or 0,
        archived=bool(repo.get("archived")),
        fork=bool(repo.get("fork")),
        pushed_at=repo.get("pushed_at"),
        has_readme=has_readme,
        has_tests=has_tests,
        has_ci=has_ci,
    )


def _path_exists(client: httpx.Client, owner: str | None, repo: str | None, path: str) -> bool:
    if not owner or not repo:
        return False
    response = client.get(f"https://api.github.com/repos/{owner}/{repo}/contents/{path}")
    return response.status_code == 200
