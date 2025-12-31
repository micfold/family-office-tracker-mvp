# modules/processing.py
import pandas as pd
from config.settings import CATEGORY_TYPE_MAP


def translate_transactions(df):
    """Placeholder for translation logic."""
    return df


def apply_categorization(df, global_rules, user_rules):
    """
    Applies Global rules first, then User rules.
    """
    if df.empty: return df

    df['Category'] = 'Uncategorized'

    # Combine rules: User rules take precedence (applied last or logic specific)
    # 1. Apply Global Rules
    sorted_global = sorted(global_rules, key=lambda x: len(x['pattern']), reverse=True)
    for rule in sorted_global:
        mask = df['Description'].str.lower().str.contains(rule['pattern'].lower(), na=False)
        df.loc[mask, 'Category'] = rule['target']

    # 2. Apply User Rules (Specific to this instance)
    if user_rules:
        sorted_user = sorted(user_rules, key=lambda x: len(x['pattern']), reverse=True)
        for rule in sorted_user:
            mask = df['Description'].str.lower().str.contains(rule['pattern'].lower(), na=False)
            df.loc[mask, 'Category'] = rule['target']

    # Map Types using the new MAP
    df['Type'] = df['Category'].map(CATEGORY_TYPE_MAP).fillna('Variable')

    # Safety net: Any positive amount is strictly treated as Income type for cashflow calc,
    # unless it's an investment withdrawal which we might treat differently.
    # For MVP, let's trust the Map, but ensure positive unmapped items are Income.
    mask_income = (df['Amount'] > 0) & (df['Type'] == 'Variable')
    df.loc[mask_income, 'Type'] = 'Income'

    return df


def suggest_patterns(df):
    """
    Analyzes 'Uncategorized' transactions.
    """
    if df.empty: return pd.DataFrame()

    uncat = df[df['Category'] == 'Uncategorized'].copy()
    if uncat.empty: return pd.DataFrame()

    suggestions = uncat.groupby('Description').agg(
        Count=('Amount', 'count'),
        Total_Value=('Amount', 'sum'),
        Example_Currency=('Currency', 'first')
    ).reset_index()

    suggestions = suggestions.sort_values(['Count', 'Total_Value'], ascending=[False, True])
    return suggestions