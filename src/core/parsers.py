import zipfile
import pandas as pd
import io
import re
from typing import Generator, Tuple, Optional

# Bank Configuration Strategy
# In a real app, this might be loaded from a config file
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


def clean_currency(value):
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