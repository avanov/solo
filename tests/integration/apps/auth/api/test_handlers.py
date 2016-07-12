def test_authentication_handler(loop, create_app_and_client):
    run = loop.run_until_complete
    app, client = run(create_app_and_client())

    async def test_url__login__be__github():
        nonlocal client
        resp = await client.post("/api/login/github", allow_redirects=False)
        assert resp.status == 302

    async def test_url__login__be__github__callback():
        nonlocal client
        resp = await client.get("/api/login/github/callback", allow_redirects=False)
        assert resp.status == 400

    run(test_url__login__be__github())
    run(test_url__login__be__github__callback())
