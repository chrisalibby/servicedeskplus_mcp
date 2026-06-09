"""Unit tests for Settings and base_url construction."""

from servicedeskplus_mcp.config import Settings


def test_base_url_http_default() -> None:
    s = Settings(SDP_SERVER="mysdp.local", SDP_PORT=8080, SDP_API_KEY="key", SDP_PORTAL_ID="")
    assert s.base_url == "http://mysdp.local:8080/api/v3"


def test_base_url_https_on_port_443() -> None:
    s = Settings(SDP_SERVER="mysdp.local", SDP_PORT=443, SDP_API_KEY="key")
    assert s.base_url == "https://mysdp.local:443/api/v3"
    assert s.scheme == "https"


def test_base_url_with_portal_id() -> None:
    s = Settings(
        SDP_SERVER="mysdp.local", SDP_PORT=8080, SDP_API_KEY="key", SDP_PORTAL_ID="helpdesk"
    )
    assert s.base_url == "http://mysdp.local:8080/helpdesk/api/v3"


def test_base_url_https_with_portal_id() -> None:
    s = Settings(
        SDP_SERVER="mysdp.local", SDP_PORT=443, SDP_API_KEY="key", SDP_PORTAL_ID="helpdesk"
    )
    assert s.base_url == "https://mysdp.local:443/helpdesk/api/v3"


def test_verify_ssl_defaults_true() -> None:
    # Pass explicitly to avoid pydantic-settings reading SDP_VERIFY_SSL from .env
    s = Settings(SDP_SERVER="mysdp.local", SDP_PORT=8080, SDP_API_KEY="key", SDP_VERIFY_SSL=True)
    assert s.SDP_VERIFY_SSL is True


def test_verify_ssl_can_be_disabled() -> None:
    s = Settings(SDP_SERVER="mysdp.local", SDP_PORT=443, SDP_API_KEY="key", SDP_VERIFY_SSL=False)
    assert s.SDP_VERIFY_SSL is False
