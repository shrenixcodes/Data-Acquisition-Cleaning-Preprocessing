"""
Week 1 Task - Data Acquisition, Cleaning and Preprocessing
Dataset : Titanic passenger manifest (OpenML dataset id 40945)

Running this script reproduces the full pipeline:
acquisition -> exploration -> cleaning -> outlier analysis -> preprocessing
-> validation -> figures. All printed output is mirrored to
outputs/analysis_log.txt and every numeric finding is written to
outputs/summary.json (consumed by src/build_report.py).
"""

# ---------------------------------------------------------------------------
# 1. Import libraries
# ---------------------------------------------------------------------------
import json
import os
import urllib.request
from io import StringIO

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.preprocessing import StandardScaler

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "outputs")
FIG = os.path.join(OUT, "figures")
for d in (DATA, OUT, FIG):
    os.makedirs(d, exist_ok=True)

RAW_CSV = os.path.join(DATA, "titanic.csv")
SOURCE_URL = "https://www.openml.org/data/get_csv/16826755/phpMYEkMl"

sns.set_theme(style="whitegrid")
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 50)

summary = {}
_log_lines = []


def log(*args):
    """Print to stdout and capture the text for outputs/analysis_log.txt."""
    text = " ".join(str(a) for a in args)
    print(text)
    _log_lines.append(text)


def section(title):
    log("\n" + "=" * 78)
    log(title)
    log("=" * 78)


# ---------------------------------------------------------------------------
# 2. Load dataset (download once, then reuse the local copy)
# ---------------------------------------------------------------------------
section("1. DATA ACQUISITION")

if not os.path.exists(RAW_CSV):
    log("Local copy not found - downloading from", SOURCE_URL)
    urllib.request.urlretrieve(SOURCE_URL, RAW_CSV)
else:
    log("Using local copy:", os.path.relpath(RAW_CSV, BASE))

# The OpenML distribution encodes missing entries as the literal string "?".
df_raw = pd.read_csv(RAW_CSV, na_values=["?"])
df = df_raw.copy()

log("Source URL :", SOURCE_URL)
log("File size  :", os.path.getsize(RAW_CSV), "bytes")
log("Shape      :", df.shape)

summary["source_url"] = SOURCE_URL
summary["file_bytes"] = os.path.getsize(RAW_CSV)
summary["raw_shape"] = list(df.shape)

# ---------------------------------------------------------------------------
# 3. Initial exploration
# ---------------------------------------------------------------------------
section("2. INITIAL EXPLORATION")

log("\n--- head(5) ---")
log(df.head().to_string())

log("\n--- dimensions ---")
log("rows:", df.shape[0], " columns:", df.shape[1])

log("\n--- columns ---")
log(list(df.columns))

log("\n--- dtypes ---")
log(df.dtypes.to_string())

log("\n--- info() ---")
_buf = StringIO()
df.info(buf=_buf)
log(_buf.getvalue())

log("\n--- describe() numeric ---")
desc_num = df.describe().T
log(desc_num.to_string())

log("\n--- describe() object ---")
log(df.describe(include=["object"]).T.to_string())

miss = pd.DataFrame({
    "missing": df.isna().sum(),
    "missing_pct": (df.isna().mean() * 100).round(2),
})
miss = miss[miss["missing"] > 0].sort_values("missing", ascending=False)
log("\n--- missing values ---")
log(miss.to_string())

dup_full = int(df.duplicated().sum())
log("\n--- duplicates ---")
log("exact duplicate rows:", dup_full)

log("\n--- categorical value inspection ---")
cat_summary = {}
for c in ["pclass", "survived", "sex", "embarked"]:
    vc = df[c].value_counts(dropna=False)
    log("\n" + c + " (unique=" + str(df[c].nunique(dropna=True)) + ")")
    log(vc.to_string())
    cat_summary[c] = {str(k): int(v) for k, v in vc.items()}
for c in ["name", "ticket", "cabin", "home.dest", "boat"]:
    log(c + ": " + str(df[c].nunique()) + " unique values")

_head = df.head()
summary["head_cols"] = list(df.columns)
summary["head_rows"] = _head.astype(object).where(_head.notna(), "").values.tolist()
summary["dtypes"] = {c: str(t) for c, t in df.dtypes.items()}
summary["describe_numeric"] = desc_num.round(3).reset_index().values.tolist()
summary["describe_numeric_cols"] = ["column"] + list(desc_num.columns)
summary["missing_rows"] = miss.reset_index().values.tolist()
summary["dup_full_before"] = dup_full
summary["categorical"] = cat_summary
summary["nunique"] = {c: int(df[c].nunique()) for c in df.columns}

# ---------------------------------------------------------------------------
# 4. Data-quality investigation
# ---------------------------------------------------------------------------
section("3. DATA-QUALITY INVESTIGATION")

log("\n[Q1] Columns dominated by missingness or leaking the target")
for c in ["boat", "body", "home.dest", "cabin"]:
    log("  %-10s missing=%5d (%5.2f%%)  unique=%d"
        % (c, df[c].isna().sum(), df[c].isna().mean() * 100, df[c].nunique()))
boat_surv = df.groupby(df["boat"].notna())["survived"].mean().round(4)
log("  survival rate by whether a lifeboat number was recorded:")
log(boat_surv.to_string())
summary["boat_leak"] = {str(k): float(v) for k, v in boat_surv.items()}
body_survivors = int(df.loc[df["body"].notna(), "survived"].sum())
log("  passengers with a body-recovery number who survived: " + str(body_survivors))
summary["body_leak_survivors"] = body_survivors

zero_fare = df["fare"] == 0
log("\n[Q2] fare == 0 : " + str(int(zero_fare.sum()))
    + " records (a purchased ticket cannot cost zero) - by class:")
log(df.loc[zero_fare, "pclass"].value_counts().sort_index().to_string())
summary["zero_fare_count"] = int(zero_fare.sum())
summary["zero_fare_by_class"] = {str(k): int(v) for k, v in
                                 df.loc[zero_fare, "pclass"].value_counts().sort_index().items()}

id_cols = ["name", "ticket", "cabin", "boat", "body", "home.dest"]
dup_subset = int(df.drop(columns=id_cols).duplicated().sum())
name_dupes = df[df["name"].duplicated(keep=False)].sort_values("name")
log("\n[Q3] duplicate check")
log("  exact duplicate rows                   : " + str(dup_full))
log("  duplicates ignoring identifier columns : " + str(dup_subset))
log("  repeated passenger names               : " + str(int(df["name"].duplicated().sum())))
_nd_cols = ["pclass", "survived", "name", "sex", "age", "ticket", "fare", "embarked"]
log(name_dupes[_nd_cols].to_string())
summary["dup_subset"] = dup_subset
summary["name_dupes_cols"] = _nd_cols
summary["name_dupes_rows"] = name_dupes[_nd_cols].fillna("").values.tolist()

age_by_class = (df.groupby("pclass")["age"].apply(lambda x: x.isna().mean() * 100)).round(2)
cabin_by_class = (df.groupby("pclass")["cabin"].apply(lambda x: x.isna().mean() * 100)).round(2)
log("\n[Q3b] is the missingness random? rate (%) by passenger class")
log("  age   : " + ", ".join("class %s = %.2f" % (k, v) for k, v in age_by_class.items()))
log("  cabin : " + ", ".join("class %s = %.2f" % (k, v) for k, v in cabin_by_class.items()))
log("  Missingness is concentrated in the lower classes, so it is not")
log("  missing completely at random.")
summary["age_missing_by_class"] = {str(k): float(v) for k, v in age_by_class.items()}
summary["cabin_missing_by_class"] = {str(k): float(v) for k, v in cabin_by_class.items()}

log("\n[Q4] data types needing attention")
log("  survived / pclass stored as int64 but are categorical")
log("  sex, embarked stored as free text and must be encoded for modelling")
log("  body stored as float64 although it is an identifier, not a measurement")

log("\n[Q5] suspicious numeric values")
log("  age  min=%.4f  max=%.1f" % (df["age"].min(), df["age"].max()))
log("  age below 1 year: " + str(int((df["age"] < 1).sum())) + " records (infants - plausible)")
log("  fare min=%.4f  max=%.4f" % (df["fare"].min(), df["fare"].max()))
log("  sibsp max=%d  parch max=%d" % (df["sibsp"].max(), df["parch"].max()))
_tf_cols = ["pclass", "name", "ticket", "fare", "sibsp", "parch"]
top_fare = df.loc[df["fare"] > 300, _tf_cols]
log("  highest fares (shared-ticket check):")
log(top_fare.to_string())
log("  passengers sharing ticket 'PC 17755': " + str(int((df["ticket"] == "PC 17755").sum())))
summary["top_fare_cols"] = _tf_cols
summary["top_fare_rows"] = top_fare.round(4).fillna("").values.tolist()
summary["pc17755_group"] = int((df["ticket"] == "PC 17755").sum())
summary["age_min"] = float(df["age"].min())
summary["age_max"] = float(df["age"].max())
summary["infants"] = int((df["age"] < 1).sum())

# ---------------------------------------------------------------------------
# 5. Missing-value treatment
# ---------------------------------------------------------------------------
section("4. MISSING-VALUE TREATMENT")

drop_cols = ["boat", "body", "home.dest"]
df = df.drop(columns=drop_cols)
log("Dropped columns (post-outcome leakage / unusable free text): " + str(drop_cols))

df["deck"] = df["cabin"].str[0].fillna("Unknown")
log("\ncabin -> deck (first letter); missing kept as an explicit 'Unknown' level:")
log(df["deck"].value_counts().to_string())
summary["deck_counts"] = {str(k): int(v) for k, v in df["deck"].value_counts().items()}

df["title"] = df["name"].str.extract(r",\s*([^.]*)\.", expand=False).str.strip()
raw_titles = df["title"].value_counts()
log("\nraw titles extracted from 'name':")
log(raw_titles.to_string())
title_map = {
    "Mlle": "Miss", "Ms": "Miss", "Mme": "Mrs", "Lady": "Rare", "Sir": "Rare",
    "the Countess": "Rare", "Dona": "Rare", "Don": "Rare", "Jonkheer": "Rare",
    "Capt": "Rare", "Col": "Rare", "Major": "Rare", "Dr": "Rare", "Rev": "Rare",
}
df["title"] = df["title"].replace(title_map)
log("\ntitles after consolidating equivalent and rare forms:")
log(df["title"].value_counts().to_string())
summary["raw_titles"] = {str(k): int(v) for k, v in raw_titles.items()}
summary["title_counts"] = {str(k): int(v) for k, v in df["title"].value_counts().items()}

df.loc[df["fare"] == 0, "fare"] = np.nan
fare_medians = df.groupby("pclass")["fare"].median()
log("\nfare medians by pclass used for imputation:")
log(fare_medians.round(4).to_string())
df["fare"] = df["fare"].fillna(df["pclass"].map(fare_medians))
summary["fare_medians"] = {str(k): round(float(v), 4) for k, v in fare_medians.items()}
summary["fare_imputed_total"] = int(summary["zero_fare_count"]) + 1

emb_missing = int(df["embarked"].isna().sum())
emb_mode = df["embarked"].mode()[0]
log("\nembarked: " + str(emb_missing) + " missing -> imputed with the mode '" + emb_mode + "'")
df["embarked"] = df["embarked"].fillna(emb_mode)
summary["embarked_mode"] = emb_mode
summary["embarked_missing"] = emb_missing

age_missing_before = int(df["age"].isna().sum())
age_stats_before = df["age"].describe()
grp_median = df.groupby(["pclass", "sex", "title"])["age"].transform("median")
df["age"] = df["age"].fillna(grp_median)
df["age"] = df["age"].fillna(df["age"].median())   # safety net for empty groups
age_stats_after = df["age"].describe()
log("\nage: %d missing (%.2f%%) -> median within (pclass, sex, title) groups"
    % (age_missing_before, age_missing_before / len(df) * 100))
age_cmp = pd.DataFrame({"before": age_stats_before, "after": age_stats_after}).round(3)
log(age_cmp.to_string())
summary["age_missing_before"] = age_missing_before
summary["age_stats_rows"] = age_cmp.reset_index().values.tolist()

log("\nremaining missing values: " + str(int(df.isna().sum().sum())))

# ---------------------------------------------------------------------------
# 6. Duplicate analysis
# ---------------------------------------------------------------------------
section("5. DUPLICATE HANDLING")

rows_before = len(df)
log("rows before duplicate handling      : " + str(rows_before))
log("exact duplicate rows detected       : " + str(int(df.duplicated().sum())))
log("duplicates on non-identifier subset : " + str(dup_subset))
log("The subset matches and the two repeated names belong to genuinely")
log("different passengers (different tickets, fares or ports), so no rows")
log("were removed - deleting them would discard real observations.")
rows_after = len(df)
summary["rows_before_dup"] = rows_before
summary["dup_removed"] = rows_before - rows_after
summary["rows_after_dup"] = rows_after

# ---------------------------------------------------------------------------
# 7. Outlier analysis (IQR method)
# ---------------------------------------------------------------------------
section("6. OUTLIER ANALYSIS (IQR)")

num_cols = ["age", "fare", "sibsp", "parch"]
iqr_rows = []
for c in num_cols:
    q1, q3 = df[c].quantile([0.25, 0.75])
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    n_out = int(((df[c] < lo) | (df[c] > hi)).sum())
    iqr_rows.append([c, round(q1, 3), round(q3, 3), round(iqr, 3),
                     round(lo, 3), round(hi, 3), n_out, round(n_out / len(df) * 100, 2)])
iqr_cols = ["column", "Q1", "Q3", "IQR", "lower", "upper", "n_outliers", "pct"]
iqr_tbl = pd.DataFrame(iqr_rows, columns=iqr_cols)
log(iqr_tbl.to_string(index=False))
summary["iqr_cols"] = iqr_cols
summary["iqr_rows"] = iqr_rows

log("\nFare outliers are dominated by shared group tickets: the full ticket")
log("price is repeated on every passenger travelling on that ticket.")
ticket_size = df.groupby("ticket")["ticket"].transform("size")
df["fare_per_person"] = df["fare"] / ticket_size
q1, q3 = df["fare_per_person"].quantile([0.25, 0.75])
iqr = q3 - q1
fpp_out = int(((df["fare_per_person"] < q1 - 1.5 * iqr) |
               (df["fare_per_person"] > q3 + 1.5 * iqr)).sum())
fare_out_before = int(iqr_tbl.loc[iqr_tbl["column"] == "fare", "n_outliers"].iloc[0])
log("fare outliers before per-person adjustment : " + str(fare_out_before))
log("fare_per_person outliers after adjustment  : " + str(fpp_out))
summary["fare_out_before"] = fare_out_before
summary["fare_out_after_pp"] = fpp_out

df["fare_log"] = np.log1p(df["fare_per_person"])
q1, q3 = df["fare_log"].quantile([0.25, 0.75])
iqr = q3 - q1
flog_out = int(((df["fare_log"] < q1 - 1.5 * iqr) |
                (df["fare_log"] > q3 + 1.5 * iqr)).sum())
log("log1p(fare_per_person) outliers            : " + str(flog_out))
log("Note: the per-person figure also narrows the IQR itself, so the flagged")
log("count rises even though the distribution is less distorted; skewness is")
log("the more informative measure here.")
summary["fare_out_log"] = flog_out
log("skewness fare            : %.3f" % df["fare"].skew())
log("skewness fare_per_person : %.3f" % df["fare_per_person"].skew())
log("skewness log1p(fare_pp)  : %.3f" % df["fare_log"].skew())
summary["skew"] = {
    "fare": round(float(df["fare"].skew()), 3),
    "fare_per_person": round(float(df["fare_per_person"].skew()), 3),
    "fare_log": round(float(df["fare_log"].skew()), 3),
}

_bf_cols = ["name", "ticket", "sibsp", "parch"]
big_fam = df.loc[df["sibsp"] >= 5, _bf_cols]
log("\nlargest sibsp values (" + str(len(big_fam)) + " records, two real families):")
log(big_fam.to_string())
summary["big_family_cols"] = _bf_cols
summary["big_family_rows"] = big_fam.round(2).fillna("").values.tolist()
summary["big_family_n"] = len(big_fam)
log("\nDecision: no outlier rows were deleted or capped. Every extreme value")
log("traces back to a documented passenger (infants, large families,")
log("first-class group tickets); the skew is handled by the per-person and")
log("logarithmic transforms instead.")

# ---------------------------------------------------------------------------
# 8. Preprocessing
# ---------------------------------------------------------------------------
section("7. PREPROCESSING")

df["family_size"] = df["sibsp"] + df["parch"] + 1
df["is_alone"] = (df["family_size"] == 1).astype(int)
log("engineered features: family_size, is_alone, fare_per_person, fare_log, title, deck")

df_clean = df.drop(columns=["name", "ticket", "cabin"])
log("dropped identifier columns: name, ticket, cabin")
log("(their information is retained through title, fare_per_person and deck)")

df_clean["sex"] = df_clean["sex"].map({"male": 0, "female": 1}).astype("int8")
df_clean["survived"] = df_clean["survived"].astype("int8")
df_clean["pclass"] = df_clean["pclass"].astype("int8")
log("encoded: sex -> {male:0, female:1}; survived and pclass cast to int8")

cat_cols = ["embarked", "title", "deck"]
n_before = df_clean.shape[1]
df_proc = pd.get_dummies(df_clean, columns=cat_cols, drop_first=True, dtype="int8")
log("one-hot encoded (drop_first=True): " + str(cat_cols) + " -> "
    + str(df_proc.shape[1] - n_before + len(cat_cols)) + " indicator columns")

scale_cols = ["age", "fare_log", "family_size"]
scaler = StandardScaler()
df_proc[scale_cols] = scaler.fit_transform(df_proc[scale_cols])
log("standardised to zero mean and unit variance: " + str(scale_cols))
_sd = df_proc[scale_cols].describe().round(4)
log(_sd.to_string())
summary["scale_cols"] = scale_cols
summary["scaled_desc_cols"] = ["stat"] + scale_cols
summary["scaled_desc_rows"] = _sd.reset_index().values.tolist()
summary["encoded_cols"] = list(df_proc.columns)

# ---------------------------------------------------------------------------
# 9. Validation
# ---------------------------------------------------------------------------
section("8. VALIDATION")

log("remaining missing values : " + str(int(df_proc.isna().sum().sum())))
log("exact duplicate rows     : " + str(int(df_proc.duplicated().sum())))
log("final shape              : " + str(df_proc.shape))
log("\nfinal dtypes:")
log(df_proc.dtypes.to_string())
log("\nfinal describe():")
log(df_proc.describe().T.round(4).to_string())
log("\ninvalid-value checks:")
log("  negative fare_per_person : " + str(int((df["fare_per_person"] < 0).sum())))
log("  age outside (0, 100]     : " + str(int(((df["age"] <= 0) | (df["age"] > 100)).sum())))
log("  survived outside {0,1}   : " + str(int((~df_proc["survived"].isin([0, 1])).sum())))
log("  pclass outside {1,2,3}   : " + str(int((~df_proc["pclass"].isin([1, 2, 3])).sum())))

dup_records_after = int(df.duplicated().sum())      # identifiers still present
dup_vectors_after = int(df_proc.duplicated().sum())  # identifiers removed
log("\nduplicate records with identifiers retained : " + str(dup_records_after))
log("repeated feature vectors after identifier removal : " + str(dup_vectors_after))
log("(these are separate passengers whose remaining attributes coincide,")
log("not duplicated records, so they are retained)")
summary["dup_records_after"] = dup_records_after
summary["dup_vectors_after"] = dup_vectors_after

comparison = pd.DataFrame({
    "Metric": ["Rows", "Columns", "Total missing values",
               "Columns containing missing values",
               "Duplicate records (identifiers included)",
               "Repeated feature vectors (identifiers removed)",
               "Zero-valued fares", "Text (object) columns",
               "Numeric / encoded columns", "Ready for modelling"],
    "Before": [df_raw.shape[0], df_raw.shape[1], int(df_raw.isna().sum().sum()),
               int((df_raw.isna().sum() > 0).sum()), dup_full, dup_subset,
               int((df_raw["fare"] == 0).sum()),
               int((df_raw.dtypes == object).sum()),
               int((df_raw.dtypes != object).sum()), "No"],
    "After": [df_proc.shape[0], df_proc.shape[1], int(df_proc.isna().sum().sum()),
              int((df_proc.isna().sum() > 0).sum()), dup_records_after,
              dup_vectors_after,
              int((df_clean["fare"] == 0).sum()),
              int((df_proc.dtypes == object).sum()),
              int((df_proc.dtypes != object).sum()), "Yes"],
})
log("\n--- BEFORE vs AFTER ---")
log(comparison.to_string(index=False))
summary["comparison_cols"] = list(comparison.columns)
summary["comparison_rows"] = comparison.astype(str).values.tolist()
summary["final_shape"] = list(df_proc.shape)
_ph = df_proc.head()
summary["proc_head_cols"] = list(df_proc.columns)
summary["proc_head_rows"] = _ph.round(3).astype(str).values.tolist()
summary["final_dtypes"] = {str(k): int(v) for k, v in df_proc.dtypes.value_counts().items()}

df_clean.to_csv(os.path.join(DATA, "titanic_cleaned.csv"), index=False)
df_proc.to_csv(os.path.join(DATA, "titanic_processed.csv"), index=False)
log("\nsaved data/titanic_cleaned.csv and data/titanic_processed.csv")

# ---------------------------------------------------------------------------
# 10. Visualisation
# ---------------------------------------------------------------------------
section("9. FIGURES")

# Figure 1 - missing values
fig, ax = plt.subplots(1, 2, figsize=(13, 4.6))
mp = (df_raw.isna().mean() * 100).sort_values(ascending=False)
sns.barplot(x=mp.values, y=mp.index, ax=ax[0], color="#4C72B0")
ax[0].set_xlabel("Missing (%)")
ax[0].set_ylabel("")
ax[0].set_xlim(0, 105)
ax[0].set_title("Missing values per column (raw dataset)")
for i, v in enumerate(mp.values):
    if v > 0:
        ax[0].text(v + 1.5, i, "%.1f%%" % v, va="center", fontsize=8)
sns.heatmap(df_raw.isna(), cbar=False, yticklabels=False,
            cmap=["#EAEAF2", "#C44E52"], ax=ax[1])
ax[1].set_title("Missing-value map (rows x columns)")
plt.tight_layout()
plt.savefig(os.path.join(FIG, "01_missing_values.png"), dpi=150)
plt.close()

# Figure 2 - boxplots before treatment
fig, axes = plt.subplots(1, 4, figsize=(13, 4))
for a, c in zip(axes, num_cols):
    sns.boxplot(y=df_raw[c], ax=a, color="#55A868")
    n_out = int(iqr_tbl.loc[iqr_tbl["column"] == c, "n_outliers"].iloc[0])
    a.set_title(c + "\n(IQR outliers: " + str(n_out) + ")")
fig.suptitle("Boxplots of the numerical variables before treatment", y=1.03)
plt.tight_layout()
plt.savefig(os.path.join(FIG, "02_boxplots_before.png"), dpi=150, bbox_inches="tight")
plt.close()

# Figure 3 - fare transformation
fig, axes = plt.subplots(1, 3, figsize=(13, 4))
sns.boxplot(y=df_clean["fare"], ax=axes[0], color="#C44E52")
axes[0].set_title("fare (skew %.2f)" % df["fare"].skew())
sns.boxplot(y=df_clean["fare_per_person"], ax=axes[1], color="#DD8452")
axes[1].set_title("fare_per_person (skew %.2f)" % df["fare_per_person"].skew())
sns.boxplot(y=df_clean["fare_log"], ax=axes[2], color="#4C72B0")
axes[2].set_title("log1p(fare_per_person) (skew %.2f)" % df["fare_log"].skew())
fig.suptitle("Fare outlier treatment: group-fare adjustment and log transform", y=1.03)
plt.tight_layout()
plt.savefig(os.path.join(FIG, "03_fare_outlier_treatment.png"), dpi=150, bbox_inches="tight")
plt.close()

# Figure 4 - age before / after imputation
fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))
sns.histplot(df_raw["age"].dropna(), bins=30, kde=True, ax=axes[0], color="#C44E52")
axes[0].set_title("age before imputation (n=%d)" % int(df_raw["age"].notna().sum()))
sns.histplot(df_clean["age"], bins=30, kde=True, ax=axes[1], color="#55A868")
axes[1].set_title("age after group-median imputation (n=%d)" % len(df_clean))
for a in axes:
    a.set_xlabel("age (years)")
fig.suptitle("Effect of missing-value imputation on the age distribution", y=1.03)
plt.tight_layout()
plt.savefig(os.path.join(FIG, "04_age_before_after.png"), dpi=150, bbox_inches="tight")
plt.close()

# Figure 5 - categorical distributions
fig, axes = plt.subplots(1, 4, figsize=(14, 4))
for a, c in zip(axes, ["pclass", "sex", "embarked", "title"]):
    src = df_raw[c] if c != "title" else df["title"]
    sns.countplot(x=src, order=src.value_counts().index, ax=a,
                  hue=src, legend=False, palette="deep")
    a.set_title(c)
    a.set_xlabel("")
    a.tick_params(axis="x", rotation=30)
fig.suptitle("Categorical variable distributions", y=1.03)
plt.tight_layout()
plt.savefig(os.path.join(FIG, "05_categorical_distributions.png"), dpi=150, bbox_inches="tight")
plt.close()

# Figure 6 - correlation of the processed features
corr_cols = ["survived", "pclass", "sex", "age", "sibsp", "parch",
             "family_size", "is_alone", "fare_log"]
plt.figure(figsize=(8.5, 6.5))
sns.heatmap(df_proc[corr_cols].corr(), annot=True, fmt=".2f", cmap="vlag",
            center=0, square=True, cbar_kws={"shrink": 0.8})
plt.title("Correlation matrix of the preprocessed feature set")
plt.tight_layout()
plt.savefig(os.path.join(FIG, "06_correlation_processed.png"), dpi=150)
plt.close()

log("figures written to " + os.path.relpath(FIG, BASE))

with open(os.path.join(OUT, "analysis_log.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(_log_lines))
with open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=1, default=str)

log("\nPipeline complete.")
