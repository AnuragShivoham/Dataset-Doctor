"""
Dataset Doctor Synthetic Meta-Dataset Generator

Generates synthetic dataset-quality records for training:

1. Health-score regression models
2. Dataset-diagnosis classification models
3. Recommendation-generation systems

Output:
    dataset_doctor_synthetic_25000.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd


# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

RANDOM_SEED = 42
NUMBER_OF_SAMPLES = 25_000
OUTPUT_FILE = Path("dataset_25k_synthetic.csv")

rng = np.random.default_rng(RANDOM_SEED)


# -------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------

def clipped_normal(
    mean: float,
    std: float,
    minimum: float,
    maximum: float,
    size: int
) -> np.ndarray:
    """Generate normally distributed values clipped to a valid range."""
    values = rng.normal(mean, std, size)
    return np.clip(values, minimum, maximum)


def generate_issue_severity(size: int) -> np.ndarray:
    """
    Generate a latent issue-severity value.

    Lower values represent healthier datasets.
    Higher values represent lower-quality datasets.
    """
    quality_groups = rng.choice(
        ["healthy", "minor", "moderate", "critical"],
        size=size,
        p=[0.25, 0.30, 0.30, 0.15]
    )

    severity = np.zeros(size)

    group_parameters = {
        "healthy": (0.08, 0.05),
        "minor": (0.25, 0.08),
        "moderate": (0.50, 0.10),
        "critical": (0.78, 0.12)
    }

    for group, (mean, std) in group_parameters.items():
        mask = quality_groups == group
        severity[mask] = rng.normal(mean, std, mask.sum())

    return np.clip(severity, 0, 1)


def assign_diagnosis(health_score: float) -> str:
    """Convert health score into a diagnosis class."""
    if health_score >= 85:
        return "Healthy"
    if health_score >= 70:
        return "Minor Issues"
    if health_score >= 45:
        return "Moderate Issues"
    return "Critical"


def generate_recommendations(row: pd.Series) -> str:
    """Generate preprocessing recommendations based on quality metrics."""
    recommendations = []

    if row["missing_percentage"] >= 20:
        recommendations.append("Investigate and impute or remove heavily missing data")
    elif row["missing_percentage"] >= 5:
        recommendations.append("Impute missing values")

    if row["duplicate_percentage"] >= 3:
        recommendations.append("Remove duplicate records")

    if row["outlier_percentage"] >= 10:
        recommendations.append("Investigate and treat severe outliers")
    elif row["outlier_percentage"] >= 3:
        recommendations.append("Review numerical outliers")

    if row["class_imbalance_ratio"] >= 10:
        recommendations.append("Apply class weighting or resampling")
    elif row["class_imbalance_ratio"] >= 3:
        recommendations.append("Review class imbalance")

    if row["datatype_errors"] > 0:
        recommendations.append("Correct invalid data types")

    if row["constant_columns"] > 0:
        recommendations.append("Remove constant columns")

    if row["highly_correlated_features"] > 0:
        recommendations.append("Review highly correlated features")

    if row["leakage_detected"] == 1:
        recommendations.append("Remove features causing target leakage")

    if row["high_missing_columns"] > 0:
        recommendations.append("Remove or investigate columns with excessive missing values")

    if row["average_absolute_skewness"] >= 2:
        recommendations.append("Transform highly skewed numerical features")

    if row["infinite_value_percentage"] > 0:
        recommendations.append("Replace infinite values")

    if row["invalid_category_percentage"] > 0:
        recommendations.append("Clean inconsistent categorical values")

    if row["target_missing_percentage"] > 0:
        recommendations.append("Remove or recover records with missing target values")

    if not recommendations:
        recommendations.append("Dataset is ready for model development")

    return "; ".join(recommendations)


# -------------------------------------------------------------------
# Generate latent quality severity
# -------------------------------------------------------------------

severity = generate_issue_severity(NUMBER_OF_SAMPLES)


# -------------------------------------------------------------------
# Generate dataset structure features
# -------------------------------------------------------------------

num_rows = np.round(
    np.exp(rng.uniform(np.log(100), np.log(1_000_000), NUMBER_OF_SAMPLES))
).astype(int)

num_columns = np.round(
    np.exp(rng.uniform(np.log(3), np.log(500), NUMBER_OF_SAMPLES))
).astype(int)

categorical_ratio = rng.beta(2, 3, NUMBER_OF_SAMPLES)

categorical_columns = np.round(num_columns * categorical_ratio).astype(int)
categorical_columns = np.minimum(categorical_columns, num_columns)

numerical_columns = num_columns - categorical_columns

memory_usage_mb = (
    num_rows
    * num_columns
    * rng.uniform(4, 16, NUMBER_OF_SAMPLES)
    / (1024 ** 2)
)

memory_usage_mb = np.round(memory_usage_mb, 3)


# -------------------------------------------------------------------
# Generate quality-related features
# -------------------------------------------------------------------

missing_percentage = np.clip(
    severity * rng.uniform(20, 65, NUMBER_OF_SAMPLES)
    + rng.normal(0, 2.5, NUMBER_OF_SAMPLES),
    0,
    95
)

duplicate_percentage = np.clip(
    severity * rng.uniform(5, 35, NUMBER_OF_SAMPLES)
    + rng.normal(0, 1.5, NUMBER_OF_SAMPLES),
    0,
    80
)

outlier_percentage = np.clip(
    severity * rng.uniform(5, 40, NUMBER_OF_SAMPLES)
    + rng.normal(0, 2, NUMBER_OF_SAMPLES),
    0,
    75
)

infinite_value_percentage = np.clip(
    severity * rng.uniform(0, 4, NUMBER_OF_SAMPLES)
    + rng.normal(0, 0.15, NUMBER_OF_SAMPLES),
    0,
    15
)

invalid_category_percentage = np.clip(
    severity * rng.uniform(0, 10, NUMBER_OF_SAMPLES)
    + rng.normal(0, 0.5, NUMBER_OF_SAMPLES),
    0,
    40
)

target_missing_percentage = np.clip(
    severity * rng.uniform(0, 8, NUMBER_OF_SAMPLES)
    + rng.normal(0, 0.3, NUMBER_OF_SAMPLES),
    0,
    30
)

class_imbalance_ratio = np.clip(
    1
    + severity * rng.uniform(1, 35, NUMBER_OF_SAMPLES)
    + rng.lognormal(0, 0.25, NUMBER_OF_SAMPLES),
    1,
    100
)

average_absolute_skewness = np.clip(
    severity * rng.uniform(0.5, 5, NUMBER_OF_SAMPLES)
    + rng.normal(0.2, 0.25, NUMBER_OF_SAMPLES),
    0,
    15
)

datatype_errors = rng.poisson(
    severity * np.maximum(num_columns * 0.08, 1)
)

constant_columns = rng.poisson(
    severity * np.maximum(num_columns * 0.025, 0.2)
)

highly_correlated_features = rng.poisson(
    severity * np.maximum(numerical_columns * 0.08, 0.2)
)

high_missing_columns = rng.poisson(
    severity * np.maximum(num_columns * 0.04, 0.2)
)

unique_identifier_columns = rng.poisson(
    np.maximum(num_columns * rng.uniform(0.001, 0.01, NUMBER_OF_SAMPLES), 0.05)
)

datatype_errors = np.minimum(datatype_errors, num_columns)
constant_columns = np.minimum(constant_columns, num_columns)
highly_correlated_features = np.minimum(
    highly_correlated_features,
    numerical_columns
)
high_missing_columns = np.minimum(high_missing_columns, num_columns)
unique_identifier_columns = np.minimum(
    unique_identifier_columns,
    num_columns
)


# -------------------------------------------------------------------
# Binary quality indicators
# -------------------------------------------------------------------

leakage_probability = np.clip(
    0.01 + severity * 0.35,
    0,
    0.75
)

leakage_detected = rng.binomial(1, leakage_probability)

schema_mismatch_probability = np.clip(
    0.02 + severity * 0.45,
    0,
    0.80
)

schema_mismatch_detected = rng.binomial(
    1,
    schema_mismatch_probability
)

encoding_issue_probability = np.clip(
    0.01 + severity * 0.25,
    0,
    0.60
)

encoding_issue_detected = rng.binomial(
    1,
    encoding_issue_probability
)


# -------------------------------------------------------------------
# Additional dataset characteristics
# -------------------------------------------------------------------

task_type = rng.choice(
    ["Classification", "Regression"],
    size=NUMBER_OF_SAMPLES,
    p=[0.65, 0.35]
)

number_of_classes = np.where(
    task_type == "Classification",
    rng.integers(2, 21, NUMBER_OF_SAMPLES),
    0
)

train_test_overlap_percentage = np.clip(
    leakage_detected
    * rng.uniform(0.5, 25, NUMBER_OF_SAMPLES)
    + rng.normal(0, 0.2, NUMBER_OF_SAMPLES),
    0,
    50
)

feature_name_quality_score = np.clip(
    100
    - severity * rng.uniform(10, 65, NUMBER_OF_SAMPLES)
    + rng.normal(0, 4, NUMBER_OF_SAMPLES),
    0,
    100
)


# -------------------------------------------------------------------
# Calculate health score
# -------------------------------------------------------------------

health_score = (
    100
    - missing_percentage * 0.28
    - duplicate_percentage * 0.18
    - outlier_percentage * 0.12
    - infinite_value_percentage * 0.90
    - invalid_category_percentage * 0.35
    - target_missing_percentage * 0.80
    - np.minimum(class_imbalance_ratio - 1, 30) * 0.20
    - datatype_errors * 0.55
    - constant_columns * 0.45
    - highly_correlated_features * 0.20
    - high_missing_columns * 1.25
    - leakage_detected * 18
    - schema_mismatch_detected * 7
    - encoding_issue_detected * 4
    - train_test_overlap_percentage * 0.35
    - average_absolute_skewness * 0.65
)

# Add small uncertainty so the target is not completely deterministic.
health_score += rng.normal(0, 2.5, NUMBER_OF_SAMPLES)

health_score = np.clip(health_score, 0, 100)
health_score = np.round(health_score, 2)

diagnosis = np.array(
    [assign_diagnosis(score) for score in health_score]
)


# -------------------------------------------------------------------
# Build DataFrame
# -------------------------------------------------------------------

dataset = pd.DataFrame({
    "dataset_id": [
        f"DD_{index:05d}"
        for index in range(1, NUMBER_OF_SAMPLES + 1)
    ],
    "task_type": task_type,
    "num_rows": num_rows,
    "num_columns": num_columns,
    "numerical_columns": numerical_columns,
    "categorical_columns": categorical_columns,
    "number_of_classes": number_of_classes,
    "memory_usage_mb": memory_usage_mb,
    "missing_percentage": np.round(missing_percentage, 2),
    "duplicate_percentage": np.round(duplicate_percentage, 2),
    "outlier_percentage": np.round(outlier_percentage, 2),
    "infinite_value_percentage": np.round(
        infinite_value_percentage,
        2
    ),
    "invalid_category_percentage": np.round(
        invalid_category_percentage,
        2
    ),
    "target_missing_percentage": np.round(
        target_missing_percentage,
        2
    ),
    "class_imbalance_ratio": np.round(
        class_imbalance_ratio,
        2
    ),
    "average_absolute_skewness": np.round(
        average_absolute_skewness,
        2
    ),
    "datatype_errors": datatype_errors,
    "constant_columns": constant_columns,
    "highly_correlated_features": highly_correlated_features,
    "high_missing_columns": high_missing_columns,
    "unique_identifier_columns": unique_identifier_columns,
    "leakage_detected": leakage_detected,
    "schema_mismatch_detected": schema_mismatch_detected,
    "encoding_issue_detected": encoding_issue_detected,
    "train_test_overlap_percentage": np.round(
        train_test_overlap_percentage,
        2
    ),
    "feature_name_quality_score": np.round(
        feature_name_quality_score,
        2
    ),
    "health_score": health_score,
    "diagnosis": diagnosis
})


# -------------------------------------------------------------------
# Generate textual recommendations
# -------------------------------------------------------------------

dataset["recommendations"] = dataset.apply(
    generate_recommendations,
    axis=1
)


# -------------------------------------------------------------------
# Shuffle and save
# -------------------------------------------------------------------

dataset = dataset.sample(
    frac=1,
    random_state=RANDOM_SEED
).reset_index(drop=True)

dataset.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8"
)


# -------------------------------------------------------------------
# Validation and summary
# -------------------------------------------------------------------

print("=" * 65)
print("Dataset Doctor synthetic dataset generated successfully")
print("=" * 65)
print(f"Output file        : {OUTPUT_FILE.resolve()}")
print(f"Number of records  : {len(dataset):,}")
print(f"Number of columns  : {len(dataset.columns)}")
print(f"Missing cells      : {dataset.isna().sum().sum():,}")

print("\nDiagnosis distribution:")
print(dataset["diagnosis"].value_counts())

print("\nDiagnosis percentage:")
print(
    dataset["diagnosis"]
    .value_counts(normalize=True)
    .mul(100)
    .round(2)
    .astype(str)
    + "%"
)

print("\nHealth-score summary:")
print(dataset["health_score"].describe().round(2))

print("\nFirst five records:")
print(dataset.head())