"""
Integration tests for the real-world-usage punch list fixes against a live SDP instance.
Run with: uv run pytest tests/integration/ -v -m integration
"""

import json

import pytest

from .conftest import TEST_TECHNICIAN_EMAIL, skip_if_no_server

pytestmark = [pytest.mark.integration, skip_if_no_server]


async def test_list_products(client) -> None:
    params = {"input_data": json.dumps({"list_info": {"start_index": 0, "row_count": 5}})}
    result = await client.get("/products", params=params)
    assert "error" not in result, result
    products = result.get("products", [])
    assert products, "Expected at least one product in the catalog"
    print(f"\nProducts (first 5): {[p.get('name') for p in products]}")


async def test_list_product_types(client) -> None:
    params = {"input_data": json.dumps({"list_info": {"start_index": 0, "row_count": 100}})}
    result = await client.get("/product_types", params=params)
    assert "error" not in result, result
    types = result.get("product_types", [])
    assert types, "Expected at least one product type"
    names = [t.get("name") for t in types]
    print(f"\nProduct types: {names[:15]}")


async def test_list_products_filtered_by_name(client) -> None:
    list_info = {
        "row_count": 10,
        "search_criteria": [{"field": "name", "condition": "contains", "value": "EliteBook"}],
    }
    result = await client.get(
        "/products", params={"input_data": json.dumps({"list_info": list_info})}
    )
    assert "error" not in result, result
    print(f"\nEliteBook products: {[p.get('name') for p in result.get('products', [])]}")


async def test_create_asset_end_to_end(client) -> None:
    """Create an asset with nested product ID, verify, then delete it."""
    params = {"input_data": json.dumps({"list_info": {"start_index": 0, "row_count": 1}})}
    products = (await client.get("/products", params=params)).get("products", [])
    if not products:
        pytest.skip("No products in catalog")
    product_id = products[0]["id"]

    asset = {"name": "MCP-INTEGRATION-TEST-ASSET", "product": {"id": product_id}}
    created = await client.post("/assets", {"asset": asset})
    assert "error" not in created, created
    asset_id = created["asset"]["id"]
    print(f"\nCreated asset {asset_id} with product {product_id}")

    fetched = await client.get(f"/assets/{asset_id}")
    assert fetched["asset"]["name"] == "MCP-INTEGRATION-TEST-ASSET"

    deleted = await client.delete(f"/assets/{asset_id}")
    print(f"Delete result: {deleted.get('response_status', deleted.get('error'))}")


async def test_create_request_urgency_rejected_quirk(client) -> None:
    """Documented quirk: this instance rejects urgency on requests in every format
    (name and ID, on create and update) — the field is not on the request form.
    If this test starts failing, urgency became supported: update the quirk docs."""
    request = {
        "subject": "MCP integration test — urgency quirk probe",
        "description": "Safe to delete; created by automated test.",
        "requester": {"name": "Chris Libby"},
        "category": {"name": "User Administration"},
        "subcategory": {"name": "Password Reset"},
        "urgency": {"id": "2"},
    }
    created = await client.post("/requests", {"request": request})
    assert "error" in created, "urgency was accepted — quirk no longer applies, update docs"
    assert created["status_code"] == 400
    print("\nConfirmed: urgency rejected on create (400) — matches documented quirk")


async def test_list_changes_desc_sort(client) -> None:
    """Newest-first sort — the fix for 'oldest change from 2020 first'."""
    list_info = {"row_count": 5, "sort_field": "created_time", "sort_order": "desc"}
    result = await client.get(
        "/changes", params={"input_data": json.dumps({"list_info": list_info})}
    )
    assert "error" not in result, result
    changes = result.get("changes", [])
    times = [int(c["created_time"]["value"]) for c in changes if c.get("created_time")]
    assert times == sorted(times, reverse=True), f"Not desc-sorted: {times}"
    print(f"\nNewest change: {changes[0].get('title') if changes else 'none'}")


async def test_contracts_available(client) -> None:
    params = {"input_data": json.dumps({"list_info": {"start_index": 0, "row_count": 3}})}
    result = await client.get("/contracts", params=params)
    assert "error" not in result, result
    print(f"\nContracts (first 3): {[c.get('name') for c in result.get('contracts', [])]}")


async def test_contract_create_update_delete(client) -> None:
    """Contract write support — mandatory fields confirmed live (2026-07-20):
    name, custom_contract_id, type, vendor, from_date, to_date."""
    params = {"input_data": json.dumps({"list_info": {"start_index": 0, "row_count": 1}})}
    contracts = await client.get("/contracts", params=params)
    existing = contracts.get("contracts", [])
    if not existing:
        pytest.skip("No contracts on this instance to source a vendor id from")
    vendor_id = existing[0]["vendor"]["id"]

    created = await client.post("/contracts", {
        "contract": {
            "name": "[TEST] integration probe - safe to delete",
            "custom_contract_id": "MCP-TEST-0001",
            "type": {"name": "Software"},
            "vendor": {"id": vendor_id},
            "from_date": {"value": "1784550000000"},
            "to_date": {"value": "1816086000000"},
        }
    })
    assert "error" not in created, created.get("error")
    contract_id = created["contract"]["id"]
    try:
        updated = await client.put(
            f"/contracts/{contract_id}", {"contract": {"total_price": "500.00"}}
        )
        assert "error" not in updated, updated.get("error")
        assert updated["contract"]["total_price"] == "500.00"
    finally:
        cleanup = await client.delete(f"/contracts/{contract_id}")
        assert "error" not in cleanup, cleanup.get("error")


async def test_purchase_orders_available(client) -> None:
    params = {"input_data": json.dumps({"list_info": {"start_index": 0, "row_count": 3}})}
    result = await client.get("/purchase_orders", params=params)
    assert "error" not in result, result
    pos = result.get("purchase_orders", [])
    print(f"\nPurchase orders (first 3): {[p.get('custom_po_id') for p in pos]}")


async def test_purchase_order_create_update_delete(client) -> None:
    """PO write support — mandatory fields confirmed live (2026-08-01): name, custom_po_id,
    vendor, requested_by, items (each needs product, ordered_quantity, price, category)."""
    params = {"input_data": json.dumps({"list_info": {"start_index": 0, "row_count": 1}})}
    existing = await client.get("/purchase_orders", params=params)
    pos = existing.get("purchase_orders", [])
    if not pos:
        pytest.skip("No purchase orders on this instance to source a vendor/product from")
    sample = await client.get(f"/purchase_orders/{pos[0]['id']}")
    assert "error" not in sample, sample.get("error")
    po = sample["purchase_order"]
    vendor_id = po["vendor"]["id"]
    requested_by_id = po["requested_by"]["id"]
    product_id = po["items"][0]["product"]["id"]
    category_id = po["items"][0]["category"]["id"]

    created = await client.post("/purchase_orders", {
        "purchase_order": {
            "name": "[TEST] integration probe - safe to delete",
            "custom_po_id": "MCP-TEST-PO-0001",
            "vendor": {"id": vendor_id},
            "requested_by": {"id": requested_by_id},
            "items": [
                {
                    "product": {"id": product_id},
                    "ordered_quantity": "1.00",
                    "price": "1.00",
                    "category": {"id": category_id},
                }
            ],
        }
    })
    assert "error" not in created, created.get("error")
    po_id = created["purchase_order"]["id"]
    try:
        updated = await client.put(
            f"/purchase_orders/{po_id}", {"purchase_order": {"name": "[TEST] renamed"}}
        )
        assert "error" not in updated, updated.get("error")
        assert updated["purchase_order"]["name"] == "[TEST] renamed"
    finally:
        cleanup = await client.delete(f"/purchase_orders/{po_id}")
        assert "error" not in cleanup, cleanup.get("error")


async def test_assets_missing_product_type_filter_accepted(client) -> None:
    """SDP null-check convention: condition 'is' with empty values — must not 400."""
    list_info = {
        "row_count": 3,
        "search_criteria": [{"field": "product_type", "condition": "is", "values": []}],
    }
    result = await client.get(
        "/assets", params={"input_data": json.dumps({"list_info": list_info})}
    )
    assert "error" not in result, result
    print(f"\nAssets missing product_type: {len(result.get('assets', []))}")


async def test_request_attachment_list_and_download(client) -> None:
    """Find a request with an attachment, list it, download it, verify byte size matches."""
    list_info = {
        "start_index": 0, "row_count": 50,
        "sort_field": "created_time", "sort_order": "desc",
    }
    result = await client.get(
        "/requests", params={"input_data": json.dumps({"list_info": list_info})}
    )
    assert "error" not in result, result
    request_id = None
    attachment = None
    for req in result.get("requests", []):
        full = await client.get(f"/requests/{req['id']}")
        if "error" in full:
            continue
        atts = full.get("request", {}).get("attachments") or []
        if atts:
            request_id = req["id"]
            attachment = atts[0]
            break
    if request_id is None or attachment is None:
        pytest.skip("No request with an attachment found among the 50 most recent — "
                    "download path verified against docs only, not live")

    listed = await client.get(f"/requests/{request_id}/attachments")
    assert "error" not in listed, listed
    listed_att = next(a for a in listed["attachments"] if a["id"] == attachment["id"])
    expected_size = listed_att["size"]["value"]

    downloaded = await client.get_binary(
        f"/requests/{request_id}/attachments/{attachment['id']}/_download"
    )
    assert "error" not in downloaded, downloaded
    assert len(downloaded["content"]) == expected_size
    print(f"\nDownloaded {listed_att['name']} ({expected_size} bytes) from request {request_id}")


async def test_request_attachment_upload_roundtrip(client) -> None:
    """Upload a small file to a fresh request, list/verify, download+compare, then trash it."""
    request = {
        "subject": "MCP TEST — attachment upload probe, safe to delete",
        "description": "Safe to delete; created by automated attachment upload test.",
        "requester": {"name": "Chris Libby"},
        "category": {"name": "User Administration"},
        "subcategory": {"name": "Password Reset"},
    }
    created = await client.post("/requests", {"request": request})
    assert "error" not in created, created
    request_id = created["request"]["id"]

    try:
        content = b"MCP attachment upload roundtrip test content\n"
        uploaded = await client.put_multipart(
            f"/requests/{request_id}/upload",
            files={"input_file": ("roundtrip.txt", content, "text/plain")},
            params={"description": "roundtrip probe"},
        )
        assert "error" not in uploaded, uploaded
        attachment_id = uploaded["attachment"]["id"]
        assert uploaded["attachment"]["description"] == "roundtrip probe"

        listed = await client.get(f"/requests/{request_id}/attachments")
        assert "error" not in listed, listed
        listed_att = next(a for a in listed["attachments"] if a["id"] == attachment_id)
        assert listed_att["size"]["value"] == len(content)

        downloaded = await client.get_binary(
            f"/requests/{request_id}/attachments/{attachment_id}/_download"
        )
        assert "error" not in downloaded, downloaded
        assert downloaded["content"] == content
        print(f"\nUploaded and verified {listed_att['name']} on request {request_id}")
    finally:
        cleanup = await client.delete(f"/requests/{request_id}/move_to_trash")
        assert "error" not in cleanup, cleanup
        print(f"Trashed request {request_id}")


async def test_request_task_get_update_delete_roundtrip(client) -> None:
    """New Part 2 tools: get_request_task / update_request_task / delete_request_task."""
    request = {
        "subject": "MCP TEST — task crud probe, safe to delete",
        "description": "Safe to delete; created by automated task-crud roundtrip test.",
        "requester": {"name": "Chris Libby"},
        "category": {"name": "User Administration"},
        "subcategory": {"name": "Password Reset"},
    }
    created = await client.post("/requests", {"request": request})
    assert "error" not in created, created.get("error")
    request_id = created["request"]["id"]

    try:
        task = await client.post(
            f"/requests/{request_id}/tasks", {"task": {"title": "[TEST] task crud probe"}}
        )
        assert "error" not in task, task.get("error")
        task_id = task["task"]["id"]

        fetched = await client.get(f"/requests/{request_id}/tasks/{task_id}")
        assert "error" not in fetched, fetched.get("error")
        assert fetched["task"]["title"] == "[TEST] task crud probe"

        updated = await client.put(
            f"/requests/{request_id}/tasks/{task_id}",
            {
                "task": {
                    "title": "[TEST] task crud probe updated",
                    "description": "updated description",
                    "owner": {"name": "Chris Libby"},
                    "status": {"name": "Closed"},
                }
            },
        )
        assert "error" not in updated, updated.get("error")
        assert updated["task"]["title"] == "[TEST] task crud probe updated"
        assert updated["task"]["status"]["name"] == "Closed"

        deleted = await client.delete(f"/requests/{request_id}/tasks/{task_id}")
        assert "error" not in deleted, deleted.get("error")

        gone = await client.get(f"/requests/{request_id}/tasks/{task_id}")
        assert "error" in gone
    finally:
        await client.delete(f"/requests/{request_id}/move_to_trash")


async def test_problem_worklog_update_delete_roundtrip(client) -> None:
    """New Part 3 tools: update_problem_worklog / delete_problem_worklog."""
    if not TEST_TECHNICIAN_EMAIL:
        pytest.skip("SDP_TEST_TECHNICIAN_EMAIL not set in .env")
    params = {"input_data": json.dumps({"list_info": {"start_index": 0, "row_count": 1}})}
    problems = await client.get("/problems", params=params)
    plist = problems.get("problems", [])
    if not plist:
        pytest.skip("No problems on this instance to test against")
    problem_id = plist[0]["id"]

    worklog = await client.post(
        f"/problems/{problem_id}/worklogs",
        {
            "worklog": {
                "description": "[TEST] worklog edit/delete roundtrip - safe to delete",
                "time_spent": {"hours": 0, "minutes": 1},
                "owner": {"email_id": TEST_TECHNICIAN_EMAIL},
            }
        },
    )
    assert "error" not in worklog, worklog.get("error")
    worklog_id = worklog["worklog"]["id"]

    try:
        updated = await client.put(
            f"/problems/{problem_id}/worklogs/{worklog_id}",
            {"worklog": {"description": "[TEST] worklog edited"}},
        )
        assert "error" not in updated, updated.get("error")
        assert updated["worklog"]["description"] == "[TEST] worklog edited"
    finally:
        deleted = await client.delete(f"/problems/{problem_id}/worklogs/{worklog_id}")
        assert "error" not in deleted, deleted.get("error")


async def test_request_merge_roundtrip(client) -> None:
    """New tool: merge_requests. Merge B into A, verify B is gone (merged), trash A."""
    base_request = {
        "description": "Integration test - safe to close/delete",
        "requester": {"name": "Chris Libby"},
        "category": {"name": "User Administration"},
        "subcategory": {"name": "Password Reset"},
    }
    req_a = await client.post(
        "/requests",
        {"request": {**base_request, "subject": "[MCP TEST] merge probe A - safe to delete"}},
    )
    assert "error" not in req_a, req_a.get("error")
    parent_id = req_a["request"]["id"]

    req_b = await client.post(
        "/requests",
        {"request": {**base_request, "subject": "[MCP TEST] merge probe B - safe to delete"}},
    )
    assert "error" not in req_b, req_b.get("error")
    child_id = req_b["request"]["id"]

    try:
        merged = await client.put(
            f"/requests/{parent_id}/merge_requests",
            {"merge_requests": [{"id": child_id}]},
        )
        assert "error" not in merged, merged.get("error")

        gone = await client.get(f"/requests/{child_id}")
        assert "error" in gone, "merged child request should no longer be fetchable"
    finally:
        await client.delete(f"/requests/{parent_id}/move_to_trash")


async def test_request_summary_and_associations(client) -> None:
    """New tools: get_request_summary, associate_problem/dissociate_problem,
    associate_change/dissociate_change (both initiated and caused_by)."""
    req = await client.post(
        "/requests",
        {
            "request": {
                "subject": "[MCP TEST] summary/association probe - safe to delete",
                "description": "Integration test - safe to close/delete",
                "requester": {"name": "Chris Libby"},
                "category": {"name": "User Administration"},
                "subcategory": {"name": "Password Reset"},
            }
        },
    )
    assert "error" not in req, req.get("error")
    request_id = req["request"]["id"]

    try:
        summary = await client.get(f"/requests/{request_id}/summary")
        assert "error" not in summary, summary.get("error")
        assert "request_summary" in summary

        problems = await client.get(
            "/problems",
            params={"input_data": json.dumps({"list_info": {"start_index": 0, "row_count": 1}})},
        )
        plist = problems.get("problems", [])
        if plist:
            problem_id = plist[0]["id"]
            assoc = await client.post(
                f"/requests/{request_id}/problem",
                {"request_problem_association": {"problem": {"id": problem_id}}},
            )
            assert "error" not in assoc, assoc.get("error")
            check = await client.get(f"/requests/{request_id}")
            assert check["request"]["has_problem"] is True
            dissoc = await client.delete(
                f"/requests/{request_id}/problem",
                {"request_problem_association": {"problem": {"id": problem_id}}},
            )
            assert "error" not in dissoc, dissoc.get("error")
            check = await client.get(f"/requests/{request_id}")
            assert check["request"]["has_problem"] is False

        changes = await client.get(
            "/changes",
            params={"input_data": json.dumps({"list_info": {"start_index": 0, "row_count": 1}})},
        )
        clist = changes.get("changes", [])
        if clist:
            change_id = clist[0]["id"]
            assoc = await client.post(
                f"/requests/{request_id}/request_initiated_change",
                {"request_initiated_change": {"change": {"id": change_id}}},
            )
            assert "error" not in assoc, assoc.get("error")
            check = await client.get(f"/requests/{request_id}")
            assert check["request"]["has_request_initiated_change"] is True
            dissoc = await client.delete(
                f"/requests/{request_id}/request_initiated_change",
                {"request_initiated_change": {"change": {"id": change_id}}},
            )
            assert "error" not in dissoc, dissoc.get("error")
            check = await client.get(f"/requests/{request_id}")
            assert check["request"]["has_request_initiated_change"] is False

            assoc = await client.post(
                f"/requests/{request_id}/request_caused_by_change",
                {"request_caused_by_change": {"change": {"id": change_id}}},
            )
            assert "error" not in assoc, assoc.get("error")
            check = await client.get(f"/requests/{request_id}")
            assert check["request"]["has_request_caused_by_change"] is True
            dissoc = await client.delete(
                f"/requests/{request_id}/request_caused_by_change",
                {"request_caused_by_change": {"change": {"id": change_id}}},
            )
            assert "error" not in dissoc, dissoc.get("error")
            check = await client.get(f"/requests/{request_id}")
            assert check["request"]["has_request_caused_by_change"] is False
    finally:
        await client.delete(f"/requests/{request_id}/move_to_trash")


async def test_request_note_get_delete_roundtrip(client) -> None:
    """New Part 1 tools: get_request_note / delete_request_note."""
    request = {
        "subject": "MCP TEST — note get/delete probe, safe to delete",
        "description": "Safe to delete; created by automated note-crud roundtrip test.",
        "requester": {"name": "Chris Libby"},
        "category": {"name": "User Administration"},
        "subcategory": {"name": "Password Reset"},
    }
    created = await client.post("/requests", {"request": request})
    assert "error" not in created, created.get("error")
    request_id = created["request"]["id"]

    try:
        note = await client.post(
            f"/requests/{request_id}/notes",
            {"note": {"description": "[TEST] note get/delete probe", "show_to_requester": False}},
        )
        assert "error" not in note, note.get("error")
        note_id = note["note"]["id"]

        fetched = await client.get(f"/requests/{request_id}/notes/{note_id}")
        assert "error" not in fetched, fetched.get("error")
        assert fetched["note"]["id"] == note_id

        deleted = await client.delete(f"/requests/{request_id}/notes/{note_id}")
        assert "error" not in deleted, deleted.get("error")

        gone = await client.get(f"/requests/{request_id}/notes/{note_id}")
        assert "error" in gone
    finally:
        await client.delete(f"/requests/{request_id}/move_to_trash")


async def test_request_approval_roundtrip(client) -> None:
    """New tools: list_request_approval_levels, add_request_approval_level,
    list_request_approvals, add_request_approver (implicit via level create),
    send_request_approval_notification, approve_request.

    CAUTION: approver is the API key owner (Chris Libby) only — never point this at a
    real colleague, since send_request_approval_notification sends a real email."""
    if not TEST_TECHNICIAN_EMAIL:
        pytest.skip("SDP_TEST_TECHNICIAN_EMAIL not set in .env")
    req = await client.post(
        "/requests",
        {
            "request": {
                "subject": "MCP TEST — approvals probe, safe to delete",
                "description": "Integration test - safe to delete",
                "requester": {"name": "Chris Libby"},
                "category": {"name": "Security"},
                "subcategory": {"name": "Vulnerability Management"},
            }
        },
    )
    assert "error" not in req, req.get("error")
    request_id = req["request"]["id"]

    try:
        levels = await client.get(f"/requests/{request_id}/approval_levels")
        assert "error" not in levels, levels.get("error")
        assert levels["approval_levels"] == []

        approver = {"approver": {"email_id": TEST_TECHNICIAN_EMAIL}}
        created = await client.post(
            f"/requests/{request_id}/approval_levels",
            {"approval_level": {"approvals": [approver]}},
        )
        assert "error" not in created, created.get("error")
        level_id = created["approval_level"]["id"]
        approval_id = created["approval_level"]["approvals"][0]["id"]

        levels = await client.get(f"/requests/{request_id}/approval_levels")
        assert len(levels["approval_levels"]) == 1

        approvals = await client.get(f"/requests/{request_id}/approval_levels/{level_id}/approvals")
        assert "error" not in approvals, approvals.get("error")
        assert approvals["approvals"][0]["id"] == approval_id

        content = await client.get(
            f"/requests/{request_id}/approval_levels/{level_id}/approvals/get_notification_content"
        )
        assert "error" not in content, content.get("error")

        sent = await client.put(
            f"/requests/{request_id}/approval_levels/{level_id}/approvals/send_notification"
            f"?ids={approval_id}",
            {"approval": {"notification": content["notification"]}},
        )
        assert "error" not in sent, sent.get("error")

        approved = await client.put(
            f"/requests/{request_id}/approval_levels/{level_id}/approvals/{approval_id}/_approve",
            {"approval": {"comments": "MCP integration test self-approval"}},
        )
        assert "error" not in approved, approved.get("error")

        check = await client.get(
            f"/requests/{request_id}/approval_levels/{level_id}/approvals/{approval_id}"
        )
        assert check["approval"]["status"]["name"] == "Approved"
    finally:
        await client.delete(f"/requests/{request_id}/move_to_trash")
