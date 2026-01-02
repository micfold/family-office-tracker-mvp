# src/container.py
import streamlit as st
from src.core.database import init_db

# Repositories
from src.domain.repositories.sql_repository import (
    SqlAssetRepository,
    SqlTransactionRepository,
    SqlPortfolioRepository,
    SqlLiabilityRepository,
    SqlTaxLotRepository
)

# Services
from src.application.asset_service import AssetService
from src.application.ledger_service import LedgerService
from src.application.portfolio_service import PortfolioService
from src.application.summary_service import SummaryService
from src.application.auth_service import AuthService
from src.application.liability_service import LiabilityService

# --- NEW IMPORTS ---
from src.application.rule_service import RuleService
from src.application.ingestion_service import IngestionService
from src.views.models.portfolio_vm import PortfolioViewModel


@st.cache_resource
def get_container():
    init_db()

    # 1. Repos
    asset_repo = SqlAssetRepository()
    ledger_repo = SqlTransactionRepository()
    portfolio_repo = SqlPortfolioRepository()
    liability_repo = SqlLiabilityRepository()
    tax_repo = SqlTaxLotRepository()

    # 2. Base Services
    auth_service = AuthService()
    rule_service = RuleService()  # New

    # 3. Ingestion Service (Depends on RuleService)
    ingestion_service = IngestionService(rule_service)

    # 4. Domain Services
    asset_service = AssetService(asset_repo)

    # Ledger Service NOW depends on IngestionService
    ledger_service = LedgerService(ledger_repo, ingestion_service)

    portfolio_service = PortfolioService(portfolio_repo)
    liability_service = LiabilityService(liability_repo)

    # 5. Summary (Aggregator)
    summary_service = SummaryService(
        asset_service,
        ledger_service,
        portfolio_service,
        liability_service
    )

    # 6. ViewModels
    portfolio_vm = PortfolioViewModel(portfolio_service)

    return {
        "auth": auth_service,
        "asset": asset_service,
        "ledger": ledger_service,
        "portfolio": portfolio_service,
        "liability": liability_service,
        "summary": summary_service,
        "rule": rule_service,
        "ingestion": ingestion_service,
        "portfolio_vm": portfolio_vm
    }