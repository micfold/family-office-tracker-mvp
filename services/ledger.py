# services/ledger.py
import pandas as pd
import io
import re
import zipfile
from services.auth import AuthService
from core.config import GLOBAL_RULES
from core.enums import TransactionType, CATEGORY_METADATA


class LedgerService:
    def __init__(self):
        self.auth = AuthService()
        self.filename = "ledger.csv"

    def load_ledger(self):
        """Loads the user's ledger file."""
        path = self.auth.get_file_path(self.filename)
        if path.exists():
            df = pd.read_csv(path)
            df['Date'] = pd.to_datetime(df['Date'])
            return df
        return pd.DataFrame(columns=['Date', 'Description', 'Amount', 'Currency', 'Category', 'Type', 'Source'])

    def save_ledger(self, df):
        """Saves the ledger to disk."""
        path = self.auth.get_file_path(self.filename)
        df.to_csv(path, index=False)

    def categorize_transaction(self, description, amount):
        """Determines category based on rules."""
        # 1. Check Global Rules
        for rule in GLOBAL_RULES:
            if rule['pattern'].lower() in str(description).lower():
                # Return mapped Enum value
                return rule['category'], rule['type']

        # 2. Default Fallback
        return "Uncategorized", TransactionType.EXPENSE if amount < 0 else TransactionType.INCOME

    def process_upload(self, uploaded_files):
        """Parses bank statements (logic ported from ingestion.py)."""
        new_txs = []

        for file in uploaded_files:
            # Handle ZIPs or CSVs (simplified for brevity)
            if file.name.endswith('.csv'):
                df = self._parse_csv(file)
                if df is not None: new_txs.append(df)
            # Add ZIP logic here if needed from old code

        if not new_txs:
            return pd.DataFrame()

        full_df = pd.concat(new_txs)

        # Apply Categorization
        for idx, row in full_df.iterrows():
            cat, t_type = self.categorize_transaction(row['Description'], row['Amount'])
            full_df.at[idx, 'Category'] = cat.value if hasattr(cat, 'value') else cat
            full_df.at[idx, 'Type'] = t_type.value if hasattr(t_type, 'value') else t_type

        return full_df

    def _parse_csv(self, file_obj):
        """Helper to parse generic bank CSVs."""
        try:
            df = pd.read_csv(file_obj, sep=None, engine='python')
            # Basic normalization (adjust based on your specific bank formats)
            cols = [c.lower() for c in df.columns]

            # Simple Mapping heuristic
            norm = pd.DataFrame()
            if 'date' in cols or 'datum' in cols:
                # Find date col
                d_col = next(c for c in df.columns if 'dat' in c.lower())
                norm['Date'] = pd.to_datetime(df[d_col], dayfirst=True, errors='coerce')

            if 'amount' in cols or 'castka' in cols:
                # Find amount col
                a_col = next(c for c in df.columns if 'amount' in c.lower() or 'castka' in c.lower())
                norm['Amount'] = pd.to_numeric(df[a_col].astype(str).str.replace(',', '.').str.replace(' ', ''),
                                               errors='coerce')

            norm['Description'] = df.iloc[:, 1].astype(str)  # Fallback description
            norm['Currency'] = 'CZK'
            norm['Source'] = file_obj.name
            return norm.dropna(subset=['Date', 'Amount'])
        except Exception as e:
            print(f"Error parsing {file_obj.name}: {e}")
            return None