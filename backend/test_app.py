from fastapi.testclient import TestClient

from backend.app import app

client = TestClient(app)


def test_upload_csv_returns_analysis_summary() -> None:
    csv_content = b'health_score,task_type,feature_a\n0.8,alpha,1\n0.7,beta,2\n0.6,alpha,3\n'

    response = client.post(
        '/api/v1/analyses',
        files={'file': ('sample.csv', csv_content, 'text/csv')},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['datasetName'] == 'sample.csv'
    assert payload['rowCount'] == 3
    assert payload['healthScore'] >= 0
    assert payload['topIssues']
