# services/ledger.py
import pandas as pd
import json
from services.auth import AuthService
from core.config import GLOBAL_RULES
from core.enums import TransactionType
from modules import processing, ingestion


class LedgerService:
    def __init__(self):
        self.auth = AuthService()
        self.filename = "ledger.csv"
        self.rules_filename = "user_rules.json"

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

    def categorize_transaction(description, amount):
        """Determines category based on rules."""
        # 1. Check Global Rules
        for rule in GLOBAL_RULES:
            if rule['pattern'].lower() in str(description).lower():
                # Return mapped Enum value
                return rule['category'], rule['type']

        # 2. Default Fallback
        return "Uncategorized", TransactionType.EXPENSE if amount < 0 else TransactionType.INCOME

    def process_upload(self, uploaded_files, user_rules=None):
        """
        Parses and categorizes bank statements.
        Accepts user_rules to override global defaults.
        """

        # Load rules if not provided
        if user_rules is None:
            user_rules = self.load_user_rules()

        new_txs = []
        report = []

        for filename, df, error in ingestion.process_uploaded_files(uploaded_files):
            stats = {'file': filename, 'rows': 0, 'min': '-', 'max': '-', 'error': None}

            if error:
                stats['error'] = error
            elif df is not None:
                stats['rows'] = len(df)
                if not df.empty:
                    stats['min'] = df['Date'].min().strftime('%Y-%m-%d')
                    stats['max'] = df['Date'].max().strftime('%Y-%m-%d')

                # Categorize immediately
                for idx, row in df.iterrows():
                    cat, t_type = self.categorize_transaction(row['Description'], row['Amount'])
                    df.at[idx, 'Category'] = cat.value if hasattr(cat, 'value') else cat
                    df.at[idx, 'Type'] = t_type.value if hasattr(t_type, 'value') else t_type

                new_txs.append(df)
            else:
                stats['error'] = "No data extracted."

            report.append(stats)

        if not new_txs:
            return pd.DataFrame()

        full_df = pd.concat(new_txs)

        # USE THE PROCESSING MODULE FOR CATEGORIZATION
        # This ensures we use the exact logic from Master
        full_df = processing.apply_categorization(full_df, GLOBAL_RULES, user_rules)

        return full_df

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