# components/visuals.py
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

# --- BALANCE SHEET ---
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

# --- CASHFLOW ---
def render_trend_line(df):
    if df.empty: return
    fig = go.Figure()
    if 'Income' in df.columns:
        fig.add_trace(go.Bar(x=df['Month'], y=df['Income'], name='Inc', marker_color='#2ecc71'))
    if 'Total Expenses' in df.columns:
        fig.add_trace(go.Bar(x=df['Month'], y=-df['Total Expenses'], name='Exp', marker_color='#e74c3c'))
    fig.update_layout(barmode='relative', height=300)
    st.plotly_chart(fig, use_container_width=True)

def render_pie(df, values, names, title):
    if df.empty: return
    fig = px.pie(df, values=values, names=names, title=title, hole=0.5)
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)

def render_bar(df, x, y, title, color=None):
    if df.empty: return
    fig = px.bar(df, x=x, y=y, title=title, color=color)
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)

def render_balance_history(df):
    if df.empty: return
    fig = px.line(df, x='Date', y='Running Balance', title="Reconciliation Curve")
    st.plotly_chart(fig, use_container_width=True)

# --- PORTFOLIO (Full Restoration) ---
def render_unified_portfolio(snap, hist):
    val = snap['value'] if snap else (hist['value_proxy'] if hist else 0)
    cost = snap['cost'] if snap else (hist['total_invested'] if hist else 0)
    profit = snap['profit'] if snap else (val - cost)
    divs = hist['divs_earned'] if hist else (snap['divs_earned'] if snap else 0)

    # Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Portfolio Value", f"{val:,.0f} CZK")
    if cost > 0:
        p_pct = (profit / cost) * 100
        m2.metric("Total Profit", f"{profit:,.0f} CZK", delta=f"{p_pct:.1f}%")
    else:
        m2.metric("Total Profit", "0 CZK")
    m3.metric("Invested Capital", f"{cost:,.0f} CZK")
    m4.metric("Total Divs Earned", f"{divs:,.0f} CZK")
    st.divider()

    # Charts
    c1, c2 = st.columns(2)
    with c1:
        if snap and 'Sector' in snap['df'].columns:
            st.subheader("Sector Allocation")
            st.plotly_chart(px.pie(snap['df'], values='Current value', names='Sector', hole=0.4), use_container_width=True)
        elif hist:
            st.subheader("Annual Dividends")
            st.plotly_chart(px.bar(hist['annual_divs'], x='Year', y='DividendCZK'), use_container_width=True)

    with c2:
        if hist:
            st.subheader("Invested Capital")
            fig = px.area(hist['history_df'], x='Date', y='Invested Capital')
            fig.update_traces(line_color='#2980b9', fillcolor='rgba(41, 128, 185, 0.3)')
            st.plotly_chart(fig, use_container_width=True)
        elif snap:
            st.subheader("Top Winners")
            st.plotly_chart(px.bar(snap['top_10'], x='Holding', y='Total profit'), use_container_width=True)

    # Dividend Intelligence
    if snap and hist:
        st.subheader("Dividend Intelligence")
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Realized', x=['Dividends'], y=[hist['divs_earned']], marker_color='#f1c40f'))
        fig.add_trace(go.Bar(name='Projected', x=['Dividends'], y=[snap['divs_projected']], marker_color='#27ae60'))
        st.plotly_chart(fig, use_container_width=True)

    # Data Tables
    t1, t2 = st.tabs(["Current Holdings", "Transaction Log"])
    with t1:
        if snap: st.dataframe(snap['df'], use_container_width=True)
    with t2:
        if hist: st.dataframe(hist['raw'], use_container_width=True)