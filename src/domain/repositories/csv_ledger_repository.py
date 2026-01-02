import logging

import pandas as pd
from typing import List
from uuid import UUID
from pathlib import Path
from src.application.auth_service import AuthService
from src.domain.repositories.transaction_repository import TransactionRepository
from src.domain.models.MTransaction import Transaction
import re
from datetime import datetime

# Precompile regex for normalization
_WS_RE = re.compile(r"[\s\-]+")

# Module logger
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    # Create mapping for known aliases to canonical names
    alias_map = {
        'date': 'date',
        'transaction_date': 'date',
        'txn_date': 'date',
        'description': 'description',
        'desc': 'description',
        'amount': 'amount',
        'amt': 'amount',
        'currency': 'currency',
        'type': 'type',
        'transaction_type': 'type',
        'category': 'category',
        'source_account': 'source_account',
        'source account': 'source_account',
        'target_account': 'target_account',
        'target account': 'target_account',
        'batch_id': 'batch_id',
        'batch id': 'batch_id',
        'id': 'id'
    }

    new_cols = {}
    for col in df.columns:
        key = col.strip().lower()
        # use precompiled regex to satisfy type-checkers
        key = _WS_RE.sub('_', key)
        canon = alias_map.get(key, key)
        new_cols[col] = canon

    df = df.rename(columns=new_cols)

    # Parse date if present
    if 'date' in df.columns:
        try:
            df['date'] = pd.to_datetime(df['date'])
        except Exception:
            # fallback: try manual parsing row-wise
            def _try_parse(v):
                if pd.isna(v):
                    return pd.NaT
                if isinstance(v, (pd.Timestamp, datetime)):
                    return pd.to_datetime(v)
                s = str(v).strip()
                for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"):
                    try:
                        return pd.to_datetime(datetime.strptime(s, fmt))
                    except Exception:
                        continue
                # last resort
                try:
                    return pd.to_datetime(s)
                except Exception:
                    return pd.NaT

            df['date'] = df['date'].apply(_try_parse)

    return df


class CsvTransactionRepository(TransactionRepository):
    def __init__(self):
        self.auth = AuthService()
        self.filename = "ledger.csv"

    def _get_path(self) -> Path:
        return self.auth.get_file_path(self.filename)

    def get_as_dataframe(self, user_id: UUID) -> pd.DataFrame:
        path = self._get_path()
        if not path.exists():
            return pd.DataFrame()

        df = pd.read_csv(path)
        df = _normalize_columns(df)

        # Filter by Owner (if we had owner column in CSV, currently implicit by file location)
        # In this architecture, file location implies owner, so we just return the df.
        return df

    def get_all(self, user_id: UUID) -> List[Transaction]:
        df = self.get_as_dataframe(user_id)
        if df.empty:
            return []

        # Convert DataFrame rows to Transaction Objects
        transactions = []
        for idx, row in df.iterrows():
            try:
                # Map CSV columns to Model fields (use canonical names)
                t = Transaction(
                    id=UUID(row.get('id')) if pd.notna(row.get('id')) else None,  # Handle legacy missing IDs
                    date=row['date'],
                    description=row.get('description'),
                    amount=row.get('amount'),
                    currency=row.get('currency', 'CZK'),
                    category=row.get('category', 'Uncategorized'),
                    transaction_type=row.get('type', 'Expense'),
                    source_account=row.get('source_account'),
                    target_account=row.get('target_account'),
                    batch_id=str(row.get('batch_id', 'Legacy')),
                    owner=user_id  # Injected context
                )
                transactions.append(t)
            except Exception as exc:
                try:
                    preview = {k: (str(v)[:100] + '...' if isinstance(v, str) and len(v) > 100 else v) for k, v in row.to_dict().items()}
                except Exception:
                    preview = '<unavailable>'
                logger.exception("Skipping malformed transaction at index %s; preview=%s", idx, preview, exc_info=exc)
                continue
        return transactions

    def save_bulk(self, transactions: List[Transaction]) -> None:
        path = self._get_path()

        # 1. Convert new objects to DataFrame
        new_data = [t.model_dump(mode='json') for t in transactions]
        new_df = pd.DataFrame(new_data)
        new_df = _normalize_columns(new_df)

        # 2. Load existing
        if path.exists():
            existing_df = pd.read_csv(path)
            existing_df = _normalize_columns(existing_df)
            # Combine
            combined = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            combined = new_df

        combined.to_csv(path, index=False)

    def delete_batch(self, batch_id: str, user_id: UUID) -> None:
        path = self._get_path()
        if not path.exists():
            return

        df = pd.read_csv(path)
        df = _normalize_columns(df)
        if 'batch_id' in df.columns:
            df = df[df['batch_id'] != batch_id]
            df.to_csv(path, index=False)
