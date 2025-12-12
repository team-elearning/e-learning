from pydantic import BaseModel

class MediaCookieOutput(BaseModel):
    expires_at: int
    expires_in_seconds: int
    resource: str