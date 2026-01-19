import pandas as pd
import numpy as np
import glob
import os
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 6)

# ============================================================================
# STEP 0 — DATA LOADING & SANITY CHECK
# ============================================================================

def load_and_combine_csv(folder_path, dataset_name):
    """Load and combine all CSV files from a folder"""
    files = glob.glob(os.path.join(folder_path, "*.csv"))
    print(f"\n{'='*70}")
    print(f"LOADING {dataset_name.upper()}: Found {len(files)} files in {folder_path}")
    print(f"{'='*70}")
    
    if not files:
        print(f"❌ No CSV files found in {folder_path}")
        return None
    
    df_list = []
    for file in files:
        try:
            df = pd.read_csv(file)
            df_list.append(df)
            print(f"  ✓ Loaded: {os.path.basename(file)} — Shape: {df.shape}")
        except Exception as e:
            print(f"  ❌ Error loading {os.path.basename(file)}: {e}")
    
    combined_df = pd.concat(df_list, ignore_index=True)
    print(f"\n✓ Combined {dataset_name} shape: {combined_df.shape}")
    return combined_df

# Load datasets
enroll_df = load_and_combine_csv("enrolment", "Enrolment")
demo_df = load_and_combine_csv("demographic", "Demographic")
bio_df = load_and_combine_csv("biometric", "Biometric")

# ============================================================================
# STEP 0: Standardize column names and inspect
# ============================================================================

def standardize_and_inspect(df, name):
    """Standardize columns and print inspection report"""
    print(f"\n{'-'*70}")
    print(f"INSPECTION: {name}")
    print(f"{'-'*70}")
    
    # Display original columns
    print(f"Original columns: {list(df.columns)}")
    print(f"Shape: {df.shape}")
    print(f"\nFirst few rows:")
    print(df.head(2))
    
    # Convert date column to datetime (assuming 'date' column exists)
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        print(f"\n✓ Date range: {df['date'].min()} to {df['date'].max()}")
    
    # Check for missing values
    print(f"\nMissing values:")
    missing = df.isnull().sum()
    print(missing[missing > 0] if missing.sum() > 0 else "  None detected")
    
    # Check duplicates
    duplicates = df.duplicated().sum()
    print(f"\nDuplicates: {duplicates} rows")
    
    # Unique states and districts
    if 'state' in df.columns:
        print(f"Unique states: {df['state'].nunique()}")
    if 'district' in df.columns:
        print(f"Unique districts: {df['district'].nunique()}")
    
    return df

# Standardize each dataset
enroll_df = standardize_and_inspect(enroll_df, "ENROLMENT")
demo_df = standardize_and_inspect(demo_df, "DEMOGRAPHIC")
bio_df = standardize_and_inspect(bio_df, "BIOMETRIC")

print(f"\n{'='*70}")
print("STEP 0 COMPLETE: Data loaded and sanitized")
print(f"{'='*70}")

# ============================================================================
# STEP 1 — CREATE A COMMON ANALYSIS GRAIN (District + Month)
# ============================================================================

def create_analysis_grain(df, value_cols):
    """
    Convert date to year_month and aggregate by state, district, year_month
    """
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    
    # Remove rows with missing dates
    df = df.dropna(subset=['date'])
    
    # Create year_month
    df['year_month'] = df['date'].dt.to_period('M')
    
    # Aggregate
    agg_dict = {col: 'sum' for col in value_cols}
    grain_df = df.groupby(['state', 'district', 'year_month'], as_index=False).agg(agg_dict)
    
    return grain_df

# Create common grain for all datasets
enroll_cols = ['age_0_5', 'age_5_17', 'age_18_greater']
enroll_grain = create_analysis_grain(enroll_df, enroll_cols)
enroll_grain.rename(columns={'age_0_5': 'enrol_0_5', 'age_5_17': 'enrol_5_17', 'age_18_greater': 'enrol_18+'}, inplace=True)
enroll_grain['total_enrolments'] = enroll_grain[['enrol_0_5', 'enrol_5_17', 'enrol_18+']].sum(axis=1)

demo_cols = ['demo_age_5_17', 'demo_age_17_']
demo_grain = create_analysis_grain(demo_df, demo_cols)
demo_grain.rename(columns={'demo_age_5_17': 'demo_5_17', 'demo_age_17_': 'demo_17+'}, inplace=True)
demo_grain['total_demo_updates'] = demo_grain[['demo_5_17', 'demo_17+']].sum(axis=1)

bio_cols = ['bio_age_5_17', 'bio_age_17_']
bio_grain = create_analysis_grain(bio_df, bio_cols)
bio_grain.rename(columns={'bio_age_5_17': 'bio_5_17', 'bio_age_17_': 'bio_17+'}, inplace=True)
bio_grain['total_bio_updates'] = bio_grain[['bio_5_17', 'bio_17+']].sum(axis=1)

print(f"\n{'='*70}")
print("STEP 1 COMPLETE: Common grain created (District + Month)")
print(f"{'='*70}")
print(f"Enrolment grain shape: {enroll_grain.shape}")
print(f"Demographic grain shape: {demo_grain.shape}")
print(f"Biometric grain shape: {bio_grain.shape}")

# ============================================================================
# STEP 2 — BASELINE ENROLMENT ANALYSIS
# ============================================================================

print(f"\n{'='*70}")
print("STEP 2: BASELINE ENROLMENT ANALYSIS")
print(f"{'='*70}")

# Total enrolments over time
enrol_by_month = enroll_grain.groupby('year_month')[['total_enrolments']].sum()
print(f"\nTotal enrolments by month:")
print(enrol_by_month.tail(10))

# Age-wise enrolment share
age_share = enroll_grain[['enrol_0_5', 'enrol_5_17', 'enrol_18+']].sum()
print(f"\nAge-wise enrolment share:")
print(age_share)
print(f"Percentages: 0-5: {age_share['enrol_0_5']/age_share.sum()*100:.1f}%, 5-17: {age_share['enrol_5_17']/age_share.sum()*100:.1f}%, 18+: {age_share['enrol_18+']/age_share.sum()*100:.1f}%")

# District-wise enrolment distribution
district_enrol = enroll_grain.groupby('district')[['total_enrolments']].sum().sort_values('total_enrolments', ascending=False)
print(f"\nTop 10 districts by enrolment:")
print(district_enrol.head(10))

# Chart 1: Line chart - total enrolments per month
fig, ax = plt.subplots(figsize=(14, 6))
enrol_by_month.plot(ax=ax, linewidth=2, color='#2E86AB', marker='o')
ax.set_title('Total Enrolments Over Time (Monthly)', fontsize=14, fontweight='bold')
ax.set_xlabel('Month', fontsize=12)
ax.set_ylabel('Total Enrolments', fontsize=12)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('01_enrolment_trend.png', dpi=300, bbox_inches='tight')
print("\n✓ Saved: 01_enrolment_trend.png")
plt.close()

# Chart 2: Stacked bar - age groups
age_by_month = enroll_grain.groupby('year_month')[['enrol_0_5', 'enrol_5_17', 'enrol_18+']].sum()
fig, ax = plt.subplots(figsize=(14, 6))
age_by_month.plot(kind='bar', stacked=True, ax=ax, color=['#A23B72', '#F18F01', '#C73E1D'])
ax.set_title('Enrolment by Age Group (Monthly)', fontsize=14, fontweight='bold')
ax.set_xlabel('Month', fontsize=12)
ax.set_ylabel('Enrolments', fontsize=12)
ax.legend(['Age 0-5', 'Age 5-17', 'Age 18+'], loc='upper left')
ax.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig('02_enrolment_age_stacked.png', dpi=300, bbox_inches='tight')
print("✓ Saved: 02_enrolment_age_stacked.png")
plt.close()

# Chart 3: Bar chart - top 10 districts
fig, ax = plt.subplots(figsize=(14, 6))
district_enrol.head(10).plot(kind='barh', ax=ax, color='#2E86AB')
ax.set_title('Top 10 Districts by Total Enrolments', fontsize=14, fontweight='bold')
ax.set_xlabel('Total Enrolments', fontsize=12)
ax.grid(True, alpha=0.3, axis='x')
plt.tight_layout()
plt.savefig('03_top_districts_enrolment.png', dpi=300, bbox_inches='tight')
print("✓ Saved: 03_top_districts_enrolment.png")
plt.close()

# ============================================================================
# STEP 3 — BASELINE UPDATE ANALYSIS (Demographic + Biometric)
# ============================================================================

print(f"\n{'='*70}")
print("STEP 3: BASELINE UPDATE ANALYSIS")
print(f"{'='*70}")

# Total updates over time
demo_by_month = demo_grain.groupby('year_month')[['total_demo_updates']].sum()
bio_by_month = bio_grain.groupby('year_month')[['total_bio_updates']].sum()

print(f"\nTotal demographic updates by month:")
print(demo_by_month.tail(5))
print(f"\nTotal biometric updates by month:")
print(bio_by_month.tail(5))

# Age-wise contribution
demo_age_share = demo_grain[['demo_5_17', 'demo_17+']].sum()
bio_age_share = bio_grain[['bio_5_17', 'bio_17+']].sum()

print(f"\nDemographic age-wise: 5-17: {demo_age_share['demo_5_17']/demo_age_share.sum()*100:.1f}%, 17+: {demo_age_share['demo_17+']/demo_age_share.sum()*100:.1f}%")
print(f"Biometric age-wise: 5-17: {bio_age_share['bio_5_17']/bio_age_share.sum()*100:.1f}%, 17+: {bio_age_share['bio_17+']/bio_age_share.sum()*100:.1f}%")

# Chart 4: Line chart - demo vs bio updates
fig, ax = plt.subplots(figsize=(14, 6))
demo_by_month.plot(ax=ax, linewidth=2, label='Demographic Updates', marker='o', color='#06A77D')
bio_by_month.plot(ax=ax, linewidth=2, label='Biometric Updates', marker='s', color='#D62828')
ax.set_title('Demographic vs Biometric Updates Over Time', fontsize=14, fontweight='bold')
ax.set_xlabel('Month', fontsize=12)
ax.set_ylabel('Total Updates', fontsize=12)
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('04_demo_vs_bio_updates.png', dpi=300, bbox_inches='tight')
print("\n✓ Saved: 04_demo_vs_bio_updates.png")
plt.close()

# Chart 5: Stacked bar - update types by age
update_by_age = pd.DataFrame({
    'demo_5_17': demo_grain.groupby('year_month')['demo_5_17'].sum(),
    'demo_17+': demo_grain.groupby('year_month')['demo_17+'].sum(),
    'bio_5_17': bio_grain.groupby('year_month')['bio_5_17'].sum(),
    'bio_17+': bio_grain.groupby('year_month')['bio_17+'].sum(),
})

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# Demographic stacked
demo_stack = pd.DataFrame({
    'Age 5-17': demo_grain.groupby('year_month')['demo_5_17'].sum(),
    'Age 17+': demo_grain.groupby('year_month')['demo_17+'].sum(),
})
demo_stack.plot(kind='bar', stacked=True, ax=ax1, color=['#06A77D', '#118AB2'])
ax1.set_title('Demographic Updates by Age Group', fontsize=13, fontweight='bold')
ax1.set_ylabel('Updates', fontsize=11)
ax1.legend(loc='upper left')
ax1.grid(True, alpha=0.3, axis='y')

# Biometric stacked
bio_stack = pd.DataFrame({
    'Age 5-17': bio_grain.groupby('year_month')['bio_5_17'].sum(),
    'Age 17+': bio_grain.groupby('year_month')['bio_17+'].sum(),
})
bio_stack.plot(kind='bar', stacked=True, ax=ax2, color=['#D62828', '#F77F00'])
ax2.set_title('Biometric Updates by Age Group', fontsize=13, fontweight='bold')
ax2.set_ylabel('Updates', fontsize=11)
ax2.legend(loc='upper left')
ax2.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('05_updates_age_breakdown.png', dpi=300, bbox_inches='tight')
print("✓ Saved: 05_updates_age_breakdown.png")
plt.close()

# ============================================================================
# STEP 4 — MERGE DATASETS
# ============================================================================

print(f"\n{'='*70}")
print("STEP 4: MERGING DATASETS")
print(f"{'='*70}")

# Merge all three on state + district + year_month
merged_df = enroll_grain[['state', 'district', 'year_month', 'total_enrolments']].copy()
merged_df = merged_df.merge(demo_grain[['state', 'district', 'year_month', 'total_demo_updates']], 
                            on=['state', 'district', 'year_month'], how='left')
merged_df = merged_df.merge(bio_grain[['state', 'district', 'year_month', 'total_bio_updates']], 
                            on=['state', 'district', 'year_month'], how='left')

# Fill NaN with 0
merged_df = merged_df.fillna(0)

# Create total updates
merged_df['total_updates'] = merged_df['total_demo_updates'] + merged_df['total_bio_updates']

print(f"\nMerged dataset shape: {merged_df.shape}")
print(f"Date range: {merged_df['year_month'].min()} to {merged_df['year_month'].max()}")
print(f"Sample rows:")
print(merged_df.head(10))

# ============================================================================
# STEP 5 — DERIVE OPERATIONAL METRICS
# ============================================================================

print(f"\n{'='*70}")
print("STEP 5: DERIVING OPERATIONAL METRICS")
print(f"{'='*70}")

# Metric 1: Update-to-Enrolment Ratio (UER)
merged_df['UER'] = merged_df.apply(
    lambda row: row['total_updates'] / row['total_enrolments'] if row['total_enrolments'] > 0 else 0,
    axis=1
)

# Metric 2: Biometric Stress Index (BSI)
merged_df['BSI'] = merged_df.apply(
    lambda row: row['total_bio_updates'] / row['total_updates'] if row['total_updates'] > 0 else 0,
    axis=1
)

# Metric 3: District Deviation Index (DDI)
# Calculate state averages by month
state_avg_by_month = merged_df.groupby(['state', 'year_month']).agg({
    'UER': 'mean',
    'BSI': 'mean'
}).reset_index()
state_avg_by_month.rename(columns={'UER': 'state_avg_UER', 'BSI': 'state_avg_BSI'}, inplace=True)

# Merge back
merged_df = merged_df.merge(state_avg_by_month, on=['state', 'year_month'], how='left')

# Calculate DDI for UER and BSI
merged_df['DDI_UER'] = merged_df.apply(
    lambda row: (row['UER'] - row['state_avg_UER']) / row['state_avg_UER'] if row['state_avg_UER'] > 0 else 0,
    axis=1
)
merged_df['DDI_BSI'] = merged_df.apply(
    lambda row: (row['BSI'] - row['state_avg_BSI']) / row['state_avg_BSI'] if row['state_avg_BSI'] > 0 else 0,
    axis=1
)

print(f"\nUER (Update-to-Enrolment Ratio) statistics:")
print(merged_df['UER'].describe())

print(f"\nBSI (Biometric Stress Index) statistics:")
print(merged_df['BSI'].describe())

print(f"\nDDI_UER (District Deviation Index for UER) statistics:")
print(merged_df['DDI_UER'].describe())

print(f"\nTop 10 districts by average UER:")
top_uer = merged_df.groupby('district')['UER'].mean().sort_values(ascending=False).head(10)
print(top_uer)

print(f"\nTop 10 districts by average BSI:")
top_bsi = merged_df.groupby('district')['BSI'].mean().sort_values(ascending=False).head(10)
print(top_bsi)

# ============================================================================
# STEP 6 — OPERATIONAL STRESS CLASSIFICATION
# ============================================================================

print(f"\n{'='*70}")
print("STEP 6: OPERATIONAL STRESS IDENTIFICATION")
print(f"{'='*70}")

# Define stress thresholds based on percentiles
uer_p75 = merged_df['UER'].quantile(0.75)
uer_p50 = merged_df['UER'].quantile(0.50)

bsi_p75 = merged_df['BSI'].quantile(0.75)
bsi_p50 = merged_df['BSI'].quantile(0.50)

ddi_uer_p75 = merged_df['DDI_UER'].quantile(0.75)

def classify_stress(row):
    """Classify stress level"""
    uer_score = 0
    bsi_score = 0
    ddi_score = 0
    
    if row['UER'] > uer_p75:
        uer_score = 2
    elif row['UER'] > uer_p50:
        uer_score = 1
    
    if row['BSI'] > bsi_p75:
        bsi_score = 2
    elif row['BSI'] > bsi_p50:
        bsi_score = 1
    
    if row['DDI_UER'] > ddi_uer_p75:
        ddi_score = 1
    
    total_score = uer_score + bsi_score + ddi_score
    
    if total_score >= 4:
        return 'High'
    elif total_score >= 2:
        return 'Medium'
    else:
        return 'Low'

merged_df['stress_level'] = merged_df.apply(classify_stress, axis=1)

stress_counts = merged_df['stress_level'].value_counts()
print(f"\nStress level distribution:")
print(stress_counts)

# Aggregate stress by district (average across months)
district_stress = merged_df.groupby('district').agg({
    'UER': 'mean',
    'BSI': 'mean',
    'DDI_UER': 'mean',
    'total_enrolments': 'sum',
    'total_updates': 'sum'
}).reset_index()
district_stress['stress_level'] = district_stress.apply(classify_stress, axis=1)

top_stress_districts = district_stress[district_stress['stress_level'] == 'High'].sort_values('UER', ascending=False).head(15)
print(f"\nTop 15 High-Stress Districts:")
print(top_stress_districts[['district', 'UER', 'BSI', 'DDI_UER', 'stress_level']])

# Chart 6: Heatmap - district × month stress score
# Create a pivot table for heatmap (select top 20 high-stress districts)
top_20_stressed = merged_df[merged_df['district'].isin(top_stress_districts.head(20)['district'])]
heatmap_data = top_20_stressed.pivot_table(
    index='district',
    columns='year_month',
    values='UER',
    aggfunc='mean'
)

fig, ax = plt.subplots(figsize=(16, 10))
sns.heatmap(heatmap_data, cmap='RdYlGn_r', ax=ax, cbar_kws={'label': 'UER (Update-to-Enrolment Ratio)'})
ax.set_title('District Stress Heatmap (UER) - Top 20 High-Stress Districts', fontsize=14, fontweight='bold')
ax.set_xlabel('Month', fontsize=12)
ax.set_ylabel('District', fontsize=12)
plt.tight_layout()
plt.savefig('06_stress_heatmap.png', dpi=300, bbox_inches='tight')
print("\n✓ Saved: 06_stress_heatmap.png")
plt.close()

# Chart 7: Ranked bar - top 15 stress districts
fig, ax = plt.subplots(figsize=(12, 8))
top_stress_ranked = top_stress_districts.sort_values('UER', ascending=True)
ax.barh(range(len(top_stress_ranked)), top_stress_ranked['UER'], color='#D62828')
ax.set_yticks(range(len(top_stress_ranked)))
ax.set_yticklabels(top_stress_ranked['district'])
ax.set_title('Top 15 High-Stress Districts (by UER)', fontsize=14, fontweight='bold')
ax.set_xlabel('Update-to-Enrolment Ratio (UER)', fontsize=12)
ax.grid(True, alpha=0.3, axis='x')
plt.tight_layout()
plt.savefig('07_top_stress_districts.png', dpi=300, bbox_inches='tight')
print("✓ Saved: 07_top_stress_districts.png")
plt.close()

# ============================================================================
# STEP 7 — ANOMALY DETECTION
# ============================================================================

print(f"\n{'='*70}")
print("STEP 7: ANOMALY DETECTION")
print(f"{'='*70}")

# Calculate rolling mean and std for each district
merged_df['rolling_mean'] = merged_df.groupby('district')['total_bio_updates'].transform(
    lambda x: x.rolling(window=3, min_periods=1).mean()
)
merged_df['rolling_std'] = merged_df.groupby('district')['total_bio_updates'].transform(
    lambda x: x.rolling(window=3, min_periods=1).std()
)

# Z-score calculation
merged_df['bio_zscore'] = merged_df.apply(
    lambda row: (row['total_bio_updates'] - row['rolling_mean']) / (row['rolling_std'] + 1) if row['rolling_std'] > 0 else 0,
    axis=1
)

# Identify anomalies: Z-score > 2 or < -2
merged_df['is_anomaly'] = (merged_df['bio_zscore'].abs() > 2).astype(int)

anomalies = merged_df[merged_df['is_anomaly'] == 1].copy()
anomalies = anomalies.sort_values('bio_zscore', ascending=False)

print(f"\nTotal anomalies detected: {len(anomalies)}")
print(f"\nTop 20 anomalies (bio update spikes):")
print(anomalies[['state', 'district', 'year_month', 'total_bio_updates', 'rolling_mean', 'bio_zscore']].head(20))

# Save anomaly table
anomaly_table = anomalies[['state', 'district', 'year_month', 'total_enrolments', 'total_demo_updates', 'total_bio_updates', 'bio_zscore']].head(20)
anomaly_table.to_csv('anomaly_table.csv', index=False)
print("\n✓ Saved: anomaly_table.csv")

# Chart 8: Scatter plot - anomalies visualization
fig, ax = plt.subplots(figsize=(14, 8))
normal = merged_df[merged_df['is_anomaly'] == 0]
anomaly_points = merged_df[merged_df['is_anomaly'] == 1]

ax.scatter(normal['total_enrolments'], normal['total_bio_updates'], alpha=0.5, s=30, label='Normal', color='#2E86AB')
ax.scatter(anomaly_points['total_enrolments'], anomaly_points['total_bio_updates'], alpha=0.8, s=100, label='Anomaly', color='#D62828', marker='X')

ax.set_xlabel('Total Enrolments', fontsize=12)
ax.set_ylabel('Total Biometric Updates', fontsize=12)
ax.set_title('Anomaly Detection: Bio Update Patterns', fontsize=14, fontweight='bold')
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('08_anomalies_scatter.png', dpi=300, bbox_inches='tight')
print("✓ Saved: 08_anomalies_scatter.png")
plt.close()

# ============================================================================
# STEP 8 — EARLY WARNING / LIGHT PREDICTION
# ============================================================================

print(f"\n{'='*70}")
print("STEP 8: EARLY WARNING / LIGHT PREDICTION")
print(f"{'='*70}")

from sklearn.linear_model import LinearRegression

# Prepare data for prediction
# Get monthly totals
monthly_totals = merged_df.groupby('year_month').agg({
    'total_bio_updates': 'sum',
    'total_enrolments': 'sum'
}).reset_index()

# Convert year_month to numeric for regression
monthly_totals['month_num'] = range(len(monthly_totals))

# Fit linear regression
X = monthly_totals[['month_num']].values
y = monthly_totals['total_bio_updates'].values

model = LinearRegression()
model.fit(X, y)

# Predict next 3 months
last_month_num = monthly_totals['month_num'].max()
future_months = np.array([[last_month_num + 1], [last_month_num + 2], [last_month_num + 3]])
predictions = model.predict(future_months)

print(f"\nBiometric Update Trend Analysis:")
print(f"Current trend slope: {model.coef_[0]:.2f} updates/month")
print(f"Intercept: {model.intercept_:.2f}")
print(f"\nPredicted bio updates for next 3 months:")
for i, pred in enumerate(predictions, 1):
    print(f"  Month +{i}: {pred:.0f} biometric updates")

# Chart 9: Trend + Prediction
fig, ax = plt.subplots(figsize=(14, 6))

# Plot historical
ax.plot(monthly_totals['month_num'], monthly_totals['total_bio_updates'], 'o-', linewidth=2, label='Historical', color='#2E86AB', markersize=8)

# Plot fitted line
fit_line = model.predict(X)
ax.plot(monthly_totals['month_num'], fit_line, '--', linewidth=2, label='Trend Line', color='#06A77D', alpha=0.7)

# Plot predictions
future_x = np.array([last_month_num, last_month_num + 1, last_month_num + 2, last_month_num + 3])
future_y = np.concatenate([[y[-1]], predictions])
ax.plot(future_x, future_y, 's--', linewidth=2, label='Forecast (3 months)', color='#D62828', markersize=8)

ax.set_xlabel('Month', fontsize=12)
ax.set_ylabel('Total Biometric Updates', fontsize=12)
ax.set_title('Biometric Update Trend & 3-Month Forecast', fontsize=14, fontweight='bold')
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('09_forecast_trend.png', dpi=300, bbox_inches='tight')
print("\n✓ Saved: 09_forecast_trend.png")
plt.close()

# ============================================================================
# STEP 9 — CONSOLIDATE INSIGHTS
# ============================================================================

print(f"\n{'='*70}")
print("STEP 9: CONSOLIDATING INSIGHTS")
print(f"{'='*70}")

insights = []

# Insight 1
insights.append({
    'Insight': 'Enrolment Trend Analysis',
    'Evidence': 'Chart 01 (Enrolment Trend)',
    'Finding': f"Total enrolments peaked in {enrol_by_month.idxmax()[0]} with {enrol_by_month.max()[0]:.0f} registrations. Current trend indicates {'declining' if enrol_by_month.iloc[-1][0] < enrol_by_month.iloc[-12][0] else 'stable'} pattern.",
    'UIDAI Value': 'Helps forecast resource allocation and staffing needs for upcoming quarters.'
})

# Insight 2
age_dist = age_share / age_share.sum()
insights.append({
    'Insight': 'Age Distribution in Enrolment',
    'Evidence': 'Chart 02 (Age-wise Stacked Bar)',
    'Finding': f"Adults (18+) dominate enrolment at {age_dist['enrol_18+']*100:.1f}%, while children (0-5) represent only {age_dist['enrol_0_5']*100:.1f}%. This reflects late-stage adult enrolment.",
    'UIDAI Value': 'Indicates potential for targeted outreach programs in underrepresented demographics.'
})

# Insight 3
demo_total = demo_grain['total_demo_updates'].sum()
bio_total = bio_grain['total_bio_updates'].sum()
insights.append({
    'Insight': 'Update Pattern: Demographic vs Biometric',
    'Evidence': 'Chart 04 (Demo vs Bio Line Chart)',
    'Finding': f"Biometric updates ({bio_total:.0f}) outnumber demographic updates ({demo_total:.0f}) by {(bio_total/demo_total):.1f}x. Bio updates are more resource-intensive.",
    'UIDAI Value': 'Biometric infrastructure requires more robust device allocation and technician training.'
})

# Insight 4
high_stress_count = len(top_stress_districts)
insights.append({
    'Insight': 'Operational Stress Concentration',
    'Evidence': 'Chart 06, 07 (Stress Heatmap & Ranking)',
    'Finding': f"{high_stress_count} districts classified as 'High Stress' with UER > {uer_p75:.2f}. Top district: {top_stress_districts.iloc[0]['district']} (UER: {top_stress_districts.iloc[0]['UER']:.2f}).",
    'UIDAI Value': 'These districts need immediate support: additional staff, device calibration, or process optimization.'
})

# Insight 5
anomaly_pct = (len(anomalies) / len(merged_df)) * 100
insights.append({
    'Insight': 'Anomaly Detection & Early Warnings',
    'Evidence': 'Chart 08 (Anomaly Scatter), anomaly_table.csv',
    'Finding': f"{len(anomalies)} anomalous district-month records ({anomaly_pct:.2f}% of data) detected. Most are biometric spikes beyond 2 standard deviations.",
    'UIDAI Value': 'Early warning system for unusual patterns—could signal system issues, device failures, or operational changes.'
})

# Insight 6
forecast_trend = 'increasing' if model.coef_[0] > 0 else 'decreasing'
insights.append({
    'Insight': '3-Month Forecast for Biometric Updates',
    'Evidence': 'Chart 09 (Forecast Trend)',
    'Finding': f"Linear trend shows {forecast_trend} biometric demand (slope: {model.coef_[0]:.0f}/month). Forecast next 3 months: {predictions[0]:.0f}, {predictions[1]:.0f}, {predictions[2]:.0f} updates.",
    'UIDAI Value': 'Enables proactive planning for hardware procurement, maintenance windows, and seasonal staffing adjustments.'
})

# Insight 7
top_3_states = merged_df.groupby('state')['total_enrolments'].sum().sort_values(ascending=False).head(3)
insights.append({
    'Insight': 'Geographic Concentration of Activity',
    'Evidence': 'Merged dataset aggregation',
    'Finding': f"Top 3 states: {', '.join([f'{s} ({v:.0f})' for s, v in top_3_states.items()])}. These 3 states account for {top_3_states.sum()/merged_df['total_enrolments'].sum()*100:.1f}% of national enrolments.",
    'UIDAI Value': 'Resource distribution strategy—prioritize infrastructure in high-activity zones; monitor slower regions for bottlenecks.'
})

# Save insights
insights_df = pd.DataFrame(insights)
insights_df.to_csv('insights_summary.csv', index=False)
print("\nInsights Summary:")
print(insights_df.to_string())
print("\n✓ Saved: insights_summary.csv")

print(f"\n{'='*70}")
print("ALL STEPS COMPLETE!")
print(f"{'='*70}")
print("\nDeliverables:")
print("  Charts Generated: 9 (PNG format)")
print("  Data Files: anomaly_table.csv, insights_summary.csv")
print("  Total Records Analyzed: {:.0f} district-months".format(len(merged_df)))
print(f"  Date Range: {merged_df['year_month'].min()} to {merged_df['year_month'].max()}")
print(f"\n✓ All analysis complete. Ready for PDF write-up!")

