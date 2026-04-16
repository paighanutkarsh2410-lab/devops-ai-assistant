"""Database optimization API endpoints."""
import sys
import os
from fastapi import APIRouter, Depends
from utils.auth import get_current_user

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "database", "optimization"))

router = APIRouter(prefix="/db", tags=["database"])


@router.get("/analysis")
def db_analysis(current_user=Depends(get_current_user)):
    """Run database performance analysis."""
    from analyze_queries import DatabaseAnalyzer
    analyzer = DatabaseAnalyzer()
    return analyzer.run_full_analysis()
