import os

# OpenMP fix - must precede sklearn/scipy imports
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"

import warnings
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

warnings.filterwarnings("ignore")

# Load credentials from .env
load_dotenv()

# Configuration
PG_HOST     = os.getenv("PG_HOST", "localhost")
PG_PORT     = int(os.getenv("PG_PORT", 5432))
PG_USER     = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "")
PG_DB       = os.getenv("PG_DB", "socioeconomic_analytics")

INCOME_ORDER = [
    "Low income",
    "Lower middle income",
    "Upper middle income",
    "High income",
]

# ── Database helpers ───────────────────────────────────────────────────────────
@st.cache_resource
def get_engine():
    return create_engine(
        f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
    )


@st.cache_data(ttl=300)
def load_merged() -> pd.DataFrame:
    with get_engine().connect() as conn:
        return pd.read_sql(
            text("SELECT * FROM merged_development_data ORDER BY country_code, year"),
            conn,
        )


@st.cache_data(ttl=300)
def load_countries() -> pd.DataFrame:
    with get_engine().connect() as conn:
        return pd.read_sql(text("SELECT * FROM countries"), conn)


# ── Page setup ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Global Socioeconomic Analytics",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🌍 Global Socioeconomic Development Analytics")
st.caption(
    "Data sourced from the World Bank Development Indicators API. "
    "Stored in MongoDB Atlas and PostgreSQL."
)

# ── Load data ──────────────────────────────────────────────────────────────────
try:
    df_full  = load_merged()
    df_ctry  = load_countries()
except Exception as exc:
    st.error(
        f"Could not connect to PostgreSQL. "
        f"Run the Jupyter notebook first to populate the database.\n\n{exc}"
    )
    st.stop()

# ── Sidebar filters ────────────────────────────────────────────────────────────
st.sidebar.header("Filters")

min_yr = int(df_full["year"].min())
max_yr = int(df_full["year"].max())
year_range = st.sidebar.slider(
    "Year range", min_value=min_yr, max_value=max_yr,
    value=(2005, max_yr), step=1,
)

all_regions = sorted(df_full["region"].dropna().unique().tolist())
sel_regions = st.sidebar.multiselect(
    "Regions", options=all_regions, default=all_regions
)

all_incomes = [i for i in INCOME_ORDER if i in df_full["income_group"].dropna().unique()]
sel_incomes = st.sidebar.multiselect(
    "Income groups", options=all_incomes, default=all_incomes
)

# Apply filters
df = df_full[
    (df_full["year"] >= year_range[0])
    & (df_full["year"] <= year_range[1])
    & (df_full["region"].isin(sel_regions))
    & (df_full["income_group"].isin(sel_incomes))
].copy()

if df.empty:
    st.warning("No data matches the current filter selection.")
    st.stop()

# ── Top-level KPI row ──────────────────────────────────────────────────────────
st.divider()
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

df_latest = (
    df.sort_values("year")
      .groupby("country_code", as_index=False)
      .last()
)

kpi1.metric("Countries", f"{df_latest['country_code'].nunique():,}")
kpi2.metric(
    "Avg GDP per Capita",
    f"${df_latest['gdp_per_capita'].mean():,.0f}",
)
kpi3.metric(
    "Avg Life Expectancy",
    f"{df_latest['life_expectancy'].mean():.1f} yrs",
)
kpi4.metric(
    "Avg Literacy Rate",
    f"{df_latest['literacy_rate'].mean():.1f}%",
)
kpi5.metric(
    "Avg Unemployment",
    f"{df_latest['unemployment_rate'].mean():.1f}%",
)
st.divider()

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🗺️ Global Overview",
    "📈 Economic Trends",
    "🎓 Education Analysis",
    "🔗 Correlations",
    "🏳️ Country Deep Dive",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Global Overview
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("GDP per Capita — Latest Available Year per Country")

    map_metric = st.selectbox(
        "Map metric",
        options=["gdp_per_capita", "life_expectancy",
                 "literacy_rate", "unemployment_rate"],
        format_func=lambda c: c.replace("_", " ").title(),
    )

    df_map = (
        df.dropna(subset=[map_metric])
          .sort_values("year")
          .groupby("country_code", as_index=False)
          .last()
    )

    fig_map = px.choropleth(
        df_map,
        locations="country_code",
        color=map_metric,
        hover_name="country_name",
        hover_data={"year": True, map_metric: ":.2f"},
        color_continuous_scale="Viridis",
        labels={map_metric: map_metric.replace("_", " ").title()},
        title=f"World Map — {map_metric.replace('_', ' ').title()}",
    )
    fig_map.update_layout(height=480, margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig_map, use_container_width=True)

    # Income group breakdown
    st.subheader("Income Group Summary")
    df_ig = (
        df_latest
        .dropna(subset=["income_group"])
        .groupby("income_group")[["gdp_per_capita", "life_expectancy",
                                   "literacy_rate", "unemployment_rate"]]
        .mean()
        .reindex([i for i in INCOME_ORDER if i in df_latest["income_group"].unique()])
        .round(2)
    )
    st.dataframe(df_ig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Economic Trends
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Average GDP per Capita by Region Over Time")

    df_reg_trend = (
        df.dropna(subset=["gdp_per_capita", "region"])
          .groupby(["region", "year"], as_index=False)["gdp_per_capita"]
          .mean()
    )
    fig_reg = px.line(
        df_reg_trend,
        x="year", y="gdp_per_capita",
        color="region",
        markers=True,
        labels={"gdp_per_capita": "GDP per Capita (USD)", "year": "Year"},
    )
    fig_reg.update_traces(marker=dict(size=4))
    st.plotly_chart(fig_reg, use_container_width=True)

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Top 15 Countries by GDP per Capita")
        yr_top = st.slider("Select year", min_yr, max_yr, max_yr, key="top_yr")
        df_top = (
            df.query(f"year == {yr_top}")
              .dropna(subset=["gdp_per_capita"])
              .nlargest(15, "gdp_per_capita")
        )
        fig_top = px.bar(
            df_top.sort_values("gdp_per_capita"),
            x="gdp_per_capita", y="country_name",
            orientation="h", color="income_group",
            labels={"gdp_per_capita": "GDP per Capita (USD)", "country_name": ""},
        )
        st.plotly_chart(fig_top, use_container_width=True)

    with col_b:
        st.subheader("GDP per Capita Distribution by Income Group")
        df_box = df.dropna(subset=["gdp_per_capita", "income_group"]).copy()
        df_box["income_group"] = pd.Categorical(
            df_box["income_group"], categories=INCOME_ORDER, ordered=True
        )
        fig_box = px.box(
            df_box.dropna(subset=["income_group"]),
            x="income_group", y="gdp_per_capita",
            color="income_group",
            category_orders={"income_group": INCOME_ORDER},
            labels={"gdp_per_capita": "GDP per Capita (USD)",
                    "income_group": "Income Group"},
            points=False,
        )
        st.plotly_chart(fig_box, use_container_width=True)

    st.subheader("G7 & BRICS — GDP per Capita Trend")
    G7    = ["USA", "GBR", "DEU", "FRA", "JPN", "ITA", "CAN"]
    BRICS = ["BRA", "RUS", "IND", "CHN", "ZAF"]
    df_focus = (
        df[df["country_code"].isin(G7 + BRICS)]
          .dropna(subset=["gdp_per_capita"])
          .sort_values("year")
    )
    fig_focus = px.line(
        df_focus, x="year", y="gdp_per_capita",
        color="country_name", markers=True,
        labels={"gdp_per_capita": "GDP per Capita (USD)", "country_name": "Country"},
    )
    fig_focus.update_traces(marker=dict(size=4))
    st.plotly_chart(fig_focus, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Education Analysis
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Education Indicators by Income Group")

    col_c, col_d = st.columns(2)

    with col_c:
        df_lit = (
            df.dropna(subset=["literacy_rate", "income_group"])
              .groupby(["income_group", "year"], as_index=False)["literacy_rate"]
              .mean()
        )
        fig_lit = px.line(
            df_lit, x="year", y="literacy_rate",
            color="income_group",
            category_orders={"income_group": INCOME_ORDER},
            markers=True,
            title="Literacy Rate Trend by Income Group",
            labels={"literacy_rate": "Literacy Rate (%)", "income_group": "Income Group"},
        )
        fig_lit.update_traces(marker=dict(size=4))
        st.plotly_chart(fig_lit, use_container_width=True)

    with col_d:
        df_sec = (
            df.dropna(subset=["secondary_enrollment", "income_group"])
              .groupby(["income_group", "year"], as_index=False)["secondary_enrollment"]
              .mean()
        )
        fig_sec = px.area(
            df_sec, x="year", y="secondary_enrollment",
            color="income_group",
            category_orders={"income_group": INCOME_ORDER},
            title="Secondary Enrollment Trend by Income Group",
            labels={"secondary_enrollment": "Enrollment (%)",
                    "income_group": "Income Group"},
        )
        st.plotly_chart(fig_sec, use_container_width=True)

    st.subheader("Education Expenditure vs GDP per Capita")
    df_exp = df.dropna(subset=["edu_expenditure_pct_gdp", "gdp_per_capita",
                                "income_group"])
    fig_exp = px.scatter(
        df_exp,
        x="gdp_per_capita",
        y="edu_expenditure_pct_gdp",
        color="income_group",
        log_x=True,
        opacity=0.45,
        hover_name="country_name",
        hover_data={"year": True},
        trendline="ols",
        category_orders={"income_group": INCOME_ORDER},
        labels={
            "gdp_per_capita"          : "GDP per Capita (USD, log scale)",
            "edu_expenditure_pct_gdp" : "Education Expenditure (% GDP)",
            "income_group"            : "Income Group",
        },
    )
    st.plotly_chart(fig_exp, use_container_width=True)

    st.subheader("Education Expenditure by Region (Latest 5-Year Average)")
    df_edu_reg = (
        df.query(f"year >= {max(year_range[1] - 4, min_yr)}")
          .dropna(subset=["edu_expenditure_pct_gdp", "region"])
          .groupby("region", as_index=False)["edu_expenditure_pct_gdp"]
          .mean()
          .sort_values("edu_expenditure_pct_gdp", ascending=False)
    )
    fig_edu_reg = px.bar(
        df_edu_reg, x="region", y="edu_expenditure_pct_gdp",
        color="region",
        labels={"edu_expenditure_pct_gdp": "Education Expenditure (% GDP)",
                "region": "Region"},
        text_auto=".2f",
    )
    fig_edu_reg.update_traces(textposition="outside")
    st.plotly_chart(fig_edu_reg, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — Correlations
# ═══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Bubble Chart — GDP vs Life Expectancy (sized by Population)")

    yr_bubble = st.select_slider(
        "Select year for bubble chart",
        options=sorted(df["year"].unique()),
        value=2019,
        key="bubble_yr",
    )
    df_bubble = df.query(f"year == {yr_bubble}").dropna(
        subset=["gdp_per_capita", "life_expectancy", "population", "income_group"]
    )
    fig_bubble = px.scatter(
        df_bubble,
        x="gdp_per_capita", y="life_expectancy",
        size="population",
        color="income_group",
        hover_name="country_name",
        size_max=60, log_x=True,
        category_orders={"income_group": INCOME_ORDER},
        labels={
            "gdp_per_capita" : "GDP per Capita (USD, log)",
            "life_expectancy": "Life Expectancy (years)",
            "income_group"   : "Income Group",
        },
        title=f"GDP per Capita vs Life Expectancy ({yr_bubble})",
    )
    st.plotly_chart(fig_bubble, use_container_width=True)

    st.subheader("Correlation Heatmap")
    corr_options = [
        "gdp_per_capita", "log_gdp_per_capita", "life_expectancy",
        "unemployment_rate", "literacy_rate",
        "secondary_enrollment", "tertiary_enrollment",
        "edu_expenditure_pct_gdp", "fdi_inflows",
    ]
    sel_corr = st.multiselect(
        "Select indicators for correlation",
        options=corr_options,
        default=["gdp_per_capita", "life_expectancy", "unemployment_rate",
                 "literacy_rate", "secondary_enrollment", "edu_expenditure_pct_gdp"],
    )
    if len(sel_corr) >= 2:
        corr_mat = df[sel_corr].dropna().corr()
        fig_heat = px.imshow(
            corr_mat.round(2),
            text_auto=True,
            color_continuous_scale="RdYlGn",
            zmin=-1, zmax=1,
            aspect="auto",
            title="Pearson Correlation Matrix",
        )
        fig_heat.update_layout(height=500)
        st.plotly_chart(fig_heat, use_container_width=True)
    else:
        st.info("Select at least 2 indicators.")

    st.subheader("Unemployment vs Log GDP per Capita")
    df_unemp = df.dropna(subset=["unemployment_rate", "log_gdp_per_capita", "region"])
    fig_unemp = px.scatter(
        df_unemp,
        x="log_gdp_per_capita", y="unemployment_rate",
        color="region", opacity=0.4,
        hover_name="country_name",
        trendline="ols",
        labels={
            "log_gdp_per_capita" : "Log GDP per Capita",
            "unemployment_rate"  : "Unemployment Rate (%)",
        },
    )
    st.plotly_chart(fig_unemp, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 — Country Deep Dive
# ═══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.subheader("Country Deep Dive")

    all_countries = sorted(df["country_name"].dropna().unique().tolist())
    sel_countries = st.multiselect(
        "Select countries (up to 8)",
        options=all_countries,
        default=["United States", "China", "India", "Germany",
                 "Brazil", "Nigeria", "Japan", "South Africa"],
        max_selections=8,
    )

    if not sel_countries:
        st.info("Select at least one country.")
    else:
        df_sel = df[df["country_name"].isin(sel_countries)].sort_values("year")

        col_e, col_f = st.columns(2)

        with col_e:
            fig_c1 = px.line(
                df_sel.dropna(subset=["gdp_per_capita"]),
                x="year", y="gdp_per_capita",
                color="country_name", markers=True,
                title="GDP per Capita Over Time",
                labels={"gdp_per_capita": "GDP per Capita (USD)",
                        "country_name": "Country"},
            )
            fig_c1.update_traces(marker=dict(size=4))
            st.plotly_chart(fig_c1, use_container_width=True)

        with col_f:
            fig_c2 = px.line(
                df_sel.dropna(subset=["life_expectancy"]),
                x="year", y="life_expectancy",
                color="country_name", markers=True,
                title="Life Expectancy Over Time",
                labels={"life_expectancy": "Life Expectancy (years)",
                        "country_name": "Country"},
            )
            fig_c2.update_traces(marker=dict(size=4))
            st.plotly_chart(fig_c2, use_container_width=True)

        col_g, col_h = st.columns(2)

        with col_g:
            fig_c3 = px.line(
                df_sel.dropna(subset=["unemployment_rate"]),
                x="year", y="unemployment_rate",
                color="country_name", markers=True,
                title="Unemployment Rate Over Time",
                labels={"unemployment_rate": "Unemployment (%)",
                        "country_name": "Country"},
            )
            fig_c3.update_traces(marker=dict(size=4))
            st.plotly_chart(fig_c3, use_container_width=True)

        with col_h:
            fig_c4 = px.line(
                df_sel.dropna(subset=["secondary_enrollment"]),
                x="year", y="secondary_enrollment",
                color="country_name", markers=True,
                title="Secondary School Enrollment Over Time",
                labels={"secondary_enrollment": "Enrollment (%)",
                        "country_name": "Country"},
            )
            fig_c4.update_traces(marker=dict(size=4))
            st.plotly_chart(fig_c4, use_container_width=True)

        st.subheader("Latest Indicators Summary")
        df_summary = (
            df_sel.sort_values("year")
                  .groupby("country_name", as_index=False)
                  .last()
                  [["country_name", "year", "region", "income_group",
                     "gdp_per_capita", "life_expectancy", "unemployment_rate",
                     "literacy_rate", "secondary_enrollment",
                     "edu_expenditure_pct_gdp"]]
                  .rename(columns={
                      "country_name"           : "Country",
                      "year"                   : "Year",
                      "region"                 : "Region",
                      "income_group"           : "Income Group",
                      "gdp_per_capita"         : "GDP per Capita",
                      "life_expectancy"        : "Life Expectancy",
                      "unemployment_rate"      : "Unemployment %",
                      "literacy_rate"          : "Literacy %",
                      "secondary_enrollment"   : "Sec. Enrollment %",
                      "edu_expenditure_pct_gdp": "Edu Exp % GDP",
                  })
        )
        st.dataframe(df_summary.set_index("Country").round(2),
                     use_container_width=True)

st.divider()
st.caption(
    "Data: World Bank Development Indicators API · "
    "Storage: MongoDB Atlas + PostgreSQL · "
    "Dashboard: Streamlit + Plotly"
)
