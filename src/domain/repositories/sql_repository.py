# src/domain/repositories/sql_repository.py
from typing import List
from uuid import UUID
import pandas as pd
from sqlmodel import Session, select, delete
from src.core.database import engine

# Models
from src.domain.models.MAsset import Asset
from src.domain.models.MTransaction import Transaction
from src.domain.models.MPortfolio import InvestmentPosition, InvestmentEvent
from src.domain.models.MLiability import Liability  # <--- NEW

# Repository Interfaces
from src.domain.repositories.asset_repository import AssetRepository
from src.domain.repositories.transaction_repository import TransactionRepository
from src.domain.repositories.portfolio_repository import PortfolioRepository
from src.domain.repositories.liability_repository import LiabilityRepository  # <--- NEW


# --- ASSET REPO ---
class SqlAssetRepository(AssetRepository):
    def get_all(self, user_id: UUID) -> List[Asset]:
        with Session(engine) as session:
            statement = select(Asset).where(Asset.owner == user_id)
            return list(session.exec(statement).all())

    def save(self, asset: Asset) -> None:
        with Session(engine) as session:
            session.merge(asset)
            session.commit()

    def delete(self, asset_id: UUID) -> None:
        with Session(engine) as session:
            statement = select(Asset).where(Asset.id == asset_id)
            obj = session.exec(statement).first()
            if obj:
                session.delete(obj)
                session.commit()

    def save_all(self, assets: List[Asset]) -> None:
        with Session(engine) as session:
            for asset in assets:
                session.merge(asset)
            session.commit()


# --- LIABILITY REPO (NEW) ---
class SqlLiabilityRepository(LiabilityRepository):
    def get_all(self, user_id: UUID) -> List[Liability]:
        with Session(engine) as session:
            statement = select(Liability).where(Liability.owner == user_id)
            return list(session.exec(statement).all())

    def save(self, liability: Liability) -> None:
        with Session(engine) as session:
            session.merge(liability)
            session.commit()

    def delete(self, liability_id: UUID) -> None:
        with Session(engine) as session:
            statement = select(Liability).where(Liability.id == liability_id)
            obj = session.exec(statement).first()
            if obj:
                session.delete(obj)
                session.commit()


# --- TRANSACTION REPO ---
class SqlTransactionRepository(TransactionRepository):
    def get_all(self, user_id: UUID) -> List[Transaction]:
        with Session(engine) as session:
            statement = select(Transaction).where(Transaction.owner == user_id).order_by(Transaction.date.desc())
            return list(session.exec(statement).all())

    def get_as_dataframe(self, user_id: UUID) -> pd.DataFrame:
        txs = self.get_all(user_id)
        if not txs: return pd.DataFrame()
        return pd.DataFrame([t.model_dump() for t in txs])

    def save_bulk(self, transactions: List[Transaction]) -> None:
        with Session(engine) as session:
            for t in transactions:
                session.add(t)
            session.commit()

    def delete_batch(self, batch_id: str, user_id: UUID) -> None:
        with Session(engine) as session:
            statement = delete(Transaction).where(Transaction.batch_id == batch_id).where(Transaction.owner == user_id)
            session.exec(statement)
            session.commit()


# --- PORTFOLIO REPO ---
class SqlPortfolioRepository(PortfolioRepository):
    def get_snapshot(self, user_id: UUID) -> List[InvestmentPosition]:
        with Session(engine) as session:
            return list(session.exec(select(InvestmentPosition).where(InvestmentPosition.owner == user_id)).all())

    def get_history(self, user_id: UUID) -> List[InvestmentEvent]:
        with Session(engine) as session:
            return list(session.exec(select(InvestmentEvent).where(InvestmentEvent.owner == user_id)).all())

    def save_snapshot_file(self, file_obj) -> None: pass

    def save_history_file(self, file_obj) -> None: pass

    def save_positions(self, positions: List[InvestmentPosition]):
        with Session(engine) as session:
            if positions:
                uid = positions[0].owner
                session.exec(delete(InvestmentPosition).where(InvestmentPosition.owner == uid))
                session.add_all(positions)
                session.commit()

    def save_events(self, events: List[InvestmentEvent]):
        with Session(engine) as session:
            session.add_all(events)
            session.commit()