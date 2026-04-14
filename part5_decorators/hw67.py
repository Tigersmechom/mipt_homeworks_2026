import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from functools import wraps
from typing import Any, ParamSpec, TypeVar
from urllib.request import urlopen

INVALID_CRITICAL_COUNT = "Breaker count must be positive integer!"
INVALID_RECOVERY_TIME = "Breaker recovery time must be positive integer!"
VALIDATIONS_FAILED = "Invalid decorator args."
TOO_MUCH = "Too much requests, just wait."

P = ParamSpec("P")
T = TypeVar("T")


class BreakerError(Exception):
    def __init__(self, func_name: str, block_time: datetime) -> None:
        super().__init__(TOO_MUCH)
        self.func_name = func_name
        self.block_time = block_time


class CircuitBreaker:
    def __init__(
        self,
        critical_count: int = 5,
        time_to_recover: int = 30,
        triggers_on: type[Exception] = Exception,
    ) -> None:
        errors = []

        if type(critical_count) is not int or critical_count <= 0:
            errors.append(ValueError(INVALID_CRITICAL_COUNT))
        if type(time_to_recover) is not int or time_to_recover <= 0:
            errors.append(ValueError(INVALID_RECOVERY_TIME))

        if errors:
            raise ExceptionGroup(VALIDATIONS_FAILED, errors)

        self.critical_count = critical_count
        self.time_to_recover = time_to_recover
        self.triggers_on = triggers_on

        self._failed_count = 0
        self._blocked_until: datetime | None = None
        self._block_time: datetime | None = None

    def _reset(self) -> None:
        self._failed_count = 0
        self._blocked_until = None
        self._block_time = None

    def __call__(self, func: Callable[P, T]) -> Callable[P, T]:
        func_name = f"{func.__module__}.{func.__name__}"

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            now = datetime.now(UTC)

            if self._blocked_until is not None and now < self._blocked_until:
                raise BreakerError(func_name, self._block_time)

            if self._blocked_until is not None:
                self._reset()

            try:
                result = func(*args, **kwargs)
            except Exception as error:
                if isinstance(error, self.triggers_on):
                    self._failed_count += 1
                    if self._failed_count >= self.critical_count:
                        self._failed_count = 0
                        self._block_time = datetime.now(UTC)
                        self._blocked_until = self._block_time + timedelta(seconds=self.time_to_recover)
                        raise BreakerError(func_name, self._block_time) from error
                raise
            else:
                self._failed_count = 0
                return result

        return wrapper


def get_comments(post_id: int) -> Any:
    response = urlopen(f"https://jsonplaceholder.typicode.com/comments?postId={post_id}")
    return json.loads(response.read())
