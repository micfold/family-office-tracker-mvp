# src/container.py
import streamlit as st
from src.core.database import init_db

# Repositories
from src.domain.repositories.sql_repository import (
    SqlAssetRepository,
    SqlTransactionRepository,
    SqlPortfolioRepository,
    SqlLiabilityRepository
)

# Services
from src.application.asset_service import AssetService
from src.application.ledger_service import LedgerService
from src.application.portfolio_service import PortfolioService
from src.application.summary_service import SummaryService
from src.application.auth_service import AuthService
from src.application.liability_service import LiabilityService


@st.cache_resource
def get_container():
    init_db()

    # Repos
    asset_repo = SqlAssetRepository()
    ledger_repo = SqlTransactionRepository()
    portfolio_repo = SqlPortfolioRepository()
    liability_repo = SqlLiabilityRepository()

    # Services
    auth_service = AuthService()
    asset_service = AssetService(asset_repo)
    ledger_service = LedgerService(ledger_repo)
    portfolio_service = PortfolioService(portfolio_repo)
    liability_service = LiabilityService(liability_repo)

    # Summary depends on all
    summary_service = SummaryService(
        asset_service,
        ledger_service,
        portfolio_service,
        liability_service
    )

    return {
        "auth": auth_service,
        "asset": asset_service,
        "ledger": ledger_service,
        "portfolio": portfolio_service,
        "liability": liability_service,
        "summary": summary_service
    }