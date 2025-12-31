# components/visuals.py
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px


def render_t_form(house_val, fleet_val, stocks_val, cash_dict, mortgage_val):
    total_cash = sum(cash_dict.values())
    total_assets = house_val + fleet_val + stocks_val + total_cash
    equity = total_assets - mortgage_val

    def c(v): return f"{v:,.0f} CZK"

    with st.container(border=True):
        st.markdown("### ⚖️ Balance Sheet")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 🟢 Assets")
            st.write(f"**Real Estate:** {c(house_val)}")
            st.write(f"**Vehicles:** {c(fleet_val)}")
            st.write(f"**Portfolio:** {c(stocks_val)}")
            with st.popover(f"**Cash:** {c(total_cash)}"):
                for k, v in cash_dict.items(): st.write(f"{k}: {c(v)}")
            st.divider()
            st.metric("Total Assets", c(total_assets))
        with c2:
            st.markdown("#### 🔴 Liabilities")
            st.write(f"**Mortgage:** {c(mortgage_val)}")
            st.markdown("<br>", unsafe_allow_html=True)
            st.divider()
            st.metric("Liabilities", c(mortgage_val), delta_color="inverse")
        st.markdown(f"<h3 style='text-align:center'>Net Worth: {c(equity)}</h3>", unsafe_allow_html=True)

def render_balance_history(df):
    if df.empty: return
    fig = px.line(df, x='Date', y='Running Balance', title="Reconciliation Curve")
    st.plotly_chart(fig, width='stretch')


def render_pie(df, values, names, title):
    if df.empty: return
    fig = px.pie(df, values=values, names=names, title=title, hole=0.5)
    fig.update_layout(height=350)
    st.plotly_chart(fig, width='stretch')


def render_bar(df, x, y, title, color=None):
    if df.empty: return
    fig = px.bar(df, x=x, y=y, title=title, color=color)
    fig.update_layout(height=350)
    st.plotly_chart(fig, width='stretch')


def render_trend_line(df):
    if df.empty: return
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['Month'], y=df['Income'], name='Inc', marker_color='#2ecc71'))
    fig.add_trace(go.Bar(x=df['Month'], y=-df['Total Expenses'], name='Exp', marker_color='#e74c3c'))
    fig.update_layout(barmode='relative', height=300)
    st.plotly_chart(fig, width='stretch')


def render_dividend_comparison(earned, projected):
    """Comparison Bar Chart for Dividends."""
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Earned (YTD)', x=['Dividends'], y=[earned], marker_color='#f1c40f'))
    fig.add_trace(go.Bar(name='Projected (Annual)', x=['Dividends'], y=[projected], marker_color='#27ae60'))
    fig.update_layout(title="Dividend Income: Realized vs Projected", barmode='group', height=300)
    st.plotly_chart(fig, width='stretch')

def render_invested_capital_curve(history_df):
    """Renders the Invested Capital over time."""
    if history_df.empty: return

    fig = px.area(history_df, x='Date', y='Invested Capital',
                  title="Invested Capital History (Cost Basis)",
                  labels={'Invested Capital': 'Accumulated Cost (CZK)'})
    fig.update_traces(line_color='#2980b9', fillcolor='rgba(41, 128, 185, 0.3)')
    fig.update_layout(height=350)
    st.plotly_chart(fig, width='stretch')


def render_dividend_history(annual_df, quarterly_df):
    """Renders Dividend bars."""
    t1, t2 = st.tabs(["Yearly", "Quarterly"])

    with t1:
        if not annual_df.empty:
            fig = px.bar(annual_df, x='Year', y='DividendCZK',
                         title="Annual Dividends Received", text_auto='.2s')
            fig.update_traces(marker_color='#27ae60')
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("No dividend data found.")

    with t2:
        if not quarterly_df.empty:
            fig = px.bar(quarterly_df, x='Quarter', y='DividendCZK',
                         title="Quarterly Dividends Received")
            fig.update_traces(marker_color='#2ecc71')
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("No dividend data found.")


def render_portfolio_visuals(metrics):
    """Updated to handle both Snapshot and History metrics."""
    # Logic for Snapshot (Holdings)
    if metrics.get('type') == 'snapshot':
        df = metrics['df']
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Sector Allocation")
            if 'Sector' in df.columns:
                st.plotly_chart(px.pie(df, values='Current value', names='Sector', hole=0.4), width='stretch')
        with c2:
            st.subheader("Top Winners")
            if not metrics['top_10'].empty:
                st.plotly_chart(px.bar(metrics['top_10'], x='Holding', y='Total profit', color='Total profit',
                                       color_continuous_scale='RdYlGn'), width='stretch')

    # Logic for History
    elif metrics.get('type') == 'history':
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Total Invested Capital", f"{metrics['total_invested']:,.0f} CZK", help="Cumulative Cost Basis")
        with c2:
            st.metric("Total Dividends Earned", f"{metrics['total_divs']:,.0f} CZK", help="Lifetime Dividends")

        st.divider()
        render_invested_capital_curve(metrics['history_df'])
        render_dividend_history(metrics['annual_divs'], metrics['quarterly_divs'])


def render_unified_portfolio(snap, hist):
    """
    Renders a merged view of Snapshot and History data.
    snap: Dict from process_snapshot (or None)
    hist: Dict from process_history (or None)
    """

    # 1. METRICS ROW
    # We prioritize Snapshot for Value, History for Invested

    val = snap['value'] if snap else (hist['value_proxy'] if hist else 0)
    cost = snap['cost'] if snap else (hist['total_invested'] if hist else 0)
    profit = snap['profit'] if snap else (val - cost)
    divs = hist['divs_earned'] if hist else (snap['divs_earned'] if snap else 0)
    yield_pct = snap['portfolio_yield'] if snap else 0
    proj_divs = snap['divs_projected'] if snap else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Portfolio Value", f"{val:,.0f} CZK", help="Current Market Value" if snap else "Cost Basis Proxy")

    if cost > 0:
        p_pct = (profit / cost) * 100
        m2.metric("Total Profit", f"{profit:,.0f} CZK", delta=f"{p_pct:.1f}%")
    else:
        m2.metric("Total Profit", "0 CZK")

    m3.metric("Invested Capital", f"{cost:,.0f} CZK", help="Total Cash Invested")
    m4.metric("Total Divs Earned", f"{divs:,.0f} CZK", help="Lifetime Dividends")

    st.divider()

    # 2. CHARTS AREA
    # Left Col: Allocation (Snap) or Divs (Hist)
    # Right Col: Invested Curve (Hist) or Winners (Snap)

    c_left, c_right = st.columns(2)

    with c_left:
        if snap:
            st.subheader("Sector Allocation")
            if 'Sector' in snap['df'].columns:
                st.plotly_chart(px.pie(snap['df'], values='Current value', names='Sector', hole=0.4),
                                width='stretch')
        elif hist:
            st.subheader("Annual Dividends")
            st.plotly_chart(px.bar(hist['annual_divs'], x='Year', y='DividendCZK'), width='stretch')

    with c_right:
        if hist:
            st.subheader("Invested Capital Over Time")
            fig = px.area(hist['history_df'], x='Date', y='Invested Capital')
            fig.update_traces(line_color='#2980b9', fillcolor='rgba(41, 128, 185, 0.3)')
            st.plotly_chart(fig, width='stretch')
        elif snap:
            st.subheader("Top Winners")
            st.plotly_chart(px.bar(snap['top_10'], x='Holding', y='Total profit', color='Total profit'),
                            width='stretch')

    # 3. ADVANCED SECTIONS
    st.divider()

    # Dividend Intelligence (Requires both or specific one)
    if snap and hist:
        st.subheader("Dividend Intelligence")
        # Compare Realized (Hist) vs Projected (Snap)
        fig = go.Figure()
        fig.add_trace(
            go.Bar(name='Realized (Lifetime)', x=['Dividends'], y=[hist['divs_earned']], marker_color='#f1c40f'))
        fig.add_trace(
            go.Bar(name='Projected (Annual)', x=['Dividends'], y=[snap['divs_projected']], marker_color='#27ae60'))
        st.plotly_chart(fig, width='stretch')

    # Data Tables
    t1, t2 = st.tabs(["Current Holdings", "Transaction Log"])
    with t1:
        if snap:
            st.dataframe(snap['df'], width='stretch')
        else:
            st.info("No Snapshot Data")
    with t2:
        if hist:
            st.dataframe(hist['raw'], width='stretch')
        else:
            st.info("No History Data")