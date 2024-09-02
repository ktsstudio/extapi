from aiohttp.test_utils import TestServer
from multidict import CIMultiDict
from yarl import URL

from extapi.http.backends.aiohttp import AiohttpExecutor
from extapi.http.types import RequestData


class TestAiohttpBackend:
    async def test_init(self):
        async with AiohttpExecutor(
            ssl=True, default_timeout=1.0, trust_env=True
        ) as executor:
            assert executor._default_timeout == 1.0
            assert executor._ssl is True
            assert executor._session._trust_env is True

    async def test_execute(self, dummy_server: TestServer):
        async with AiohttpExecutor() as executor:
            request = RequestData(
                method="GET",
                url=URL(f"http://localhost:{dummy_server.port}/get"),
            )

            response = await executor.execute(request)
            assert response.status == 200
            assert response.url == request.url
            assert response.original.status == 200

    async def test_execute_unknown(self, dummy_server: TestServer):
        async with AiohttpExecutor() as executor:
            request = RequestData(
                method="GET",
                url=URL(f"http://localhost:{dummy_server.port}/unknown"),
            )

            response = await executor.execute(request)
            assert response.status == 404
            assert response.url == request.url
            assert response.original.status == 404

    async def test_read(self, dummy_server: TestServer):
        async with AiohttpExecutor() as executor:
            request = RequestData(
                method="GET",
                url=URL(f"http://localhost:{dummy_server.port}/get"),
                auto_read_body=False,
            )

            response = await executor.execute(request)
            async with response:
                res = await response.read()
                assert res == b'{"status": "ok"}'

    async def test_read_supplied(self, dummy_server: TestServer):
        async with AiohttpExecutor() as executor:
            request = RequestData(
                method="GET",
                url=URL(f"http://localhost:{dummy_server.port}/get"),
                auto_read_body=True,
            )

            response = await executor.execute(request)
            async with response:
                res = await response.read()
                assert res == b'{"status": "ok"}'

    async def test_json_supplied(self, dummy_server: TestServer):
        async with AiohttpExecutor() as executor:
            request = RequestData(
                method="GET",
                url=URL(f"http://localhost:{dummy_server.port}/get"),
                auto_read_body=True,
            )

            response = await executor.execute(request)
            async with response:
                res = await response.json()
                assert res == {"status": "ok"}

    async def test_json(self, dummy_server: TestServer):
        async with AiohttpExecutor() as executor:
            request = RequestData(
                method="GET",
                url=URL(f"http://localhost:{dummy_server.port}/get"),
                auto_read_body=False,
            )

            response = await executor.execute(request)
            async with response:
                res = await response.json()
                assert res == {"status": "ok"}

    async def test_headers(self, dummy_server: TestServer):
        async with AiohttpExecutor() as executor:
            request = RequestData(
                method="GET",
                url=URL(f"http://localhost:{dummy_server.port}/get"),
                headers=CIMultiDict(
                    {"X-Test-Header-1": "one", "X-Test-Header-2": "two"}
                ),
            )

            response = await executor.execute(request)
            async with response:
                assert response.headers["X-Test-Header-1"] == "one"
                assert response.headers["X-Test-Header-2"] == "two"
