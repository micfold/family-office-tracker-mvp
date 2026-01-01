import pandas as pd
import streamlit as st
from typing import List, Tuple
from uuid import UUID
from datetime import datetime

from src.domain.models.MTransaction import Transaction
from src.domain.enums import TransactionType, ExpenseCategory, IncomeCategory
from src.domain.repositories.transaction_repository import TransactionRepository
from src.core.parsers import process_uploaded_files
# Using the config for rules mapping, or move to domain
from config import GLOBAL_RULES, CATEGORY_TYPE_MAP


def _get_user_id() -> UUID:
    return UUID(st.session_state["user"]["id"])


class LedgerService:
    def __init__(self, repo: TransactionRepository):
        self.repo = repo

    def get_recent_transactions(self) -> pd.DataFrame:
        """Returns DF for the UI Grid."""
        return self.repo.get_as_dataframe(_get_user_id())

    def get_batch_history(self) -> pd.DataFrame:
        """Analytics on uploads."""
        df = self.get_recent_transactions()
        if df.empty or 'Batch_ID' not in df.columns:
            return pd.DataFrame()

        stats = df.groupby('Batch_ID').agg(
            Upload_Date=('Date', 'max'),
            Tx_Count=('Amount', 'count'),
            Total_In=('Amount', lambda x: x[x > 0].sum()),
            Total_Out=('Amount', lambda x: x[x < 0].sum())
        ).reset_index()
        return stats.sort_values('Upload_Date', ascending=False)

    def process_uploads(self, files) -> Tuple[int, int]:
        """
        Orchestrates: Parse -> Categorize -> Save
        Returns: (processed_count, duplicates_skipped) - logic handled by repo mostly
        """
        user_id = _get_user_id()
        batch_id = f"Import_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        transactions_to_save = []

        # 1. Parse
        for filename, df, error in process_uploaded_files(files):
            if df is not None and not df.empty:
                # 2. Categorize & Convert to Objects
                for _, row in df.iterrows():
                    cat, t_type = self._apply_rules(row['Description'], row['Amount'])

                    tx = Transaction(
                        date=row['Date'],
                        description=row['Description'],
                        amount=row['Amount'],
                        currency='CZK',
                        category=cat,
                        type=t_type,
                        source_account=row.get('Source_Account'),
                        target_account=row.get('Target_Account'),
                        batch_id=batch_id,
                        owner=user_id
                    )
                    transactions_to_save.append(tx)

        if not transactions_to_save:
            return 0, 0

        # 3. Save
        # Note: We rely on Repo deduplication for the "duplicates_skipped" count,
        # which is harder to calculate with this clean architecture split
        # without querying first. For MVP, we just save.
        self.repo.save_bulk(transactions_to_save)

        return len(transactions_to_save), 0

    def add_manual_transaction(self, data: dict):
        tx = Transaction(
            **data,
            owner=_get_user_id()
        )
        self.repo.save_bulk([tx])

    def delete_batch(self, batch_id: str):
        self.repo.delete_batch(batch_id, _get_user_id())

    def _apply_rules(self, description: str, amount: float) -> Tuple[str, str]:
        """Categorization Engine."""
        desc_lower = str(description).lower()

        # 1. Pattern Matching
        for rule in GLOBAL_RULES:
            if rule['pattern'].lower() in desc_lower:
                # Direction check
                direction = rule.get('direction')
                if direction == 'positive' and amount < 0: continue
                if direction == 'negative' and amount > 0: continue

                return rule['category'], rule['type']

        # 2. Default
        t_type = TransactionType.EXPENSE if amount < 0 else TransactionType.INCOME
        return "Uncategorized", t_type