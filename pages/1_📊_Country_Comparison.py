"""
Country Comparison Page
Compare transport emissions across multiple selected countries.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.data_loader import load_country_data


# ============================================================================
# PAGE CONFIG
# ============================================================================
st.set_page_config(
    page_title="Country Comparison",
    page_icon="📊",
    layout="wide",
)

# ============================================================================
# CUSTOM CSS (matches main page theme)
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
        font-size: 1.1rem;
        color: #40916C;
        margin-bottom: 2rem;
    }
    div[data-testid="stMetric"] {
        background-color: #F1F8E9;
        border: 1px solid #D8F3DC;
        padding: 1rem;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# LOAD DATA
# ============================================================================
df = load_country_data()


# ============================================================================
# HEADER
# ============================================================================
st.markdown('<div class="main-header">📊 Country Comparison</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Compare transport emissions across countries '
    'and spot divergent trajectories.</div>',
    unsafe_allow_html=True
)


# ============================================================================
# COUNTRY SELECTOR
# ============================================================================
all_countries = sorted(df['country'].unique().tolist())

# Pre-populate with top 5 emitters in latest year
latest_year = df['year'].max()
default_countries = (
    df[df['year'] == latest_year]
    .nlargest(5, 'emissions_mtco2e')['country']
    .tolist()
)

selected_countries = st.multiselect(
    "🌎 Select countries to compare (up to 8 recommended):",
    options=all_countries,
    default=default_countries,
    help="Start typing to search. Selected countries appear as chips below.",
)

if len(selected_countries) == 0:
    st.warning("⚠️ Please select at least one country to see the comparison.")
    st.stop()

if len(selected_countries) > 8:
    st.info("ℹ️ You selected more than 8 countries — the charts may be harder to read.")

df_selected = df[df['country'].isin(selected_countries)]

st.markdown("---")


# ============================================================================
# METRIC CARDS
# ============================================================================
st.markdown(f"### 📈 Snapshot — {latest_year}")

cols = st.columns(min(len(selected_countries), 4))
for i, country in enumerate(selected_countries[:4]):
    country_data = df_selected[
        (df_selected['country'] == country) & (df_selected['year'] == latest_year)
    ]
    if not country_data.empty:
        value = country_data.iloc[0]['emissions_mtco2e']

        # Get year-over-year change
        country_2020 = df_selected[
            (df_selected['country'] == country) & (df_selected['year'] == latest_year - 1)
        ]
        if not country_2020.empty:
            prev_value = country_2020.iloc[0]['emissions_mtco2e']
            yoy = ((value - prev_value) / prev_value) * 100
            delta_text = f"{yoy:+.1f}% vs prev year"
        else:
            delta_text = None

        with cols[i]:
            st.metric(
                label=country,
                value=f"{value:,.1f} MtCO₂e",
                delta=delta_text,
                delta_color="inverse",  # lower is better for emissions
            )


# ============================================================================
# CHART TABS
# ============================================================================
st.markdown("---")
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Trend Lines", "🕸️ Radar", "📊 Growth Rate", "📋 Ranking Table"
])

# ----- TAB 1: Line chart -----
with tab1:
    st.markdown("#### Emissions Trend Over Time")

    y_axis_type = st.radio(
        "Y-axis scale:",
        options=["Linear", "Logarithmic"],
        horizontal=True,
        help="Use logarithmic when comparing countries of very different sizes.",
    )

    fig_line = px.line(
        df_selected,
        x='year',
        y='emissions_mtco2e',
        color='country',
        markers=True,
        title='Transport Emissions Over Time by Country',
        labels={'emissions_mtco2e': 'Emissions (MtCO₂e)', 'year': 'Year'},
    )
    fig_line.update_layout(
        height=500,
        hovermode='x unified',
        yaxis_type='log' if y_axis_type == 'Logarithmic' else 'linear',
    )
    st.plotly_chart(fig_line, use_container_width=True)

# ----- TAB 2: Radar chart -----
with tab2:
    st.markdown("#### Multi-Dimensional Comparison (Radar Chart)")
    st.caption("Comparing across key metrics: Latest emissions, Peak emissions, Growth since 1990, Volatility")

    radar_data = []
    for country in selected_countries:
        cdata = df_selected[df_selected['country'] == country]
        if cdata.empty:
            continue

        latest_val = cdata[cdata['year'] == latest_year]['emissions_mtco2e']
        latest_val = latest_val.iloc[0] if not latest_val.empty else 0

        peak_val = cdata['emissions_mtco2e'].max()

        earliest = cdata.sort_values('year').iloc[0]
        latest = cdata.sort_values('year').iloc[-1]
        growth = ((latest['emissions_mtco2e'] - earliest['emissions_mtco2e']) / earliest['emissions_mtco2e']) * 100 if earliest['emissions_mtco2e'] > 0 else 0

        volatility = cdata['emissions_mtco2e'].std()

        radar_data.append({
            'country': country,
            'Latest': latest_val,
            'Peak': peak_val,
            'Growth %': growth,
            'Volatility': volatility,
        })

    if radar_data:
        radar_df = pd.DataFrame(radar_data).set_index('country')
        # Normalize each metric to 0-100 for visual comparison
        radar_norm = ((radar_df - radar_df.min()) / (radar_df.max() - radar_df.min())) * 100
        radar_norm = radar_norm.fillna(0)

        fig_radar = go.Figure()
        for country in radar_norm.index:
            fig_radar.add_trace(go.Scatterpolar(
                r=radar_norm.loc[country].values,
                theta=radar_norm.columns,
                fill='toself',
                name=country,
            ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=True,
            height=500,
            title="Normalized Metrics (0-100 scale across selected countries)",
        )
        st.plotly_chart(fig_radar, use_container_width=True)

        with st.expander("🔍 See raw values"):
            st.dataframe(radar_df.round(2), use_container_width=True)

# ----- TAB 3: Growth bar chart -----
with tab3:
    st.markdown("#### Emissions Growth (% change since 1990)")

    growth_data = []
    for country in selected_countries:
        cdata = df_selected[df_selected['country'] == country].sort_values('year')
        if len(cdata) < 2:
            continue
        start = cdata.iloc[0]['emissions_mtco2e']
        end = cdata.iloc[-1]['emissions_mtco2e']
        if start > 0:
            growth_data.append({
                'country': country,
                'growth_pct': ((end - start) / start) * 100,
            })

    if growth_data:
        growth_df = pd.DataFrame(growth_data).sort_values('growth_pct')
        fig_growth = px.bar(
            growth_df,
            x='growth_pct',
            y='country',
            orientation='h',
            color='growth_pct',
            color_continuous_scale='RdYlGn_r',  # red=bad growth, green=reduction
            title='Emissions % Change (1990 → Latest)',
            labels={'growth_pct': '% Change', 'country': ''},
        )
        fig_growth.update_layout(height=max(350, 50 * len(growth_df)), showlegend=False)
        st.plotly_chart(fig_growth, use_container_width=True)

# ----- TAB 4: Table + Download -----
with tab4:
    st.markdown("#### Data Table")

    pivot = df_selected.pivot_table(
        index='country',
        columns='year',
        values='emissions_mtco2e',
    ).round(2)

    st.dataframe(pivot, use_container_width=True, height=400)

    st.markdown("#### 📥 Download Filtered Data")
    csv = df_selected.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="💾 Download CSV",
        data=csv,
        file_name=f"emissions_comparison_{'_'.join(selected_countries[:3])}.csv",
        mime="text/csv",
    )


# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.caption(f"Showing {len(selected_countries)} countries across {df_selected['year'].nunique()} years.")