"""
Transport Emissions Dashboard
Main page: Global Overview

Developed for 5DATA004C Data Science Project Lifecycle
University of Westminster
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.data_loader import load_country_data, get_kpi_metrics


# ============================================================================
# PAGE CONFIG
# ============================================================================
st.set_page_config(
    page_title="Transport Emissions Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================================
# CUSTOM CSS
# ============================================================================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1B4332;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #2D6A4F;
        margin-bottom: 1.5rem;
    }
    .sub-header {
        font-size: 1.25rem;
        color: #40916C;
        margin-bottom: 2rem;
    }
    div[data-testid="stMetric"] {
        background-color: #F1F8E9;
        border: 1px solid #D8F3DC;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    div[data-testid="stMetric"] label {
        color: #40916C !important;
        font-weight: 600 !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #1B4332 !important;
        font-size: 1.8rem !important;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# LOAD DATA
# ============================================================================
df = load_country_data()
kpis = get_kpi_metrics(df)


# ============================================================================
# SIDEBAR
# ============================================================================
with st.sidebar:
    st.title("🌍 Transport Emissions")
    st.markdown("**5DATA004C Coursework**")
    st.markdown("---")

    st.markdown("### 📌 About")
    st.markdown(
        "Interactive dashboard analyzing global transport-sector "
        "greenhouse gas emissions (1990–2021)."
    )
    st.markdown("---")

    st.markdown("### 🎛️ Filters")
    year_range = st.slider(
        "Year range",
        min_value=int(df['year'].min()),
        max_value=int(df['year'].max()),
        value=(int(df['year'].min()), int(df['year'].max())),
    )

    continents = ['All'] + sorted(df['continent'].unique().tolist())
    selected_continent = st.selectbox("Continent", continents)

    st.markdown("---")
    st.markdown("### 📊 Dataset")
    st.markdown("**Source:** WRI Climate Watch")
    st.markdown("**Access:** World Bank Data360")


# ============================================================================
# FILTER DATA BASED ON SIDEBAR
# ============================================================================
df_filtered = df[
    (df['year'] >= year_range[0]) &
    (df['year'] <= year_range[1])
]
if selected_continent != 'All':
    df_filtered = df_filtered[df_filtered['continent'] == selected_continent]


# ============================================================================
# MAIN CONTENT
# ============================================================================
st.markdown('<div class="main-header">🌍 Global Transport Emissions Overview</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Greenhouse gas emissions from the global '
    'transport sector (1990–2021)</div>',
    unsafe_allow_html=True
)

# ----- KPI ROW -----
st.markdown("### 📈 Headline Metrics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="🌐 Latest Global Emissions",
        value=f"{kpis['total_latest']:,.0f} MtCO₂e",
        delta=f"{kpis['pct_change']:+.1f}% since {kpis['earliest_year']}",
    )

with col2:
    st.metric(
        label="🏭 Top Emitter",
        value=kpis['top_emitter'],
        delta=f"{kpis['top_emitter_value']:,.0f} MtCO₂e",
        delta_color="off"
    )

with col3:
    st.metric(
        label="🌎 Countries Tracked",
        value=f"{kpis['num_countries']}",
    )

with col4:
    st.metric(
        label="📅 Years of Data",
        value=f"{kpis['num_years']}",
        delta=f"{kpis['earliest_year']}–{kpis['latest_year']}",
        delta_color="off"
    )

st.markdown("---")

# ----- TABS FOR MAIN CHARTS -----
tab1, tab2, tab3 = st.tabs(["🗺️ World Map", "📊 Top Emitters", "📈 Global Trend"])

with tab1:
    st.markdown("#### Interactive World Map")
    st.markdown("*Hover over countries to see exact emission values. Use the slider below to change the year.*")

    selected_year = st.slider(
        "Select year for map",
        min_value=int(df_filtered['year'].min()),
        max_value=int(df_filtered['year'].max()),
        value=int(df_filtered['year'].max()),
    )

    map_df = df_filtered[df_filtered['year'] == selected_year]

    fig_map = px.choropleth(
        map_df,
        locations='country_code',
        color='emissions_mtco2e',
        hover_name='country',
        hover_data={'emissions_mtco2e': ':,.1f', 'continent': True, 'country_code': False},
        color_continuous_scale='Reds',
        title=f'Transport Emissions by Country — {selected_year}',
        labels={'emissions_mtco2e': 'MtCO₂e'},
    )
    fig_map.update_layout(
        height=550,
        geo=dict(showframe=False, showcoastlines=True, projection_type='natural earth'),
        margin=dict(l=0, r=0, t=50, b=0),
    )
    st.plotly_chart(fig_map, use_container_width=True)

with tab2:
    st.markdown("#### Top 10 Emitters")

    view_year = st.slider(
        "Select year for ranking",
        min_value=int(df_filtered['year'].min()),
        max_value=int(df_filtered['year'].max()),
        value=int(df_filtered['year'].max()),
        key='top10_year',
    )

    top10 = df_filtered[df_filtered['year'] == view_year].nlargest(10, 'emissions_mtco2e')

    fig_bar = px.bar(
        top10.sort_values('emissions_mtco2e'),
        x='emissions_mtco2e',
        y='country',
        orientation='h',
        color='emissions_mtco2e',
        color_continuous_scale='Reds',
        title=f'Top 10 Transport Emitters — {view_year}',
        labels={'emissions_mtco2e': 'Emissions (MtCO₂e)', 'country': ''},
    )
    fig_bar.update_layout(height=500, showlegend=False)
    st.plotly_chart(fig_bar, use_container_width=True)

    # Show concentration stat
    total_top10 = top10['emissions_mtco2e'].sum()
    total_world = df_filtered[df_filtered['year'] == view_year]['emissions_mtco2e'].sum()
    concentration = (total_top10 / total_world) * 100
    st.info(f"💡 **Insight:** The top 10 countries account for **{concentration:.1f}%** of global transport emissions in {view_year}.")

with tab3:
    st.markdown("#### Global Transport Emissions Over Time")

    yearly_total = df_filtered.groupby('year')['emissions_mtco2e'].sum().reset_index()

    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(
        x=yearly_total['year'],
        y=yearly_total['emissions_mtco2e'],
        mode='lines',
        fill='tozeroy',
        line=dict(color='#2D6A4F', width=3),
        fillcolor='rgba(45, 106, 79, 0.2)',
        name='Total Global Emissions',
        hovertemplate='Year: %{x}<br>Emissions: %{y:,.0f} MtCO₂e<extra></extra>',
    ))

    # Highlight COVID-19 dip if 2020 is in range
    if 2020 in yearly_total['year'].values:
        fig_line.add_vline(x=2020, line_dash="dash", line_color="crimson", opacity=0.7)
        fig_line.add_annotation(
            x=2020, y=yearly_total[yearly_total['year'] == 2020]['emissions_mtco2e'].values[0],
            text="COVID-19<br>Dip",
            showarrow=True, arrowhead=1,
            bgcolor="crimson", font=dict(color="white"),
        )

    fig_line.update_layout(
        title='Global Transport Emissions Trend',
        xaxis_title='Year',
        yaxis_title='Total Emissions (MtCO₂e)',
        height=500,
        hovermode='x unified',
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # Year-over-year commentary
    if len(yearly_total) > 1:
        first_year = yearly_total.iloc[0]
        last_year = yearly_total.iloc[-1]
        pct = ((last_year['emissions_mtco2e'] - first_year['emissions_mtco2e']) / first_year['emissions_mtco2e']) * 100
        st.info(
            f"💡 **Insight:** From **{first_year['year']}** to **{last_year['year']}**, "
            f"global transport emissions changed by **{pct:+.1f}%**, going from "
            f"{first_year['emissions_mtco2e']:,.0f} to {last_year['emissions_mtco2e']:,.0f} MtCO₂e."
        )

st.markdown("---")
st.caption("📚 Data source: WRI Climate Watch via World Bank Data360 • Dashboard by Madhushakar")