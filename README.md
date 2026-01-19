# UIDAI Operational Analytics Data Pack

Dataset-focused package for Aadhaar enrolment and update activity (biometric, demographic, enrolment). Scope: Jan–Dec 2025, district-month grain, ~3.94M records across 985 districts.

## Contents
- Core scripts: core scripts/PHASE2_enhancements.py, core scripts/PHASE3_implementation_roadmap_v2.py, core scripts/res.py
- Summaries/guides: Exec summaries/COMPLETE_PACKAGE_SUMMARY.md, Exec summaries/HOW_TO_READ_DATA.md, Exec summaries/PHASE2_EXECUTIVE_SUMMARY.md
- Charts (PNG): images/01_enrolment_trend.png … images/09_forecast_trend.png
- Tables (CSV): anomaly tables/anomaly_table.csv, anomaly tables/PHASE2_anomaly_table.csv, csv/insights_summary.csv, csv/PHASE2_insights_enhanced.csv, csv/PHASE3_budget_breakdown.csv, csv/PHASE3_district_adaptations.csv, roadmap/PHASE3_implementation_roadmap.csv, roadmap/PHASE3_staffing_model.csv
- Optional data samples: biometric/*.csv, demographic/*.csv, enrolment/*.csv (include only non-sensitive slices)

## What the scripts do
- res.py: loads enrolment, demographic, and biometric CSVs; aggregates to district-month; produces metrics and charts.
- PHASE2_enhancements.py: computes anomaly scores using weighted biometric/demographic deltas; writes enhanced insights.
- PHASE3_implementation_roadmap_v2.py: prioritizes districts by risk-adjusted ROI under a budget; outputs roadmap and staffing CSVs.

## Quick start
```bash
cd d:\projects\clg\uidai\uidai
python "core scripts/res.py"
python "core scripts/PHASE2_enhancements.py"
python "core scripts/PHASE3_implementation_roadmap_v2.py"
```
- Requires: Python 3.10+, pandas, numpy (install via `python -m pip install pandas numpy`).
- Input CSVs must be present in biometric/, demographic/, enrolment/.

## Outputs produced
- images/: 9 PNG charts (enrolment trend, age mix, top districts, demo vs bio updates, age breakdown, stress heatmap, top stress districts, anomalies scatter, forecast trend).
- anomaly tables/: anomaly_table.csv, PHASE2_anomaly_table.csv.
- csv/: insights_summary.csv, PHASE2_insights_enhanced.csv, PHASE3_budget_breakdown.csv, PHASE3_district_adaptations.csv.
- roadmap/: PHASE3_implementation_roadmap.csv, PHASE3_staffing_model.csv.

## Data notes
- Grain: district-month; date-null rows removed before aggregation.
- Duplicates retained (assumed valid repeated transactions).
- Age groups standardized across enrolment/update files.

## Folder structure (key items)
```
uidai/
  uidai/
    biometric/
    demographic/
    enrolment/
    core scripts/
    Exec summaries/
    anomaly tables/
    csv/
    images/
    presentation/
    roadmap/
    README.md
```
