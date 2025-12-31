import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Family Office HQ", layout="wide")


def detect_and_parse(file):
    # Try comma first, then semicolon
    try:
        df = pd.read_csv(file)
        if len(df.columns) < 2: raise ValueError
    except:
        file.seek(0)  # Reset file pointer for re-reading
        df = pd.read_csv(file, sep=';')

    cols = df.columns.tolist()

    # Logic based on our 'Training' session
    if 'Own account name' in cols and 'Note' in cols:
        # CS Credit Card
        parsed = pd.DataFrame({
            'Date': pd.to_datetime(df['Processing Date'], dayfirst=True),
            'Description': df['Partner Name'].fillna('') + " " + df['Note'].fillna(''),
            'Amount': df['Amount'],
            'Source': "ČS Credit Card"
        })
    elif 'Own account name' in cols:
        # CS Bank Account
        parsed = pd.DataFrame({
            'Date': pd.to_datetime(df['Processing Date'], dayfirst=True),
            'Description': df['Partner Name'].fillna(''),
            'Amount': df['Amount'],
            'Source': "ČS Current Account"
        })
    elif 'Datum provedení' in cols:
        # RB Bank Account
        amounts = df['Zaúčtovaná částka'].astype(str).str.replace(' ', '').str.replace(',', '.')
        parsed = pd.DataFrame({
            'Date': pd.to_datetime(df['Datum provedení'], dayfirst=True),
            'Description': df['Název protiúčtu'].fillna('') + " " + df['Zpráva'].fillna(''),
            'Amount': pd.to_numeric(amounts),
            'Source': "RB Current Account"
        })
    elif 'Číslo kreditní karty' in cols:
        # RB Credit Card
        amounts = df['Zaúčtovaná částka'].astype(str).str.replace(' ', '').str.replace(',', '.')
        parsed = pd.DataFrame({
            'Date': pd.to_datetime(df['Datum transakce'], dayfirst=True),
            'Description': df['Popis/Místo transakce'].fillna('') + " " + df['Název obchodníka'].fillna(''),
            'Amount': pd.to_numeric(amounts),
            'Source': "RB Credit Card"
        })
    else:
        return None

    return parsed


def auto_tag(row):
    desc = str(row['Description']).lower()
    if any(x in desc for x in ['albert', 'lidl', 'rohlik', 'globus', 'tesco', 'billa']):
        return 'Living (Groceries)'
    if any(x in desc for x in ['shell', 'omv', 'benzina', 'mol']):
        return 'Fleet Fund (Fuel)'
    if any(x in desc for x in ['hypoteka', 'mortgage']):
        return 'Fixed OPEX (Mortgage)'
    return 'Uncategorized'


st.title("Family Office Command Center")
st.sidebar.header("Upload Statements")
uploaded_files = st.sidebar.file_uploader("Upload CSVs", type=['csv'], accept_multiple_files=True)

if uploaded_files:
    all_data = []
    for f in uploaded_files:
        parsed = detect_and_parse(f)
        if parsed is not None:
            all_data.append(parsed)
            st.success(f"Loaded {f.name}")

    if all_data:
        master_ledger = pd.concat(all_data).sort_values('Date', ascending=False)
        master_ledger['Target Basin'] = master_ledger.apply(auto_tag, axis=1)

        st.write("### Consolidated Reality")
        st.dataframe(master_ledger)

        # Dashboard Visual
        spend = master_ledger[master_ledger['Amount'] < 0].groupby('Target Basin')['Amount'].sum().abs()
        fig = go.Figure(data=[go.Pie(labels=spend.index, values=spend.values, hole=.3)])
        st.plotly_chart(fig)