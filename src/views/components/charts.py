# src/views/components/charts.py
import streamlit as st
import plotly.express as px
import pandas as pd
from typing import List
from src.domain.models.MPortfolio import InvestmentPosition
import plotly.graph_objects as go


def render_portfolio_allocation(positions: List[InvestmentPosition]):
    if not positions:
        st.info("No positions to chart.")
        return

    # Transformation logic belongs here, closer to the UI
    data = [{"Sector": p.sector, "Value": float(p.market_value)} for p in positions]
    fig = px.pie(data, values='Value', names='Sector', hole=0.4, title="Sector Allocation")
    st.plotly_chart(fig, use_container_width=True)


def render_invested_capital_curve(df: pd.DataFrame):
    if df.empty:
        st.info("No history data available.")
        return

    if 'Date' in df.columns: df.rename(columns={'Date': 'date'}, inplace=True)
    if 'Invested Capital' not in df.columns:
        # Fallback if your VM uses different naming
        pass

    fig = px.area(df, x='date', y='Invested Capital', title="Invested Capital Over Time")
    fig.update_traces(line_color='#2980b9', fillcolor='rgba(41, 128, 185, 0.3)')
    st.plotly_chart(fig, use_container_width=True)


def render_spending_trend(df: pd.DataFrame):
    if df.empty:
        return

    chart_df = df.copy()

    date_col = 'date' if 'date' in chart_df.columns else 'Date'
    amt_col = 'amount' if 'amount' in chart_df.columns else 'Amount'

    chart_df['Month'] = pd.to_datetime(chart_df[date_col]).dt.to_period('M').astype(str)

    monthly = chart_df.groupby('Month')[amt_col].agg(
        Income=lambda x: x[x > 0].sum(),
        Expense=lambda x: x[x < 0].sum()
    ).reset_index()

    if monthly.empty:
        st.info("Not enough data for trends.")
        return

    fig = go.Figure()
    fig.add_trace(go.Bar(x=monthly['Month'], y=monthly['Income'], name='Income', marker_color='#2ecc71'))
    fig.add_trace(go.Bar(x=monthly['Month'], y=monthly['Expense'], name='Expenses', marker_color='#e74c3c'))

    fig.update_layout(barmode='relative', title="Monthly Cashflow Trend", height=350)
    st.plotly_chart(fig, use_container_width=True)