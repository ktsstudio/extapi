import asyncio
import functools
from collections.abc import Awaitable, Callable
from typing import Any, ParamSpec, TypeVar, cast, overload

P = ParamSpec("P")
R = TypeVar("R")


@overload
async def execute_sync_async(
    f: Callable[P, Awaitable[R]], *args: P.args, **kwargs: P.kwargs
) -> R: ...


@overload
async def execute_sync_async(
    f: Callable[P, R], *args: P.args, **kwargs: P.kwargs
) -> R: ...


async def execute_sync_async(
    f: Callable[P, Awaitable[R]] | Callable[P, R], *args: P.args, **kwargs: P.kwargs
) -> R:
    if not is_async_callable(f):
        return cast(R, f(*args, **kwargs))

    return await cast(Callable[P, Awaitable[R]], f)(*args, **kwargs)


def is_async_callable(obj: Any) -> bool:
    while isinstance(obj, functools.partial):
        obj = obj.func

    return asyncio.iscoroutinefunction(obj) or (
        callable(obj) and asyncio.iscoroutinefunction(obj.__call__)
    )
