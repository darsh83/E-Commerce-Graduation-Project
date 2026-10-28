from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(page_title="E-commerce Performance Dashboard", layout="wide")

CHART_COLORS = ["#3F6F58", "#D2A45F", "#6D98A3", "#91AE98"]
CHART_COLOR_SCALE = [[0, "#E4EDE6"], [0.55, "#91AE98"], [1, "#3F6F58"]]
CHART_LAYOUT = {
    "height": 300,
    "font": {"size": 10, "color": "#52685C"},
    "margin": {"l": 30, "r": 20, "t": 48, "b": 35},
}

st.markdown(
    """
    <style>
        .stApp { background: #F7FAFC; }
        .dashboard-title {
            color: #355548;
            font-size: 2.55rem;
            font-weight: 800;
            line-height: 1.2;
            margin: 0 0 0.55rem 0;
        }
        .dashboard-caption {
            color: #728579;
            font-size: 1rem;
            margin: 0 0 1.15rem 0;
        }
        .section-heading {
            color: #3F6F58;
            font-size: 1.35rem;
            font-weight: 700;
            border-bottom: 2px solid #DCE8DF;
            padding-bottom: 0.4rem;
            margin: 1.3rem 0 0.8rem 0;
        }
        .kpi-card {
            background: #FFFFFF;
            border: 1px solid #DCE8DF;
            border-top: 3px solid #91AE98;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 6px -1px rgba(53, 85, 72, 0.08),
                        0 2px 4px -1px rgba(53, 85, 72, 0.04);
            margin-bottom: 10px;
        }
        .kpi-title {
            font-size: 14px;
            color: #728579;
            font-weight: bold;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .kpi-value {
            font-size: 24px;
            color: #355548;
            font-weight: 800;
            white-space: nowrap;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<h1 class="dashboard-title">E-commerce Sales and Customer Performance Dashboard</h1>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="dashboard-caption">Interactive analytics for e-commerce performance</p>',
    unsafe_allow_html=True,
)


@st.cache_data
def load_data():
    data_dir = Path(__file__).resolve().parent
    customers = pd.read_csv(data_dir / "customers_clean.csv")
    orders = pd.read_csv(data_dir / "orders_clean.csv")
    items = pd.read_csv(data_dir / "order_items_clean.csv")

    orders["Order_Date"] = pd.to_datetime(orders["Order_Date"], errors="coerce")
    orders["Delivery_Date"] = pd.to_datetime(orders["Delivery_Date"], errors="coerce")

    customer_orders = orders.merge(customers, on="Customer_ID", how="inner")
    item_totals = (
        items.groupby("Order_ID", as_index=False)
        .agg(
            Total_Sales_EGP=("Line_Sales_EGP", "sum"),
            Total_Cost_EGP=("Line_Cost_EGP", "sum"),
            Total_Profit_EGP=("Line_Profit_EGP", "sum"),
            Total_Quantity=("Quantity", "sum"),
        )
    )
    dashboard_data = customer_orders.merge(item_totals, on="Order_ID", how="inner")
    dashboard_data["Order_Month"] = dashboard_data["Order_Date"].dt.strftime("%Y-%m")
    dashboard_data["Delivery_Time_Days"] = (
        dashboard_data["Delivery_Date"] - dashboard_data["Order_Date"]
    ).dt.days
    return dashboard_data, items


df, items_df = load_data()
if df.empty:
    st.error("No matching order data was found. Check the input CSV files and their IDs.")
    st.stop()

st.sidebar.markdown(
    '<h2 style="color:#3F6F58; font-size:1.15rem;">Filters</h2>',
    unsafe_allow_html=True,
)
all_label = "All"
channels = [all_label] + sorted(df["Sales_Channel"].dropna().unique().tolist())
selected_channel = st.sidebar.selectbox("Sales Channel", channels)
segments = [all_label] + sorted(df["Customer_Segment"].dropna().unique().tolist())
selected_segment = st.sidebar.selectbox("Customer Segment", segments)
cities = [all_label] + sorted(df["City"].dropna().unique().tolist())
selected_city = st.sidebar.selectbox("City", cities)

filtered = df.copy()
if selected_channel != all_label:
    filtered = filtered[filtered["Sales_Channel"] == selected_channel]
if selected_segment != all_label:
    filtered = filtered[filtered["Customer_Segment"] == selected_segment]
if selected_city != all_label:
    filtered = filtered[filtered["City"] == selected_city]

total_orders = len(filtered)
total_sales = filtered["Total_Sales_EGP"].sum()
total_profit = filtered["Total_Profit_EGP"].sum()
average_order_value = filtered["Total_Sales_EGP"].mean() if total_orders else 0.0

metrics = [
    ("Total Orders", f"{total_orders:,}"),
    ("Total Sales", f"{total_sales:,.2f} EGP"),
    ("Total Profit", f"{total_profit:,.2f} EGP"),
    ("Average Order Value", f"{average_order_value:,.2f} EGP"),
]
for column, (label, value) in zip(st.columns(4), metrics):
    with column:
        st.markdown(
            f"<div class='kpi-card'><div class='kpi-title'>{label}</div>"
            f"<div class='kpi-value'>{value}</div></div>",
            unsafe_allow_html=True,
        )

st.markdown("<br />", unsafe_allow_html=True)
st.markdown('<h2 class="section-heading">Sales and Customer Trends</h2>', unsafe_allow_html=True)
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    monthly = (
        filtered.groupby("Order_Month", as_index=False)
        .agg(Sales=("Total_Sales_EGP", "sum"))
        .sort_values("Order_Month")
    )
    fig1 = px.line(
        monthly,
        x="Order_Month",
        y="Sales",
        markers=True,
        title="Monthly Sales Trend",
        labels={"Order_Month": "Month", "Sales": "Sales (EGP)"},
        color_discrete_sequence=["#3F6F58"],
    )
    fig1.update_layout(
        **CHART_LAYOUT, title_font_color="#355548", title_font_size=13,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig1, width="stretch", config={"displayModeBar": False})

with row1_col2:
    segment_sales = filtered.groupby("Customer_Segment", as_index=False).agg(
        Sales=("Total_Sales_EGP", "sum")
    )
    fig2 = px.pie(
        segment_sales,
        values="Sales",
        names="Customer_Segment",
        hole=0.5,
        title="Sales by Customer Segment",
        color_discrete_sequence=CHART_COLORS,
    )
    fig2.update_layout(
        **CHART_LAYOUT, title_font_color="#355548", title_font_size=13,
        paper_bgcolor="rgba(0,0,0,0)",
    )
    fig2.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig2, width="stretch", config={"displayModeBar": False})

st.markdown('<h2 class="section-heading">Product and Regional Performance</h2>', unsafe_allow_html=True)
row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    filtered_order_ids = filtered["Order_ID"].unique()
    items_filtered = items_df[items_df["Order_ID"].isin(filtered_order_ids)]
    category_profit = (
        items_filtered.groupby("Category", as_index=False)
        .agg(Profit=("Line_Profit_EGP", "sum"))
        .sort_values("Profit", ascending=True)
    )
    fig3 = px.bar(
        category_profit,
        x="Profit",
        y="Category",
        orientation="h",
        title="Profit by Product Category",
        labels={"Profit": "Profit (EGP)", "Category": "Category"},
        color="Profit",
        color_continuous_scale=CHART_COLOR_SCALE,
    )
    fig3.update_layout(
        **CHART_LAYOUT, title_font_color="#355548", title_font_size=13,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig3, width="stretch", config={"displayModeBar": False})

with row2_col2:
    city_sales = (
        filtered.groupby("City", as_index=False)
        .agg(Sales=("Total_Sales_EGP", "sum"), Orders=("Order_ID", "count"))
        .sort_values("Sales", ascending=False)
    )
    fig4 = px.bar(
        city_sales,
        x="City",
        y="Sales",
        text="Orders",
        title="Sales and Orders by City",
        labels={"City": "City", "Sales": "Sales (EGP)"},
        color="Sales",
        color_continuous_scale=CHART_COLOR_SCALE,
    )
    fig4.update_layout(
        **CHART_LAYOUT, title_font_color="#355548", title_font_size=13,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    fig4.update_traces(textposition="outside")
    st.plotly_chart(fig4, width="stretch", config={"displayModeBar": False})

st.markdown('<h2 class="section-heading">Regional Breakdown</h2>', unsafe_allow_html=True)
regional_performance = (
    filtered.groupby("City", as_index=False)
    .agg(
        Orders=("Order_ID", "count"),
        Total_Sales_EGP=("Total_Sales_EGP", "sum"),
        Total_Profit_EGP=("Total_Profit_EGP", "sum"),
        Average_Delivery_Days=("Delivery_Time_Days", "mean"),
    )
    .sort_values("Total_Sales_EGP", ascending=False)
)
st.dataframe(
    regional_performance.style.format(
        {
            "Total_Sales_EGP": "{:,.2f} EGP",
            "Total_Profit_EGP": "{:,.2f} EGP",
            "Average_Delivery_Days": "{:.2f} days",
        }
    ),
    use_container_width=True,
)

st.markdown('<h2 class="section-heading">Recommended Actions</h2>', unsafe_allow_html=True)
st.markdown(
    """
    - **Improve website checkout:** Prioritize checkout speed and usability to increase completed purchases.
    - **Bundle high-margin products:** Pair popular products with complementary, slower-moving accessories to increase average order value.
    - **Launch a loyalty program:** Offer relevant rewards to encourage repeat purchases.
    - **Test free-shipping thresholds:** Run an A/B test to measure whether a free-shipping offer increases new-customer order value.
    """
)
