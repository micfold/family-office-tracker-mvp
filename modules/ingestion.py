# micfold/family-office-tracker-mvp/family-office-tracker-mvp-feat-clean-architecture/modules/ingestion.py
import zipfile
import pandas as pd
import io
import re


def clean_currency(value):
    """Robust currency cleaner."""
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

BANK_CONFIGS = {
    'CS': {
        'trigger': 'Own account name',
        'date': 'Processing Date',
        'desc': ['Partner Name', 'Note'],
        'amt': 'Amount',
        'own_acc': 'Own account number',  # New mapping
        'target_acc': 'Partner account number' # New mapping
    },
    'RB_CUR': {
        'trigger': 'Datum provedení',
        'date': 'Datum provedení',
        'desc': ['Název protiúčtu', 'Zpráva'],
        'amt': 'Zaúčtovaná částka',
        'own_acc': 'Číslo účtu', # New mapping
        'target_acc': 'Číslo protiúčtu' # New mapping
    },
}


def parse_bank_file_content(content, filename):
    sep = ';' if ';' in content.split('\n')[0] else ','
    df = pd.read_csv(io.StringIO(content), sep=sep)

    for bank, cfg in BANK_CONFIGS.items():
        if cfg['trigger'] in df.columns:
            standard_df = pd.DataFrame()
            standard_df['Date'] = pd.to_datetime(df[cfg['date']], dayfirst=True)
            standard_df['Amount'] = df[cfg['amt']].apply(clean_currency)
            # Scalable description merging
            standard_df['Source_Account'] = df.get(cfg.get('own_acc'), '')
            standard_df['Target_Account'] = df.get(cfg.get('target_acc'), '')
            standard_df['Description'] = df[cfg['desc']].fillna('').agg(' '.join, axis=1)
            standard_df['Source'] = f"{bank} {filename}"
            standard_df['Currency'] = 'CZK'
            return standard_df
    return None


def process_uploaded_files(uploaded_files):
    """
    Generator yielding (filename, dataframe, error_message).
    Handles robust encoding detection.
    """
    encodings = ['utf-8', 'utf-16', 'windows-1250', 'cp1250']

    for file in uploaded_files:
        # 1. READ BYTES
        file.seek(0)
        raw_data = file.read()

        # 2. DETECT ZIP vs CSV
        if file.name.lower().endswith('.zip'):
            with zipfile.ZipFile(io.BytesIO(raw_data)) as z:
                for z_name in z.namelist():
                    if z_name.lower().endswith('.csv') and not z_name.startswith('__MACOSX'):
                        with z.open(z_name) as f:
                            z_bytes = f.read()
                            yield _decode_and_parse(z_name, z_bytes, encodings)
        else:
            yield _decode_and_parse(file.name, raw_data, encodings)


def _decode_and_parse(filename, raw_bytes, encodings):
    """Helper to try multiple encodings."""
    content = None
    last_error = None

    # Try decoding
    for enc in encodings:
        try:
            content = raw_bytes.decode(enc)
            # Quick sanity check: if it decodes but is garbage, pandas will fail later.
            break
        except UnicodeDecodeError:
            continue

    if content is None:
        # Fallback to replace
        content = raw_bytes.decode('utf-8', errors='replace')

    try:
        df = parse_bank_file_content(content, filename)
        if df is None:
            return filename, None, "Unknown format or empty file."
        return filename, df, None
    except Exception as e:
        return filename, None, str(e)