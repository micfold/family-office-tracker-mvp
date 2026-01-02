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
from src.application.rule_service import RuleService
from src.application.ingestion_service import IngestionService

# ViewModels
from src.views.models.portfolio_vm import PortfolioViewModel


def get_container():
    if "container" not in st.session_state:
        init_db()

        # Repos
        asset_repo = SqlAssetRepository()
        ledger_repo = SqlTransactionRepository()
        portfolio_repo = SqlPortfolioRepository()
        liability_repo = SqlLiabilityRepository()
        # TODO: TaxLot Repo not used yet
        tax_repo = SqlTaxLotRepository()

        # 2. Base Services
        auth_service = AuthService()
        rule_service = RuleService()
        asset_service = AssetService(asset_repo)
        ingestion_service = IngestionService(rule_service, asset_service)
        ledger_service = LedgerService(ledger_repo, ingestion_service)
        portfolio_service = PortfolioService(portfolio_repo)
        liability_service = LiabilityService(liability_repo)

        # Summary (Aggregator)
        summary_service = SummaryService(
            asset_service,
            ledger_service,
            portfolio_service,
            liability_service
        )

        # ViewModels
        portfolio_vm = PortfolioViewModel(portfolio_service)

        st.session_state["container"] = {
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

    return st.session_state["container"]
