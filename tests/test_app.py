from llm.api.app import app


def test_app_title() -> None:
    assert app.title == "DevFlow Agent API"


def test_health_route_exists() -> None:
    route_paths = {route.path for route in app.routes}
    assert "/health" in route_paths
