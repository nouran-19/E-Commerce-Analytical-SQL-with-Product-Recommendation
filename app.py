"""
app.py – Streamlit dashboard for the E-Commerce Data Warehouse project.

Run with:  streamlit run app.py
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

import db

# ---------------------------------------------------------------------------
# Page config & global styling
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="E-Commerce Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Premium dark-theme CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ---------- Global ---------- */
html, body, [class*="st-"] {
    font-family: 'Inter', sans-serif;
}
.stApp {
    background: linear-gradient(135deg, #0f0c29 0%, #1a1a2e 40%, #16213e 100%);
}
header[data-testid="stHeader"] {
    background: transparent;
}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {
    background: rgba(15, 12, 41, 0.95);
    border-right: 1px solid rgba(255,255,255,0.06);
}
section[data-testid="stSidebar"] .stRadio label {
    color: #e0e0e0 !important;
}

/* ---------- KPI cards ---------- */
.kpi-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 1.2rem 1.5rem;
    backdrop-filter: blur(10px);
    transition: transform 0.25s, box-shadow 0.25s;
    text-align: center;
}
.kpi-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 30px rgba(99,102,241,0.18);
}
.kpi-label {
    font-size: 0.78rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: #a0aec0;
    margin-bottom: 0.3rem;
}
.kpi-value {
    font-size: 1.6rem;
    font-weight: 700;
    background: linear-gradient(135deg, #667eea, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* ---------- Section titles ---------- */
.section-title {
    font-size: 1.15rem;
    font-weight: 600;
    color: #e2e8f0;
    margin: 1.8rem 0 0.6rem 0;
    padding-bottom: 0.3rem;
    border-bottom: 2px solid rgba(99,102,241,0.3);
    display: inline-block;
}

/* ---------- Recommendation cards ---------- */
.rec-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 14px;
    padding: 1.2rem;
    backdrop-filter: blur(8px);
    transition: transform 0.2s, box-shadow 0.2s;
    height: 100%;
}
.rec-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 24px rgba(139,92,246,0.2);
}
.rec-rank {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #a78bfa;
    margin-bottom: 0.3rem;
}
.rec-name {
    font-size: 1rem;
    font-weight: 600;
    color: #f1f5f9;
    margin-bottom: 0.5rem;
    line-height: 1.3;
}
.rec-detail {
    font-size: 0.78rem;
    color: #94a3b8;
    margin-bottom: 0.15rem;
}
.rec-score {
    font-size: 1.35rem;
    font-weight: 700;
    background: linear-gradient(135deg, #34d399, #6ee7b7);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-top: 0.6rem;
}

/* ---------- Tables ---------- */
.stDataFrame {
    border-radius: 12px;
    overflow: hidden;
}
</style>
""", unsafe_allow_html=True)

# Plotly dark template
_PLOTLY_TEMPLATE = "plotly_dark"
_COLOR_SEQ = ["#667eea", "#a78bfa", "#34d399", "#fbbf24", "#f87171",
              "#60a5fa", "#c084fc", "#38bdf8", "#fb923c", "#4ade80"]


def _plotly_defaults(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        template=_PLOTLY_TEMPLATE,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#e2e8f0"),
        margin=dict(l=40, r=20, t=40, b=40),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.05)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.05)")
    return fig


def _kpi_html(label: str, value: str) -> str:
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
    </div>"""


# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🛒 E-Commerce DW")
    st.caption("Analytical SQL Dashboard")
    page = st.radio(
        "Navigate",
        ["📊 Overview", "📈 Revenue Analysis", "📦 Product Analytics",
         "👥 Customer Analytics", "🎯 Recommendations"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.caption("Built with Streamlit · SQLite · Plotly")


# =====================================================================
#  PAGE: Overview
# =====================================================================
if page == "📊 Overview":
    st.markdown("# 📊 Dashboard Overview")
    st.caption("Key performance indicators at a glance")

    kpis = db.get_overview_kpis()

    cols = st.columns(6)
    cards = [
        ("Total Revenue", f"EGP {kpis['total_revenue']:,.0f}"),
        ("Gross Profit", f"EGP {kpis['total_profit']:,.0f}"),
        ("Total Orders", f"{int(kpis['total_orders']):,}"),
        ("Customers", f"{int(kpis['total_customers']):,}"),
        ("Avg Order Value", f"EGP {kpis['aov']:,.0f}"),
        ("Profit Margin", f"{kpis['profit_margin_pct']:.1f}%"),
    ]
    for col, (label, value) in zip(cols, cards):
        col.markdown(_kpi_html(label, value), unsafe_allow_html=True)

    st.markdown("")  # spacer

    # Monthly revenue trend
    monthly = db.get_monthly_kpis()
    fig = px.area(
        monthly, x="ym_label", y="revenue",
        title="Monthly Revenue Trend",
        labels={"ym_label": "Month", "revenue": "Revenue (EGP)"},
        color_discrete_sequence=["#667eea"],
    )
    fig.update_traces(fill="tozeroy", fillcolor="rgba(102,126,234,0.15)", line_width=2.5)
    st.plotly_chart(_plotly_defaults(fig), use_container_width=True)

    # Profit & orders dual chart
    c1, c2 = st.columns(2)
    with c1:
        fig2 = px.bar(
            monthly, x="ym_label", y="gross_profit",
            title="Monthly Gross Profit",
            labels={"ym_label": "Month", "gross_profit": "Profit (EGP)"},
            color_discrete_sequence=["#34d399"],
        )
        st.plotly_chart(_plotly_defaults(fig2), use_container_width=True)
    with c2:
        fig3 = px.line(
            monthly, x="ym_label", y="unique_customers",
            title="Monthly Active Customers",
            labels={"ym_label": "Month", "unique_customers": "Customers"},
            color_discrete_sequence=["#a78bfa"],
            markers=True,
        )
        st.plotly_chart(_plotly_defaults(fig3), use_container_width=True)


# =====================================================================
#  PAGE: Revenue Analysis
# =====================================================================
elif page == "📈 Revenue Analysis":
    st.markdown("# 📈 Revenue Analysis")
    st.caption("Month-over-month growth, cumulative revenue, and moving averages")

    df = db.get_monthly_revenue_growth()

    # MoM growth bar chart
    fig = go.Figure()
    colors = ["#34d399" if v and v >= 0 else "#f87171" for v in df["mom_growth_pct"]]
    fig.add_trace(go.Bar(
        x=df["ym_label"], y=df["mom_growth_pct"],
        marker_color=colors, name="MoM Growth %",
        text=[f"{v:+.1f}%" if pd.notna(v) else "" for v in df["mom_growth_pct"]],
        textposition="outside",
    ))
    fig.update_layout(title="Month-over-Month Revenue Growth (%)")
    st.plotly_chart(_plotly_defaults(fig), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        # Cumulative revenue
        fig2 = px.area(
            df, x="ym_label", y="cumulative_revenue",
            title="Cumulative Revenue",
            labels={"ym_label": "Month", "cumulative_revenue": "Cumulative (EGP)"},
            color_discrete_sequence=["#fbbf24"],
        )
        fig2.update_traces(fill="tozeroy", fillcolor="rgba(251,191,36,0.12)", line_width=2.5)
        st.plotly_chart(_plotly_defaults(fig2), use_container_width=True)

    with c2:
        # Revenue + 3-month MA
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            x=df["ym_label"], y=df["revenue"],
            name="Revenue", marker_color="rgba(102,126,234,0.5)",
        ))
        fig3.add_trace(go.Scatter(
            x=df["ym_label"], y=df["ma_3m"],
            name="3-Month MA", mode="lines+markers",
            line=dict(color="#f87171", width=2.5),
        ))
        fig3.update_layout(title="Revenue vs 3-Month Moving Average", barmode="overlay")
        st.plotly_chart(_plotly_defaults(fig3), use_container_width=True)

    # Detailed table
    st.markdown('<div class="section-title">Detailed Monthly Metrics</div>', unsafe_allow_html=True)
    display_df = df[["ym_label", "revenue", "mom_growth_pct", "cumulative_revenue", "ma_3m",
                      "total_orders", "unique_customers", "aov", "profit_margin_pct"]].copy()
    display_df.columns = ["Month", "Revenue", "MoM %", "Cumulative", "3M MA",
                           "Orders", "Customers", "AOV", "Margin %"]
    st.dataframe(display_df, use_container_width=True, hide_index=True)


# =====================================================================
#  PAGE: Product Analytics
# =====================================================================
elif page == "📦 Product Analytics":
    st.markdown("# 📦 Product Analytics")
    st.caption("Top products, category breakdown, and product rankings")

    top_n = st.slider("Show top N products", 5, 40, 15)
    top_prods = db.get_top_products(top_n)

    # Horizontal bar chart
    fig = px.bar(
        top_prods.sort_values("product_revenue"),
        y="product_name", x="product_revenue",
        orientation="h",
        title=f"Top {top_n} Products by Revenue",
        labels={"product_name": "", "product_revenue": "Revenue (EGP)"},
        color="product_revenue",
        color_continuous_scale=["#1e1b4b", "#667eea", "#a78bfa"],
    )
    fig.update_layout(height=max(400, top_n * 32), coloraxis_showscale=False)
    st.plotly_chart(_plotly_defaults(fig), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        cat = db.get_category_share()
        fig2 = px.pie(
            cat, values="category_revenue", names="category_name",
            title="Category Revenue Share",
            color_discrete_sequence=_COLOR_SEQ,
            hole=0.45,
        )
        fig2.update_traces(textinfo="percent+label", textfont_size=11)
        st.plotly_chart(_plotly_defaults(fig2), use_container_width=True)

    with c2:
        fig3 = px.scatter(
            top_prods, x="product_revenue", y="product_profit",
            size="units_sold", color="brand",
            title="Revenue vs Profit (bubble = units)",
            labels={"product_revenue": "Revenue", "product_profit": "Profit"},
            color_discrete_sequence=_COLOR_SEQ,
            hover_name="product_name",
        )
        st.plotly_chart(_plotly_defaults(fig3), use_container_width=True)

    # Rankings table
    st.markdown('<div class="section-title">Product Rankings</div>', unsafe_allow_html=True)
    st.dataframe(
        top_prods[["revenue_rank", "product_name", "brand", "subcategory",
                    "product_revenue", "product_profit", "orders_count", "units_sold"]].rename(
            columns={
                "revenue_rank": "Rank", "product_name": "Product", "brand": "Brand",
                "subcategory": "Category", "product_revenue": "Revenue",
                "product_profit": "Profit", "orders_count": "Orders", "units_sold": "Units",
            }
        ),
        use_container_width=True, hide_index=True,
    )


# =====================================================================
#  PAGE: Customer Analytics
# =====================================================================
elif page == "👥 Customer Analytics":
    st.markdown("# 👥 Customer Analytics")
    st.caption("Lifetime value, segments, spending quartiles, and repeat purchases")

    clv = db.get_clv()
    rate = db.get_repeat_rate()
    segs = db.get_customer_segments()

    # KPI row
    cols = st.columns(4)
    cols[0].markdown(_kpi_html("Total Customers", f"{int(rate['total_customers'])}"), unsafe_allow_html=True)
    cols[1].markdown(_kpi_html("Repeat Customers", f"{int(rate['repeat_customers'])}"), unsafe_allow_html=True)
    cols[2].markdown(_kpi_html("Repeat Rate", f"{rate['repeat_purchase_rate_pct']:.1f}%"), unsafe_allow_html=True)
    avg_clv = clv["lifetime_revenue"].mean()
    cols[3].markdown(_kpi_html("Avg CLV", f"EGP {avg_clv:,.0f}"), unsafe_allow_html=True)

    st.markdown("")

    c1, c2 = st.columns(2)
    with c1:
        # CLV histogram
        fig = px.histogram(
            clv, x="lifetime_revenue", nbins=20,
            title="Customer Lifetime Value Distribution",
            labels={"lifetime_revenue": "Lifetime Revenue (EGP)"},
            color_discrete_sequence=["#667eea"],
        )
        st.plotly_chart(_plotly_defaults(fig), use_container_width=True)

    with c2:
        # Segment comparison
        fig2 = px.bar(
            segs, x="customer_segment", y="avg_revenue",
            color="customer_segment",
            title="Avg Revenue by Customer Segment",
            labels={"customer_segment": "Segment", "avg_revenue": "Avg Revenue (EGP)"},
            color_discrete_sequence=_COLOR_SEQ,
            text="avg_revenue",
        )
        fig2.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        st.plotly_chart(_plotly_defaults(fig2), use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        # Quartile breakdown
        q_counts = clv["spending_quartile"].value_counts().sort_index().reset_index()
        q_counts.columns = ["Quartile", "Count"]
        q_counts["Quartile"] = q_counts["Quartile"].map({1: "Q1 (Top)", 2: "Q2", 3: "Q3", 4: "Q4 (Bottom)"})
        fig3 = px.pie(
            q_counts, values="Count", names="Quartile",
            title="Spending Quartile Breakdown",
            color_discrete_sequence=["#667eea", "#a78bfa", "#fbbf24", "#f87171"],
            hole=0.4,
        )
        st.plotly_chart(_plotly_defaults(fig3), use_container_width=True)

    with c4:
        # Top 20 customers
        fig4 = px.bar(
            clv.head(20).sort_values("lifetime_revenue"),
            y="customer_name", x="lifetime_revenue",
            orientation="h",
            title="Top 20 Customers by CLV",
            labels={"customer_name": "", "lifetime_revenue": "Revenue (EGP)"},
            color="customer_segment",
            color_discrete_sequence=_COLOR_SEQ,
        )
        fig4.update_layout(height=500)
        st.plotly_chart(_plotly_defaults(fig4), use_container_width=True)

    # Full table
    st.markdown('<div class="section-title">All Customers</div>', unsafe_allow_html=True)
    st.dataframe(
        clv[["customer_name", "customer_segment", "city", "age_group",
             "total_orders", "lifetime_revenue", "lifetime_profit", "customer_aov",
             "spending_quartile"]].rename(columns={
            "customer_name": "Customer", "customer_segment": "Segment",
            "city": "City", "age_group": "Age",
            "total_orders": "Orders", "lifetime_revenue": "Revenue",
            "lifetime_profit": "Profit", "customer_aov": "AOV",
            "spending_quartile": "Quartile",
        }),
        use_container_width=True, hide_index=True,
    )


# =====================================================================
#  PAGE: Recommendations
# =====================================================================
elif page == "🎯 Recommendations":
    st.markdown("# 🎯 Product Recommendations")
    st.caption("Select a product to see its top-4 recommended products based on co-purchase scoring")

    products = db.get_product_list()

    # Build label → key mapping
    product_options = {
        f"{row['product_name']}  ({row['product_id']})": row["product_key"]
        for _, row in products.iterrows()
    }

    selected_label = st.selectbox(
        "Choose a product",
        options=list(product_options.keys()),
        index=0,
    )
    selected_key = product_options[selected_label]

    recs = db.get_recommendations_for(selected_key)

    if recs.empty:
        st.info("No recommendations available for this product (no co-purchase data).")
    else:
        cols = st.columns(len(recs))
        for col, (_, row) in zip(cols, recs.iterrows()):
            col.markdown(f"""
            <div class="rec-card">
                <div class="rec-rank">#{int(row['recommendation_rank'])} Recommendation</div>
                <div class="rec-name">{row['candidate_product_name']}</div>
                <div class="rec-detail">🏷️ {row['candidate_brand']} · {row['candidate_subcategory']}</div>
                <div class="rec-detail">💰 EGP {row['candidate_price']:,.0f}</div>
                <div class="rec-score">{row['recommendation_score']:.1f}</div>
                <div class="rec-detail" style="margin-top:2px">recommendation score</div>
            </div>
            """, unsafe_allow_html=True)

    # Show scoring explanation
    with st.expander("📐 How recommendations are scored"):
        st.markdown("""
        The recommendation score (0–100) is a **weighted composite** of five normalized signals
        plus an availability bonus. All signals are normalized **per-source product** (for frequency
        and recency) or globally (for popularity and margin). Uses **exponential recency decay**
        for sharper trend sensitivity.

        | Factor | Weight | Description |
        |--------|--------|-------------|
        | **Co-purchase frequency** | 40% | How often the two products appear in the same order (normalized per source product) |
        | **Recency** | 25% | Exponential time-decay — recent co-purchases score much higher (90-day half-life) |
        | **Category match** | 10% | Same subcategory = full bonus, same parent category = half bonus |
        | **Candidate popularity** | 10% | How many distinct orders the recommended product has |
        | **Profit margin** | 10% | Higher-margin candidates are preferred |
        | **Availability** | 5% | Only active products are recommended |

        All signals use `COALESCE` to safely handle NULL values. Inactive products are filtered out.
        """)

    # Full table
    st.markdown('<div class="section-title">All Recommendations for This Product</div>',
                unsafe_allow_html=True)
    if not recs.empty:
        st.dataframe(
            recs[["recommendation_rank", "candidate_product_name", "candidate_brand",
                  "candidate_subcategory", "candidate_price", "recommendation_score"]].rename(
                columns={
                    "recommendation_rank": "Rank", "candidate_product_name": "Product",
                    "candidate_brand": "Brand", "candidate_subcategory": "Category",
                    "candidate_price": "Price (EGP)", "recommendation_score": "Score",
                }
            ),
            use_container_width=True, hide_index=True,
        )
