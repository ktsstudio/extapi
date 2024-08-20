from extapi.http.abc import AbstractExecutor
from extapi.http.types import RequestData, Response


class DummyExecutor(AbstractExecutor[str]):
    def __init__(self, status: int = 200):
        self._status = status

    async def execute(self, request: RequestData) -> Response[str]:
        return Response(status=self._status, url=request.url, backend_response="heyo")
