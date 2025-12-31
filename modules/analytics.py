# modules/analytics.py
import pandas as pd


def get_net_cashflow_period(df):
    """Returns (Total Income, Total Expenses, Net Cashflow)."""
    if df.empty: return 0, 0, 0
    income = df[df['Amount'] > 0]['Amount'].sum()
    expenses = df[df['Amount'] < 0]['Amount'].sum()
    return income, expenses, income + expenses


def get_expense_breakdown(df):
    """Returns DataFrame of expenses grouped by Category."""
    if df.empty: return pd.DataFrame()
    expenses = df[df['Amount'] < 0].copy()
    expenses['AbsAmount'] = expenses['Amount'].abs()
    return expenses.groupby('Category')['AbsAmount'].sum().sort_values(ascending=False).reset_index()


def get_fixed_vs_variable(df):
    """Returns DataFrame comparing Fixed vs Variable costs."""
    if df.empty: return pd.DataFrame()
    mask = df['Type'].isin(['Fixed', 'Variable']) & (df['Amount'] < 0)
    expenses = df[mask].copy()
    expenses['AbsAmount'] = expenses['Amount'].abs()
    return expenses.groupby('Type')['AbsAmount'].sum().reset_index()


def get_monthly_trend(df):
    """Returns DataFrame for Period-over-Period trends."""
    if df.empty: return pd.DataFrame()
    df = df.copy()
    df['Month'] = df['Date'].dt.to_period('M')

    monthly = df.groupby(['Month', 'Type'])['Amount'].sum().unstack(fill_value=0)
    if 'Income' not in monthly.columns: monthly['Income'] = 0

    expense_cols = [c for c in monthly.columns if c != 'Income']
    monthly['Total Expenses'] = monthly[expense_cols].sum(axis=1)

    monthly.index = monthly.index.astype(str)
    return monthly.reset_index()


def calculate_running_balance(df, start_date, start_balance):
    """
    Calculates a running balance curve backwards and forwards from a known checkpoint.
    Useful for reconciliation.
    """
    if df.empty: return pd.DataFrame()

    df = df.sort_values('Date').copy()

    # Split data into "Before Checkpoint" and "After Checkpoint"
    # Note: We assume the checkpoint balance is the Closing Balance of that date.

    # 1. Calculate cumulative sum of all transactions
    df['Cumulative_Change'] = df['Amount'].cumsum()

    # 2. Find the cumulative change value at the checkpoint date
    # We take the last transaction of that specific date to anchor "Closing Balance"
    checkpoint_mask = df['Date'] <= pd.to_datetime(start_date)
    if not checkpoint_mask.any():
        # If no transactions before start date, just offset everything
        offset = start_balance
    else:
        val_at_checkpoint = df.loc[checkpoint_mask, 'Cumulative_Change'].iloc[-1]
        offset = start_balance - val_at_checkpoint

    df['Running Balance'] = df['Cumulative_Change'] + offset
    return df