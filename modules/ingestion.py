# modules/ingestion.py
import zipfile
import pandas as pd
import io
import re


def clean_currency(value):
    """
    Robust currency cleaner handling various EU/US formats.
    e.g., "-41,060.93" -> -41060.93 and "-5,00" -> -5.00
    """
    if pd.isna(value): return 0.0
    val_str = str(value).strip().replace('\xa0', '').replace(' ', '')

    # Handle mixed comma/dot formats
    if ',' in val_str and '.' in val_str:
        if val_str.find('.') > val_str.find(','):  # Format: 1,000.00
            val_str = val_str.replace(',', '')
        else:  # Format: 1.000,00
            val_str = val_str.replace('.', '').replace(',', '.')
    elif ',' in val_str:
        # If 2 digits after comma, assume decimal (EU style)
        if re.search(r',\d{2}$', val_str):
            val_str = val_str.replace(',', '.')
        else:  # Assume thousands separator
            val_str = val_str.replace(',', '')

    return pd.to_numeric(val_str, errors='coerce')


def parse_bank_file(file_obj, filename=None):
    """
    Parses a single CSV file object.
    Args:
        file_obj: The file-like object (BytesIO or UploadedFile)
        filename: String name of the file (required if file_obj doesn't have .name)
    """
    # If filename isn't provided, try to get it from the object
    if not filename:
        filename = getattr(file_obj, 'name', 'unknown_file.csv')

    # Attempt to read file with different encodings
    encodings = ['utf-8', 'windows-1250', 'cp1250', 'utf-16']
    df = None

    # Ensure we are at the start of the file
    file_obj.seek(0)
    raw_bytes = file_obj.read()

    for enc in encodings:
        try:
            content = raw_bytes.decode(enc)
            first_line = content.split('\n')[0]
            sep = ';' if ';' in first_line else ','
            df = pd.read_csv(io.StringIO(content), sep=sep)
            if len(df.columns) > 1: break
        except: continue

    if df is None or df.empty: return None

    cols = df.columns.tolist()
    standard_df = pd.DataFrame()

    # Logic: Česká spořitelna
    if 'Own account name' in cols:
        standard_df['Date'] = pd.to_datetime(df['Processing Date'], dayfirst=True, errors='coerce')
        desc = df['Partner Name'].fillna('') + ' ' + df.get('Note', pd.Series([''] * len(df))).fillna('')
        standard_df['Description'] = desc
        standard_df['Amount'] = df['Amount'].apply(clean_currency)
        standard_df['Currency'] = df.get('Currency', 'CZK')
        standard_df['Source'] = f"CS {filename}"

    # Logic: RB Current
    elif 'Datum provedení' in cols:
        standard_df['Date'] = pd.to_datetime(df['Datum provedení'], dayfirst=True, errors='coerce')
        desc = df['Název protiúčtu'].fillna('') + ' ' + df['Zpráva'].fillna('')
        standard_df['Description'] = desc
        standard_df['Amount'] = df['Zaúčtovaná částka'].apply(clean_currency)
        standard_df['Currency'] = df.get('Měna účtu', 'CZK')
        standard_df['Source'] = f"RB Current {filename}"

    # Logic: RB Credit Card
    elif 'Číslo kreditní karty' in cols:
        standard_df['Date'] = pd.to_datetime(df['Datum transakce'], dayfirst=True, errors='coerce')
        desc = df['Popis/Místo transakce'].fillna('') + ' ' + df['Název obchodníka'].fillna('')
        standard_df['Description'] = desc
        standard_df['Amount'] = df['Zaúčtovaná částka'].apply(clean_currency)
        standard_df['Currency'] = df.get('Měna zaúčtování', 'CZK')
        standard_df['Source'] = f"RB CC {filename}"

    if standard_df.empty: return None

    # Global Cleanup
    standard_df['Date'] = standard_df['Date'].dt.normalize()
    standard_df['Description'] = standard_df['Description'].str.strip()
    return standard_df

def process_uploaded_files(uploaded_files):
    """
    Generator that yields (filename, file_object) for both
    individual CSVs and files packed inside ZIPs.
    """
    for file in uploaded_files:
        if file.name.lower().endswith('.zip'):
            # Handle ZIP Archive
            with zipfile.ZipFile(file) as z:
                for z_name in z.namelist():
                    # Skip macOS metadata and non-CSVs
                    if z_name.lower().endswith('.csv') and not z_name.startswith('__MACOSX'):
                        with z.open(z_name) as f:
                            # Read into memory so pandas can use it
                            yield z_name, io.BytesIO(f.read())
        else:
            # Handle Standard CSV
            yield file.name, file