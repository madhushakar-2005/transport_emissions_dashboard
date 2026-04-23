"""
Data Explorer Page
Interactive filtering, custom charts, and data export.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_loader import load_country_data


# ============================================================================
# PAGE CONFIG
# ============================================================================
st.set_page_config(
    page_title="Data Explorer",
    page_icon="🔍",
    layout="wide",
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
        font-size: 1.1rem;
        color: #40916C;
        margin-bottom: 2rem;
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
st.markdown('<div class="main-header">🔍 Data Explorer</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Slice the dataset any way you like. '
    'Build custom charts, filter, sort, and export.</div>',
    unsafe_allow_html=True
)


# ============================================================================
# SIDEBAR FILTERS
# ============================================================================
with st.sidebar:
    st.markdown("### 🎛️ Filters")

    # Continent filter
    all_continents = sorted(df['continent'].unique().tolist())
    selected_continents = st.multiselect(
        "Continent(s)",
        options=all_continents,
        default=all_continents,
    )

    # Year range filter
    year_range = st.slider(
        "Year range",
        min_value=int(df['year'].min()),
        max_value=int(df['year'].max()),
        value=(int(df['year'].min()), int(df['year'].max())),
    )

    # Emission threshold filter
    max_em = float(df['emissions_mtco2e'].max())
    emission_range = st.slider(
        "Emissions range (MtCO₂e)",
        min_value=0.0,
        max_value=max_em,
        value=(0.0, max_em),
        step=10.0,
    )

    # Country search
    country_search = st.text_input(
        "🔎 Search country name (optional)",
        placeholder="e.g. Germany",
    )


# ============================================================================
# APPLY FILTERS
# ============================================================================
df_filtered = df[
    (df['continent'].isin(selected_continents)) &
    (df['year'] >= year_range[0]) &
    (df['year'] <= year_range[1]) &
    (df['emissions_mtco2e'] >= emission_range[0]) &
    (df['emissions_mtco2e'] <= emission_range[1])
]

if country_search:
    df_filtered = df_filtered[
        df_filtered['country'].str.contains(country_search, case=False, na=False)
    ]


# ============================================================================
# SUMMARY STATS
# ============================================================================
st.markdown("### 📊 Summary of Filtered Data")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Rows", f"{len(df_filtered):,}")
with col2:
    st.metric("Countries", df_filtered['country'].nunique())
with col3:
    st.metric("Total emissions", f"{df_filtered['emissions_mtco2e'].sum():,.0f} MtCO₂e")
with col4:
    st.metric("Mean emissions", f"{df_filtered['emissions_mtco2e'].mean():.2f} MtCO₂e")


# ============================================================================
# TABS: TABLE + CUSTOM CHART
# ============================================================================
st.markdown("---")
tab1, tab2, tab3 = st.tabs(["📋 Data Table", "🎨 Custom Chart Builder", "📊 Statistics"])


# ----- TAB 1: Interactive Table -----
with tab1:
    st.markdown("#### Filtered Dataset")
    st.caption("Click any column header to sort. Use the search box above the table for in-table search.")

    if df_filtered.empty:
        st.warning("⚠️ No rows match your filters. Try broadening them.")
    else:
        # Format display
        display_df = df_filtered.copy()
        display_df['emissions_mtco2e'] = display_df['emissions_mtco2e'].round(2)
        display_df['yoy_change_pct'] = display_df['yoy_change_pct'].round(2)

        st.dataframe(
            display_df,
            use_container_width=True,
            height=500,
            column_config={
                'country_code': st.column_config.TextColumn('Code', width='small'),
                'country': st.column_config.TextColumn('Country'),
                'year': st.column_config.NumberColumn('Year', format='%d'),
                'emissions_mtco2e': st.column_config.NumberColumn(
                    'Emissions (MtCO₂e)', format='%.2f'
                ),
                'yoy_change_pct': st.column_config.NumberColumn(
                    'YoY Change (%)', format='%.2f'
                ),
                'continent': st.column_config.TextColumn('Continent'),
                'region': None,  # hide duplicate column
                'decade': st.column_config.NumberColumn('Decade', format='%d'),
            },
        )

        # Download button
        csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="💾 Download filtered data as CSV",
            data=csv,
            file_name="transport_emissions_filtered.csv",
            mime="text/csv",
        )


# ----- TAB 2: Custom Chart Builder -----
with tab2:
    st.markdown("#### 🎨 Build Your Own Chart")
    st.caption("Pick your axes and chart type. Great for ad-hoc exploration.")

    if df_filtered.empty:
        st.warning("No data to chart. Adjust filters.")
    else:
        col1, col2, col3 = st.columns(3)

        with col1:
            chart_type = st.selectbox(
                "Chart type",
                options=["Line", "Bar", "Scatter", "Box", "Histogram"],
            )

        with col2:
            x_options = ['year', 'country', 'continent', 'decade', 'emissions_mtco2e']
            x_axis = st.selectbox("X-axis", options=x_options, index=0)

        with col3:
            y_options = ['emissions_mtco2e', 'yoy_change_pct', 'year']
            y_axis = st.selectbox("Y-axis", options=y_options, index=0)

        color_by = st.selectbox(
            "Color by (optional)",
            options=['None', 'continent', 'country', 'decade'],
        )
        color_col = None if color_by == 'None' else color_by

        try:
            if chart_type == "Line":
                fig = px.line(
                    df_filtered, x=x_axis, y=y_axis, color=color_col,
                    title=f'{y_axis} vs {x_axis}',
                    markers=True,
                )
            elif chart_type == "Bar":
                agg_df = (
                    df_filtered.groupby([x_axis] + ([color_col] if color_col else []))[y_axis]
                    .mean().reset_index()
                )
                fig = px.bar(
                    agg_df, x=x_axis, y=y_axis, color=color_col,
                    title=f'Average {y_axis} by {x_axis}',
                )
            elif chart_type == "Scatter":
                fig = px.scatter(
                    df_filtered, x=x_axis, y=y_axis, color=color_col,
                    hover_data=['country', 'year'],
                    title=f'{y_axis} vs {x_axis}',
                )
            elif chart_type == "Box":
                fig = px.box(
                    df_filtered, x=x_axis, y=y_axis, color=color_col,
                    title=f'Distribution of {y_axis} by {x_axis}',
                )
            else:  # Histogram
                fig = px.histogram(
                    df_filtered, x=y_axis, color=color_col,
                    title=f'Distribution of {y_axis}',
                    nbins=40,
                )

            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Could not build chart: {e}")


# ----- TAB 3: Statistics -----
with tab3:
    st.markdown("#### Statistical Summary")

    if df_filtered.empty:
        st.warning("No data to summarize.")
    else:
        st.markdown("##### Numeric columns")
        st.dataframe(
            df_filtered[['emissions_mtco2e', 'yoy_change_pct', 'year']].describe().round(2),
            use_container_width=True,
        )

        st.markdown("##### Top 5 & Bottom 5 by average emissions")
        country_avg = (
            df_filtered.groupby('country')['emissions_mtco2e']
            .mean().round(2).sort_values(ascending=False)
        )
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**🔴 Top 5 (highest avg emissions)**")
            st.dataframe(country_avg.head(5), use_container_width=True)
        with col_b:
            st.markdown("**🟢 Bottom 5 (lowest avg emissions)**")
            st.dataframe(country_avg.tail(5), use_container_width=True)

        st.markdown("##### Row count by continent")
        continent_counts = df_filtered['continent'].value_counts()
        st.bar_chart(continent_counts)


# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.caption(
    f"📦 Showing {len(df_filtered):,} rows out of {len(df):,} total • "
    f"Years {year_range[0]}–{year_range[1]} • "
    f"{len(selected_continents)} continent(s)"
)