from collections import Counter

from pydantic import BaseModel, Field

from app.integrations.github import GitHubProfile
from app.profile.schemas import EvidenceCandidate

ANALYSIS_VERSION = "github-profile-analysis-v1"


class GitHubAnalysisResult(BaseModel):
    analysis_version: str = ANALYSIS_VERSION
    username: str
    repository_count: int = Field(ge=0)
    analyzed_repository_count: int = Field(ge=0)
    primary_languages: list[str] = Field(default_factory=list)
    readme_repository_count: int = Field(ge=0)
    test_signal_count: int = Field(ge=0)
    ci_signal_count: int = Field(ge=0)
    recent_activity_count: int = Field(ge=0)
    notable_repositories: list[str] = Field(default_factory=list)
    signals: dict[str, bool] = Field(default_factory=dict)


def analyze_github_profile(profile: GitHubProfile) -> GitHubAnalysisResult:
    repositories = [repo for repo in profile.repositories if not repo.fork and not repo.archived]
    languages = Counter(repo.language for repo in repositories if repo.language)
    notable = sorted(
        repositories,
        key=lambda repo: (
            repo.stargazers_count + repo.forks_count,
            int(repo.has_readme),
            int(repo.has_tests),
            repo.pushed_at or "",
        ),
        reverse=True,
    )[:5]
    readme_count = sum(1 for repo in repositories if repo.has_readme)
    test_count = sum(1 for repo in repositories if repo.has_tests)
    ci_count = sum(1 for repo in repositories if repo.has_ci)
    recent_count = sum(1 for repo in repositories if repo.pushed_at)
    return GitHubAnalysisResult(
        username=profile.username,
        repository_count=profile.public_repos,
        analyzed_repository_count=len(repositories),
        primary_languages=[language for language, _ in languages.most_common(5)],
        readme_repository_count=readme_count,
        test_signal_count=test_count,
        ci_signal_count=ci_count,
        recent_activity_count=recent_count,
        notable_repositories=[repo.full_name for repo in notable],
        signals={
            "has_public_repositories": bool(repositories),
            "has_readme_signals": readme_count > 0,
            "has_testing_signals": test_count > 0,
            "has_ci_signals": ci_count > 0,
            "has_language_signals": bool(languages),
        },
    )


def github_evidence(
    *,
    profile_id: str,
    source_id: str | None,
    analysis: GitHubAnalysisResult,
) -> list[EvidenceCandidate]:
    evidence: list[EvidenceCandidate] = []
    for language in analysis.primary_languages:
        evidence.append(
            EvidenceCandidate(
                fact_type="github_language",
                fact_key=language.lower(),
                excerpt=f"Public GitHub repositories use {language}.",
                normalized_value=language,
                confidence=0.75,
                location_json={
                    "source": "github",
                    "profile_id": profile_id,
                    "source_id": source_id,
                },
            )
        )
    for repo in analysis.notable_repositories:
        evidence.append(
            EvidenceCandidate(
                fact_type="github_repository",
                fact_key=repo.lower(),
                excerpt=f"Public repository: {repo}",
                normalized_value=repo,
                confidence=0.7,
                location_json={
                    "source": "github",
                    "profile_id": profile_id,
                    "source_id": source_id,
                },
            )
        )
    return evidence
