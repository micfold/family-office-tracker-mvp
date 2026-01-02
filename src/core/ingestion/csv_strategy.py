# src/core/ingestion/csv_strategy.py
import pandas as pd
import io
from decimal import Decimal
from typing import List, Tuple, Optional
from .base import IngestionStrategy, NormalizedTransaction

# Configs mapped to your specific bank exports
BANK_CONFIGS = {
    'CS': {'trigger': 'Own account name', 'date': 'Processing Date', 'desc': ['Partner Name', 'Note'], 'amt': 'Amount'},
    'RB': {'trigger': 'Datum provedení', 'date': 'Datum provedení', 'desc': ['Název protiúčtu', 'Zpráva'],
           'amt': 'Zaúčtovaná částka'},
}


class CsvBankStrategy(IngestionStrategy):
    def can_handle(self, filename: str, content: bytes) -> bool:
        return filename.lower().endswith('.csv')

    def parse(self, filename: str, content: bytes) -> Tuple[List[NormalizedTransaction], Optional[str]]:
        text_data = self._decode(content)
        if not text_data:
            return [], "Failed to decode file (Unknown encoding)."

        # Robust Separator Detection
        sep = ';' if text_data.count(';') > text_data.count(',') else ','

        try:
            # Skip bad lines to be safe
            df = pd.read_csv(io.StringIO(text_data), sep=sep, on_bad_lines='skip')
        except Exception as e:
            return [], f"CSV Parsing Error: {str(e)}"

        if df.empty:
            return [], "File is empty."

        # Identify Bank
        config = None
        for key, cfg in BANK_CONFIGS.items():
            if cfg['trigger'] in df.columns:
                config = cfg
                break

        if not config:
            # Helpful error message listing found columns
            found_cols = ", ".join(df.columns[:3]) + "..."
            return [], f"Unknown Bank Format. Could not find trigger columns. Found: [{found_cols}]"

        # Extract
        results = []
        errors = []
        for idx, row in df.iterrows():
            try:
                amt_str = str(row[config['amt']]).replace(' ', '').replace('\xa0', '').replace(',', '.')
                amt = Decimal(amt_str)

                desc_parts = [str(row.get(col, '')) for col in config['desc']]
                full_desc = " ".join([d for d in desc_parts if d and d != 'nan']).strip()

                raw_date = row[config['date']]
                dt = pd.to_datetime(raw_date, dayfirst=True).date()

                results.append(NormalizedTransaction(
                    date=dt,
                    description=full_desc,
                    amount=amt,
                    raw_source=filename
                ))
            except Exception as e:
                # Log specific row failure but continue
                errors.append(f"Row {idx}: {str(e)}")
                continue

        if not results and errors:
            return [], f"Found valid header but failed to parse rows. First error: {errors[0]}"

        return results, None

    def _decode(self, content: bytes) -> str:
        for enc in ['utf-8', 'cp1250', 'windows-1250', 'latin1']:
            try:
                return content.decode(enc)
            except:
                continue
        return ""