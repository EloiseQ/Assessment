# Lead Quality Analysis Project

## Project Structure

```
.
├── 01_load_and_clean.ipynb          # Data loading, cleaning, feature engineering
├── 02_trend_analysis.ipynb          # Question 1: Trend analysis
├── 03_driver_analysis.ipynb        # Question 2: Driver analysis
├── 04_uplift_scenarios.ipynb       # Question 3: 9.6% target scenario simulation
├── report.md                        # Executive Summary report
├── report.html                      # HTML Executive Summary report
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## Usage Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Execution Order

**Notebooks must be executed in order:**

1. **01_load_and_clean.ipynb**
   - Load Excel data
   - Data quality checks
   - CallStatus mapping
   - Feature engineering
   - Save cleaned data to `df_cleaned.pkl`

2. **02_trend_analysis.ipynb**
   - Load `df_cleaned.pkl`
   - Daily/weekly aggregation analysis
   - Trend visualization
   - Statistical significance tests (z-test, logistic regression)

3. **03_driver_analysis.ipynb**
   - Load `df_cleaned.pkl`
   - Univariate segmentation analysis
   - Multivariate models (Logistic Regression + Random Forest)
   - Driver summary

4. **04_uplift_scenarios.ipynb**
   - Load `df_cleaned.pkl`
   - Three scenario simulations
   - 9.6% target feasibility analysis

5. **Generate Report**
   - After running all notebooks, execute: `python3 generate_report.py`
   - Automatically generates both `report.md` and `report.html` formats
   - HTML report is more visually appealing and can be opened in a browser

## Key Metrics Definition

### Lead Quality Primary Metrics

1. **GoodQualityRate** (Primary)
   - Definition: (Closed + EP Sent + EP Received + EP Confirmed) / All
   - This is the primary quality metric

2. **CloseRate**
   - Definition: Closed / All

3. **BadRate**
   - Definition: (Unable to Contact + Invalid Profile + Doesn't Qualify) / All

### CallStatus Groups

- **Closed** (converted)
- **Good quality:** EP Sent / EP Received / EP Confirmed
- **Bad quality:** Unable to Contact / Invalid Profile / Doesn't Qualify
- **Unknown:** Neither good nor bad

## Notes

1. **Data File Path:** Ensure `Analyst_case_study_dataset_1_(1) (1).xls` is in the current directory
2. **Column Name Mapping:** Code automatically finds column names, but manual adjustment may be needed if names don't match
3. **Missing Value Handling:** Missing values for AddressScore and PhoneScore are analyzed separately
4. **WidgetName Parsing:** 300250 and 302252 are merged into the same category

## Output Files

- `df_cleaned.pkl` - Cleaned data (for use by subsequent notebooks)
- `trend_daily.png` - Trend chart (if generated)
- `segments_comparison.png` - Segment comparison chart (if generated)
- `scenario_a_results.png` - Scenario A results chart (if generated)
- `report.md` - Executive Summary in Markdown format
- `report.html` - **Executive Summary in HTML format** (visually appealing, can be opened in browser)

## Generate Report

After running all notebooks:

```bash
python3 generate_report.py
```

This automatically generates:
- ✅ `report.md` - Report in Markdown format
- ✅ `report.html` - **Report in HTML format** (visually appealing, can be opened in browser)

**Open HTML Report:**
```bash
open report.html  # Mac
# Or simply double-click the report.html file
```

HTML Report Features:
- 📱 Responsive design (mobile/tablet/desktop compatible)
- 🎨 Modern UI with colored metric cards
- 📊 Clear tables and scenario displays
- ✅ Suitable for sharing and presentation

## Troubleshooting

If you encounter issues, please check:
1. Data file exists and is readable
2. All dependencies are installed (including xlrd)
3. Notebooks are executed in order
4. Column names match actual data
