import logging
import functools
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class ServiceError(Exception):
    def __init__(self, message: str, service_name: str = "", original_error: Optional[Exception] = None):
        self.message = message
        self.service_name = service_name
        self.original_error = original_error
        super().__init__(self.message)


def safe_service_call(
    default_value: Any = None,
    service_name: str = "",
    log_error: bool = True,
    reraise: bool = False,
) -> Callable:
    """
    Service层异常隔离装饰器。

    捕获被装饰函数中的所有异常，记录日志，并返回默认值或抛出ServiceError。

    参数:
        default_value: 异常发生时返回的默认值
        service_name: 用于日志标识的服务名称
        log_error: 是否记录错误日志
        reraise: 是否将异常包装为ServiceError后重新抛出

    使用示例:
        @safe_service_call(default_value={}, service_name="StatsService")
        def get_stats_overview():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ServiceError:
                raise
            except Exception as e:
                name = service_name or func.__name__
                if log_error:
                    logger.exception(
                        "[ServiceError] %s failed: %s - args=%s, kwargs=%s",
                        name,
                        str(e),
                        str(args)[:200],
                        str(kwargs)[:200],
                    )
                if reraise:
                    raise ServiceError(
                        message=str(e),
                        service_name=name,
                        original_error=e,
                    ) from e
                return default_value
        return wrapper
    return decorator


def safe_view_call(default_response: Any = None, status_code: int = 200):
    """
    View层异常隔离装饰器（配合DRF Response使用）。

    用于装饰ViewSet的action方法，确保单个接口异常不会导致依赖此接口的聚合接口整体失败。
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, request, *args, **kwargs):
            from rest_framework.response import Response
            try:
                return func(self, request, *args, **kwargs)
            except Exception as e:
                logger.exception(
                    "[ViewError] %s failed: %s",
                    func.__name__,
                    str(e),
                )
                if default_response is not None:
                    return Response(default_response, status=status_code)
                return Response(
                    {"error": "服务暂时不可用，请稍后重试", "detail": str(e)},
                    status=500,
                )
        return wrapper
    return decorator
