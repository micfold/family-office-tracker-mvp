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


def parse_bank_file_content(content, filename):
    """Parses string content into a standardized DataFrame."""
    try:
        # Determine separator
        first_line = content.split('\n')[0]
        sep = ';' if ';' in first_line else ','
        df = pd.read_csv(io.StringIO(content), sep=sep)
    except Exception as e:
        raise ValueError(f"CSV Parsing Failed: {str(e)}")

    if df.empty: return None

    cols = df.columns.tolist()
    standard_df = pd.DataFrame()

    # 1. Česká spořitelna
    if 'Own account name' in cols:
        standard_df['Date'] = pd.to_datetime(df['Processing Date'], dayfirst=True, errors='coerce')
        standard_df['Description'] = df['Partner Name'].fillna('') + ' ' + df.get('Note',
                                                                                  pd.Series([''] * len(df))).fillna('')
        standard_df['Amount'] = df['Amount'].apply(clean_currency)
        standard_df['Currency'] = df.get('Currency', 'CZK')
        standard_df['Source'] = f"CS {filename}"

    # 2. RB Current
    elif 'Datum provedení' in cols:
        standard_df['Date'] = pd.to_datetime(df['Datum provedení'], dayfirst=True, errors='coerce')
        standard_df['Description'] = df['Název protiúčtu'].fillna('') + ' ' + df['Zpráva'].fillna('')
        standard_df['Amount'] = df['Zaúčtovaná částka'].apply(clean_currency)
        standard_df['Currency'] = df.get('Měna účtu', 'CZK')
        standard_df['Source'] = f"RB Current {filename}"

    # 3. RB Credit Card
    elif 'Číslo kreditní karty' in cols:
        standard_df['Date'] = pd.to_datetime(df['Datum transakce'], dayfirst=True, errors='coerce')
        standard_df['Description'] = df['Popis/Místo transakce'].fillna('') + ' ' + df['Název obchodníka'].fillna('')
        standard_df['Amount'] = df['Zaúčtovaná částka'].apply(clean_currency)
        standard_df['Currency'] = df.get('Měna zaúčtování', 'CZK')
        standard_df['Source'] = f"RB CC {filename}"

    else:
        return None

    standard_df['Date'] = standard_df['Date'].dt.normalize()
    standard_df['Description'] = standard_df['Description'].str.strip()
    return standard_df


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