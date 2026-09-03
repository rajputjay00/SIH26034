import os
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import _parse_origins

def create_test_app(env_origins: str, env_name: str = "production"):
    app = FastAPI()
    os.environ["ENVIRONMENT"] = env_name
    
    parsed = _parse_origins(env_origins)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=parsed,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    @app.get("/api/v1/cases")
    def dummy_cases():
        return []
        
    @app.post("/api/v1/auth/login")
    def dummy_login():
        return {}
        
    return app, parsed

def test_cors_preflight_login_allowed_origin():
    # Simulate Vercel string with accidental literal quotes inside the env variable
    app, origins = create_test_app('"https://frontend-gyrvoap2q-rajputjay001.vercel.app"')
    
    client = TestClient(app)
    response = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "https://frontend-gyrvoap2q-rajputjay001.vercel.app",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization, content-type"
        }
    )
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    assert response.headers.get("access-control-allow-origin") == "https://frontend-gyrvoap2q-rajputjay001.vercel.app"
    assert response.headers.get("access-control-allow-credentials") == "true"
    assert "POST" in response.headers.get("access-control-allow-methods", "")

def test_cors_preflight_cases_allowed_origin():
    app, origins = create_test_app('"https://frontend-gyrvoap2q-rajputjay001.vercel.app"')
    client = TestClient(app)
    response = client.options(
        "/api/v1/cases",
        headers={
            "Origin": "https://frontend-gyrvoap2q-rajputjay001.vercel.app",
            "Access-Control-Request-Method": "GET",
        }
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://frontend-gyrvoap2q-rajputjay001.vercel.app"

def test_cors_preflight_invalid_origin_blocked():
    app, origins = create_test_app('"https://frontend-gyrvoap2q-rajputjay001.vercel.app"')
    client = TestClient(app)
    response = client.options(
        "/api/v1/cases",
        headers={
            "Origin": "https://malicious-site.com",
            "Access-Control-Request-Method": "GET",
        }
    )
    # FastAPI's CORSMiddleware returns 400 Bad Request if origin is not allowed
    assert response.status_code == 400
    assert "Disallowed CORS origin" in response.text
    
def test_cors_preflight_localhost_in_dev_vs_prod():
    # Production without explicit localhost should block it
    app_prod, origins_prod = create_test_app('"https://frontend-gyrvoap2q-rajputjay001.vercel.app"', "production")
    client_prod = TestClient(app_prod)
    
    response = client_prod.options(
        "/api/v1/cases",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        }
    )
    assert response.status_code == 400
    
    # Development without explicit localhost should implicitly allow it
    app_dev, origins_dev = create_test_app('"https://frontend-gyrvoap2q-rajputjay001.vercel.app"', "development")
    client_dev = TestClient(app_dev)
    
    response = client_dev.options(
        "/api/v1/cases",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        }
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
