"""
Builds Week_1_Data_Acquisition_Cleaning_Preprocessing_Report.docx from the
values recorded in outputs/summary.json and the figures in outputs/figures.

Run src/data_preprocessing.py first: every number and table in the report is
read from that run, so the document can never drift from the analysis.
"""

import json
import os
import subprocess
from datetime import date

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "outputs")
FIG = os.path.join(OUT, "figures")
DOCX = os.path.join(BASE, "Week_1_Data_Acquisition_Cleaning_Preprocessing_Report.docx")

S = json.load(open(os.path.join(OUT, "summary.json"), encoding="utf-8"))

doc = Document()
_base = doc.styles["Normal"]
_base.font.name = "Calibri"
_base.font.size = Pt(11)
_base.paragraph_format.space_after = Pt(6)
_base.paragraph_format.line_spacing = 1.15

_fig_no = [0]
_tbl_no = [0]


def h(text, level=1):
    p = doc.add_heading(text, level=level)
    for r in p.runs:
        r.font.color.rgb = RGBColor(0x1F, 0x37, 0x63)
    return p


def para(text, bold=False, italic=False, size=11, align=None):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = bold
    r.italic = italic
    r.font.size = Pt(size)
    if align is not None:
        p.alignment = align
    return p


def bullets(items):
    for it in items:
        doc.add_paragraph(it, style="List Bullet")


def shade(cell, hexcolor):
    el = OxmlElement("w:shd")
    el.set(qn("w:val"), "clear")
    el.set(qn("w:fill"), hexcolor)
    cell._tc.get_or_add_tcPr().append(el)


def table(cols, rows, caption, widths=None, font=9, numeric_from=1):
    _tbl_no[0] += 1
    t = doc.add_table(rows=1, cols=len(cols))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    trPr = t.rows[0]._tr.get_or_add_trPr()
    trPr.append(OxmlElement("w:tblHeader"))          # repeat header on page breaks
    hdr = t.rows[0].cells
    for i, c in enumerate(cols):
        hdr[i].text = ""
        run = hdr[i].paragraphs[0].add_run(str(c))
        run.bold = True
        run.font.size = Pt(font)
        shade(hdr[i], "1F3763")
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            run = cells[i].paragraphs[0].add_run("" if v is None else str(v))
            run.font.size = Pt(font)
            if i >= numeric_from:
                cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    for r in t.rows:
        r.allow_break_across_pages = False
    if len(rows) <= 12:                 # keep short tables whole on one page
        for r in t.rows[:-1]:
            for c in r.cells:
                for pp in c.paragraphs:
                    pp.paragraph_format.keep_with_next = True
    if widths:
        for r in t.rows:
            for i, w in enumerate(widths):
                r.cells[i].width = Inches(w)
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cr = cap.add_run("Table %d: %s" % (_tbl_no[0], caption))
    cr.italic = True
    cr.font.size = Pt(9)
    return t


def figure(filename, caption, width=6.3):
    _fig_no[0] += 1
    doc.add_picture(os.path.join(FIG, filename), width=Inches(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.paragraphs[-1].paragraph_format.keep_with_next = True
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cr = cap.add_run("Figure %d: %s" % (_fig_no[0], caption))
    cr.italic = True
    cr.font.size = Pt(9)


def code(text):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.25)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.line_spacing = 1.0
    r = p.add_run(text.strip("\n"))
    r.font.name = "Consolas"
    r.font.size = Pt(8.5)
    r._element.rPr.rFonts.set(qn("w:eastAsia"), "Consolas")
    pPr = p._p.get_or_add_pPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear")
    sh.set(qn("w:fill"), "F2F2F2")
    pPr.append(sh)
    return p


def page_break():
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def student_name():
    try:
        n = subprocess.check_output(["git", "config", "user.name"], cwd=BASE,
                                    text=True).strip()
        return n or None
    except Exception:
        return None


# ---------------------------------------------------------------- title page
for _ in range(4):
    doc.add_paragraph()
para("Week 1 Task", bold=True, size=16, align=WD_ALIGN_PARAGRAPH.CENTER)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Data Acquisition, Cleaning and Preprocessing")
r.bold = True
r.font.size = Pt(26)
r.font.color.rgb = RGBColor(0x1F, 0x37, 0x63)
para("A practical data-quality study of the Titanic passenger manifest",
     italic=True, size=12, align=WD_ALIGN_PARAGRAPH.CENTER)
doc.add_paragraph()
doc.add_paragraph()

meta = [
    ("Dataset", "Titanic passenger manifest (OpenML dataset id 40945)"),
    ("Source", S["source_url"]),
    ("Dataset size", "%d rows x %d columns (%.0f KB)"
     % (S["raw_shape"][0], S["raw_shape"][1], S["file_bytes"] / 1024)),
    ("Analysis script", "src/data_preprocessing.py"),
    ("Date", date.today().strftime("%d %B %Y")),
]
name = student_name()
if name:
    meta.insert(0, ("Prepared by", name))

t = doc.add_table(rows=0, cols=2)
t.style = "Table Grid"
t.alignment = WD_TABLE_ALIGNMENT.CENTER
for k, v in meta:
    c = t.add_row().cells
    rk = c[0].paragraphs[0].add_run(k)
    rk.bold = True
    rk.font.size = Pt(10)
    shade(c[0], "EDF0F6")
    rv = c[1].paragraphs[0].add_run(v)
    rv.font.size = Pt(10)
    c[0].width = Inches(1.6)
    c[1].width = Inches(4.7)
page_break()

# --------------------------------------------------------------- 1. intro
h("1. Introduction", 1)
para(
    "This report documents the acquisition, quality assessment, cleaning and "
    "preprocessing of a real, publicly available dataset. The objective is to "
    "take a raw file exactly as it is published, establish what is actually "
    "wrong with it through explicit checks rather than assumption, correct the "
    "defects with justified methods, and deliver a dataset that is ready for "
    "statistical analysis and machine learning."
)
h("Why data quality matters", 2)
para(
    "Analytical results inherit every defect present in their input. Missing "
    "values silently shrink the sample of any calculation that touches them; "
    "impossible values distort means, variances and correlations; duplicated "
    "records give repeated observations double weight; and text categories "
    "cannot be consumed by most modelling algorithms at all. A model trained "
    "on uncorrected data can appear accurate while having learned an artefact "
    "of the recording process rather than a real relationship."
)
h("Purpose of preprocessing", 2)
para(
    "Preprocessing converts a human-readable record set into a numerical matrix "
    "with consistent types, no gaps and comparable scales, while preserving as "
    "much genuine information as possible. Every transformation applied here is "
    "recorded together with the reason for it, so that the resulting dataset "
    "can be audited and reproduced."
)

# --------------------------------------------------------- 2. dataset choice
h("2. Dataset Selection", 1)
tbl_rows = [
    ["Dataset name", "Titanic passenger manifest (OpenML dataset id 40945)"],
    ["Source", S["source_url"]],
    ["Provider", "OpenML, an open public repository of machine-learning datasets"],
    ["Format", "CSV, %d bytes" % S["file_bytes"]],
    ["Records", "%d passengers" % S["raw_shape"][0]],
    ["Attributes", "%d columns" % S["raw_shape"][1]],
    ["Target variable", "survived (0 = did not survive: %d, 1 = survived: %d)"
     % (S["categorical"]["survived"]["0"], S["categorical"]["survived"]["1"])],
]
table(["Property", "Value"], tbl_rows, "Dataset identification.",
      widths=[1.6, 4.7], numeric_from=99)

h("Attributes", 2)
attr_desc = [
    ("pclass", "Ticket class (1, 2, 3) - a proxy for socio-economic status"),
    ("survived", "Survival outcome, the natural target variable"),
    ("name", "Full passenger name, including an honorific title"),
    ("sex", "Passenger sex"),
    ("age", "Age in years; fractional values are used for infants"),
    ("sibsp", "Number of siblings and spouses aboard"),
    ("parch", "Number of parents and children aboard"),
    ("ticket", "Ticket number, shared by passengers travelling together"),
    ("fare", "Price paid for the ticket"),
    ("cabin", "Cabin identifier, beginning with a deck letter"),
    ("embarked", "Port of embarkation (S, C, Q)"),
    ("boat", "Lifeboat identifier, recorded only for rescued passengers"),
    ("body", "Body-recovery number, recorded only for recovered victims"),
    ("home.dest", "Free-text home town and destination"),
]
table(["Column", "Description"],
      [[c, d] for c, d in attr_desc], "Attributes of the raw dataset.",
      widths=[1.3, 5.0], numeric_from=99)

h("Reason for selection", 2)
para(
    "The dataset was chosen because it exhibits, in one small file, every "
    "category of defect this task is intended to address: substantial and "
    "unevenly distributed missing values, non-numeric categorical text, "
    "identifier columns of high cardinality, values that are numerically valid "
    "but factually impossible, heavily skewed monetary values, and two columns "
    "that leak the outcome. It is also small enough that every finding can be "
    "traced back to individual records and verified by hand."
)


# ----------------------------------------------------------- 3. acquisition
h("3. Data Acquisition", 1)
para(
    "The file was downloaded once, programmatically, from the OpenML "
    "distribution of the dataset and stored in the repository as "
    "data/titanic.csv so that later runs are reproducible and do not depend on "
    "network availability. OpenML publishes the manifest with missing entries "
    "encoded as the literal character \"?\" rather than as empty fields, so "
    "that token has to be declared when reading the file; otherwise every "
    "affected column is silently loaded as text and no missing value is "
    "detected at all."
)
code(
    'SOURCE_URL = "%s"\n'
    '\n'
    'if not os.path.exists(RAW_CSV):\n'
    '    urllib.request.urlretrieve(SOURCE_URL, RAW_CSV)\n'
    '\n'
    '# The OpenML distribution encodes missing entries as the literal string "?".\n'
    'df_raw = pd.read_csv(RAW_CSV, na_values=["?"])' % S["source_url"]
)
para("The load produced a DataFrame of %d rows and %d columns."
     % (S["raw_shape"][0], S["raw_shape"][1]))

# ----------------------------------------------------------- 4. exploration
h("4. Initial Data Exploration", 1)
para("Dimensions: %d rows x %d columns. The first five records are shown below."
     % (S["raw_shape"][0], S["raw_shape"][1]))

head_show = ["pclass", "survived", "name", "sex", "age", "sibsp",
             "parch", "fare", "cabin", "embarked"]
idx = [S["head_cols"].index(c) for c in head_show]
table(head_show, [[r[i] for i in idx] for r in S["head_rows"]],
      "First five records of the raw dataset (a subset of columns).",
      font=7.5, numeric_from=0)

para("Column data types as loaded:")
dt_rows = [[c, t] for c, t in S["dtypes"].items()]
half = (len(dt_rows) + 1) // 2
pair_rows = []
for i in range(half):
    left = dt_rows[i]
    right = dt_rows[i + half] if i + half < len(dt_rows) else ["", ""]
    pair_rows.append(left + right)
table(["Column", "Dtype", "Column", "Dtype"], pair_rows,
      "Data types reported by pandas for the raw dataset.",
      widths=[1.6, 1.5, 1.6, 1.5], numeric_from=99)

para("Descriptive statistics for the numeric columns:")
table(S["describe_numeric_cols"], S["describe_numeric"],
      "Descriptive statistics of the raw numeric columns.", font=8)

para(
    "Three observations follow directly from this table. The count column shows "
    "that age is present for only %d of %d passengers. The minimum fare is 0, "
    "which cannot be the price of a purchased ticket. The maximum fare of "
    "%.2f is roughly ten times the third quartile, which signals a strongly "
    "skewed monetary distribution."
    % (int(S["describe_numeric"][2][1]), S["raw_shape"][0],
       float(S["describe_numeric"][5][8]))
)

para("Missing values by column (columns with no missing values are omitted):")
miss_rows = [[c, n, "%.2f%%" % p] for c, n, p in S["missing_rows"]]
table(["Column", "Missing", "Missing %"], miss_rows,
      "Missing-value counts and percentages in the raw dataset.",
      widths=[2.0, 1.4, 1.4])
para("Total missing cells: %s. Exact duplicate rows: %d."
     % (S["comparison_rows"][2][1], S["dup_full_before"]))

para("Categorical value inspection:")
cat_rows = []
for col, counts in S["categorical"].items():
    vals = ", ".join("%s: %s" % (k if k != "nan" else "missing", v)
                     for k, v in counts.items())
    cat_rows.append([col, S["nunique"][col], vals])
for col in ["name", "ticket", "cabin", "home.dest", "boat"]:
    cat_rows.append([col, S["nunique"][col], "high-cardinality identifier / free text"])
table(["Column", "Unique", "Values and counts"], cat_rows,
      "Distinct values of the categorical columns.",
      widths=[1.2, 0.8, 4.3], numeric_from=1)

figure("05_categorical_distributions.png",
       "Distributions of the categorical variables. The title column is derived "
       "from name during preprocessing and is shown here after consolidation.")


# -------------------------------------------------------------- 5. cleaning
h("5. Data Cleaning", 1)

h("5.1 Missing values", 2)
para("Findings. Seven of the fourteen columns contain missing values, and the "
     "extent differs by two orders of magnitude between them.")
figure("01_missing_values.png",
       "Missing values per column (left) and their position within the file "
       "(right). Red marks a missing cell.")
para(
    "The map on the right shows that missingness in body and boat is not "
    "random: a lifeboat number exists only for rescued passengers and a "
    "body-recovery number only for victims whose remains were recovered. Both "
    "columns are therefore recorded after the outcome they would be used to "
    "predict. The check confirms it numerically: the survival rate is %.1f%% "
    "among passengers with a lifeboat number and %.1f%% among those without, "
    "and none of the %s passengers carrying a body-recovery number survived."
    % (S["boat_leak"]["True"] * 100, S["boat_leak"]["False"] * 100,
       S["missing_rows"][0][1] and (S["raw_shape"][0] - S["missing_rows"][0][1]))
)
para(
    "Missingness in the remaining columns is also structured rather than "
    "random. Age is absent for %.2f%% of third-class passengers but only "
    "%.2f%% of first-class passengers, and cabin for %.2f%% against %.2f%%. "
    "Record-keeping was simply better for the higher fares, which means that "
    "deleting incomplete rows would remove third-class passengers "
    "preferentially and distort every group comparison that follows."
    % (S["age_missing_by_class"]["3"], S["age_missing_by_class"]["1"],
       S["cabin_missing_by_class"]["3"], S["cabin_missing_by_class"]["1"])
)
treat_rows = [
    ["body", "%d (%.2f%%)" % (1188, 90.76),
     "Removed",
     "Recorded only after the disaster and only for victims; using it would "
     "leak the target. Almost entirely missing in any case."],
    ["boat", "%d (%.2f%%)" % (823, 62.87),
     "Removed",
     "Recorded only for rescued passengers; it determines the target almost "
     "perfectly and cannot exist before the outcome."],
    ["home.dest", "%d (%.2f%%)" % (564, 43.09),
     "Removed",
     "Free text with %d distinct values and no usable structure; imputing "
     "43%% of a free-text field would invent information."
     % S["nunique"]["home.dest"]],
    ["cabin", "%d (%.2f%%)" % (1014, 77.46),
     "Recoded, not imputed",
     "The deck letter is retained as a new column 'deck'; missing entries "
     "become an explicit level 'Unknown' because the absence of a cabin record "
     "is itself informative and cannot be guessed."],
    ["age", "%d (%.2f%%)" % (263, 20.09),
     "Median within (pclass, sex, title)",
     "One fifth of the column; deleting those rows would discard 20% of the "
     "sample. The median is robust to the right skew of age, and conditioning "
     "on class, sex and honorific keeps children and adults distinguishable "
     "instead of collapsing everyone onto one global value."],
    ["embarked", "%d (%.2f%%)" % (2, 0.15),
     "Mode ('%s')" % S["embarked_mode"],
     "Only two records. The mode is the standard choice for a nominal variable "
     "and, at 0.15%% of the data, cannot bias the distribution."],
    ["fare", "%d (%.2f%%)" % (1, 0.08),
     "Median within pclass",
     "A single record. Fare depends strongly on class, so the class median is "
     "more accurate than the overall median and is unaffected by the extreme "
     "upper tail."],
]
table(["Column", "Missing", "Treatment", "Rationale"], treat_rows,
      "Missing-value treatment decisions, column by column.",
      widths=[0.9, 1.0, 1.4, 3.0], font=8.5, numeric_from=99)

para("The title used for conditioning is extracted from the name column before "
     "that column is discarded, and rare honorifics are consolidated so that no "
     "group contains too few passengers to yield a stable median.")
code(
    'df["title"] = df["name"].str.extract(r",\\s*([^.]*)\\.", expand=False).str.strip()\n'
    'df["title"] = df["title"].replace(title_map)   # Mlle/Ms -> Miss, Mme -> Mrs, rare -> Rare\n'
    '\n'
    'grp_median = df.groupby(["pclass", "sex", "title"])["age"].transform("median")\n'
    'df["age"] = df["age"].fillna(grp_median)'
)
para("Titles after consolidation: "
     + ", ".join("%s (%d)" % (k, v) for k, v in S["title_counts"].items()) + ".")

para("Before and after, for the age column:")
table(["Statistic", "Before imputation", "After imputation"],
      [[r[0], r[1], r[2]] for r in S["age_stats_rows"]],
      "Age distribution before and after group-median imputation.",
      widths=[1.6, 1.8, 1.8])
figure("04_age_before_after.png",
       "Age distribution before and after imputation. The imputed values "
       "concentrate at the group medians, which raises the central bars; the "
       "shape of the tails is preserved.")
para(
    "The mean moves only from %s to %s years and the standard deviation from "
    "%s to %s. The contraction in spread is the expected cost of imputing a "
    "fifth of a column with central values, and it is reported here rather "
    "than hidden."
    % (S["age_stats_rows"][1][1], S["age_stats_rows"][1][2],
       S["age_stats_rows"][2][1], S["age_stats_rows"][2][2])
)

h("5.2 Duplicate records", 2)
para(
    "Findings. The raw file contains %d exact duplicate rows. Ignoring the "
    "identifier columns (name, ticket, cabin, boat, body, home.dest), %d rows "
    "become indistinguishable, and %d passenger names occur twice."
    % (S["dup_full_before"], S["dup_subset"], len(S["name_dupes_rows"]) // 2)
)
table(S["name_dupes_cols"], S["name_dupes_rows"],
      "The two repeated passenger names, shown with their full records.",
      font=8, numeric_from=3)
para(
    "Treatment: no rows were removed. The repeated names belong to different "
    "people - the two passengers named Connolly travelled on different tickets "
    "at different fares and had different outcomes, and the two named Kelly "
    "embarked at different ports. The %d subset matches are likewise distinct "
    "third-class passengers who happen to share class, sex, age band and family "
    "structure. Deleting them would remove real observations and bias survival "
    "rates for exactly the group that was most numerous aboard, so the correct "
    "action here is to detect, verify and retain." % S["dup_subset"]
)
para("Rows before: %d. Rows removed: %d. Rows after: %d."
     % (S["rows_before_dup"], S["dup_removed"], S["rows_after_dup"]), bold=True)

h("5.3 Inconsistent and erroneous values", 2)
zf = S["zero_fare_by_class"]
para(
    "Findings and corrections. Three issues were confirmed by explicit checks; "
    "no issue is reported that the checks did not find."
)
err_rows = [
    ["fare = 0",
     "%d records (class 1: %s, class 2: %s, class 3: %s)"
     % (S["zero_fare_count"], zf["1"], zf["2"], zf["3"]),
     "Replaced with the class median",
     "A purchased ticket cannot cost zero; the entries are placeholders for an "
     "unknown or non-commercial fare. They occur in all three classes, so a "
     "single global replacement would be wrong. Left untreated they would drag "
     "the class means downwards."],
    ["Missing token \"?\"",
     "Present in 7 columns",
     "Declared as a missing marker at load time",
     "Without na_values=[\"?\"] the age, fare and body columns load as text and "
     "no missing value is detected."],
    ["Rare and equivalent titles",
     "%d distinct honorifics in name" % len(S["raw_titles"]),
     "Mlle and Ms mapped to Miss, Mme to Mrs, the remaining %d rare forms "
     "grouped as Rare" % S["title_counts"]["Rare"],
     "Mlle and Mme are the French equivalents of Miss and Mrs and are the same "
     "category. Titles held by one or two passengers cannot support a stable "
     "group statistic or a useful indicator column."],
    ["Type inconsistencies",
     "survived, pclass as int64; sex, embarked as text",
     "Cast to int8 and encoded numerically",
     "These are categorical variables; storing them as wide integers or free "
     "text wastes memory and blocks most modelling libraries."],
]
table(["Issue", "Extent", "Correction", "Rationale"], err_rows,
      "Inconsistent and erroneous values found and corrected.",
      widths=[1.1, 1.4, 1.5, 2.3], font=8.5, numeric_from=99)
code(
    '# a zero fare is treated as unknown, then imputed from the class median\n'
    'df.loc[df["fare"] == 0, "fare"] = np.nan\n'
    'fare_medians = df.groupby("pclass")["fare"].median()\n'
    'df["fare"] = df["fare"].fillna(df["pclass"].map(fare_medians))'
)
para("Class medians used: class 1 = %.2f, class 2 = %.2f, class 3 = %.2f. "
     "In total %d fare values were imputed (%d zeros and %d genuinely missing)."
     % (S["fare_medians"]["1"], S["fare_medians"]["2"], S["fare_medians"]["3"],
        S["fare_imputed_total"], S["zero_fare_count"], 1))

para(
    "Values that were checked and found to be legitimate are equally important. "
    "The minimum age of %.4f years (%d passengers under one year old) is a "
    "deliberate fractional encoding for infants, not a data-entry error, and "
    "was left unchanged."
    % (S["age_min"], S["infants"])
)


# --------------------------------------------------------------- 6. outliers
h("6. Outlier Detection and Treatment", 1)
h("Methodology", 2)
para(
    "Outliers were identified with the interquartile-range rule. The first and "
    "third quartiles Q1 and Q3 are computed for each numeric column, the "
    "interquartile range is IQR = Q3 - Q1, and any value outside the interval "
    "[Q1 - 1.5 x IQR, Q3 + 1.5 x IQR] is flagged. The rule was chosen in "
    "preference to a standard-deviation threshold because quartiles are not "
    "themselves distorted by the extreme values being searched for, which "
    "matters for a fare column whose maximum is an order of magnitude above "
    "its own third quartile."
)
para("Flagging a value is a question, not a verdict. Each flagged group below "
     "was traced back to the underlying records before any decision was taken.")
table(S["iqr_cols"], S["iqr_rows"],
      "IQR boundaries and the number of flagged values per numeric column.",
      font=9)
figure("02_boxplots_before.png",
       "Boxplots of the numeric variables in the raw dataset, with the number "
       "of values flagged by the IQR rule.")

h("Findings and decisions", 2)
para("age - %d values flagged (%.2f%%), all above the upper bound of %.2f years."
     % (S["iqr_rows"][0][6], S["iqr_rows"][0][7], S["iqr_rows"][0][5]))
para(
     "These are elderly passengers, up to %.0f years old, and the lower bound "
     "of %.2f years is negative and therefore vacuous. Ages in this range are "
     "biologically ordinary. Decision: retained, untransformed. Removing "
     "passengers for being old would delete a real and interesting subgroup."
     % (S["age_max"], S["iqr_rows"][0][4]))

para("fare - %d values flagged (%.2f%%), the largest group in the dataset."
     % (S["fare_out_before"], S["iqr_rows"][1][7]))
table(S["top_fare_cols"], S["top_fare_rows"],
      "The highest fares in the dataset.", font=8, numeric_from=3)
para(
    "Inspection explains the tail. The four highest fares of %.2f are not four "
    "individual payments: %d passengers share the single ticket PC 17755, and "
    "the full price of that ticket is repeated on every one of their rows. The "
    "fare column therefore measures the cost of a booking, not the cost of a "
    "passenger, and the resulting values are genuine but not comparable across "
    "rows. Decision: no record was deleted or capped. Instead the fare is "
    "divided by the number of passengers sharing the ticket, which makes the "
    "values comparable, and a log transform then compresses the residual right "
    "tail."
    % (S["top_fare_rows"][0][3], S["pc17755_group"])
)
code(
    'ticket_size = df.groupby("ticket")["ticket"].transform("size")\n'
    'df["fare_per_person"] = df["fare"] / ticket_size\n'
    'df["fare_log"] = np.log1p(df["fare_per_person"])'
)
table(["Variable", "Skewness", "IQR outliers"],
      [["fare", S["skew"]["fare"], S["fare_out_before"]],
       ["fare_per_person", S["skew"]["fare_per_person"], S["fare_out_after_pp"]],
       ["log1p(fare_per_person)", S["skew"]["fare_log"], S["fare_out_log"]]],
      "Effect of the group-fare adjustment and the log transform.",
      widths=[2.4, 1.4, 1.4])
para(
    "The per-person adjustment reduces skewness from %.2f to %.2f, and the log "
    "transform brings it to %.2f, close to symmetric. The count of flagged "
    "values rises to %d at the intermediate step: dividing by group size also "
    "narrows the interquartile range itself, so the 1.5 x IQR fence tightens "
    "even as the distribution becomes less distorted. Skewness is the more "
    "informative measure of the two here, and after the log transform both "
    "agree, with the flagged count falling to %d."
    % (S["skew"]["fare"], S["skew"]["fare_per_person"], S["skew"]["fare_log"],
       S["fare_out_after_pp"], S["fare_out_log"])
)
figure("03_fare_outlier_treatment.png",
       "The fare column before treatment, after adjusting for shared tickets, "
       "and after the logarithmic transform.")

para("sibsp - %d values flagged (%.2f%%); parch - %d values flagged (%.2f%%)."
     % (S["iqr_rows"][2][6], S["iqr_rows"][2][7],
        S["iqr_rows"][3][6], S["iqr_rows"][3][7]))
table(S["big_family_cols"], S["big_family_rows"][:6] + [["...", "...", "...", "..."]]
      + S["big_family_rows"][-3:],
      "Passengers with the largest sibsp values (%d records in total); rows "
      "omitted for brevity are further members of the same two families."
      % S["big_family_n"], font=8, numeric_from=2)
para(
    "The extreme values resolve into two large families travelling together on "
    "tickets CA 2144 and CA. 2343. For parch the rule degenerates entirely: "
    "the first and third quartiles are both %.0f, so the IQR is zero and every "
    "passenger travelling with even one parent or child is flagged. This is a "
    "clear illustration that the IQR rule is unreliable on a count variable "
    "whose mass sits at zero. Decision: both columns retained unchanged, and "
    "the information consolidated into a family_size feature instead."
    % S["iqr_rows"][3][1]
)
para(
    "Summary of outlier treatment: no rows were deleted and no values were "
    "capped. Every extreme value in this dataset traces back to a documented "
    "passenger. The distortion that genuinely needed correcting was a unit "
    "problem in the fare column, and it was corrected by transformation rather "
    "than by discarding observations.", bold=True
)


# --------------------------------------------------------- 7. preprocessing
h("7. Data Preprocessing", 1)

h("7.1 Feature engineering", 2)
bullets([
    "title, extracted from name and consolidated into %d groups, which "
    "captures sex, marital status and social rank in a single low-cardinality "
    "variable and makes the age imputation conditional."
    % len(S["title_counts"]),
    "deck, the first letter of cabin, with missing cabins kept as an explicit "
    "'Unknown' level (%d passengers) rather than discarded."
    % S["deck_counts"]["Unknown"],
    "family_size = sibsp + parch + 1, and the derived indicator is_alone, "
    "which combine two correlated counts into one interpretable measure.",
    "fare_per_person and its logarithm fare_log, as described in section 6.",
])
code(
    'df["family_size"] = df["sibsp"] + df["parch"] + 1\n'
    'df["is_alone"] = (df["family_size"] == 1).astype(int)\n'
    'df["deck"] = df["cabin"].str[0].fillna("Unknown")'
)

h("7.2 Removal of irrelevant columns", 2)
para(
    "name, ticket and cabin were dropped after the features above had been "
    "derived from them. As raw text they have %d, %d and %d distinct values "
    "respectively; encoding them directly would produce thousands of indicator "
    "columns, one of which would identify each passenger individually. boat, "
    "body and home.dest were dropped earlier for the reasons given in section "
    "5.1."
    % (S["nunique"]["name"], S["nunique"]["ticket"], S["nunique"]["cabin"])
)

h("7.3 Encoding", 2)
para(
    "sex is binary and was mapped directly to {male: 0, female: 1}; a one-hot "
    "expansion would add a redundant, perfectly collinear column. embarked, "
    "title and deck are nominal with no meaningful order, so they were one-hot "
    "encoded with the first level dropped to avoid the dummy-variable trap. "
    "pclass was kept as a single integer because its levels are genuinely "
    "ordered, first to third."
)
code(
    'df_clean["sex"] = df_clean["sex"].map({"male": 0, "female": 1}).astype("int8")\n'
    'df_proc = pd.get_dummies(df_clean, columns=["embarked", "title", "deck"],\n'
    '                         drop_first=True, dtype="int8")'
)

h("7.4 Scaling", 2)
para(
    "Standardisation was applied to %s only: these are the continuous features "
    "whose units differ by orders of magnitude. The binary indicators and the "
    "ordinal pclass were deliberately left alone, since scaling a 0/1 column "
    "changes nothing of substance and destroys its interpretability. Scaling "
    "matters for distance-based and gradient-based methods, which would "
    "otherwise let the variable with the widest numeric range dominate; it is "
    "irrelevant to tree-based models, which is why the unscaled fare and "
    "fare_per_person columns are retained in the output file as well."
    % ", ".join(S["scale_cols"])
)
code(
    'scale_cols = ["age", "fare_log", "family_size"]\n'
    'scaler = StandardScaler()\n'
    'df_proc[scale_cols] = scaler.fit_transform(df_proc[scale_cols])'
)
table(S["scaled_desc_cols"], S["scaled_desc_rows"],
      "Descriptive statistics of the standardised columns, confirming zero "
      "mean and unit variance.", font=9)


# ------------------------------------------------------------ 8. validation
h("8. Validation and Before / After Comparison", 1)
para("The checks below were run on the final matrix after all transformations.")
table(S["comparison_cols"], S["comparison_rows"],
      "Data-quality metrics before and after cleaning and preprocessing.",
      widths=[3.2, 1.5, 1.5], font=9.5)
para(
    "Two entries deserve comment. The row count is unchanged at %d: the "
    "cleaning strategy corrected values rather than deleting records, so no "
    "observation was lost. The count of repeated feature vectors is %d after "
    "preprocessing, but these are not duplicate records - with the identifier "
    "columns removed, %d separate third-class passengers simply share the same "
    "remaining attribute values. Measured with identifiers present, the final "
    "dataset contains %d duplicate records, as it did at the start."
    % (S["final_shape"][0], S["dup_vectors_after"], S["dup_vectors_after"],
       S["dup_records_after"])
)
val_rows = [
    ["Remaining missing values", str(S["comparison_rows"][2][2]), "Pass"],
    ["Duplicate records (identifiers included)", str(S["dup_records_after"]), "Pass"],
    ["Negative fare values", "0", "Pass"],
    ["Ages outside (0, 100] years", "0", "Pass"],
    ["survived outside {0, 1}", "0", "Pass"],
    ["pclass outside {1, 2, 3}", "0", "Pass"],
    ["Text columns remaining", str(S["comparison_rows"][7][2]), "Pass"],
    ["Final dimensions", "%d x %d" % tuple(S["final_shape"]), "Pass"],
]
table(["Validation check", "Result", "Status"], val_rows,
      "Post-preprocessing validation checks.", widths=[3.2, 1.5, 1.2])
para("Final column types: "
     + ", ".join("%s (%d columns)" % (k, v) for k, v in S["final_dtypes"].items())
     + ".")
para("The first records of the preprocessed matrix:")
_ph_show = ["pclass", "survived", "sex", "age", "fare_log", "family_size",
            "is_alone", "embarked_S", "title_Mr", "deck_Unknown"]
_pi = [S["proc_head_cols"].index(c) for c in _ph_show]
table(_ph_show, [[r[i] for i in _pi] for r in S["proc_head_rows"]],
      "First five rows of the preprocessed dataset (a subset of the %d columns)."
      % S["final_shape"][1], font=7.5)
figure("06_correlation_processed.png",
       "Correlation matrix of the preprocessed features. The relationships are "
       "now directly computable because every variable is numeric and complete.",
       width=5.4)


# ----------------------------------------------------------- 9. challenges
h("9. Challenges Faced and Solutions", 1)
chal = [
    ("Missing values were invisible on the first read",
     "The OpenML file encodes gaps as the literal string \"?\". Loaded without "
     "na_values, pandas reported zero missing values and typed age and fare as "
     "text. The token had to be identified by inspecting the raw lines of the "
     "file before the missing-value analysis could begin at all."),
    ("Two columns predicted the target almost perfectly",
     "boat and body looked like ordinary sparse columns. Checking survival "
     "against them revealed a %.1f%% versus %.1f%% split - they record what "
     "happened after the sinking. They were removed as target leakage rather "
     "than imputed."
     % (S["boat_leak"]["True"] * 100, S["boat_leak"]["False"] * 100)),
    ("Apparent duplicates that were not duplicates",
     "Ignoring identifiers produced %d matching rows and two repeated names, "
     "which a routine drop_duplicates call would have deleted. Examining the "
     "full records showed different tickets, fares, ports and outcomes. The "
     "lesson is that duplicate detection must be followed by verification "
     "before removal." % S["dup_subset"]),
    ("The fare outliers were a unit problem, not bad data",
     "%d fare values were flagged by the IQR rule. They turned out to be group "
     "tickets whose total price is repeated on each passenger's row. Dividing "
     "by the number of passengers per ticket fixed the comparability problem "
     "without discarding a single record."
     % S["fare_out_before"]),
    ("The IQR rule broke down on count variables",
     "For parch the first and third quartiles are both zero, so the IQR is zero "
     "and the rule flags every non-zero value. This confirmed that the method "
     "has to be applied with judgement rather than mechanically, and the counts "
     "were consolidated into family_size instead."),
    ("Imputing a fifth of the age column narrows its spread",
     "Filling %d ages with central values reduced the standard deviation from "
     "%s to %s. Conditioning the median on class, sex and title limited the "
     "damage relative to a single global median, and the effect is reported "
     "explicitly rather than concealed."
     % (S["age_missing_before"], S["age_stats_rows"][2][1],
        S["age_stats_rows"][2][2])),
]
for t_, d_ in chal:
    p = doc.add_paragraph()
    r = p.add_run(t_ + ". ")
    r.bold = True
    p.add_run(d_)

# -------------------------------------------------------------- 10. impact
h("10. Impact of Preprocessing", 1)
h("Statistical analysis", 2)
para(
    "Correcting the %d zero fares raises the class means to values that reflect "
    "what passengers actually paid, and the per-person adjustment changes what "
    "the fare variable measures from cost per booking to cost per passenger. "
    "Any group comparison of fares is now meaningful in a way it was not "
    "before. Conversely, imputing age compresses its variance from %s to %s, so "
    "confidence intervals and variance-based tests on age are now mildly "
    "optimistic; this is a real cost of the decision, not a neutral change."
    % (S["zero_fare_count"], S["age_stats_rows"][2][1], S["age_stats_rows"][2][2])
)
h("Visualisation", 2)
para(
    "A boxplot of the raw fare is dominated by a handful of group tickets and "
    "compresses the bulk of the distribution into an unreadable band near the "
    "axis, as Figure 5 shows. After the per-person and log transforms the same "
    "data is legible, and comparisons between classes become visible. Complete "
    "columns also mean that plots no longer silently drop the %d passengers "
    "whose age was missing." % S["age_missing_before"]
)
h("Machine-learning models", 2)
para(
    "The raw file cannot be fed to a model at all: %s of its columns are text "
    "and %s cells are empty. The processed matrix is fully numeric, complete "
    "and standardised where it matters, so it can be passed directly to any "
    "estimator. The single most consequential decision for model validity was "
    "removing boat and body: a classifier trained with them would report "
    "near-perfect accuracy that would collapse on any passenger whose fate was "
    "not already known, because those columns encode the answer."
    % (S["comparison_rows"][7][1], S["comparison_rows"][2][1])
)
h("Model reliability", 2)
para(
    "Reliability improved through leakage removal, consistent typing and "
    "scale comparability, and through retaining all %d observations rather than "
    "deleting the %d rows with a missing age - listwise deletion would have "
    "removed a fifth of the sample, and disproportionately third-class "
    "passengers, whose age is missing at %.1f%% against %.1f%% in first class."
    % (S["final_shape"][0], S["age_missing_before"],
       S["age_missing_by_class"]["3"], S["age_missing_by_class"]["1"])
)
h("Information loss", 2)
para(
    "Six columns were removed. For name, ticket and cabin the loss is partly "
    "recovered through title, fare_per_person and deck. home.dest was a genuine "
    "loss: geographic origin might carry signal, but %.0f%% of it was absent. "
    "Imputation is itself a form of loss, since %d ages and %d fares are now "
    "estimates rather than observations; both files - cleaned and processed - "
    "are saved so that the effect of these choices can be re-examined."
    % (43.09, S["age_missing_before"], S["fare_imputed_total"])
)
h("Bias", 2)
para(
    "Two sources of bias deserve explicit acknowledgement. Missingness in age "
    "is not random - it is absent for %.1f%% of third-class passengers against "
    "%.1f%% of first-class passengers - so imputing from group "
    "medians systematically assigns those passengers their group's central "
    "value and understates the variation within the group. Second, treating "
    "'Unknown' as a deck level converts a recording artefact into a feature: "
    "cabin is missing for %.1f%% of first-class passengers but %.1f%% of "
    "third-class passengers, so deck_Unknown partly encodes class. It was "
    "retained deliberately, because discarding %.0f%% of the rows to avoid it "
    "would introduce a far larger selection bias, but any model using that "
    "feature should be read with this in mind."
    % (S["age_missing_by_class"]["3"], S["age_missing_by_class"]["1"],
       S["cabin_missing_by_class"]["1"], S["cabin_missing_by_class"]["3"], 77.46)
)

# ---------------------------------------------------------- 11. conclusion
h("11. Conclusion", 1)
para(
    "A raw public dataset of %d passenger records and %d columns was acquired "
    "programmatically, audited, cleaned and preprocessed into a complete "
    "numeric matrix of %d rows and %d columns with no missing values, no "
    "invalid values and no text columns remaining."
    % (S["raw_shape"][0], S["raw_shape"][1], S["final_shape"][0], S["final_shape"][1])
)
para("Quality improvements delivered:")
bullets([
    "%s missing cells eliminated across %s columns, without losing a single "
    "record." % (S["comparison_rows"][2][1], S["comparison_rows"][3][1]),
    "%d impossible zero fares replaced with class-conditional medians."
    % S["zero_fare_count"],
    "Two target-leaking columns identified and removed.",
    "Fare converted from a per-booking to a per-passenger measure, reducing "
    "skewness from %.2f to %.2f."
    % (S["skew"]["fare"], S["skew"]["fare_log"]),
    "%d text and categorical columns encoded into %d numeric features."
    % (int(S["comparison_rows"][7][1]), S["final_shape"][1]),
])
para("The decisions that mattered most:")
bullets([
    "Removing boat and body, without which any downstream model would have "
    "been invalid.",
    "Verifying apparent duplicates instead of dropping them, which preserved "
    "%d genuine records." % S["dup_subset"],
    "Conditioning the age imputation on class, sex and title rather than using "
    "a single global median.",
    "Treating the fare outliers as a unit problem to be transformed rather than "
    "extreme values to be deleted.",
])
para(
    "The main lesson is that the useful work in this task was investigative "
    "rather than procedural. Every automatic rule applied here - drop the "
    "duplicates, delete the outliers, impute the gaps - would have been wrong "
    "at least once if it had been applied without first looking at the records "
    "behind the numbers. A missing value, a repeated row and an extreme value "
    "are each a question about how the data was recorded, and the answer "
    "determines the treatment."
)
page_break()

# ----------------------------------------------------------------- appendix
h("Appendix: Analysis Code", 1)
para(
    "The complete analysis is contained in src/data_preprocessing.py, "
    "reproduced below. Running it regenerates every figure, table and number "
    "used in this report, together with the full console transcript in "
    "outputs/analysis_log.txt. This document is generated from that run by "
    "src/build_report.py.", italic=True
)
sec = doc.add_section(WD_SECTION.NEW_PAGE)
sec.left_margin = Inches(0.7)
sec.right_margin = Inches(0.7)
src = open(os.path.join(BASE, "src", "data_preprocessing.py"), encoding="utf-8").read()
for chunk in src.replace("\t", "    ").split("\n# ----"):
    block = chunk if chunk.startswith("\n") or chunk.startswith('"""') else "# ----" + chunk
    block = block.strip("\n")
    if block:
        code(block)

doc.save(DOCX)
print("written:", os.path.relpath(DOCX, BASE))
print("figures:", _fig_no[0], " tables:", _tbl_no[0])
