"""
Dataset Doctor - Complete XGBoost Pipeline

This single Python file performs:

1. Dataset loading
2. Basic validation
3. Data preprocessing
4. Exploratory Data Analysis
5. Train-test splitting
6. XGBoost regression training
7. Model evaluation
8. Feature-importance analysis
9. Prediction visualization
10. Model and preprocessing metadata saving

Target:
    health_score

Output files:
    outputs/eda/
    outputs/models/dataset_doctor_xgboost.pkl
    outputs/models/model_features.json
    outputs/results/model_metrics.json
    outputs/results/test_predictions.csv
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor


# ============================================================
# 1. CONFIGURATION
# ============================================================

RANDOM_STATE = 42
TEST_SIZE = 0.20

# Change this path when required.
DATASET_PATH = Path("dataset_25k_synthetic.csv")

OUTPUT_DIRECTORY = Path("outputs")
EDA_DIRECTORY = OUTPUT_DIRECTORY / "eda"
MODEL_DIRECTORY = OUTPUT_DIRECTORY / "models"
RESULTS_DIRECTORY = OUTPUT_DIRECTORY / "results"

MODEL_PATH = MODEL_DIRECTORY / "dataset_doctor_xgboost.pkl"
FEATURES_PATH = MODEL_DIRECTORY / "model_features.json"
METRICS_PATH = RESULTS_DIRECTORY / "model_metrics.json"
PREDICTIONS_PATH = RESULTS_DIRECTORY / "test_predictions.csv"

TARGET_COLUMN = "health_score"

NON_FEATURE_COLUMNS = [
    "dataset_id",
    "diagnosis",
    "recommendations",
]

CATEGORICAL_COLUMNS = [
    "task_type",
]


# ============================================================
# 2. CREATE OUTPUT DIRECTORIES
# ============================================================

def create_output_directories() -> None:
    """Create all required output directories."""

    for directory in [
        OUTPUT_DIRECTORY,
        EDA_DIRECTORY,
        MODEL_DIRECTORY,
        RESULTS_DIRECTORY,
    ]:
        directory.mkdir(parents=True, exist_ok=True)


# ============================================================
# 3. LOAD DATASET
# ============================================================

def load_dataset(file_path: Path) -> pd.DataFrame:
    """Load the synthetic Dataset Doctor CSV file."""

    if not file_path.exists():
        raise FileNotFoundError(
            f"\nDataset file was not found:\n{file_path.resolve()}\n\n"
            "Place dataset_doctor_synthetic_25000.csv in the same folder "
            "as this script or update DATASET_PATH."
        )

    print("\nLoading dataset...")

    dataframe = pd.read_csv(file_path)

    if dataframe.empty:
        raise ValueError("The dataset is empty.")

    print("Dataset loaded successfully.")
    print(f"Rows   : {dataframe.shape[0]:,}")
    print(f"Columns: {dataframe.shape[1]}")

    return dataframe


# ============================================================
# 4. VALIDATE DATASET
# ============================================================

def validate_dataset(dataframe: pd.DataFrame) -> None:
    """Check whether required columns are available."""

    required_columns = (
        [TARGET_COLUMN]
        + NON_FEATURE_COLUMNS
        + CATEGORICAL_COLUMNS
    )

    missing_columns = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            "The following required columns are missing:\n"
            f"{missing_columns}"
        )

    if dataframe[TARGET_COLUMN].isna().all():
        raise ValueError(
            f"The target column '{TARGET_COLUMN}' contains no usable values."
        )


# ============================================================
# 5. DATASET OVERVIEW
# ============================================================

def print_dataset_overview(dataframe: pd.DataFrame) -> None:
    """Print important dataset information."""

    print("\n" + "=" * 70)
    print("DATASET OVERVIEW")
    print("=" * 70)

    print("\nFirst five rows:")
    print(dataframe.head())

    print("\nDataset shape:")
    print(dataframe.shape)

    print("\nColumn data types:")
    print(dataframe.dtypes)

    print("\nMissing values:")
    missing_values = dataframe.isna().sum()
    print(missing_values[missing_values > 0])

    if missing_values.sum() == 0:
        print("No missing values found.")

    duplicate_count = int(dataframe.duplicated().sum())

    print("\nDuplicate rows:")
    print(duplicate_count)

    print("\nTarget summary:")
    print(dataframe[TARGET_COLUMN].describe().round(2))

    if "diagnosis" in dataframe.columns:
        print("\nDiagnosis distribution:")
        print(dataframe["diagnosis"].value_counts())

        print("\nDiagnosis percentages:")
        diagnosis_percentage = (
            dataframe["diagnosis"]
            .value_counts(normalize=True)
            .mul(100)
            .round(2)
        )
        print(diagnosis_percentage.astype(str) + "%")


# ============================================================
# 6. PREPROCESSING
# ============================================================

def preprocess_dataset(
    dataframe: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series]:
    """
    Prepare the dataset for XGBoost regression.

    Returns:
        X: Input features
        y: Health score target
    """

    print("\n" + "=" * 70)
    print("DATA PREPROCESSING")
    print("=" * 70)

    processed_dataframe = dataframe.copy()

    initial_rows = len(processed_dataframe)

    processed_dataframe = processed_dataframe.drop_duplicates().reset_index(
        drop=True
    )

    removed_duplicates = initial_rows - len(processed_dataframe)

    print(f"Duplicate rows removed: {removed_duplicates}")

    # Convert target to numeric.
    processed_dataframe[TARGET_COLUMN] = pd.to_numeric(
        processed_dataframe[TARGET_COLUMN],
        errors="coerce",
    )

    target_missing_count = int(
        processed_dataframe[TARGET_COLUMN].isna().sum()
    )

    if target_missing_count > 0:
        print(
            f"Rows removed because target was missing: "
            f"{target_missing_count}"
        )

        processed_dataframe = processed_dataframe.dropna(
            subset=[TARGET_COLUMN]
        )

    # Separate target before dropping columns.
    y = processed_dataframe[TARGET_COLUMN].copy()

    columns_to_drop = NON_FEATURE_COLUMNS + [TARGET_COLUMN]

    X = processed_dataframe.drop(
        columns=columns_to_drop,
        errors="ignore",
    )

    # Identify categorical columns that actually exist.
    available_categorical_columns = [
        column
        for column in CATEGORICAL_COLUMNS
        if column in X.columns
    ]

    # One-hot encode categorical columns.
    X = pd.get_dummies(
        X,
        columns=available_categorical_columns,
        drop_first=False,
        dtype=int,
    )

    # Convert remaining columns to numeric.
    for column in X.columns:
        X[column] = pd.to_numeric(
            X[column],
            errors="coerce",
        )

    # Fill missing numeric values using medians.
    numeric_medians = X.median(numeric_only=True)

    X = X.fillna(numeric_medians)

    # If any column is still missing, fill with zero.
    X = X.fillna(0)

    # Replace infinite values.
    X = X.replace([np.inf, -np.inf], np.nan)
    X = X.fillna(X.median(numeric_only=True))
    X = X.fillna(0)

    # Ensure all features are numeric.
    non_numeric_columns = X.select_dtypes(
        exclude=[np.number, "bool"]
    ).columns.tolist()

    if non_numeric_columns:
        raise ValueError(
            "Non-numeric columns remain after preprocessing:\n"
            f"{non_numeric_columns}"
        )

    print(f"Final rows       : {len(X):,}")
    print(f"Final features   : {X.shape[1]}")
    print(f"Missing cells    : {int(X.isna().sum().sum())}")
    print(f"Infinite values  : {int(np.isinf(X.to_numpy()).sum())}")

    print("\nFinal feature columns:")

    for index, column in enumerate(X.columns, start=1):
        print(f"{index:02d}. {column}")

    return X, y


# ============================================================
# 7. EXPLORATORY DATA ANALYSIS
# ============================================================

def create_health_score_distribution(
    dataframe: pd.DataFrame,
) -> None:
    """Create health-score histogram."""

    plt.figure(figsize=(10, 6))

    plt.hist(
        dataframe[TARGET_COLUMN].dropna(),
        bins=30,
        edgecolor="black",
    )

    plt.title("Distribution of Dataset Health Scores")
    plt.xlabel("Health Score")
    plt.ylabel("Number of Records")
    plt.tight_layout()

    output_path = EDA_DIRECTORY / "health_score_distribution.png"

    plt.savefig(output_path, dpi=300)
    plt.close()

    print(f"Saved: {output_path}")


def create_diagnosis_distribution(
    dataframe: pd.DataFrame,
) -> None:
    """Create diagnosis class distribution chart."""

    if "diagnosis" not in dataframe.columns:
        return

    diagnosis_counts = dataframe["diagnosis"].value_counts()

    plt.figure(figsize=(10, 6))

    plt.bar(
        diagnosis_counts.index,
        diagnosis_counts.values,
        edgecolor="black",
    )

    plt.title("Diagnosis Class Distribution")
    plt.xlabel("Diagnosis")
    plt.ylabel("Number of Records")
    plt.xticks(rotation=20)
    plt.tight_layout()

    output_path = EDA_DIRECTORY / "diagnosis_distribution.png"

    plt.savefig(output_path, dpi=300)
    plt.close()

    print(f"Saved: {output_path}")


def create_correlation_chart(
    dataframe: pd.DataFrame,
) -> None:
    """
    Create a bar chart showing numerical feature correlations
    with the health-score target.
    """

    numeric_dataframe = dataframe.select_dtypes(include=np.number)

    if TARGET_COLUMN not in numeric_dataframe.columns:
        return

    correlations = (
        numeric_dataframe
        .corr()[TARGET_COLUMN]
        .drop(TARGET_COLUMN)
        .dropna()
        .sort_values()
    )

    plt.figure(figsize=(12, 9))

    plt.barh(
        correlations.index,
        correlations.values,
        edgecolor="black",
    )

    plt.title("Feature Correlation with Health Score")
    plt.xlabel("Correlation Coefficient")
    plt.ylabel("Feature")
    plt.tight_layout()

    output_path = EDA_DIRECTORY / "health_score_correlations.png"

    plt.savefig(output_path, dpi=300)
    plt.close()

    print(f"Saved: {output_path}")


def create_selected_scatter_plots(
    dataframe: pd.DataFrame,
) -> None:
    """Create scatter plots for important quality features."""

    selected_features = [
        "missing_percentage",
        "duplicate_percentage",
        "outlier_percentage",
        "class_imbalance_ratio",
        "train_test_overlap_percentage",
    ]

    for feature in selected_features:
        if feature not in dataframe.columns:
            continue

        plt.figure(figsize=(9, 6))

        plt.scatter(
            dataframe[feature],
            dataframe[TARGET_COLUMN],
            alpha=0.35,
        )

        readable_name = feature.replace("_", " ").title()

        plt.title(f"{readable_name} vs Health Score")
        plt.xlabel(readable_name)
        plt.ylabel("Health Score")
        plt.tight_layout()

        output_path = EDA_DIRECTORY / f"{feature}_vs_health_score.png"

        plt.savefig(output_path, dpi=300)
        plt.close()

        print(f"Saved: {output_path}")


def perform_eda(dataframe: pd.DataFrame) -> None:
    """Run exploratory data analysis and save plots."""

    print("\n" + "=" * 70)
    print("EXPLORATORY DATA ANALYSIS")
    print("=" * 70)

    create_health_score_distribution(dataframe)
    create_diagnosis_distribution(dataframe)
    create_correlation_chart(dataframe)
    create_selected_scatter_plots(dataframe)


# ============================================================
# 8. TRAIN-TEST SPLIT
# ============================================================

def split_dataset(
    X: pd.DataFrame,
    y: pd.Series,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.Series,
    pd.Series,
]:
    """Split the data into training and testing sets."""

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
    )

    print("\n" + "=" * 70)
    print("TRAIN-TEST SPLIT")
    print("=" * 70)

    print(f"Training samples: {len(X_train):,}")
    print(f"Testing samples : {len(X_test):,}")
    print(f"Training ratio  : {(1 - TEST_SIZE) * 100:.0f}%")
    print(f"Testing ratio   : {TEST_SIZE * 100:.0f}%")

    return X_train, X_test, y_train, y_test


# ============================================================
# 9. XGBOOST TRAINING
# ============================================================

def train_xgboost_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
) -> XGBRegressor:
    """Train the XGBoost regression model."""

    print("\n" + "=" * 70)
    print("XGBOOST MODEL TRAINING")
    print("=" * 70)

    model = XGBRegressor(
        objective="reg:squarederror",
        n_estimators=500,
        max_depth=6,
        learning_rate=0.05,
        min_child_weight=2,
        subsample=0.85,
        colsample_bytree=0.85,
        reg_alpha=0.1,
        reg_lambda=1.0,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        eval_metric="rmse",
    )

    model.fit(
        X_train,
        y_train,
        verbose=False,
    )

    print("XGBoost training completed successfully.")

    return model


# ============================================================
# 10. MODEL EVALUATION
# ============================================================

def evaluate_model(
    model: XGBRegressor,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> tuple[dict[str, float], np.ndarray]:
    """Evaluate the trained regression model."""

    print("\n" + "=" * 70)
    print("MODEL EVALUATION")
    print("=" * 70)

    predictions = model.predict(X_test)

    # Health scores should remain between 0 and 100.
    predictions = np.clip(predictions, 0, 100)

    mae = mean_absolute_error(y_test, predictions)
    mse = mean_squared_error(y_test, predictions)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, predictions)

    metrics = {
        "mean_absolute_error": round(float(mae), 4),
        "mean_squared_error": round(float(mse), 4),
        "root_mean_squared_error": round(float(rmse), 4),
        "r2_score": round(float(r2), 6),
        "training_samples": int(len(model.get_booster().get_dump())),
        "testing_records": int(len(y_test)),
    }

    print(f"MAE  : {mae:.4f}")
    print(f"MSE  : {mse:.4f}")
    print(f"RMSE : {rmse:.4f}")
    print(f"R²   : {r2:.6f}")

    print("\nInterpretation:")

    print(
        f"The model is wrong by approximately {mae:.2f} "
        "health-score points on average."
    )

    print(
        f"The model explains approximately {max(r2, 0) * 100:.2f}% "
        "of the variation in health scores."
    )

    return metrics, predictions


# ============================================================
# 11. PREDICTION DIAGNOSIS
# ============================================================

def score_to_diagnosis(score: float) -> str:
    """Convert predicted health score into a diagnosis."""

    if score >= 85:
        return "Healthy"

    if score >= 70:
        return "Minor Issues"

    if score >= 45:
        return "Moderate Issues"

    return "Critical"


# ============================================================
# 12. SAVE TEST PREDICTIONS
# ============================================================

def save_test_predictions(
    y_test: pd.Series,
    predictions: np.ndarray,
) -> None:
    """Save actual and predicted values for test records."""

    prediction_dataframe = pd.DataFrame(
        {
            "actual_health_score": y_test.to_numpy(),
            "predicted_health_score": np.round(predictions, 2),
        }
    )

    prediction_dataframe["absolute_error"] = np.round(
        np.abs(
            prediction_dataframe["actual_health_score"]
            - prediction_dataframe["predicted_health_score"]
        ),
        2,
    )

    prediction_dataframe["actual_diagnosis"] = (
        prediction_dataframe["actual_health_score"]
        .apply(score_to_diagnosis)
    )

    prediction_dataframe["predicted_diagnosis"] = (
        prediction_dataframe["predicted_health_score"]
        .apply(score_to_diagnosis)
    )

    prediction_dataframe.to_csv(
        PREDICTIONS_PATH,
        index=False,
    )

    print(f"\nTest predictions saved: {PREDICTIONS_PATH}")


# ============================================================
# 13. ACTUAL VS PREDICTED PLOT
# ============================================================

def create_actual_vs_predicted_plot(
    y_test: pd.Series,
    predictions: np.ndarray,
) -> None:
    """Create an actual-versus-predicted health score plot."""

    plt.figure(figsize=(9, 7))

    plt.scatter(
        y_test,
        predictions,
        alpha=0.4,
    )

    minimum_value = min(
        float(y_test.min()),
        float(predictions.min()),
    )

    maximum_value = max(
        float(y_test.max()),
        float(predictions.max()),
    )

    plt.plot(
        [minimum_value, maximum_value],
        [minimum_value, maximum_value],
        linestyle="--",
    )

    plt.title("Actual vs Predicted Health Scores")
    plt.xlabel("Actual Health Score")
    plt.ylabel("Predicted Health Score")
    plt.tight_layout()

    output_path = RESULTS_DIRECTORY / "actual_vs_predicted.png"

    plt.savefig(output_path, dpi=300)
    plt.close()

    print(f"Saved: {output_path}")


# ============================================================
# 14. RESIDUAL PLOT
# ============================================================

def create_residual_plot(
    predictions: np.ndarray,
    y_test: pd.Series,
) -> None:
    """Create a residual error plot."""

    residuals = y_test.to_numpy() - predictions

    plt.figure(figsize=(9, 6))

    plt.scatter(
        predictions,
        residuals,
        alpha=0.4,
    )

    plt.axhline(
        y=0,
        linestyle="--",
    )

    plt.title("Residual Error Plot")
    plt.xlabel("Predicted Health Score")
    plt.ylabel("Residual: Actual - Predicted")
    plt.tight_layout()

    output_path = RESULTS_DIRECTORY / "residual_plot.png"

    plt.savefig(output_path, dpi=300)
    plt.close()

    print(f"Saved: {output_path}")


# ============================================================
# 15. FEATURE IMPORTANCE
# ============================================================

def create_feature_importance_plot(
    model: XGBRegressor,
    feature_names: list[str],
) -> None:
    """Create and save the XGBoost feature-importance chart."""

    feature_importance_dataframe = pd.DataFrame(
        {
            "feature": feature_names,
            "importance": model.feature_importances_,
        }
    )

    feature_importance_dataframe = (
        feature_importance_dataframe
        .sort_values(
            by="importance",
            ascending=False,
        )
        .reset_index(drop=True)
    )

    feature_importance_dataframe.to_csv(
        RESULTS_DIRECTORY / "feature_importance.csv",
        index=False,
    )

    top_features = feature_importance_dataframe.head(20).sort_values(
        by="importance",
        ascending=True,
    )

    plt.figure(figsize=(11, 8))

    plt.barh(
        top_features["feature"],
        top_features["importance"],
        edgecolor="black",
    )

    plt.title("Top 20 XGBoost Feature Importances")
    plt.xlabel("Importance")
    plt.ylabel("Feature")
    plt.tight_layout()

    output_path = RESULTS_DIRECTORY / "feature_importance.png"

    plt.savefig(output_path, dpi=300)
    plt.close()

    print(f"Saved: {output_path}")

    print("\nTop 10 important features:")

    print(
        feature_importance_dataframe
        .head(10)
        .to_string(index=False)
    )


# ============================================================
# 16. SAVE MODEL AND METADATA
# ============================================================

def save_model_and_metadata(
    model: XGBRegressor,
    feature_names: list[str],
    metrics: dict[str, float],
) -> None:
    """Save trained model, feature names, and metrics."""

    joblib.dump(model, MODEL_PATH)

    with FEATURES_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            {
                "target_column": TARGET_COLUMN,
                "feature_count": len(feature_names),
                "feature_names": feature_names,
                "categorical_columns": CATEGORICAL_COLUMNS,
                "non_feature_columns": NON_FEATURE_COLUMNS,
            },
            file,
            indent=4,
        )

    with METRICS_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metrics,
            file,
            indent=4,
        )

    print("\n" + "=" * 70)
    print("SAVED FILES")
    print("=" * 70)

    print(f"Model          : {MODEL_PATH}")
    print(f"Feature schema : {FEATURES_PATH}")
    print(f"Metrics        : {METRICS_PATH}")


# ============================================================
# 17. SAMPLE PREDICTIONS
# ============================================================

def print_sample_predictions(
    y_test: pd.Series,
    predictions: np.ndarray,
    sample_count: int = 10,
) -> None:
    """Display sample actual and predicted scores."""

    sample_count = min(sample_count, len(y_test))

    sample_dataframe = pd.DataFrame(
        {
            "Actual Score": y_test.iloc[:sample_count].to_numpy(),
            "Predicted Score": np.round(
                predictions[:sample_count],
                2,
            ),
        }
    )

    sample_dataframe["Absolute Error"] = np.round(
        np.abs(
            sample_dataframe["Actual Score"]
            - sample_dataframe["Predicted Score"]
        ),
        2,
    )

    sample_dataframe["Predicted Diagnosis"] = (
        sample_dataframe["Predicted Score"]
        .apply(score_to_diagnosis)
    )

    print("\n" + "=" * 70)
    print("SAMPLE PREDICTIONS")
    print("=" * 70)

    print(sample_dataframe.to_string(index=False))


# ============================================================
# 18. MAIN PIPELINE
# ============================================================

def main() -> None:
    """Run the complete Dataset Doctor training pipeline."""

    print("=" * 70)
    print("DATASET DOCTOR - XGBOOST REGRESSION PIPELINE")
    print("=" * 70)

    create_output_directories()

    dataframe = load_dataset(DATASET_PATH)

    validate_dataset(dataframe)

    print_dataset_overview(dataframe)

    perform_eda(dataframe)

    X, y = preprocess_dataset(dataframe)

    X_train, X_test, y_train, y_test = split_dataset(X, y)

    model = train_xgboost_model(
        X_train,
        y_train,
    )

    metrics, predictions = evaluate_model(
        model,
        X_test,
        y_test,
    )

    save_test_predictions(
        y_test,
        predictions,
    )

    create_actual_vs_predicted_plot(
        y_test,
        predictions,
    )

    create_residual_plot(
        predictions,
        y_test,
    )

    create_feature_importance_plot(
        model,
        X.columns.tolist(),
    )

    save_model_and_metadata(
        model,
        X.columns.tolist(),
        metrics,
    )

    print_sample_predictions(
        y_test,
        predictions,
    )

    print("\n" + "=" * 70)
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 70)

    print(
        "\nYour trained XGBoost model is ready for integration "
        "with the Dataset Doctor backend."
    )


# ============================================================
# 19. PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":
    try:
        main()

    except FileNotFoundError as error:
        print(error)
        sys.exit(1)

    except ValueError as error:
        print(f"\nDataset validation error:\n{error}")
        sys.exit(1)

    except ImportError as error:
        print(
            "\nA required library is missing.\n"
            "Install the dependencies using:\n\n"
            "pip install pandas numpy matplotlib "
            "scikit-learn xgboost joblib\n"
        )
        print(f"Original error: {error}")
        sys.exit(1)

    except Exception as error:
        print("\nThe pipeline failed because of an unexpected error.")
        print(f"Error type   : {type(error).__name__}")
        print(f"Error message: {error}")
        raise