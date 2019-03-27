def test_url__login__be__github(web_client):
    resp = web_client.post("/api/login/github", allow_redirects=False)
    assert resp.status_code == 302


def test_url__login__be__github__callback(web_client):
    resp = web_client.get("/api/login/github/callback", allow_redirects=False)
    assert resp.status_code == 403
