import logging
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

logger = logging.getLogger("scoring.auth")


class CookieJWTAuthentication(JWTAuthentication):
    """
    Authenticates requests using the Authorization Bearer header first,
    falling back to the httpOnly 'access_token' cookie as required by AGENTS.md §6.
    """

    def authenticate(self, request):
        header = self.get_header(request)
        if header is not None:
            raw_token = self.get_raw_token(header)
        else:
            raw_token = request.COOKIES.get("access_token")

        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
        except (InvalidToken, TokenError) as exc:
            logger.warning(
                "Invalid or expired JWT token on [%s %s]: %s",
                request.method,
                request.path,
                exc.__class__.__name__,
            )
            if header is not None:
                raise
            return None
