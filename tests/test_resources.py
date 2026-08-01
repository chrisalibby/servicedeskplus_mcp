"""Tests for the schema documentation resources."""

from servicedeskplus_mcp.server import mcp


def _resource_uris() -> set[str]:
    resources = mcp._resource_manager.list_resources()  # type: ignore[attr-defined]
    return {str(r.uri) for r in resources}


async def _read(uri: str) -> str:
    resource = await mcp._resource_manager.get_resource(uri)  # type: ignore[attr-defined]
    assert resource is not None
    content = await resource.read()
    return content if isinstance(content, str) else content.decode()


def test_schema_resources_registered() -> None:
    uris = _resource_uris()
    assert "sdp://schema/asset" in uris
    assert "sdp://schema/ci-relationship" in uris
    assert "sdp://schema/purchase-order" in uris


async def test_asset_schema_content() -> None:
    content = await _read("sdp://schema/asset")
    assert "asset_depreciation" in content
    assert "depreciation_type" in content


async def test_ci_relationship_schema_content() -> None:
    content = await _read("sdp://schema/ci-relationship")
    assert "ci_relationships" in content
    assert "module_type" in content


async def test_purchase_order_schema_content() -> None:
    content = await _read("sdp://schema/purchase-order")
    assert "ordered_quantity" in content
    assert "Product-Vendor association" in content
