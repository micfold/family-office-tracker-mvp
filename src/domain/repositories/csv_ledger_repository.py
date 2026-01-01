import pandas as pd
from typing import List
from uuid import UUID
from pathlib import Path
from src.application.auth_service import AuthService
from src.domain.repositories.transaction_repository import TransactionRepository
from src.domain.models.MTransaction import Transaction


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
        df['Date'] = pd.to_datetime(df['Date'])

        # Filter by Owner (if we had owner column in CSV, currently implicit by file location)
        # In this architecture, file location implies owner, so we just return the df.
        return df

    def get_all(self, user_id: UUID) -> List[Transaction]:
        df = self.get_as_dataframe(user_id)
        if df.empty:
            return []

        # Convert DataFrame rows to Transaction Objects
        transactions = []
        for _, row in df.iterrows():
            try:
                # Map CSV columns to Model fields
                t = Transaction(
                    id=UUID(row.get('id')) if pd.notna(row.get('id')) else None,  # Handle legacy missing IDs
                    date=row['Date'],
                    description=row['Description'],
                    amount=row['Amount'],
                    currency=row.get('Currency', 'CZK'),
                    category=row.get('Category', 'Uncategorized'),
                    transaction_type=row.get('Type', 'Expense'),
                    source_account=row.get('Source_Account'),
                    target_account=row.get('Target_Account'),
                    batch_id=str(row.get('Batch_ID', 'Legacy')),
                    owner=user_id  # Injected context
                )
                transactions.append(t)
            except Exception as e:
                # Skip malformed rows or handle gracefully
                continue
        return transactions

    def save_bulk(self, transactions: List[Transaction]) -> None:
        path = self._get_path()

        # 1. Convert new objects to DataFrame
        new_data = [t.model_dump(mode='json') for t in transactions]
        new_df = pd.DataFrame(new_data)

        # 2. Load existing
        if path.exists():
            existing_df = pd.read_csv(path)
            # Combine
            combined = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            combined = new_df

        # 3. Deduplicate (Business Logic: Same Date, Desc, Amt, Source)
        # Note: We might want to move this logic to Service, but strictly speaking
        # the Repository should just save what it is told.
        # However, for CSV appending, simple dedupe here is safe.
        subset_cols = ['Date', 'Description', 'Amount', 'Source_Account']
        if not combined.empty:
            combined = combined.drop_duplicates(subset=subset_cols, keep='last')

        combined.to_csv(path, index=False)

    def delete_batch(self, batch_id: str, user_id: UUID) -> None:
        path = self._get_path()
        if not path.exists(): return

        df = pd.read_csv(path)
        if 'Batch_ID' in df.columns:
            df = df[df['Batch_ID'] != batch_id]
            df.to_csv(path, index=False)