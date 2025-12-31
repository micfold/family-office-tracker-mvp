import streamlit as st
import plotly.graph_objects as go
import plotly.express as px


def render_t_form(house_val, fleet_val, stocks_val, cash_dict, mortgage_val):
    total_cash = sum(cash_dict.values())
    total_assets = house_val + fleet_val + stocks_val + total_cash
    equity = total_assets - mortgage_val

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Assets")
        st.info(f"🏠 Real Estate: {house_val:,.0f} CZK")
        st.info(f"🚗 Fleet (Vehicles): {fleet_val:,.0f} CZK")
        st.info(f"📈 Portfolio: {stocks_val:,.0f} CZK")

        with st.expander(f"💵 Cash Reserves: {total_cash:,.0f} CZK"):
            for fund, val in cash_dict.items():
                st.write(f"**{fund}:** {val:,.0f} CZK")

        st.metric("Total Assets", f"{total_assets:,.0f} CZK")
    with col2:
        st.subheader("Liabilities & Equity")
        st.error(f"📉 Mortgage: {mortgage_val:,.0f} CZK")
        st.success(f"💎 Net Equity: {equity:,.0f} CZK")
        st.metric("Net Worth", f"{equity:,.0f} CZK")


def render_waterfall(income, spending_df):
    if spending_df.empty: return
    fig = go.Figure(go.Waterfall(
        orientation="v", measure=["relative"] * (len(spending_df) + 1),
        x=["Total Income"] + spending_df['Target Basin'].tolist(),
        y=[income] + [-x for x in spending_df['Amount']],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
    ))
    st.plotly_chart(fig, use_container_width=True)


def render_portfolio_visuals(metrics):
    df = metrics['df']
    c1, c2 = st.columns(2)
    with c1:
        st.write("### Sector Allocation")
        st.plotly_chart(px.pie(df, values='Current value', names='Sector', hole=0.4), use_container_width=True)
    with c2:
        st.write("### Top Holdings PnL")
        st.plotly_chart(px.bar(metrics['top_10'], x='Holding', y='Total profit', color='Total profit',
                               color_continuous_scale='RdYlGn'), use_container_width=True)