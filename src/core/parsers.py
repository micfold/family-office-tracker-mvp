# src/core/parsers.py
import logging
import zipfile
import io
import re
import pandas as pd
from typing import Generator, Tuple, Optional, List
from decimal import Decimal

from src.domain.enums import Currency
from src.domain.models.MPortfolio import InvestmentPosition, InvestmentEvent


# --- CONSTANTS ---
# MVP FX Strategy: Static rates for normalization to base currency (CZK)
# In production, this should be a service call or DB lookup.
FX_RATES = {'USD': 23.5, 'EUR': 25.2, 'GBP': 29.5, 'CZK': 1.0}

# --- BANK PARSING CONFIG ---
BANK_CONFIGS = {
    'CS': {
        'trigger': 'Own account name',
        'date': 'Processing Date',
        'desc': ['Partner Name', 'Note'],
        'amt': 'Amount',
        'own_acc': 'Own account number',
        'target_acc': 'Partner account number'
    },
    'RB_CUR': {
        'trigger': 'Datum provedení',
        'date': 'Datum provedení',
        'desc': ['Název protiúčtu', 'Zpráva'],
        'amt': 'Zaúčtovaná částka',
        'own_acc': 'Číslo účtu',
        'target_acc': 'Číslo protiúčtu'
    },
}

# --- NUMERIC HELPERS ---

def _clean_numeric_portfolio(val) -> Decimal:
    """Robust cleaner for portfolio CSV numbers (supports EU/US formats mixed)."""
    if pd.isna(val): return Decimal(0)
    s = re.sub(r'[^\d.,-]', '', str(val))
    if not s: return Decimal(0)

    # Heuristic: Determine if comma is decimal or thousands separator
    if ',' in s and '.' in s:
        if s.find('.') > s.find(','):
            s = s.replace(',', '') # 1,000.00 -> 1000.00
        else:
            s = s.replace('.', '').replace(',', '.') # 1.000,00 -> 1000.00
    elif ',' in s:
        # Assume 100,00 is 100.00 (EU decimal) if no dots are present
        s = s.replace(',', '.')

    try:
        return Decimal(s)
    except Exception:
        return Decimal(0)


def _detect_csv_df(file_obj) -> pd.DataFrame:
    """Helper to safely read CSVs with varying separators/encodings."""
    file_obj.seek(0)
    # Try reading first few lines to detect separator
    sample = file_obj.read(1024)
    file_obj.seek(0)

    # Simple separator detection
    sep = ';' if b';' in sample and sample.count(b';') > sample.count(b',') else ','

    try:
        return pd.read_csv(file_obj, sep=sep)
    except Exception:
        # Retry with different encoding if default fails
        file_obj.seek(0)
        return pd.read_csv(file_obj, sep=sep, encoding='cp1250')

def clean_currency(value):
    """Cleaner for Bank CSVs (legacy helper)."""
    if pd.isna(value): return 0.0
    val_str = str(value).strip().replace('\xa0', '').replace(' ', '')
    if ',' in val_str and '.' in val_str:
        if val_str.find('.') > val_str.find(','):
            val_str = val_str.replace(',', '')
        else:
            val_str = val_str.replace('.', '').replace(',', '.')
    elif ',' in val_str:
        if re.search(r',\d{2}$', val_str):
            val_str = val_str.replace(',', '.')
        else:
            val_str = val_str.replace(',', '')
    return pd.to_numeric(val_str, errors='coerce')


# --- PORTFOLIO PARSERS ---

def parse_portfolio_snapshot(file_obj, user_id) -> List[InvestmentPosition]:
    """Parses a snapshot CSV into InvestmentPosition objects."""
    try:
        file_obj.seek(0)
        df = pd.read_csv(file_obj)
        positions = []

        # Column Mapping (Support for Snowball / Trading 212 exports)
        col_map = {
            'ticker': ['Symbol', 'Ticker'],
            'name': ['Name', 'Holding'],
            'qty': ['Quantity', 'Shares'],
            'price': ['Price', 'Current price'],
            'value': ['Value', 'Current value', 'Amount'],
            'cost': ['Cost basis', 'Total cost'],
            'sector': ['Sector']
        }

        def get_val(row, keys):
            for k in keys:
                if k in row: return row[k]
            return None

        for _, row in df.iterrows():
            qty = _clean_numeric_portfolio(get_val(row, col_map['qty']))
            price = _clean_numeric_portfolio(get_val(row, col_map['price']))
            val = _clean_numeric_portfolio(get_val(row, col_map['value']))
            cost = _clean_numeric_portfolio(get_val(row, col_map['cost']))

            # Fallback calculation if Value is missing but Qty/Price exist
            if val == 0 and price > 0 and qty > 0:
                val = price * qty

            div_yield = _clean_numeric_portfolio(row.get('Dividend yield', 0))

            pos = InvestmentPosition(
                ticker=str(get_val(row, col_map['ticker']) or "UNK"),
                name=str(get_val(row, col_map['name']) or "Unknown"),
                quantity=qty,
                current_price=price,
                cost_basis=cost,
                market_value=val,
                gain_loss=val - cost,
                dividend_yield_projected=div_yield,
                projected_annual_income=val * (div_yield / Decimal(100)) if div_yield else 0,
                sector=str(get_val(row, col_map['sector']) or "Other"),
                owner=user_id
            )
            positions.append(pos)
        return positions
    except Exception as e:
        print(f"Error parsing snapshot: {e}")
        return []


def parse_portfolio_history(file_obj, user_id) -> List[InvestmentEvent]:
    try:
        df = _detect_csv_df(file_obj)
        events = []

        # Map Columns Robustly
        col_map = {
            'date': ['Date', 'Time', 'Datum'],
            'ticker': ['Symbol', 'Ticker', 'Instrument', 'Asset'],
            'event': ['Type', 'Event', 'Action', 'Transaction'],
            'amount': ['Amount', 'Total', 'Value', 'Net Amount', 'Cost'],
            'qty': ['Quantity', 'Shares', 'Qty'],
            'price': ['Price', 'Price per share', 'Quote'],
            'currency': ['Currency', 'Curr', 'Měna']
        }

        def get_val(row, keys):
            for k in keys:
                if k in row.index: return row[k]
            return None

        for _, row in df.iterrows():
            # Extract Data
            curr = str(get_val(row, col_map['currency']) or 'CZK').upper()
            rate = Decimal(FX_RATES.get(curr, 1.0))

            raw_amt = _clean_numeric_portfolio(get_val(row, col_map['amount']))
            # If amount is missing, try calculating it
            raw_qty = _clean_numeric_portfolio(get_val(row, col_map['qty']))
            raw_price = _clean_numeric_portfolio(get_val(row, col_map['price']))

            if raw_amt == 0 and raw_qty > 0 and raw_price > 0:
                raw_amt = raw_qty * raw_price

            amt_czk = raw_amt * rate

            # Parse Date
            raw_date = get_val(row, col_map['date'])
            try:
                dt = pd.to_datetime(raw_date, dayfirst=True)
            except (TypeError, ValueError):
                dt = pd.to_datetime(raw_date)

            evt = InvestmentEvent(
                date=dt,
                ticker=str(get_val(row, col_map['ticker']) or 'CASH'),
                event_type=str(get_val(row, col_map['event']) or 'UNK'),
                quantity=raw_qty,
                price_per_share=raw_price,
                total_amount=amt_czk,
                currency=Currency.CZK,
                owner=user_id
            )
            events.append(evt)

        return events
    except Exception as e:
        logging.error(f"Failed to parse investment history: {e}")
        return []

# --- 4. BANK PARSERS (Existing) ---

def parse_bank_content(content: str, filename: str) -> Optional[pd.DataFrame]:
    sep = ';' if ';' in content.split('\n')[0] else ','
    try:
        df = pd.read_csv(io.StringIO(content), sep=sep)
    except Exception:
        return None

    for bank, cfg in BANK_CONFIGS.items():
        if cfg['trigger'] in df.columns:
            std_df = pd.DataFrame()
            std_df['Date'] = pd.to_datetime(df[cfg['date']], dayfirst=True)
            std_df['Amount'] = df[cfg['amt']].apply(clean_currency)
            std_df['Source_Account'] = df.get(cfg.get('own_acc'), '')
            std_df['Target_Account'] = df.get(cfg.get('target_acc'), '')
            std_df['Description'] = df[cfg['desc']].fillna('').agg(' '.join, axis=1)
            std_df['Source'] = f"{bank} {filename}"
            return std_df
    return None


def process_uploaded_files(uploaded_files) -> Generator[Tuple[str, Optional[pd.DataFrame], Optional[str]], None, None]:
    encodings = ['utf-8', 'utf-16', 'windows-1250', 'cp1250']

    for file in uploaded_files:
        file.seek(0)
        raw_data = file.read()

        if file.name.lower().endswith('.zip'):
            with zipfile.ZipFile(io.BytesIO(raw_data)) as z:
                for z_name in z.namelist():
                    if z_name.lower().endswith('.csv') and not z_name.startswith('__MACOSX'):
                        with z.open(z_name) as f:
                            yield _decode_and_parse(z_name, f.read(), encodings)
        else:
            yield _decode_and_parse(file.name, raw_data, encodings)


def _decode_and_parse(filename, raw_bytes, encodings):
    content = None
    for enc in encodings:
        try:
            content = raw_bytes.decode(enc)
            break
        except UnicodeDecodeError:
            continue

    if content is None:
        content = raw_bytes.decode('utf-8', errors='replace')

    try:
        df = parse_bank_content(content, filename)
        if df is None:
            return filename, None, "Unknown format"
        return filename, df, None
    except Exception as e:
        return filename, None, str(e)

def parse_investment_history(file_obj, user_id) -> List[InvestmentEvent]:
    try:
        df = _detect_csv_df(file_obj)
        events = []

        # Map Columns Robustly
        col_map = {
            'date': ['Date', 'Time', 'Datum'],
            'ticker': ['Symbol', 'Ticker', 'Instrument', 'Asset'],
            'event': ['Type', 'Event', 'Action', 'Transaction'],
            'amount': ['Amount', 'Total', 'Value', 'Net Amount', 'Cost'],
            'qty': ['Quantity', 'Shares', 'Qty'],
            'price': ['Price', 'Price per share', 'Quote'],
            'currency': ['Currency', 'Curr', 'Měna']
        }

        def get_val(row, keys):
            for k in keys:
                if k in row.index: return row[k]
            return None

        for _, row in df.iterrows():
            # Extract Data
            curr = str(get_val(row, col_map['currency']) or 'CZK').upper()
            rate = Decimal(FX_RATES.get(curr, 1.0))

            raw_amt = _clean_numeric_portfolio(get_val(row, col_map['amount']))
            # If amount is missing, try calculating it
            raw_qty = _clean_numeric_portfolio(get_val(row, col_map['qty']))
            raw_price = _clean_numeric_portfolio(get_val(row, col_map['price']))

            if raw_amt == 0 and raw_qty > 0 and raw_price > 0:
                raw_amt = raw_qty * raw_price

            amt_czk = raw_amt * rate

            # Parse Date
            raw_date = get_val(row, col_map['date'])
            try:
                dt = pd.to_datetime(raw_date, dayfirst=True)
            except (TypeError, ValueError):
                dt = pd.to_datetime(raw_date)

            evt = InvestmentEvent(
                date=dt,
                ticker=str(get_val(row, col_map['ticker']) or 'CASH'),
                event_type=str(get_val(row, col_map['event']) or 'UNK'),
                quantity=raw_qty,
                price_per_share=raw_price,
                total_amount=amt_czk,
                currency=Currency.CZK,
                owner=user_id
            )
            events.append(evt)

        return events
    except Exception as e:
        logging.error(f"Failed to parse investment history: {e}")
        return []
