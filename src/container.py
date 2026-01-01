# src/container.py
import streamlit as st
from src.core.database import init_db

# Repositories
from src.domain.repositories.sql_repository import (
    SqlAssetRepository,
    SqlTransactionRepository,
    SqlPortfolioRepository
)

# Services
from src.application.asset_service import AssetService
from src.application.ledger_service import LedgerService
from src.application.portfolio_service import PortfolioService
from src.application.summary_service import SummaryService  # We will create this next
from services.auth import AuthService


# Singleton Cache: Ensures we don't reconnect to DB on every rerun
@st.cache_resource
def get_container():
    """
    Initializes the application core.
    Returns a dictionary or object with all services ready to use.
    """
    # 1. Init Database (Idempotent)
    init_db()

    # 2. Init Repositories
    asset_repo = SqlAssetRepository()
    ledger_repo = SqlTransactionRepository()
    portfolio_repo = SqlPortfolioRepository()

    # 3. Init Services
    # We inject the repositories into the services here.
    auth_service = AuthService()
    asset_service = AssetService(asset_repo)
    ledger_service = LedgerService(ledger_repo)
    portfolio_service = PortfolioService(portfolio_repo)

    # Summary Service needs access to other services to aggregate data
    summary_service = SummaryService(asset_service, ledger_service, portfolio_service)

    return {
        "auth": auth_service,
        "asset": asset_service,
        "ledger": ledger_service,
        "portfolio": portfolio_service,
        "summary": summary_service
    }