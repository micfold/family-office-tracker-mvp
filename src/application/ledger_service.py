import pandas as pd
import streamlit as st
from typing import List, Tuple
from uuid import UUID
from datetime import datetime
from src.application.ingestion_service import IngestionService
from src.domain.repositories.transaction_repository import TransactionRepository
from src.domain.models.MTransaction import Transaction
from src.views.models.transaction_view_model import TransactionViewModel


def _get_user_id() -> UUID:
    return UUID(st.session_state["user"]["id"])


class LedgerService:
    def __init__(self, repo: TransactionRepository, ingestion_service: IngestionService):
        self.repo = repo
        self.ingestion_svc = ingestion_service

    def get_recent_transactions(self) -> pd.DataFrame:
        transactions = self.repo.get_all(_get_user_id())
        view_models = [self._create_view_model(tx) for tx in transactions]
        return pd.DataFrame([vm.__dict__ for vm in view_models])

    def get_batch_history(self) -> pd.DataFrame:
        df = self.get_recent_transactions()
        if df.empty or 'batch_id' not in df.columns:
            return pd.DataFrame()

        stats = df.groupby('batch_id').agg(
            Upload_Date=('date', 'max'),
            Tx_Count=('amount', 'count'),
            Total_In=('amount', lambda x: x[x > 0].sum()),
            Total_Out=('amount', lambda x: x[x < 0].sum())
        ).reset_index()

        stats.rename(columns={'batch_id': 'Batch_ID'}, inplace=True)
        return stats.sort_values('Upload_Date', ascending=False)

    def process_uploads(self, files) -> Tuple[int, List[str], int]:
        user_id = _get_user_id()
        batch_id = f"Import_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Fetch Existing Transactions for Deduplication
        existing_txs = self.repo.get_all(user_id)
        existing_signatures = {
            (t.date.strftime('%Y-%m-%d'), t.amount, t.description) for t in existing_txs
        }

        transactions_to_save = []
        all_errors = []
        duplicates_count = 0

        for file in files:
            newly_parsed_txs, errors = self.ingestion_svc.process_file(
                filename=file.name,
                content=file.getvalue(),
                user_id=user_id,
                batch_id=batch_id
            )
            all_errors.extend(errors)

            for tx in newly_parsed_txs:
                # Deduplication Check
                signature = (tx.date.strftime('%Y-%m-%d'), tx.amount, tx.description)
                if signature in existing_signatures:
                    duplicates_count += 1
                    continue

                transactions_to_save.append(tx)
                existing_signatures.add(signature)

        if transactions_to_save:
            self.repo.save_bulk(transactions_to_save)

        return len(transactions_to_save), all_errors, duplicates_count

    def _create_view_model(self, tx: Transaction) -> TransactionViewModel:
        """
        Creates a view model from a transaction.
        """
        is_internal = tx.category == "Internal Transfer"

        return TransactionViewModel(
            id=str(tx.id),
            date=tx.date,
            description=tx.description,
            amount=tx.amount,
            category=tx.category or "Uncategorized",
            account=tx.account,
            is_internal=is_internal,
            is_duplicate=False,
            owner=None,
            raw_description=tx.description,
            suggested_category=None,
            confidence=None,
            notes=tx.notes,
            tags=tx.tags or []
        )

    def delete_batch(self, batch_id: str):
        self.repo.delete_batch(batch_id, _get_user_id())

    def add_manual_transaction(self, data: dict):
        # Keep existing manual entry logic
        if 'type' in data: data['transaction_type'] = data.pop('type')
        tx = Transaction(**data, owner=_get_user_id())
        self.repo.save_bulk([tx])