def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "Alehar Resource Intelligence",
    }


def test_api_documentation(client):
    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200
    schema = client.get("/openapi.json").json()
    assert schema["info"]["version"] == "0.1.0"
    operation = schema["paths"]["/lenders/{lender_id}/verify"]["post"]
    assert "requestBody" not in operation
