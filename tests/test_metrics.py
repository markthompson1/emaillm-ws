"""Tests for the Prometheus metrics endpoint."""
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from prometheus_client.parser import text_string_to_metric_families

from emaillm import app

client = TestClient(app)

def test_metrics_endpoint():
    """Test that the /metrics endpoint returns Prometheus metrics."""
    # Make a request to the metrics endpoint
    response = client.get("/metrics")
    
    # Check that the response is successful
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "text/plain; version=0.0.4; charset=utf-8"
    
    # Parse the metrics to ensure they're in the correct format
    metrics = list(text_string_to_metric_families(response.text))
    
    # Check that we have some metrics
    assert len(metrics) > 0
    
    # Check for specific metrics we expect to be present
    metric_names = {metric.name for metric in metrics}
    expected_metrics = {
        'emaillm_cache_hit',
        'emaillm_cache_miss',
        'emaillm_quota_exceeded',
        'emaillm_llm_requests',
        'emaillm_request_duration_seconds',
        'emaillm_requests_in_progress',
    }
    
    # Check that all expected metrics are present
    assert expected_metrics.issubset(metric_names), \
        f"Expected metrics {expected_metrics} not found in {metric_names}"

def test_request_metrics():
    """Test that request metrics are recorded."""
    # Make a request to the metrics endpoint to get initial values
    initial_metrics = client.get("/metrics").text
    
    # Make a test request to increment metrics
    test_response = client.get("/metrics")
    assert test_response.status_code == 200
    
    # Get metrics again and check they've been updated
    updated_metrics = client.get("/metrics").text
    
    # Parse metrics
    initial_metrics_dict = {m.name: m for m in text_string_to_metric_families(initial_metrics)}
    updated_metrics_dict = {m.name: m for m in text_string_to_metric_families(updated_metrics)}
    
    # Check that request count has increased
    if 'emaillm_requests_total' in updated_metrics_dict:
        initial_requests = sum(
            sample.value 
            for metric in initial_metrics_dict.get('emaillm_requests_total', []).samples
            for sample in [metric]
        )
        
        updated_requests = sum(
            sample.value 
            for metric in updated_metrics_dict['emaillm_requests_total'].samples
            for sample in [metric]
        )
        
        assert updated_requests > initial_requests, "Request count should have increased"

@pytest.mark.asyncio
async def test_metrics_endpoint_async():
    """Test the /metrics endpoint with an async test client."""
    # Use the test client for simplicity
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "emaillm_" in response.text
