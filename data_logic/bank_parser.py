import pandas as pd
import io
import re


def detect_and_parse_bank(file):
    # Encodings commonly used by Czech banks
    encodings = ['utf-8', 'windows-1250', 'cp1250', 'utf-16']
    df = None

    # Read raw bytes to test different decodings
    raw_bytes = file.read()
    file.seek(0)  # Reset for potential re-reads

    for enc in encodings:
        try:
            text_content = raw_bytes.decode(enc)
            # Detect separator based on the first line
            first_line = text_content.split('\n')[0]
            sep = ';' if ';' in first_line else ','

            df = pd.read_csv(io.StringIO(text_content), sep=sep)
            if len(df.columns) > 1:
                break  # Successfully decoded and parsed
        except Exception:
            continue

    if df is None or df.empty:
        return None

    cols = df.columns.tolist()

    # --- THE MAGIC CLEANER: Handles "-41,060.93" and "-5,00" ---
    def clean_currency_robust(value):
        if pd.isna(value): return 0.0
        val_str = str(value).strip().replace('\xa0', '').replace(' ', '')

        # 1. If it has both a comma and a dot (e.g., -41,060.93)
        if ',' in val_str and '.' in val_str:
            # If the dot is last, the comma is a thousand separator (US style)
            if val_str.find('.') > val_str.find(','):
                val_str = val_str.replace(',', '')
            # If the comma is last, the dot is a thousand separator (EU style)
            else:
                val_str = val_str.replace('.', '').replace(',', '.')

        # 2. If it only has a comma
        elif ',' in val_str:
            # If it's 2 digits after comma, it's a decimal (e.g. -5,00)
            if re.search(r',\d{2}$', val_str):
                val_str = val_str.replace(',', '.')
            # Otherwise, it's a thousand separator
            else:
                val_str = val_str.replace(',', '')

        return pd.to_numeric(val_str, errors='coerce')

    # --- LOGIC: ČESKÁ SPOŘITELNA (Bank or CC) ---
    if 'Own account name' in cols:
        return pd.DataFrame({
            'Date': pd.to_datetime(df['Processing Date'], dayfirst=True, errors='coerce'),
            'Description': df['Partner Name'].fillna('') + ' ' + df.get('Note', pd.Series([''] * len(df))).fillna(''),
            'Amount': df['Amount'].apply(clean_currency_robust),
            'Currency': df.get('Currency', 'CZK'),
            'Source': f"ČS {file.name}"
        })

    # --- LOGIC: RAIFFEISENBANK (Current) ---
    elif 'Datum provedení' in cols:
        return pd.DataFrame({
            'Date': pd.to_datetime(df['Datum provedení'], dayfirst=True, errors='coerce'),
            'Description': df['Název protiúčtu'].fillna('') + ' ' + df['Zpráva'].fillna('') + ' ' + df.get('Poznámka',
                                                                                                           pd.Series(
                                                                                                               [''] * len(
                                                                                                                   df))).fillna(
                ''),
            'Amount': df['Zaúčtovaná částka'].apply(clean_currency_robust),
            'Currency': df.get('Měna účtu', 'CZK'),
            'Source': f"RB Current {file.name}"
        })

    # --- LOGIC: RAIFFEISENBANK (Credit Card) ---
    elif 'Číslo kreditní karty' in cols:
        return pd.DataFrame({
            'Date': pd.to_datetime(df['Datum transakce'], dayfirst=True, errors='coerce'),
            'Description': df['Popis/Místo transakce'].fillna('') + ' ' + df['Název obchodníka'].fillna(''),
            'Amount': df['Zaúčtovaná částka'].apply(clean_currency_robust),
            'Currency': df.get('Měna zaúčtování', 'CZK'),
            'Source': f"RB CC {file.name}"
        })

    return None


def apply_magic_rules(df, rules):
    """
    Applies custom categorization logic.
    rules: List of dicts [{'pattern': 'str', 'target': 'Basin Name'}]
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=['Date', 'Description', 'Amount', 'Currency', 'Source', 'Target Basin'])

    df['Target Basin'] = 'Uncategorized'

    # Sort rules so more specific patterns (longer strings) apply first
    sorted_rules = sorted(rules, key=lambda x: len(x['pattern']), reverse=True)

    for rule in sorted_rules:
        pattern = rule['pattern'].lower()
        target = rule['target']
        mask = df['Description'].str.lower().str.contains(pattern, na=False)
        df.loc[mask, 'Target Basin'] = target

    return df


def apply_tagging(df):
    """
    Applies default tagging/categorization to transaction data.
    This is a simplified version that returns the dataframe with a Target Basin column.
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=['Date', 'Description', 'Amount', 'Currency', 'Source', 'Target Basin'])

    df = df.copy()
    df['Target Basin'] = 'Uncategorized'
    return df
