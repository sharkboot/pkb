from fastapi import HTTPException, status

class BadRequestException(HTTPException):
    def __init__(self, detail: str = "参数错误"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

class ResourceNotFoundException(HTTPException):
    def __init__(self, detail: str = "资源不存在"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class ResourceExistsException(HTTPException):
    def __init__(self, detail: str = "资源已存在"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)

class TaskExecuteException(HTTPException):
    def __init__(self, detail: str = "AI任务执行失败"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)

class FileProcessException(HTTPException):
    def __init__(self, detail: str = "文件处理失败"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)

class SystemException(HTTPException):
    def __init__(self, detail: str = "系统内部错误"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)