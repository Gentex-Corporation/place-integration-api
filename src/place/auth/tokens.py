import jwt

def decode_sub(access_token: str) -> str:
    claims = jwt.decode(access_token, options={"verify_signature": False})
    return claims["sub"]
