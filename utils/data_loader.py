"""Shared data loading utilities for the dashboard."""

import pandas as pd
import streamlit as st
from pathlib import Path


@st.cache_data
def load_country_data():
    """Load cleaned country-level emissions data."""
    root = Path(__file__).resolve().parent.parent
    path = root / "data" / "processed" / "emissions_clean.csv"
    df = pd.read_csv(path)
    return df


@st.cache_data
def load_aggregate_data():
    """Load aggregate-level data (World, European Union)."""
    root = Path(__file__).resolve().parent.parent
    path = root / "data" / "processed" / "emissions_aggregates.csv"
    df = pd.read_csv(path)
    return df


def get_kpi_metrics(df):
    """Calculate headline KPI values."""
    latest_year = df['year'].max()
    earliest_year = df['year'].min()
    latest_df = df[df['year'] == latest_year]

    total_latest = latest_df['emissions_mtco2e'].sum()
    total_earliest = df[df['year'] == earliest_year]['emissions_mtco2e'].sum()
    pct_change = ((total_latest - total_earliest) / total_earliest) * 100

    top_emitter = latest_df.nlargest(1, 'emissions_mtco2e').iloc[0]

    return {
        'latest_year': int(latest_year),
        'earliest_year': int(earliest_year),
        'total_latest': total_latest,
        'pct_change': pct_change,
        'top_emitter': top_emitter['country'],
        'top_emitter_value': top_emitter['emissions_mtco2e'],
        'num_countries': df['country'].nunique(),
        'num_years': df['year'].nunique(),
    }