import zipfile
import pandas as pd
import io
import re


def clean_currency(value):
    """Restored robust currency cleaner."""
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
    """
    Refactored to take content string + filename (Stateless).
    Logic restored from original ingestion.py
    """
    first_line = content.split('\n')[0]
    sep = ';' if ';' in first_line else ','
    try:
        df = pd.read_csv(io.StringIO(content), sep=sep)
    except:
        return None

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
    """Generator yielding (filename, dataframe)."""
    for file in uploaded_files:
        if file.name.lower().endswith('.zip'):
            with zipfile.ZipFile(file) as z:
                for z_name in z.namelist():
                    if z_name.lower().endswith('.csv') and not z_name.startswith('__MACOSX'):
                        with z.open(z_name) as f:
                            content = f.read().decode('utf-8', errors='replace')
                            parsed = parse_bank_file_content(content, z_name)
                            if parsed is not None: yield z_name, parsed
        else:
            file.seek(0)
            content = file.read().decode('utf-8', errors='replace')
            parsed = parse_bank_file_content(content, file.name)
            if parsed is not None: yield file.name, parsed