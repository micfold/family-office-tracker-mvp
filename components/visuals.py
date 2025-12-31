# components/visuals.py
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px


def render_t_form(house_val, fleet_val, stocks_val, cash_dict, mortgage_val):
    """Renders Balance Sheet T-Account."""
    total_cash = sum(cash_dict.values())
    total_assets = house_val + fleet_val + stocks_val + total_cash
    equity = total_assets - mortgage_val

    def currency(val): return f"{val:,.0f} CZK"

    with st.container(border=True):
        st.markdown("### ⚖️ Balance Sheet")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 🟢 Assets")
            st.markdown(f"**Real Estate:** {currency(house_val)}")
            st.markdown(f"**Vehicles:** {currency(fleet_val)}")
            st.markdown(f"**Portfolio:** {currency(stocks_val)}")
            with st.popover(f"**Cash:** {currency(total_cash)}"):
                for k, v in cash_dict.items(): st.write(f"{k}: {currency(v)}")
            st.divider()
            st.metric("Total Assets", currency(total_assets))
        with c2:
            st.markdown("#### 🔴 Liabilities")
            st.markdown(f"**Mortgage:** {currency(mortgage_val)}")
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.divider()
            st.metric("Total Liabilities", currency(mortgage_val), delta_color="inverse")
        st.markdown("---")
        st.markdown(f"<h3 style='text-align: center; color: #4CAF50;'>Net Worth: {currency(equity)}</h3>",
                    unsafe_allow_html=True)


def render_balance_history(df):
    """Renders Running Balance Line Chart."""
    if df.empty: return
    fig = px.line(df, x='Date', y='Running Balance', title="Cash Reconciliation: Theoretical Running Balance")
    fig.update_traces(line_color='#3498db', line_width=3)
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)


def render_dividend_comparison(earned, projected):
    """Comparison Bar Chart for Dividends."""
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Earned (YTD)', x=['Dividends'], y=[earned], marker_color='#f1c40f'))
    fig.add_trace(go.Bar(name='Projected (Annual)', x=['Dividends'], y=[projected], marker_color='#27ae60'))
    fig.update_layout(title="Dividend Income: Realized vs Projected", barmode='group', height=300)
    st.plotly_chart(fig, use_container_width=True)


def render_trend_line(df):
    if df.empty: return
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['Month'], y=df['Income'], name='Income', marker_color='#2ecc71'))
    fig.add_trace(go.Bar(x=df['Month'], y=-df['Total Expenses'], name='Expenses', marker_color='#e74c3c'))
    fig.update_layout(title="Monthly Net Cashflow", barmode='relative', height=300)
    st.plotly_chart(fig, use_container_width=True)


def render_pie(df, values, names, title):
    if df.empty: return
    fig = px.pie(df, values=values, names=names, title=title, hole=0.5)
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)


def render_bar(df, x, y, title, color=None):
    if df.empty: return
    fig = px.bar(df, x=x, y=y, title=title, color=color, text_auto='.2s')
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)


def render_portfolio_visuals(metrics):
    df = metrics['df']
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Sector Allocation")
        if 'Sector' in df.columns:
            st.plotly_chart(px.pie(df, values='Current value', names='Sector', hole=0.4), use_container_width=True)
    with c2:
        st.subheader("Top Winners")
        if not metrics['top_10'].empty:
            st.plotly_chart(px.bar(metrics['top_10'], x='Holding', y='Total profit', color='Total profit',
                                   color_continuous_scale='RdYlGn'), use_container_width=True)