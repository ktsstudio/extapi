from collections.abc import Iterable
from typing import Generic, TypeVar

from extapi.http.abc import Addon
from extapi.http.types import HttpExecuteError, RequestData, Response

T = TypeVar("T")


class StatusValidationAddon(Addon[T], Generic[T]):
    def __init__(
        self,
        expected_statuses: Iterable[int] = (200, 201),
    ):
        self._expected_statuses = set(expected_statuses)

    async def before_request(self, request: RequestData) -> None:
        return None  # pragma: no cover

    async def process_response(
        self, request: RequestData, response: Response[T]
    ) -> Response[T]:
        if response.status not in self._expected_statuses:
            raise HttpExecuteError(response)

        return response
