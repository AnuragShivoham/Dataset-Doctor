from __future__ import annotations

import math
import uuid
from typing import Any

import numpy as np
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Dataset Doctor API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ANALYSES: dict[str, dict[str, Any]] = {}


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _load_dataframe(file: UploadFile) -> pd.DataFrame:
    contents = file.file.read()
    file.file.seek(0)

    if file.filename is None:
        raise HTTPException(status_code=400, detail="A filename is required.")

    suffix = file.filename.lower()

    if suffix.endswith('.csv'):
        dataframe = pd.read_csv(pd.io.common.BytesIO(contents))
    elif suffix.endswith(('.xlsx', '.xls')):
        dataframe = pd.read_excel(pd.io.common.BytesIO(contents))
    else:
        raise HTTPException(status_code=400, detail='Unsupported file type. Please upload CSV or Excel.')

    if dataframe.empty:
        raise HTTPException(status_code=400, detail='The uploaded file is empty.')

    return dataframe


def _calculate_outlier_count(series: pd.Series) -> int:
    if series.dtype == 'object' or series.dropna().empty:
        return 0

    numeric_series = pd.to_numeric(series, errors='coerce').dropna()
    if numeric_series.empty or len(numeric_series) < 3:
        return 0

    mean_value = numeric_series.mean()
    std_value = numeric_series.std()
    if math.isnan(std_value) or std_value == 0:
        return 0

    z_scores = np.abs((numeric_series - mean_value) / std_value)
    return int((z_scores > 3).sum())


def _calculate_leakage_risk(dataframe: pd.DataFrame, target_column: str | None) -> float:
    if target_column is None:
        return 0.0
    if target_column not in dataframe.columns:
        return 0.0

    target_series = dataframe[target_column].dropna()
    if target_series.empty:
        return 0.0

    for column in dataframe.columns:
        if column == target_column:
            continue
        if any(token in column.lower() for token in ['target', 'label', 'diagnosis', 'score']):
            try:
                correlation = pd.Series(pd.to_numeric(dataframe[column], errors='coerce').dropna()).corr(target_series)
            except Exception:
                correlation = 0.0
            if pd.notna(correlation):
                return max(0.0, abs(float(correlation)))
    return 0.0


def analyze_dataset(dataframe: pd.DataFrame, filename: str, target_column: str | None) -> dict[str, Any]:
    missing_percent = float(dataframe.isna().mean().mean() * 100)
    duplicate_percent = float(dataframe.duplicated().mean() * 100)
    target_present = target_column is not None and target_column in dataframe.columns

    numeric_columns = dataframe.select_dtypes(include=[np.number]).columns.tolist()
    outlier_total = sum(_calculate_outlier_count(dataframe[column]) for column in numeric_columns)
    outlier_percent = (outlier_total / max(1, len(dataframe.columns))) * 100

    imbalance_penalty = 0.0
    if target_present:
        target_counts = dataframe[target_column].dropna().value_counts()
        if not target_counts.empty:
            imbalance_penalty = 1.0 - (target_counts.max() / target_counts.sum())

    completeness_score = max(0.0, 100.0 - missing_percent * 1.2)
    consistency_score = max(0.0, 100.0 - duplicate_percent * 1.1 - outlier_percent * 0.5)
    distribution_score = max(0.0, 100.0 - imbalance_penalty * 100.0)
    leakage_risk = _calculate_leakage_risk(dataframe, target_column)
    leakage_score = max(0.0, 100.0 - leakage_risk * 100.0)

    health_score = round((completeness_score * 0.3 + consistency_score * 0.25 + distribution_score * 0.2 + leakage_score * 0.25), 1)

    if health_score >= 80:
        score_label = 'Ready for training'
    elif health_score >= 65:
        score_label = 'Needs review'
    else:
        score_label = 'High-risk dataset'

    columns = []
    for column_name in dataframe.columns:
        column_series = dataframe[column_name]
        missing_percent_value = round(float(column_series.isna().mean() * 100), 1)
        unique_count = int(column_series.nunique(dropna=True))
        numeric_series = pd.to_numeric(column_series, errors='coerce')
        outlier_count = int(_calculate_outlier_count(column_series))
        imbalance_metric = 0.0
        if target_present and target_column in dataframe.columns:
            counts = dataframe.groupby(target_column)[column_name].count()
            if not counts.empty:
                imbalance_metric = round(1.0 - (counts.max() / counts.sum()), 2)
        columns.append(
            {
                'name': column_name,
                'inferredType': 'Numeric' if pd.api.types.is_numeric_dtype(column_series) else 'Categorical',
                'missingPercent': missing_percent_value,
                'uniqueCount': unique_count,
                'outlierCount': outlier_count,
                'imbalanceMetric': imbalance_metric,
                'leakageRisk': round(leakage_risk, 2),
                'severity': 'Critical' if missing_percent_value > 10 or outlier_count > 0 or leakage_risk > 0.7 else 'Warning' if missing_percent_value > 5 or imbalance_metric > 0.4 else 'Moderate' if missing_percent_value > 0 else 'Healthy',
            }
        )

    issues = []
    if missing_percent > 5:
        issues.append({
            'id': 'issue-missing',
            'type': 'missing-values',
            'severity': 'Moderate',
            'title': 'Missing values detected',
            'summary': 'Some cells are blank and may affect downstream training.',
            'affectedRows': int(len(dataframe) * (missing_percent / 100)),
            'affectedColumns': [column['name'] for column in columns if column['missingPercent'] > 5][:3],
            'evidence': f'{missing_percent:.1f}% of cells are missing.',
            'recommendationId': 'rec-missing',
        })
    if duplicate_percent > 0:
        issues.append({
            'id': 'issue-duplicates',
            'type': 'duplicates',
            'severity': 'Warning',
            'title': 'Duplicate rows detected',
            'summary': 'The file contains repeated rows that can distort metrics.',
            'affectedRows': int(len(dataframe) * (duplicate_percent / 100)),
            'affectedColumns': [column['name'] for column in columns[:2]],
            'evidence': f'{duplicate_percent:.1f}% of rows are duplicates.',
            'recommendationId': 'rec-duplicates',
        })
    if leakage_risk > 0.6:
        issues.append({
            'id': 'issue-leakage',
            'type': 'possible-leakage',
            'severity': 'Critical',
            'title': 'Potential leakage in the dataset',
            'summary': 'A column appears strongly linked to the target and may leak information.',
            'affectedRows': len(dataframe),
            'affectedColumns': [column['name'] for column in columns if column['leakageRisk'] > 0.6][:3],
            'evidence': 'At least one feature has a strong relationship with the target.',
            'recommendationId': 'rec-leakage',
        })
    if target_present and imbalance_penalty > 0.2:
        issues.append({
            'id': 'issue-imbalance',
            'type': 'class-imbalance',
            'severity': 'Warning',
            'title': 'Target imbalance detected',
            'summary': 'The target values are not evenly distributed.',
            'affectedRows': len(dataframe),
            'affectedColumns': [target_column] if target_column else [],
            'evidence': 'The dominant target value accounts for most observations.',
            'recommendationId': 'rec-imbalance',
        })

    factors = [
        {
            'name': 'Completeness',
            'score': round(completeness_score, 1),
            'weight': 0.3,
            'severity': 'Moderate' if missing_percent > 5 else 'Healthy',
            'explanation': 'The proportion of empty cells in the uploaded dataset.',
        },
        {
            'name': 'Consistency',
            'score': round(consistency_score, 1),
            'weight': 0.25,
            'severity': 'Warning' if duplicate_percent > 0 else 'Healthy',
            'explanation': 'Duplicate rows and suspicious values reduce consistency.',
        },
        {
            'name': 'Leakage Risk',
            'score': round(leakage_score, 1),
            'weight': 0.2,
            'severity': 'Critical' if leakage_risk > 0.6 else 'Warning' if leakage_risk > 0.3 else 'Healthy',
            'explanation': 'Strong feature-target relationships may indicate leakage.',
        },
        {
            'name': 'Distribution',
            'score': round(distribution_score, 1),
            'weight': 0.25,
            'severity': 'Warning' if imbalance_penalty > 0.2 else 'Healthy',
            'explanation': 'The target distribution influences how reliable the analysis is.',
        },
    ]

    recommendations = [
        {
            'id': 'rec-missing',
            'priority': 'High',
            'issueType': 'missing-values',
            'title': 'Impute or remove sparse values',
            'rationale': 'Filling or dropping missing values can prevent training instability.',
            'action': 'Use median imputation for numeric fields and a default category for strings.',
            'affectedColumns': [column['name'] for column in columns if column['missingPercent'] > 5][:3],
            'caution': 'Do not drop rows blindly if the missingness is informative.',
        },
        {
            'id': 'rec-leakage',
            'priority': 'Critical',
            'issueType': 'possible-leakage',
            'title': 'Review leakage-prone columns',
            'rationale': 'A highly predictive feature can make the model look unrealistically strong.',
            'action': 'Remove or inspect the feature before training.',
            'affectedColumns': [column['name'] for column in columns if column['leakageRisk'] > 0.6][:3],
            'caution': 'Confirm the meaning of the column with domain context.',
        },
        {
            'id': 'rec-imbalance',
            'priority': 'Medium',
            'issueType': 'class-imbalance',
            'title': 'Balance the target distribution',
            'rationale': 'Class imbalance can cause poor minority-class recall.',
            'action': 'Apply sampling or class weights before training.',
            'affectedColumns': [target_column] if target_column else [],
            'caution': 'Keep a validation split that reflects the original distribution.',
        },
    ]

    return {
        'analysisId': str(uuid.uuid4()),
        'status': 'ready',
        'datasetName': filename,
        'rowCount': int(len(dataframe)),
        'columnCount': int(len(dataframe.columns)),
        'targetColumn': target_column,
        'healthScore': int(health_score),
        'scoreLabel': score_label,
        'factors': factors,
        'topIssues': issues,
        'columns': columns,
        'recommendations': recommendations,
    }


@app.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok'}


@app.post('/api/v1/analyses')
async def upload_analysis(file: UploadFile = File(...)) -> dict[str, Any]:
    try:
        dataframe = _load_dataframe(file)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive path
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    target_column = None
    lower_names = {column.lower(): column for column in dataframe.columns}
    for candidate in ['health_score', 'target', 'label', 'diagnosis']:
        if candidate in lower_names:
            target_column = lower_names[candidate]
            break

    analysis = analyze_dataset(dataframe, file.filename or 'uploaded-data', target_column)
    ANALYSES[analysis['analysisId']] = analysis
    return analysis


@app.get('/api/v1/analyses/{analysis_id}')
def get_analysis(analysis_id: str) -> dict[str, Any]:
    analysis = ANALYSES.get(analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail='Analysis not found.')
    return analysis


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host='127.0.0.1', port=8002)
