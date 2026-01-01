# services/ledger.py
from datetime import datetime
from pathlib import Path

import pandas as pd
import json
from services.auth import AuthService
from config import GLOBAL_RULES
from src.domain.enums import TransactionType
from modules import processing, ingestion
from config import GLOBAL_RULES as INITIAL_RULES


class LedgerService:
    def __init__(self):
        self.auth = AuthService()
        self.filename = "ledger.csv"
        self.rules_filename = "user_rules.json"

        # System-wide rules stored in the root data folder
        self.global_rules_path = Path("data/global_rules.json")
        self._ensure_global_rules()

    def _ensure_global_rules(self):
        """Initializes global_rules.json if it doesn't exist."""
        if not self.global_rules_path.exists():
            self.global_rules_path.parent.mkdir(exist_ok=True)
            self.global_rules_path.write_text(json.dumps(INITIAL_RULES, indent=2))

    def load_global_rules(self):
        """Loads system-wide rules."""
        try:
            return json.loads(self.global_rules_path.read_text())
        except Exception:
            return INITIAL_RULES

    def save_global_rules(self, rules):
        """Saves system-wide rules (Admin logic)."""
        self.global_rules_path.write_text(json.dumps(rules, indent=2))

    def get_all_active_rules(self):
        """Merges global and user-specific rules for processing."""
        return self.load_global_rules() + self.load_user_rules()

    def load_all_rules(self):
        """Merges system global rules with user-specific rules."""
        global_rules = []
        if self.global_rules_path.exists():
            global_rules = json.loads(self.global_rules_path.read_text())

        user_rules = self.load_user_rules()
        return global_rules + user_rules

    def load_ledger(self):
        """Loads the user's ledger file and ensures required columns exist."""
        path = self.auth.get_file_path(self.filename)

        # Extended schema to include Batch_ID
        required_cols = [
            'Date', 'Description', 'Amount', 'Currency',
            'Category', 'Type', 'Source', 'Source_Account', 'Target_Account', 'Batch_ID'
        ]

        if path.exists():
            df = pd.read_csv(path)
            df['Date'] = pd.to_datetime(df['Date'])

            # Backfill missing columns for legacy data
            for col in required_cols:
                if col not in df.columns:
                    if col == 'Batch_ID':
                        df[col] = 'Legacy'
                    else:
                        df[col] = ""

            return df

        return pd.DataFrame(columns=required_cols)

    def save_ledger(self, df):
        """Saves the ledger to disk."""
        path = self.auth.get_file_path(self.filename)
        df.to_csv(path, index=False)

    def get_batch_history(self):
        """Returns statistics for each upload batch."""
        df = self.load_ledger()
        if df.empty or 'Batch_ID' not in df.columns:
            return pd.DataFrame()

        # Group by Batch_ID to calculate stats
        stats = df.groupby('Batch_ID').agg(
            Upload_Date=('Date', 'max'),  # Proxy for when it happened if not stored separate
            Tx_Count=('Amount', 'count'),
            Total_In=('Amount', lambda x: x[x > 0].sum()),
            Total_Out=('Amount', lambda x: x[x < 0].sum())
        ).reset_index()

        # Filter out empty or weird batches
        return stats.sort_values('Upload_Date', ascending=False)

    def delete_batch(self, batch_id):
        """Deletes all transactions associated with a Batch ID."""
        df = self.load_ledger()
        if 'Batch_ID' in df.columns:
            df = df[df['Batch_ID'] != batch_id]
            self.save_ledger(df)

    def load_user_rules(self):
        """Loads user-defined categorization rules."""
        path = self.auth.get_file_path(self.rules_filename)
        if path.exists():
            try:
                return json.loads(path.read_text())
            except:
                return []
        return []

    def save_user_rules(self, rules):
        """Saves user-defined categorization rules."""
        path = self.auth.get_file_path(self.rules_filename)
        path.write_text(json.dumps(rules, indent=2))

    def categorize_transaction(self, description, amount):
        """
        Determines category based on rules AND amount direction.
        """
        desc_str = str(description).lower()

        # 1. Check Global Rules
        for rule in GLOBAL_RULES:
            # Check pattern match
            if rule['pattern'].lower() in desc_str:

                # Check Direction Constraint (if exists)
                direction = rule.get('direction')  # 'positive' or 'negative'

                if direction == 'positive' and amount < 0:
                    continue  # Skip this rule, look for others
                if direction == 'negative' and amount > 0:
                    continue  # Skip this rule

                # If we passed checks, return match
                return rule['category'], rule['type']

        # 2. Default Fallback
        return "Uncategorized", TransactionType.EXPENSE if amount < 0 else TransactionType.INCOME

    def process_upload(self, uploaded_files, user_rules=None):
        """
        Parses and categorizes bank statements, tagging them with a Batch ID.
        """
        if user_rules is None:
            user_rules = self.load_user_rules()

        active_rules = self.load_global_rules() + user_rules  # Use merged rules

        new_txs = []

        # Generate a unique Batch ID for this specific upload session
        batch_id = f"Import_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        for filename, df, error in ingestion.process_uploaded_files(uploaded_files):
            if not error and df is not None and not df.empty:
                # Tag rows with the Batch ID
                df['Batch_ID'] = batch_id

                # Tag missing columns to ensure concatenation works
                for col in ['Source_Account', 'Target_Account']:
                    if col not in df.columns:
                        df[col] = ""

                new_txs.append(df)

        if not new_txs:
            return pd.DataFrame()

        new_df = pd.concat(new_txs)

        # Apply Categorization
        new_df = processing.apply_categorization(new_df, active_rules, [])

        return new_df

def _parse_csv(file_obj):
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