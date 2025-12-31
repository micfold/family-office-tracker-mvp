# modules/processing.py
import pandas as pd
from core.config import CATEGORY_TYPE_MAP
from core.enums import TransactionType

def apply_categorization(df, global_rules, user_rules):
    if df.empty: return df

    df['Category'] = 'Uncategorized'

    # 1. Apply Global Rules
    sorted_global = sorted(global_rules, key=lambda x: len(x['pattern']), reverse=True)
    for rule in sorted_global:
        mask = df['Description'].str.lower().str.contains(rule['pattern'].lower(), na=False)
        df.loc[mask, 'Category'] = rule['category']

    # 2. Apply User Rules (Override Global)
    if user_rules:
        sorted_user = sorted(user_rules, key=lambda x: len(x['pattern']), reverse=True)
        for rule in sorted_user:
            mask = df['Description'].str.lower().str.contains(rule['pattern'].lower(), na=False)
            df.loc[mask, 'Category'] = rule['target']

    # 3. Map Types (Fixed vs Variable)
    df['Type'] = df['Category'].map(CATEGORY_TYPE_MAP).fillna('Variable')

    # 4. Safety Net: Positive Amount = Income (unless Investment)
    # This prevents deposits from being labeled "Variable Expense"
    mask_income = (df['Amount'] > 0) & (df['Type'] != 'Investment')
    df.loc[mask_income, 'Type'] = 'Income'

    return df

def suggest_patterns(df):
    if df.empty: return pd.DataFrame()
    uncat = df[df['Category'] == 'Uncategorized'].copy()
    if uncat.empty: return pd.DataFrame()

    suggestions = uncat.groupby('Description').agg(
        Count=('Amount', 'count'),
        Total_Value=('Amount', 'sum')
    ).reset_index()

    return suggestions.sort_values(['Count', 'Total_Value'], ascending=[False, True])