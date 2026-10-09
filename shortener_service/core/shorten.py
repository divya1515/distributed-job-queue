import hashlib

BASE_SHORT_DOMAIN="http://localhost:8001/"

def generate_short_url(long_url:str):
    short_code=hashlib.md5(str(long_url).encode()).hexdigest()[:7]
    short_url=f"{BASE_SHORT_DOMAIN}{short_code}"
    return short_code,short_url