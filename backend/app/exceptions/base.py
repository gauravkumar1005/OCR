from __future__ import annotations

class AppException(Exception):
    def __init__(self, detail: str, status_code: int = 400) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class ValidationException(AppException):
    def __init__(self, detail: str) -> None:
        super().__init__(detail, status_code=422)


class CloudinaryException(AppException):
    def __init__(self, detail: str) -> None:
        super().__init__(detail, status_code=502)


class OCRException(AppException):
    def __init__(self, detail: str) -> None:
        super().__init__(detail, status_code=502)


class DatabaseException(AppException):
    def __init__(self, detail: str) -> None:
        super().__init__(detail, status_code=500)


class NotFoundException(AppException):
    def __init__(self, detail: str) -> None:
        super().__init__(detail, status_code=404)


class ConflictException(AppException):
    def __init__(self, detail: str) -> None:
        super().__init__(detail, status_code=409)


class MapperConfigurationException(AppException):
    def __init__(self, detail: str) -> None:
        super().__init__(detail, status_code=500)
