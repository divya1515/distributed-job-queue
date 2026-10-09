from pydantic import BaseModel , HttpUrl

class ShortenRequest(BaseModel):
    long_url: HttpUrl

class ShortenResponse(BaseModel):
    short_url: str