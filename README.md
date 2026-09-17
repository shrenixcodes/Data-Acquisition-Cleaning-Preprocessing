# Week 1 — Data Acquisition, Cleaning and Preprocessing

Data-quality study of the Titanic passenger manifest: acquisition, exploration,
missing-value treatment, duplicate verification, outlier analysis, preprocessing
and validation.

## Dataset

| | |
|---|---|
| Name | Titanic passenger manifest (OpenML dataset id 40945) |
| Source | https://www.openml.org/data/get_csv/16826755/phpMYEkMl |
| Size | 1309 rows × 14 columns |
| Local copy | `data/titanic.csv` (downloaded once; the script reuses it) |

## Requirements

```bash
pip install -r requirements.txt
```

## Running the analysis

```bash
python src/data_preprocessing.py
```

Regenerates the cleaned and processed datasets, all six figures, the full
console transcript (`outputs/analysis_log.txt`) and the machine-readable
findings (`outputs/summary.json`). Rebuild the report from that run with:

```bash
python src/build_report.py
```

## Outputs

| Path | Contents |
|---|---|
| `Week_1_Data_Acquisition_Cleaning_Preprocessing_Report.docx` | Final report |
| `data/titanic_cleaned.csv` | Cleaned data, readable column values retained |
| `data/titanic_processed.csv` | Encoded and scaled matrix, 1309 × 25 |
| `outputs/figures/` | Figures used in the report |
| `outputs/analysis_log.txt` | Complete console output of the analysis |
| `outputs/summary.json` | Every value quoted in the report |
