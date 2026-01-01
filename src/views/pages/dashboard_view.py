import streamlit as st
from src.container import get_container
from src.views.components.kpi_cards import render_executive_summary_cards, render_cashflow_summary


def render_view():
    st.title("📊 Executive Dashboard")

    # 1. Get Services from Container
    container = get_container()
    summary_svc = container['summary']

    # 2. Get Logic (One line!)
    data = summary_svc.get_executive_summary()

    # 3. Render
    render_executive_summary_cards(data)

    st.subheader("Cashflow Overview")
    render_cashflow_summary(data)