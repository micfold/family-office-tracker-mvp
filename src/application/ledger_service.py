import pandas as pd
import streamlit as st
from typing import List, Tuple
from uuid import UUID
from datetime import datetime

from src.domain.models.MTransaction import Transaction
from src.domain.repositories.transaction_repository import TransactionRepository
from src.application.ingestion_service import IngestionService  # New Dependency


def _get_user_id() -> UUID:
    return UUID(st.session_state["user"]["id"])


class LedgerService:
    def __init__(self, repo: TransactionRepository, ingestion_service: IngestionService):
        self.repo = repo
        self.ingestion_svc = ingestion_service

    def get_recent_transactions(self) -> pd.DataFrame:
        """Returns DF for the UI Grid."""
        return self.repo.get_as_dataframe(_get_user_id())

    def get_batch_history(self) -> pd.DataFrame:
        """Analytics on uploads."""
        df = self.get_recent_transactions()
        # FIX: Use lowercase 'batch_id'
        if df.empty or 'batch_id' not in df.columns:
            return pd.DataFrame()

        stats = df.groupby('batch_id').agg(
            Upload_Date=('date', 'max'),
            Tx_Count=('amount', 'count'),
            Total_In=('amount', lambda x: x[x > 0].sum()),
            Total_Out=('amount', lambda x: x[x < 0].sum())
        ).reset_index()

        # Rename for UI niceness (optional, or adjust UI to match)
        stats.rename(columns={'batch_id': 'Batch_ID'}, inplace=True)

        return stats.sort_values('Upload_Date', ascending=False)
    def process_uploads(self, files) -> Tuple[int, List[str]]:
        """Returns (count_processed, list_of_errors)"""
        user_id = _get_user_id()
        batch_id = f"Import_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        transactions_to_save = []
        all_errors = []

        for file in files:
            content = file.getvalue()
            txs, errors = self.ingestion_svc.process_file(file.name, content, user_id, batch_id)

            if errors:
                all_errors.extend(errors)

            transactions_to_save.extend(txs)

        if transactions_to_save:
            self.repo.save_bulk(transactions_to_save)

        return len(transactions_to_save), all_errors

    def add_manual_transaction(self, data: dict):
        # ... (Keep existing manual logic) ...
        if 'type' in data:
            data['transaction_type'] = data.pop('type')

        tx = Transaction(
            **data,
            owner=_get_user_id()
        )
        self.repo.save_bulk([tx])

    def delete_batch(self, batch_id: str):
        self.repo.delete_batch(batch_id, _get_user_id())