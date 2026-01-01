# modules/processing.py
import pandas as pd
from config import CATEGORY_TYPE_MAP


def apply_categorization(df, rules, user_overrides=None):
    if df.empty: return df
    df['Category'] = 'Uncategorized'

    # Combine and sort rules by pattern length (longest first for specificity)
    all_rules = rules + (user_overrides if user_overrides else [])
    sorted_rules = sorted(all_rules, key=lambda x: len(x.get('pattern', '')), reverse=True)

    for rule in sorted_rules:
        # Support both 'category' (global) and 'target' (user) keys for compatibility
        cat = rule.get('category') or rule.get('target')
        mask = df['Description'].str.lower().str.contains(rule['pattern'].lower(), na=False)

        # Apply directionality if specified
        if 'direction' in rule:
            if rule['direction'] == 'positive':
                mask &= (df['Amount'] > 0)
            elif rule['direction'] == 'negative':
                mask &= (df['Amount'] < 0)

        df.loc[mask, 'Category'] = cat

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