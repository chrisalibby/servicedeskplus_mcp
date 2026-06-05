"""Unit tests for Settings and base_url construction."""

from servicedeskplus_mcp.config import Settings


def test_base_url_no_portal() -> None:
    s = Settings(SDP_SERVER="mysdp.local", SDP_PORT=8080, SDP_API_KEY="key", SDP_PORTAL_ID="")
    assert s.base_url == "http://mysdp.local:8080/api/v3"


def test_base_url_with_portal_id() -> None:
    s = Settings(
        SDP_SERVER="mysdp.local", SDP_PORT=8080, SDP_API_KEY="key", SDP_PORTAL_ID="helpdesk"
    )
    assert s.base_url == "http://mysdp.local:8080/helpdesk/api/v3"


def test_base_url_custom_port() -> None:
    s = Settings(SDP_SERVER="10.0.0.5", SDP_PORT=443, SDP_API_KEY="key")
    assert s.base_url == "http://10.0.0.5:443/api/v3"
