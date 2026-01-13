"""
Interactive Data Cleaning Script for Lead Scoring Dataset
==========================================================

This script performs systematic data profiling and cleaning following
DS best practices: schema validation, missing value analysis, 
outlier detection, and data preparation for ML.

Run with: uv run python scripts/data_cleaning.py
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# 1. DATA LOADING
# ============================================================

print("=" * 70)
print("LEAD SCORING DATA CLEANING - INTERACTIVE MODE")
print("=" * 70)

# Load the raw data
data_path = Path(__file__).parent.parent / "Lead Scoring.csv"
df = pd.read_csv(data_path)

print(f"\n📊 Dataset loaded: {df.shape[0]:,} rows × {df.shape[1]} columns")
print(f"📁 Source: {data_path.name}")

# ============================================================
# 2. SCHEMA OVERVIEW
# ============================================================

print("\n" + "=" * 70)
print("SECTION 1: SCHEMA OVERVIEW")
print("=" * 70)

print("\n📋 Column Types Summary:")
type_summary = df.dtypes.value_counts()
for dtype, count in type_summary.items():
    print(f"   • {dtype}: {count} columns")

print("\n📋 All Columns:")
for i, (col, dtype) in enumerate(df.dtypes.items(), 1):
    null_pct = (df[col].isna().sum() / len(df)) * 100
    unique = df[col].nunique()
    print(f"   {i:2d}. {col:40s} | {str(dtype):10s} | {null_pct:5.1f}% null | {unique:,} unique")

# ============================================================
# 3. TARGET VARIABLE ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("SECTION 2: TARGET VARIABLE ANALYSIS")
print("=" * 70)

if 'Converted' in df.columns:
    print("\n🎯 Target: 'Converted' (Lead to Customer Conversion)")
    conversion_counts = df['Converted'].value_counts()
    conversion_pct = df['Converted'].value_counts(normalize=True) * 100
    print(f"   • Not Converted (0): {conversion_counts.get(0, 0):,} ({conversion_pct.get(0, 0):.1f}%)")
    print(f"   • Converted (1): {conversion_counts.get(1, 0):,} ({conversion_pct.get(1, 0):.1f}%)")
    print(f"   • Conversion Rate: {conversion_pct.get(1, 0):.1f}%")

# ============================================================
# 4. MISSING VALUE ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("SECTION 3: MISSING VALUE ANALYSIS")
print("=" * 70)

missing = df.isna().sum()
missing_pct = (missing / len(df)) * 100
missing_df = pd.DataFrame({
    'Column': missing.index,
    'Missing': missing.values,
    'Percentage': missing_pct.values
}).query('Missing > 0').sort_values('Percentage', ascending=False)

if len(missing_df) > 0:
    print(f"\n⚠️  {len(missing_df)} columns have missing values:")
    for _, row in missing_df.iterrows():
        print(f"   • {row['Column']:40s} | {row['Missing']:,} missing ({row['Percentage']:.1f}%)")
else:
    print("\n✅ No missing values found!")

# ============================================================
# 5. "SELECT" PLACEHOLDER ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("SECTION 4: PLACEHOLDER VALUE ANALYSIS ('Select' values)")
print("=" * 70)

print("\n🔍 Checking for 'Select' placeholder values (often means missing):")
select_columns = []
for col in df.select_dtypes(include=['object']).columns:
    if 'Select' in df[col].values or 'select' in df[col].str.lower().values:
        select_count = df[col].str.lower().eq('select').sum()
        if select_count > 0:
            select_pct = (select_count / len(df)) * 100
            select_columns.append((col, select_count, select_pct))
            print(f"   • {col:40s} | {select_count:,} 'Select' values ({select_pct:.1f}%)")

if not select_columns:
    print("   ✅ No placeholder 'Select' values found")

# ============================================================
# 6. NUMERICAL FEATURES ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("SECTION 5: NUMERICAL FEATURES ANALYSIS")
print("=" * 70)

numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
# Exclude ID columns and target
feature_cols = [c for c in numerical_cols if c not in ['Lead Number', 'Converted']]

print(f"\n📈 Numerical Features ({len(feature_cols)} columns):")
if feature_cols:
    stats = df[feature_cols].describe().T
    stats['missing'] = df[feature_cols].isna().sum()
    stats['missing_pct'] = (stats['missing'] / len(df)) * 100
    
    for col in feature_cols:
        s = stats.loc[col]
        print(f"\n   {col}:")
        print(f"      Range: {s['min']:.1f} - {s['max']:.1f} | Mean: {s['mean']:.2f} | Std: {s['std']:.2f}")
        print(f"      25%: {s['25%']:.1f} | 50%: {s['50%']:.1f} | 75%: {s['75%']:.1f}")
        if s['missing'] > 0:
            print(f"      ⚠️  Missing: {int(s['missing']):,} ({s['missing_pct']:.1f}%)")

# ============================================================
# 7. CATEGORICAL FEATURES ANALYSIS  
# ============================================================

print("\n" + "=" * 70)
print("SECTION 6: CATEGORICAL FEATURES ANALYSIS")
print("=" * 70)

categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
# Exclude ID column
categorical_cols = [c for c in categorical_cols if c != 'Prospect ID']

print(f"\n📊 Categorical Features ({len(categorical_cols)} columns):")
for col in categorical_cols:
    unique = df[col].nunique()
    top_val = df[col].mode().iloc[0] if not df[col].mode().empty else 'N/A'
    top_pct = (df[col].value_counts(normalize=True).iloc[0] * 100) if len(df[col].dropna()) > 0 else 0
    print(f"\n   {col}:")
    print(f"      Unique values: {unique} | Top: '{top_val}' ({top_pct:.1f}%)")
    
    # Show value distribution for low-cardinality columns
    if unique <= 10:
        for val, count in df[col].value_counts().head(5).items():
            pct = (count / len(df)) * 100
            print(f"      - {val}: {count:,} ({pct:.1f}%)")

# ============================================================
# 8. DATA CLEANING RECOMMENDATIONS
# ============================================================

print("\n" + "=" * 70)
print("SECTION 7: DATA CLEANING RECOMMENDATIONS")
print("=" * 70)

print("""
📋 CLEANING ACTIONS TO APPLY:

1. MISSING VALUES:
   • TotalVisits, Page Views Per Visit: Impute with median (behavioral metrics)
   • Categorical with low missing: Mode imputation
   • High missing (>40%): Consider dropping or creating indicator

2. PLACEHOLDER VALUES:
   • Replace 'Select' with 'Unknown' (explicit missing category)
   • This preserves the information that user didn't choose

3. FEATURE ENGINEERING FOR SEGMENTATION:
   • Create engagement_score from behavioral metrics
   • Create recency/frequency/monetary style features
   
4. COLUMNS TO DROP:
   • Prospect ID (non-predictive identifier)
   • Highly sparse columns (>70% missing)
   
5. NUMERIC OUTLIERS:
   • Cap extreme values at 99th percentile if needed
""")

# ============================================================
# 9. APPLY CLEANING
# ============================================================

print("\n" + "=" * 70)
print("SECTION 8: APPLYING DATA CLEANING")
print("=" * 70)

df_clean = df.copy()

# 9.1 Handle 'Select' placeholders
print("\n🔧 Step 1: Replacing 'Select' placeholder values with 'Unknown'...")
select_replace_count = 0
for col in df_clean.select_dtypes(include=['object']).columns:
    mask = df_clean[col].str.lower() == 'select'
    if mask.any():
        count = mask.sum()
        df_clean.loc[mask, col] = 'Unknown'
        print(f"   ✓ {col}: {count:,} values replaced")
        select_replace_count += count
print(f"   Total 'Select' values replaced: {select_replace_count:,}")

# 9.2 Handle missing numerical values
print("\n🔧 Step 2: Imputing missing numerical values with median...")
numerical_features = ['TotalVisits', 'Total Time Spent on Website', 'Page Views Per Visit']
for col in numerical_features:
    if col in df_clean.columns:
        missing_count = df_clean[col].isna().sum()
        if missing_count > 0:
            median_val = df_clean[col].median()
            df_clean[col] = df_clean[col].fillna(median_val)
            print(f"   ✓ {col}: {missing_count:,} values imputed with median ({median_val:.2f})")

# 9.3 Handle missing categorical values
print("\n🔧 Step 3: Handling missing categorical values...")
for col in df_clean.select_dtypes(include=['object']).columns:
    missing_count = df_clean[col].isna().sum()
    if missing_count > 0:
        df_clean[col] = df_clean[col].fillna('Unknown')
        print(f"   ✓ {col}: {missing_count:,} values replaced with 'Unknown'")

# 9.4 Create engagement score for clustering
print("\n🔧 Step 4: Creating engagement composite score...")
# Normalize behavioral metrics to 0-1 scale
def min_max_scale(series):
    min_val = series.min()
    max_val = series.max()
    if max_val == min_val:
        return pd.Series([0.5] * len(series), index=series.index)
    return (series - min_val) / (max_val - min_val)

if all(c in df_clean.columns for c in ['TotalVisits', 'Total Time Spent on Website', 'Page Views Per Visit']):
    visits_scaled = min_max_scale(df_clean['TotalVisits'])
    time_scaled = min_max_scale(df_clean['Total Time Spent on Website'])
    pages_scaled = min_max_scale(df_clean['Page Views Per Visit'])
    
    # Weighted engagement score
    df_clean['engagement_score'] = (visits_scaled * 0.3 + time_scaled * 0.5 + pages_scaled * 0.2)
    print(f"   ✓ engagement_score created (range: {df_clean['engagement_score'].min():.3f} - {df_clean['engagement_score'].max():.3f})")

# 9.5 Drop sparse columns (>70% missing in original)
print("\n🔧 Step 5: Identifying sparse columns...")
sparse_threshold = 0.70
original_missing = df.isna().sum() / len(df)
sparse_cols = original_missing[original_missing > sparse_threshold].index.tolist()
if sparse_cols:
    print(f"   ⚠️  Columns with >{sparse_threshold*100:.0f}% missing (keeping but flagged):")
    for col in sparse_cols:
        print(f"      - {col}: {original_missing[col]*100:.1f}% missing")
else:
    print("   ✓ No columns exceed sparsity threshold")

# ============================================================
# 10. FINAL VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("SECTION 9: CLEANED DATA VALIDATION")
print("=" * 70)

print(f"\n📊 Cleaned Dataset: {df_clean.shape[0]:,} rows × {df_clean.shape[1]} columns")

# Check remaining missing
remaining_missing = df_clean.isna().sum().sum()
print(f"✓ Remaining missing values: {remaining_missing:,}")

# Check 'Select' values
remaining_select = 0
for col in df_clean.select_dtypes(include=['object']).columns:
    remaining_select += (df_clean[col].str.lower() == 'select').sum()
print(f"✓ Remaining 'Select' placeholders: {remaining_select:,}")

# Show sample
print("\n📋 Sample of cleaned data (first 5 rows, key columns):")
key_cols = ['Lead Number', 'Lead Source', 'TotalVisits', 'Total Time Spent on Website', 
            'Converted', 'Country', 'engagement_score']
key_cols = [c for c in key_cols if c in df_clean.columns]
print(df_clean[key_cols].head().to_string(index=False))

# ============================================================
# 11. SAVE CLEANED DATA
# ============================================================

print("\n" + "=" * 70)
print("SECTION 10: SAVING CLEANED DATA")
print("=" * 70)

output_path = Path(__file__).parent.parent / "data" / "leadscored_clean.csv"
output_path.parent.mkdir(exist_ok=True)
df_clean.to_csv(output_path, index=False)
print(f"\n✅ Cleaned data saved to: {output_path}")
print(f"   Rows: {df_clean.shape[0]:,} | Columns: {df_clean.shape[1]}")

# Also save data profile summary
profile_path = Path(__file__).parent.parent / "data" / "data_profile_summary.txt"
with open(profile_path, 'w') as f:
    f.write("LEAD SCORING DATA PROFILE SUMMARY\n")
    f.write("=" * 50 + "\n\n")
    f.write(f"Original Shape: {df.shape}\n")
    f.write(f"Cleaned Shape: {df_clean.shape}\n")
    f.write(f"Conversion Rate: {df_clean['Converted'].mean()*100:.1f}%\n\n")
    f.write("Key Behavioral Metrics:\n")
    for col in ['TotalVisits', 'Total Time Spent on Website', 'Page Views Per Visit', 'engagement_score']:
        if col in df_clean.columns:
            f.write(f"  {col}: mean={df_clean[col].mean():.2f}, std={df_clean[col].std():.2f}\n")
print(f"✅ Data profile saved to: {profile_path}")

print("\n" + "=" * 70)
print("DATA CLEANING COMPLETE!")
print("=" * 70)
print("\nNext step: Run K-means clustering to create customer segments")
print("Command: uv run python scripts/create_segments.py")
