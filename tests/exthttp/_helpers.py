from extapi.http.abc import AbstractExecutor
from extapi.http.types import BackendResponseProtocol, RequestData, Response


class DummyBackendResponse(BackendResponseProtocol[bytes]):
    def __init__(self, data: bytes = b""):
        self.data = data

    def original(self) -> bytes:
        return self.data

    async def close(self) -> None:
        pass

    async def read(self) -> bytes:
        return self.data


class DummyExecutor(AbstractExecutor[bytes]):
    def __init__(self, status: int = 200):
        self._status = status

    async def execute(self, request: RequestData) -> Response[bytes]:
        return Response(
            status=self._status,
            url=request.url,
            backend_response=DummyBackendResponse(),
        )
