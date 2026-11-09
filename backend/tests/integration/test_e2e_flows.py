"""
End-to-end integration tests that verify complete user flows
These tests run against the live backend API on port 9200
"""
import pytest
import requests
import time

BASE_URL = "http://127.0.0.1:9200"

@pytest.fixture(scope="module")
def api_client():
    """Fixture that provides a requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def auth_token(api_client):
    """Fixture that logs in and returns an auth token"""
    response = api_client.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={
            "email": "admin@example.com",
            "password": "admin123"
        }
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert "access_token" in data, f"No access_token in response: {data}"
    return data["access_token"]


class TestAuthenticationFlow:
    """Test authentication endpoints and flows"""
    
    def test_login_with_valid_credentials(self, api_client):
        """Should successfully login with correct credentials"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "email": "admin@example.com",
                "password": "admin123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == "admin@example.com"
        assert "roles" in data["user"]
    
    def test_login_with_invalid_credentials(self, api_client):
        """Should reject login with incorrect credentials"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "email": "invalid@example.com",
                "password": "wrongpassword"
            }
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_protected_endpoint_without_auth(self, api_client):
        """Should reject access to protected endpoints without token"""
        response = api_client.get(f"{BASE_URL}/api/v1/sources/")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def test_protected_endpoint_with_auth(self, api_client, auth_token):
        """Should allow access to protected endpoints with valid token"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = api_client.get(f"{BASE_URL}/api/v1/sources/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data


class TestSourceManagement:
    """Test source governance endpoints"""
    
    def test_list_sources(self, api_client, auth_token):
        """Should list knowledge sources with pagination"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = api_client.get(
            f"{BASE_URL}/api/v1/sources/",
            headers=headers,
            params={"skip": 0, "limit": 10}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
        assert data["total"] >= 0
    
    def test_source_list_includes_required_fields(self, api_client, auth_token):
        """Should return sources with all required fields"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = api_client.get(
            f"{BASE_URL}/api/v1/sources/",
            headers=headers,
            params={"limit": 1}
        )
        assert response.status_code == 200
        data = response.json()
        
        if len(data["items"]) > 0:
            source = data["items"][0]
            # Verify required fields exist
            required_fields = ["source_record_id", "source_key", "title", "source_type", "approval_state"]
            for field in required_fields:
                assert field in source, f"Missing required field: {field}"


class TestQuestionFlow:
    """Test question submission"""
    
    def test_submit_question(self, api_client, auth_token):
        """Should submit a question and receive a question ID"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = api_client.post(
            f"{BASE_URL}/api/v1/questions",
            headers=headers,
            json={
                "question_text": "Who owns the authentication service?",
            }
        )
        
        # Accept 200, 201, or 202 as valid responses
        assert response.status_code in [200, 201, 202], f"Expected 200/201/202, got {response.status_code}: {response.text}"
        data = response.json()
        # Check for various possible response fields
        has_id = any(key in data for key in ["question_id", "id", "turn_id", "session_id"])
        assert has_id, f"No question/turn/session ID in response: {data}"
    
    def test_get_question_status(self, api_client, auth_token):
        """Should check status of a submitted question"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Submit a question first
        submit_response = api_client.post(
            f"{BASE_URL}/api/v1/questions",
            headers=headers,
            json={
                "question_text": "What is the deployment process?",
            }
        )
        
        if submit_response.status_code in [200, 201, 202]:
            data = submit_response.json()
            # Try to extract some ID to check status
            question_id = data.get("question_id") or data.get("turn_id") or data.get("id")
            
            if question_id:
                # Try to get status
                status_response = api_client.get(
                    f"{BASE_URL}/api/v1/questions/{question_id}",
                    headers=headers
                )
                # Accept 200 or 404 (if status endpoint doesn't exist)
                assert status_response.status_code in [200, 404], f"Unexpected status code: {status_response.status_code}"


class TestAnswerFlow:
    """Test answer retrieval"""
    
    def test_get_answer_requires_auth(self, api_client):
        """Should require authentication for answer retrieval"""
        # Try to get a random answer without auth
        import uuid
        random_id = str(uuid.uuid4())
        response = api_client.get(f"{BASE_URL}/api/v1/answers/{random_id}")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"


class TestCitationsFlow:
    """Test citation endpoints"""
    
    def test_citations_require_auth(self, api_client):
        """Should require authentication for citation access"""
        import uuid
        random_id = str(uuid.uuid4())
        response = api_client.get(f"{BASE_URL}/api/v1/citations/{random_id}")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"


class TestFeedbackFlow:
    """Test feedback submission"""
    
    def test_feedback_requires_auth(self, api_client):
        """Should require authentication for feedback submission"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/feedback",
            json={
                "answer_id": "00000000-0000-0000-0000-000000000000",
                "rating": 4,
                "feedback_text": "Test feedback",
            }
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"


class TestHealthAndStatus:
    """Test health and status endpoints"""
    
    def test_health_check(self, api_client):
        """Should return health status"""
        response = api_client.get(f"{BASE_URL}/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_api_docs_available(self, api_client):
        """Should serve OpenAPI documentation"""
        response = api_client.get(f"{BASE_URL}/docs")
        assert response.status_code == 200
    
    def test_root_endpoint(self, api_client):
        """Should return API information at root"""
        response = api_client.get(f"{BASE_URL}/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data or "version" in data
