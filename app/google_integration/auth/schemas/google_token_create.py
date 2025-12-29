from pydantic import BaseModel


class GoogleTokenCreate(BaseModel):
    GoogleTokenDto(
        user=user,
        access_token=credentials.token,
        refresh_token=credentials.refresh_token,
        token_type="Bearer",
        expires_in=None,  # Вычисляется из expiry
        expires_at=credentials.expiry,
        scope=" ".join(credentials.scopes) if credentials.scopes else None,

