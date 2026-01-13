"""
K-Means Customer Segmentation Script
=====================================

Creates customer segments from the cleaned lead scoring data
and ingests results into SQLite database for the multi-agent system.

Run with: uv run python scripts/create_segments.py
"""

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import sqlite3
from pathlib import Path
import json
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# 1. LOAD CLEANED DATA
# ============================================================

print("=" * 70)
print("K-MEANS CUSTOMER SEGMENTATION")
print("=" * 70)

data_path = Path(__file__).parent.parent / "data" / "leadscored_clean.csv"
df = pd.read_csv(data_path)

print(f"\n📊 Loaded cleaned data: {df.shape[0]:,} rows × {df.shape[1]} columns")

# ============================================================
# 2. PREPARE FEATURES FOR CLUSTERING
# ============================================================

print("\n" + "=" * 70)
print("FEATURE PREPARATION FOR CLUSTERING")
print("=" * 70)

# Select behavioral features for clustering
clustering_features = [
    'TotalVisits',
    'Total Time Spent on Website',
    'Page Views Per Visit',
    'engagement_score'
]

# Create feature matrix
X = df[clustering_features].copy()

print(f"\n📋 Clustering Features:")
for f in clustering_features:
    print(f"   • {f}")

# Handle any remaining missing values
X = X.fillna(X.median())

# Scale features for K-means
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

print(f"\n✓ Features scaled using StandardScaler")
print(f"   Shape: {X_scaled.shape}")

# ============================================================
# 3. K-MEANS CLUSTERING
# ============================================================

print("\n" + "=" * 70)
print("K-MEANS CLUSTERING (k=5)")
print("=" * 70)

# Fit K-means with 5 clusters
n_clusters = 5
kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
cluster_labels = kmeans.fit_predict(X_scaled)

# Add cluster labels to dataframe
df['cluster'] = cluster_labels

# Analyze cluster characteristics
print("\n📊 Cluster Analysis:")
cluster_summary = df.groupby('cluster')[clustering_features].mean()

# Define 5 segment names based on engagement levels
segment_label_pool = [
    "Champions",           # Highest engagement + visits
    "Highly Engaged",      # High engagement, moderate visits
    "Potential Loyalists", # Medium-high engagement
    "At Risk",             # Low-medium engagement
    "Low Value"            # Lowest engagement
]

# Rank clusters by engagement_score
cluster_ranking = cluster_summary['engagement_score'].sort_values(ascending=False).index.tolist()

# Assign segment names based on ranking
segment_names = {}
for rank, cluster_id in enumerate(cluster_ranking):
    segment_names[cluster_id] = segment_label_pool[rank]

# Map segment names to dataframe
df['Segment'] = df['cluster'].map(segment_names)

print("\n📋 Segment Distribution:")
segment_counts = df['Segment'].value_counts()
for segment, count in segment_counts.items():
    pct = (count / len(df)) * 100
    print(f"   • {segment}: {count:,} leads ({pct:.1f}%)")

print("\n📊 Segment Characteristics (Mean Values):")
segment_stats = df.groupby('Segment')[clustering_features + ['Converted']].mean()
print(segment_stats.round(2).to_string())

# ============================================================
# 4. CREATE SQLITE DATABASE (Fresh)
# ============================================================

print("\n" + "=" * 70)
print("CREATING SQLITE DATABASE")
print("=" * 70)

db_path = Path(__file__).parent.parent / "data" / "leadscored.db"
db_path.parent.mkdir(exist_ok=True)

# Remove old database if exists
if db_path.exists():
    db_path.unlink()
    print(f"\n🗑️  Removed old database: {db_path.name}")

# Rename columns to be SQL-friendly (no spaces/dashes)
db_df = df.copy()
db_df.columns = db_df.columns.str.replace(' ', '_').str.replace('-', '_')

# Simplify long column names
db_df = db_df.rename(columns={
    'Lead_Number': 'customer_id',
    'What_is_your_current_occupation': 'Occupation',
    'How_did_you_hear_about_X_Education': 'Referral_Source',
    'What_matters_most_to_you_in_choosing_a_course': 'Priority',
    'Last_Notable_Activity': 'Last_Activity_Type'
})

# Connect to SQLite and create the table
conn = sqlite3.connect(db_path)
db_df.to_sql('leadscored', conn, index=False, if_exists='replace')

# Create indices for faster queries
conn.execute("CREATE INDEX idx_segment ON leadscored(Segment)")
conn.execute("CREATE INDEX idx_customer_id ON leadscored(customer_id)")
conn.execute("CREATE INDEX idx_converted ON leadscored(Converted)")
conn.execute("CREATE INDEX idx_engagement ON leadscored(engagement_score)")
conn.commit()

# Verify
cursor = conn.execute("SELECT COUNT(*), COUNT(DISTINCT Segment) FROM leadscored")
row_count, segment_count = cursor.fetchone()

print(f"\n✓ Database created: {db_path}")
print(f"   Total rows: {row_count:,}")
print(f"   Distinct segments: {segment_count}")

# Show sample
print("\n📋 Sample Query - Top 5 Highly Engaged leads:")
sample_query = """
SELECT customer_id, Segment, engagement_score, Converted, Lead_Source
FROM leadscored WHERE Segment = 'Highly Engaged'
ORDER BY engagement_score DESC LIMIT 5
"""
print(pd.read_sql(sample_query, conn).to_string(index=False))
conn.close()

# ============================================================
# 5. SAVE SEGMENT DESCRIPTIONS
# ============================================================

segment_descriptions = {}
for seg in df['Segment'].unique():
    seg_data = df[df['Segment'] == seg]
    segment_descriptions[seg] = {
        "count": int(len(seg_data)),
        "avg_engagement": round(float(seg_data['engagement_score'].mean()), 3),
        "conversion_rate": round(float(seg_data['Converted'].mean()), 3),
        "avg_visits": round(float(seg_data['TotalVisits'].mean()), 1),
        "avg_time_on_site": round(float(seg_data['Total Time Spent on Website'].mean()), 1)
    }

segment_path = Path(__file__).parent.parent / "data" / "segment_descriptions.json"
with open(segment_path, 'w') as f:
    json.dump(segment_descriptions, f, indent=2)
print(f"\n✓ Segment descriptions saved: {segment_path}")

print("\n" + "=" * 70)
print("SEGMENTATION COMPLETE!")
print("=" * 70)

