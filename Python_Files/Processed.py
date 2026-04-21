"""
Data Preprocessing Script
Dataset: WRI Climate Watch - Transport Sector GHG Emissions (1990-2021)
Source: World Bank Data360

Cleans the raw CSV by:
1. Dropping 33 useless constant-value columns
2. Renaming columns to clean names
3. Adding continent/region metadata
4. Separating country-level data from aggregates (World, European Union)
5. Computing derived metrics (year-over-year change, decade bins)
6. Saving clean outputs to data/processed/
"""

import pandas as pd
import pycountry_convert as pc
from pathlib import Path

# ----------------------------------------------------------------------
# 0. SET UP PATHS (works from any folder, any machine)
# ----------------------------------------------------------------------
# PROJECT_ROOT = the "Data Science" folder (one level up from this script)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_CSV = PROJECT_ROOT / "data" / "raw" / "WRI_CLIMATEWATCH_ALL_GHG_TRANSPORT.csv"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Make sure the output folder exists
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# 1. LOAD RAW DATA
# ----------------------------------------------------------------------
print("Loading raw data...")
df = pd.read_csv(RAW_CSV)
print(f"Raw shape: {df.shape[0]} rows x {df.shape[1]} columns")

# ----------------------------------------------------------------------
# 2. DROP USELESS COLUMNS (33 of 37 have only 1 unique value)
# ----------------------------------------------------------------------
keep_cols = ['REF_AREA', 'REF_AREA_LABEL', 'TIME_PERIOD', 'OBS_VALUE']
df = df[keep_cols].copy()

# Rename to clean, consistent names
df.columns = ['country_code', 'country', 'year', 'emissions_mtco2e']
print(f"After column cleanup: {df.shape[0]} rows x {df.shape[1]} columns")

# ----------------------------------------------------------------------
# 3. FIX DATA TYPES
# ----------------------------------------------------------------------
df['year'] = df['year'].astype(int)
df['emissions_mtco2e'] = df['emissions_mtco2e'].astype(float)

# ----------------------------------------------------------------------
# 4. SEPARATE AGGREGATES FROM COUNTRIES
# ----------------------------------------------------------------------
AGGREGATES = ['World', 'European Union']
df_aggregates = df[df['country'].isin(AGGREGATES)].copy()
df_countries = df[~df['country'].isin(AGGREGATES)].copy()

print(f"Country rows: {len(df_countries)}")
print(f"Aggregate rows: {len(df_aggregates)}")

# ----------------------------------------------------------------------
# 5. ADD CONTINENT / REGION COLUMNS
# ----------------------------------------------------------------------
# Handle WRI naming quirks vs pycountry standard naming
NAME_FIXES = {
    'Bahamas, The': 'Bahamas',
    'Congo, Dem. Rep.': 'Congo, The Democratic Republic of the',
    'Congo, Rep.': 'Congo',
    'Egypt, Arab Rep.': 'Egypt',
    'Gambia, The': 'Gambia',
    'Iran, Islamic Rep.': 'Iran, Islamic Republic of',
    "Korea, Dem. People's Rep.": "Korea, Democratic People's Republic of",
    'Korea, Rep.': 'Korea, Republic of',
    'Kyrgyz Republic': 'Kyrgyzstan',
    'Lao PDR': "Lao People's Democratic Republic",
    'Micronesia, Fed. Sts.': 'Micronesia, Federated States of',
    'Slovak Republic': 'Slovakia',
    'St. Kitts and Nevis': 'Saint Kitts and Nevis',
    'St. Lucia': 'Saint Lucia',
    'St. Vincent and the Grenadines': 'Saint Vincent and the Grenadines',
    'Syrian Arab Republic': 'Syria',
    'Turkiye': 'Turkey',
    'Venezuela, RB': 'Venezuela, Bolivarian Republic of',
    'Viet Nam': 'Vietnam',
    'Yemen, Rep.': 'Yemen',
    "Cote d'Ivoire": "Côte d'Ivoire",
}

def get_continent(country_name):
    """Map country name to continent using pycountry_convert."""
    fixed_name = NAME_FIXES.get(country_name, country_name)
    try:
        country_alpha2 = pc.country_name_to_country_alpha2(fixed_name)
        continent_code = pc.country_alpha2_to_continent_code(country_alpha2)
        continent_map = {
            'AF': 'Africa', 'AS': 'Asia', 'EU': 'Europe',
            'NA': 'North America', 'SA': 'South America', 'OC': 'Oceania',
        }
        return continent_map.get(continent_code, 'Unknown')
    except (KeyError, LookupError):
        return 'Unknown'

print("Mapping countries to continents...")
df_countries['continent'] = df_countries['country'].apply(get_continent)
df_countries['region'] = df_countries['continent']  # alias for flexibility

# Report unmapped countries
unmapped = df_countries[df_countries['continent'] == 'Unknown']['country'].unique()
if len(unmapped) > 0:
    print(f"\nWarning: {len(unmapped)} countries need manual mapping:")
    for c in unmapped:
        print(f"  - {c}")
else:
    print("All countries successfully mapped to continents!")

# ----------------------------------------------------------------------
# 6. ADD DERIVED METRICS
# ----------------------------------------------------------------------
df_countries = df_countries.sort_values(['country', 'year']).reset_index(drop=True)

# Year-over-year percent change (growth rate)
df_countries['yoy_change_pct'] = (
    df_countries.groupby('country')['emissions_mtco2e'].pct_change() * 100
).round(2)

# Decade bin (for heatmaps)
df_countries['decade'] = (df_countries['year'] // 10) * 10

# ----------------------------------------------------------------------
# 7. SAVE PROCESSED OUTPUTS
# ----------------------------------------------------------------------
df_countries.to_csv(PROCESSED_DIR / "emissions_clean.csv", index=False)
df_aggregates.to_csv(PROCESSED_DIR / "emissions_aggregates.csv", index=False)

print(f"\nSaved: {PROCESSED_DIR / 'emissions_clean.csv'}")
print(f"Saved: {PROCESSED_DIR / 'emissions_aggregates.csv'}")

# ----------------------------------------------------------------------
# 8. SUMMARY REPORT
# ----------------------------------------------------------------------
print("\n" + "="*55)
print("PREPROCESSING SUMMARY")
print("="*55)
print(f"Years covered:      {df_countries['year'].min()} to {df_countries['year'].max()}")
print(f"Unique countries:   {df_countries['country'].nunique()}")
print(f"Unique continents:  {df_countries['continent'].nunique()}")
print(f"\nCountry rows per continent:")
print(df_countries['continent'].value_counts().to_string())
print(f"\nEmissions range (MtCO2e):")
print(f"  Min:    {df_countries['emissions_mtco2e'].min():.2f}")
print(f"  Max:    {df_countries['emissions_mtco2e'].max():.2f}")
print(f"  Mean:   {df_countries['emissions_mtco2e'].mean():.2f}")
print(f"  Median: {df_countries['emissions_mtco2e'].median():.2f}")
print("\nDone! Ready for EDA and dashboard development.")