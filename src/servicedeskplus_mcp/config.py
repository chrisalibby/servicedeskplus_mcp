from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    SDP_SERVER: str = "localhost"
    SDP_PORT: int = 8080
    SDP_API_KEY: str = ""
    SDP_PORTAL_ID: str = ""
    SDP_TIMEOUT: float = 30.0
    SDP_VERIFY_SSL: bool = True
    SDP_TRANSPORT: str = "stdio"
    SDP_HTTP_HOST: str = "127.0.0.1"
    SDP_HTTP_PORT: int = 8000
    SDP_TRUST_PROXY: bool = False

    @property
    def scheme(self) -> str:
        return "https" if self.SDP_PORT == 443 else "http"

    @property
    def base_url(self) -> str:
        host = f"{self.scheme}://{self.SDP_SERVER}:{self.SDP_PORT}"
        if self.SDP_PORTAL_ID:
            return f"{host}/{self.SDP_PORTAL_ID}/api/v3"
        return f"{host}/api/v3"


settings = Settings()  # type: ignore[call-arg]
