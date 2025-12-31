# modules/analytics.py
import pandas as pd


def get_net_cashflow_period(df):
    if df.empty: return 0, 0, 0
    income = df[df['Amount'] > 0]['Amount'].sum()
    expenses = df[df['Amount'] < 0]['Amount'].sum()
    return income, expenses, income + expenses


def get_expense_breakdown(df):
    if df.empty: return pd.DataFrame()
    expenses = df[df['Amount'] < 0].copy()
    expenses['AbsAmount'] = expenses['Amount'].abs()
    return expenses.groupby('Category')['AbsAmount'].sum().sort_values(ascending=False).reset_index()


def get_fixed_vs_variable(df):
    """Restored function for Fixed/Variable split."""
    if df.empty: return pd.DataFrame()
    # Filter for expenses only
    mask = df['Type'].isin(['Fixed', 'Variable']) & (df['Amount'] < 0)
    expenses = df[mask].copy()
    expenses['AbsAmount'] = expenses['Amount'].abs()
    return expenses.groupby('Type')['AbsAmount'].sum().reset_index()


def get_monthly_trend(df):
    if df.empty: return pd.DataFrame()
    df = df.copy()
    df['Month'] = df['Date'].dt.to_period('M')

    monthly = df.groupby(['Month', 'Type'])['Amount'].sum().unstack(fill_value=0)
    if 'Income' not in monthly.columns: monthly['Income'] = 0

    # Calculate Total Expenses
    expense_cols = [c for c in monthly.columns if c != 'Income']
    monthly['Total Expenses'] = monthly[expense_cols].sum(axis=1)

    monthly.index = monthly.index.astype(str)
    return monthly.reset_index()


def calculate_running_balance(df, start_date, start_balance):
    if df.empty: return pd.DataFrame()
    df = df.sort_values('Date').copy()
    df['Cumulative_Change'] = df['Amount'].cumsum()

    checkpoint_mask = df['Date'] <= pd.to_datetime(start_date)
    if not checkpoint_mask.any():
        offset = start_balance
    else:
        val_at_check = df.loc[checkpoint_mask, 'Cumulative_Change'].iloc[-1]
        offset = start_balance - val_at_check

    df['Running Balance'] = df['Cumulative_Change'] + offset
    return df