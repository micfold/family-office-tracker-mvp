# modules/processing.py
import pandas as pd
from config.settings import CATEGORY_TYPES


def translate_transactions(df):
    """
    Placeholder for translation logic.
    Future extension: Integrate Google Translate API or LLM.
    """
    return df

def apply_categorization(df, global_rules, user_rules):
    """
    Applies Global rules first, then User rules.
    """
    if df.empty: return df

    df['Category'] = 'Uncategorized'

    # Combine rules: User rules take precedence (applied last or logic specific)
    # Here we apply Global first, so User rules can overwrite if needed
    # or we can merge them. For simplicity: simple sequential application.

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

    # Map Types
    df['Type'] = df['Category'].map(CATEGORY_TYPES).fillna('Variable')
    df.loc[df['Amount'] > 0, 'Type'] = 'Income'

    return df


def suggest_patterns(df):
    """
    Analyzes 'Uncategorized' transactions and groups them by description
    to find high-impact rules.
    """
    if df.empty: return pd.DataFrame()

    # Filter only Uncategorized
    uncat = df[df['Category'] == 'Uncategorized'].copy()

    if uncat.empty: return pd.DataFrame()

    # Group by Description to find frequency
    # We strip numbers/dates often found in bank desc to group better (simple heuristic)
    # For now, exact string match grouping:
    suggestions = uncat.groupby('Description').agg(
        Count=('Amount', 'count'),
        Total_Value=('Amount', 'sum'),
        Example_Source=('Source', 'first'),
        Example_Currency=('Currency', 'first')
    ).reset_index()

    # Sort by Count (Frequency) then Value (Impact)
    suggestions = suggestions.sort_values(['Count', 'Total_Value'], ascending=[False, True])

    return suggestions