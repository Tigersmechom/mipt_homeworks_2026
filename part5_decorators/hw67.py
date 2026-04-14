import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from functools import wraps
from typing import Any, ParamSpec, TypeVar, cast
from urllib.request import urlopen

INVALID_CRITICAL_COUNT = "Breaker count must be positive integer!"
INVALID_RECOVERY_TIME = "Breaker recovery time must be positive integer!"
VALIDATIONS_FAILED = "Invalid decorator args."
TOO_MUCH = "Too much requests, just wait."

P = ParamSpec("P")
T = TypeVar("T")


def _validate_positive_integer(value: object, error_message: str) -> ValueError | None:
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return None
    return ValueError(error_message)


def _validate_decorator_args(critical_count: object, time_to_recover: object) -> None:
    errors = [
        error
        for error in (
            _validate_positive_integer(critical_count, INVALID_CRITICAL_COUNT),
            _validate_positive_integer(time_to_recover, INVALID_RECOVERY_TIME),
        )
        if error is not None
    ]
    if errors:
        raise ExceptionGroup(VALIDATIONS_FAILED, errors)


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
        _validate_decorator_args(critical_count, time_to_recover)
        self.critical_count = critical_count
        self.time_to_recover = time_to_recover
        self.triggers_on = triggers_on

        self._failed_count = 0
        self._blocked_until: datetime | None = None
        self._block_time: datetime | None = None

    def __call__(self, func: Callable[P, T]) -> Callable[P, T]:
        func_name = f"{func.__module__}.{func.__name__}"

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            if self._is_blocked():
                raise BreakerError(func_name, cast("datetime", self._block_time))

            try:
                result = func(*args, **kwargs)
            except Exception as error:
                self._handle_failure(error, func_name)
                raise

            self._failed_count = 0
            return result

        return wrapper

    def _is_blocked(self) -> bool:
        blocked_until = self._blocked_until
        if blocked_until is None:
            return False
        if datetime.now(UTC) >= blocked_until:
            self._failed_count = 0
            self._blocked_until = None
            self._block_time = None
            return False
        return True

    def _handle_failure(self, error: Exception, func_name: str) -> None:
        if isinstance(error, self.triggers_on):
            self._failed_count += 1
            if self._failed_count >= self.critical_count:
                block_time = datetime.now(UTC)
                self._failed_count = 0
                self._block_time = block_time
                self._blocked_until = block_time + timedelta(seconds=self.time_to_recover)
                raise BreakerError(func_name, block_time) from error


def get_comments(post_id: int) -> Any:
    response = urlopen(f"https://jsonplaceholder.typicode.com/comments?postId={post_id}")
    return json.loads(response.read())
