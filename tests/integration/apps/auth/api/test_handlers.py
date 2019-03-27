async def test_url__login__be__github(web_client):
    resp = await web_client.post("/api/login/github", allow_redirects=False)
    assert resp.status == 302


async def test_url__login__be__github__callback(web_client):
    resp = await web_client.get("/api/login/github/callback", allow_redirects=False)
    assert resp.status == 400
