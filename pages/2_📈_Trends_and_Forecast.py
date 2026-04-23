"""
Trends & Forecast Page
Analyze historical trends by continent and project future emissions.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
from utils.data_loader import load_country_data


# ============================================================================
# PAGE CONFIG
# ============================================================================
st.set_page_config(
    page_title="Trends & Forecast",
    page_icon="📈",
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
df = df[df['continent'] != 'Unknown']  # drop any unmapped

# ============================================================================
# HEADER
# ============================================================================
st.markdown('<div class="main-header">📈 Trends & Forecast</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Historical trends by continent and linear '
    'regression forecast to 2030.</div>',
    unsafe_allow_html=True
)


# ============================================================================
# TABS
# ============================================================================
tab1, tab2, tab3 = st.tabs([
    "🌎 Continental Trends", "🔥 Decade Heatmap", "🔮 Forecast 2030"
])


# ----- TAB 1: Continental stacked area chart -----
with tab1:
    st.markdown("#### Transport Emissions by Continent Over Time")

    chart_type = st.radio(
        "Display as:",
        options=["Stacked Area (absolute)", "Line Chart", "100% Stacked (share)"],
        horizontal=True,
    )

    continent_yearly = (
        df.groupby(['year', 'continent'])['emissions_mtco2e'].sum().reset_index()
    )

    if chart_type == "Stacked Area (absolute)":
        fig = px.area(
            continent_yearly,
            x='year', y='emissions_mtco2e', color='continent',
            title='Total Transport Emissions by Continent',
            labels={'emissions_mtco2e': 'Emissions (MtCO₂e)'},
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
    elif chart_type == "Line Chart":
        fig = px.line(
            continent_yearly,
            x='year', y='emissions_mtco2e', color='continent',
            markers=True,
            title='Transport Emissions Trend by Continent',
            labels={'emissions_mtco2e': 'Emissions (MtCO₂e)'},
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
    else:  # 100% stacked
        totals = continent_yearly.groupby('year')['emissions_mtco2e'].transform('sum')
        continent_yearly['share'] = (continent_yearly['emissions_mtco2e'] / totals) * 100
        fig = px.area(
            continent_yearly,
            x='year', y='share', color='continent',
            title='Continental Share of Global Transport Emissions (%)',
            labels={'share': 'Share (%)'},
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig.update_layout(yaxis_range=[0, 100])

    fig.update_layout(height=500, hovermode='x unified')
    st.plotly_chart(fig, use_container_width=True)

    # Insight box
    latest_year = df['year'].max()
    latest_continents = continent_yearly[continent_yearly['year'] == latest_year].sort_values(
        'emissions_mtco2e', ascending=False
    )
    top_continent = latest_continents.iloc[0]
    st.info(
        f"💡 **Insight:** In {latest_year}, **{top_continent['continent']}** was the "
        f"largest transport-emissions contributor at **{top_continent['emissions_mtco2e']:,.0f} MtCO₂e**."
    )


# ----- TAB 2: Decade heatmap -----
with tab2:
    st.markdown("#### Decade-by-Decade Growth Heatmap")
    st.caption("Average emissions per decade by continent. Darker cells = higher emissions.")

    decade_continent = (
        df.groupby(['decade', 'continent'])['emissions_mtco2e']
        .sum()
        .reset_index()
        .pivot(index='continent', columns='decade', values='emissions_mtco2e')
    )

    fig_heat = px.imshow(
        decade_continent,
        text_auto='.0f',
        aspect='auto',
        color_continuous_scale='Reds',
        labels={'color': 'MtCO₂e'},
        title='Transport Emissions by Continent & Decade',
    )
    fig_heat.update_layout(height=400)
    st.plotly_chart(fig_heat, use_container_width=True)

    # Compute largest decade jump
    if decade_continent.shape[1] >= 2:
        decade_changes = decade_continent.diff(axis=1).max(axis=1).sort_values(ascending=False)
        if not decade_changes.empty:
            biggest = decade_changes.index[0]
            st.info(
                f"💡 **Insight:** **{biggest}** had the largest decade-over-decade jump, "
                f"adding ~{decade_changes.iloc[0]:,.0f} MtCO₂e between two consecutive decades."
            )


# ----- TAB 3: Forecast to 2030 -----
with tab3:
    st.markdown("#### 🔮 Linear Regression Forecast to 2030")
    st.caption(
        "Forecast is a simple linear projection. Use as a baseline — "
        "real emissions pathways depend on policy, technology, and economics."
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        all_countries = sorted(df['country'].unique().tolist())
        default_countries = (
            df[df['year'] == df['year'].max()]
            .nlargest(3, 'emissions_mtco2e')['country']
            .tolist()
        )
        forecast_countries = st.multiselect(
            "Select countries to forecast:",
            options=all_countries,
            default=default_countries,
        )

    with col2:
        forecast_year = st.slider(
            "Forecast up to year:",
            min_value=2022, max_value=2035, value=2030,
        )

    if not forecast_countries:
        st.warning("Please select at least one country.")
        st.stop()

    fig_forecast = go.Figure()
    forecast_stats = []

    for country in forecast_countries:
        cdata = df[df['country'] == country].sort_values('year')

        # Fit linear model on all historical data
        X = cdata[['year']].values
        y = cdata['emissions_mtco2e'].values
        model = LinearRegression().fit(X, y)

        # Predict from (first year) to forecast_year
        future_years = np.arange(cdata['year'].min(), forecast_year + 1).reshape(-1, 1)
        predicted = model.predict(future_years)

        # Plot actual (solid)
        fig_forecast.add_trace(go.Scatter(
            x=cdata['year'], y=cdata['emissions_mtco2e'],
            mode='lines+markers', name=f'{country} (actual)',
            line=dict(width=3),
        ))

        # Plot forecast (dashed, only future portion)
        hist_max = cdata['year'].max()
        future_only_idx = future_years.flatten() >= hist_max
        fig_forecast.add_trace(go.Scatter(
            x=future_years.flatten()[future_only_idx],
            y=predicted[future_only_idx],
            mode='lines', name=f'{country} (forecast)',
            line=dict(dash='dash', width=2),
            showlegend=True,
        ))

        # Record stats
        forecast_stats.append({
            'Country': country,
            f'Latest ({hist_max})': round(y[-1], 1),
            f'Forecast ({forecast_year})': round(predicted[-1], 1),
            'Change': f"{((predicted[-1] - y[-1]) / y[-1] * 100):+.1f}%",
            'R² score': round(model.score(X, y), 3),
        })

    fig_forecast.update_layout(
        title=f"Emissions Forecast to {forecast_year}",
        xaxis_title="Year",
        yaxis_title="Emissions (MtCO₂e)",
        height=500,
        hovermode='x unified',
    )

    # Add a vertical line at the forecast boundary
    fig_forecast.add_vline(
        x=df['year'].max(), line_dash="dot", line_color="gray",
        annotation_text="Forecast begins →", annotation_position="top right",
    )

    st.plotly_chart(fig_forecast, use_container_width=True)

    # Stats table
    st.markdown("#### 📊 Forecast Summary")
    stats_df = pd.DataFrame(forecast_stats)
    st.dataframe(stats_df, use_container_width=True, hide_index=True)

    st.caption(
        "💡 **R² score** shows how well the linear model fits historical data. "
        "Closer to 1.0 = better fit. Low scores (< 0.5) mean the forecast is unreliable."
    )


# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.caption("Forecasts use simple linear regression on historical data. Real future emissions depend on many factors.")