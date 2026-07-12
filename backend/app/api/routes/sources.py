from fastapi import APIRouter

from app.api.routes.source_github import router as github_router
from app.api.routes.source_linkedin import router as linkedin_router
from app.api.routes.source_portfolio import router as portfolio_router
from app.api.routes.source_resume import router as resume_router

router = APIRouter(prefix="/profiles/{profile_id}/sources", tags=["sources"])
router.include_router(resume_router)
router.include_router(github_router)
router.include_router(portfolio_router)
router.include_router(linkedin_router)
