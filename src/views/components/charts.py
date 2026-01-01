# src/views/components/charts.py
import streamlit as st
import plotly.express as px
import pandas as pd
from typing import List
from src.domain.models.MPortfolio import InvestmentPosition


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

    fig = px.area(df, x='Date', y='Invested Capital', title="Invested Capital Over Time")
    fig.update_traces(line_color='#2980b9', fillcolor='rgba(41, 128, 185, 0.3)')
    st.plotly_chart(fig, use_container_width=True)


def render_spending_trend(df: pd.DataFrame):
    """
    Expects a DataFrame with 'Date', 'Amount' columns.
    Aggregates by Month for visualization.
    """
    if df.empty:
        return

    # Create a copy to avoid mutating the cached DF from service
    chart_df = df.copy()
    chart_df['Month'] = chart_df['Date'].dt.to_period('M').astype(str)

    # Separate Income and Expense
    monthly = chart_df.groupby('Month')['Amount'].agg(
        Income=lambda x: x[x > 0].sum(),
        Expense=lambda x: x[x < 0].sum()
    ).reset_index()

    if monthly.empty:
        st.info("Not enough data for trends.")
        return

    # Visual: Bar Chart with Overlay
    import plotly.graph_objects as go
    fig = go.Figure()
    fig.add_trace(go.Bar(x=monthly['Month'], y=monthly['Income'], name='Income', marker_color='#2ecc71'))
    fig.add_trace(go.Bar(x=monthly['Month'], y=monthly['Expense'], name='Expenses', marker_color='#e74c3c'))

    fig.update_layout(barmode='relative', title="Monthly Cashflow Trend", height=350)
    st.plotly_chart(fig, use_container_width=True)