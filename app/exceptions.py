class HTTPException(Exception):
    def __init__(self, status_code: int, description: str, detail: str = None) -> None:
        self.status_code = status_code
        self.description = description
        self.detail = detail
        self.success = False
