from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "AI Chat Bot is running"}

def test_health_check():
    # Verify that the app can start and import modules correctly
    assert app.title == "AI Chat Bot"
