# API Coverage — ServiceDesk Plus MCP

Maps the SDP On-Premise REST API v3 surface against the tools currently exposed by this MCP server.

**Sources:** On-prem docs at `manageengine.com/products/service-desk/sdpop-v3-api/` (some sub-pages 404 — those modules were cross-referenced against the cloud docs, which share the same path structure minus the `/app/<portal>/` prefix).

Legend: ✅ covered · ❌ not covered · ⚠️ instance limitation (endpoint exists but returns errors on `sdp.example.com`) · 🔵 cloud-inferred (on-prem availability unconfirmed — needs live testing)

---

## Requests

### Request record

| Operation | Endpoint | MCP tool |
|---|---|---|
| List | `GET /requests` | ✅ `list_requests` |
| Get | `GET /requests/{id}` | ✅ `get_request` |
| Create | `POST /requests` | ✅ `create_request` |
| Update | `PUT /requests/{id}` | ✅ `update_request` |
| Close | `PUT /requests/{id}/close` | ✅ `close_request` |
| Assign | `PUT /requests/{id}/assign` | ✅ `assign_request` |
| Pick up (self-assign) | `PUT /requests/{id}/pickup` | ✅ `pickup_request` |
| Move to trash | `DELETE /requests/{id}/move_to_trash` | ✅ `delete_request` |
| Merge | `PUT /requests/{id}/merge_requests` | ❌ |
| Get summary (counts) | `GET /requests/{id}/summary` | ❌ |
| Associate problem | `POST /requests/{id}/problem` | ❌ |
| Associate initiated change | `POST /requests/{id}/request_initiated_change` | ❌ |
| Associate causative change | `POST /requests/{id}/request_caused_by_change` | ❌ |
| Associate project | `POST /requests/{id}/project` | ❌ |

### Notes

| Operation | MCP tool |
|---|---|
| Add note | ✅ `add_request_note` |
| List notes | ✅ `list_request_notes` |
| Get note | ❌ |
| Edit note | ❌ |
| Delete note | ❌ |

### Tasks

| Operation | MCP tool |
|---|---|
| List tasks | ✅ `list_request_tasks` |
| Add task | ✅ `add_request_task` |
| Get / update / delete task | ❌ |
| Close / trigger / assign task | ❌ |
| Task dependencies | ❌ |
| Task attachments (list, download, delete) | ❌ |
| Task worklogs | ❌ |

### Worklogs

| Operation | MCP tool |
|---|---|
| Add worklog | ✅ `add_request_worklog` |
| List worklogs | ✅ `list_request_worklogs` |
| Get / edit / delete worklog | ❌ |

### Resolution

| Operation | MCP tool |
|---|---|
| Get resolution | ✅ `get_request_resolution` |
| Set / update resolution | ✅ `update_request_resolution` |

### Approval levels & approvals

> Confirmed in on-prem docs. Currently not implemented.

| Operation | MCP tool |
|---|---|
| Add / list / get / delete approval level | ❌ |
| Add / list / get / remove approver | ❌ |
| Approve / reject | ❌ |
| Send approval notification | ❌ |

### Drafts (email drafts)

> Confirmed in on-prem docs. Currently not implemented.

| Operation | MCP tool |
|---|---|
| Save / list / get / delete draft | ❌ |

### Attachments

| Operation | MCP tool |
|---|---|
| Upload attachment (`POST /requests/{id}/attachments`) | ❌ |

---

## Problems

### Problem record

| Operation | Endpoint | MCP tool |
|---|---|---|
| List | `GET /problems` | ✅ `list_problems` |
| Get | `GET /problems/{id}` | ✅ `get_problem` |
| Create | `POST /problems` | ✅ `create_problem` |
| Update | `PUT /problems/{id}` | ✅ `update_problem` |
| Close | `PUT /problems/{id}/close` | ✅ `close_problem` |
| Delete | `DELETE /problems/{id}` | ❌ |

### Notes

| Operation | MCP tool |
|---|---|
| Add note | ✅ `add_problem_note` |
| List / get / edit / delete note | ❌ |

### Tasks

| Operation | MCP tool |
|---|---|
| All task operations | ❌ |
| Task worklogs | ❌ |

### Worklogs

| Operation | MCP tool |
|---|---|
| All worklog operations (🔵 cloud-inferred) | ❌ |

### Approval levels & approvals

> Confirmed in cloud docs at full parity with Changes.

| Operation | MCP tool |
|---|---|
| Add / list / get / delete approval level | ❌ |
| Add / list / get / remove approver | ❌ |

---

## Changes

### Change record

| Operation | Endpoint | MCP tool |
|---|---|---|
| List | `GET /changes` | ✅ `list_changes` |
| Get | `GET /changes/{id}` | ✅ `get_change` |
| Create | `POST /changes` | ✅ `create_change` |
| Update | `PUT /changes/{id}` | ✅ `update_change` |
| Close | `PUT /changes/{id}/close` | ✅ `close_change` (⚠️ requires correct workflow state) |
| Copy | `PUT /changes/{id}/copy` | ❌ |
| Move to trash | `DELETE /changes/{id}/move_to_trash` | ❌ |
| Restore from trash | `PUT /changes/{id}/restore_from_trash` | ❌ |
| Permanently delete | `DELETE /changes/{id}` | ❌ |
| Pick up / bulk assign | `PUT /changes/pickup` | ❌ |

### Notes

| Operation | MCP tool |
|---|---|
| Add note | ✅ `add_change_note` |
| List / get / edit / delete note | ❌ |

### Tasks

| Operation | MCP tool |
|---|---|
| List tasks | ✅ `list_change_tasks` |
| Add / get / update / delete task | ❌ |
| Close / trigger / assign task | ❌ |
| Task dependencies | ❌ |
| Task attachments | ❌ |
| Task worklogs (🔵 cloud-inferred) | ❌ |

### Worklogs

> Likely exists on on-prem (same pattern as Releases which is confirmed); on-prem doc page 404s.

| Operation | MCP tool |
|---|---|
| All worklog operations | ❌ |

### Approval levels & approvals

| Operation | MCP tool |
|---|---|
| List pending approvals | ✅ `list_pending_approvals` |
| Approve | ✅ `approve_change` |
| Reject | ✅ `reject_change` |
| Add / remove approvers | ❌ |
| Approval level CRUD | ❌ |
| Send approval notification | ❌ |

---

## Releases

> Confirmed in on-prem docs at full parity with Changes. No MCP tools implemented.

### Release record

| Operation | Endpoint | MCP tool |
|---|---|---|
| List | `GET /releases` | ❌ |
| Get | `GET /releases/{id}` | ❌ |
| Create | `POST /releases` | ❌ |
| Update | `PUT /releases/{id}` | ❌ |
| Close | `PUT /releases/{id}/_close` | ❌ |
| Trash / restore / delete | various | ❌ |
| Get summary / history / permissions | various | ❌ |

### Sub-resources

| Resource | MCP tool |
|---|---|
| Notes (CRUD) | ❌ |
| Tasks (CRUD + state actions + dependencies + attachments) | ❌ |
| Worklogs (CRUD + time summary) | ❌ |
| Approval levels + approvals | ❌ |

---

## Projects

> Confirmed in on-prem docs. No MCP tools implemented.

| Resource | Operations | MCP tool |
|---|---|---|
| Project record | CRUD | ❌ |
| Members | Add / list / update / delete | ❌ |
| Milestones | CRUD + attachments | ❌ |
| Tasks | CRUD + state actions + dependencies + attachments | ❌ |
| Task worklogs (🔵 cloud-inferred) | CRUD | ❌ |
| Comments on projects / milestones / tasks (🔵 cloud-inferred) | CRUD | ❌ |

---

## Assets

### Asset record

| Operation | Endpoint | MCP tool |
|---|---|---|
| List | `GET /assets` | ✅ `list_assets` |
| Get | `GET /assets/{id}` | ✅ `get_asset` |
| Create | `POST /assets` | ✅ `create_asset` |
| Update | `PUT /assets/{id}` | ✅ `update_asset` |
| Delete | `DELETE /assets/{id}` | ❌ |
| List workstations | `GET /workstations` | ✅ `list_workstations` |
| Get workstation | `GET /workstations/{id}` | ✅ `get_workstation` |

---

## CMDB

| Operation | Endpoint | MCP tool |
|---|---|---|
| List CIs | `GET /cmdb` | ✅ `list_configuration_items` |
| Get CI | `GET /cmdb/{type}/{id}` | ✅ `get_configuration_item` |
| Create CI | `POST /cmdb/{type}` | ⚠️ `create_configuration_item` (404 on this instance) |
| Update CI | `PUT /cmdb/{type}/{id}` | ⚠️ `update_configuration_item` (404 on this instance) |
| Delete CI | `DELETE /cmdb/{type}` | ❌ |
| List relationships | `GET /cmdb/{type}/{id}/ci_relationships` | ✅ `list_ci_relationships` |
| Add relationship | `POST /cmdb/{type}/{id}/ci_relationships` | ⚠️ `add_ci_relationship` (404 on this instance) |
| Delete relationship | `DELETE /cmdb/{type}/{id}/ci_relationships/{id}` | ❌ |

---

## Solutions / Knowledge Base

| Operation | Endpoint | MCP tool |
|---|---|---|
| Search | `GET /solutions?search_fields=...` | ✅ `search_solutions` |
| Get | `GET /solutions/{id}` | ✅ `get_solution` |
| Create | `POST /solutions` | ✅ `create_solution` |
| Update | `PUT /solutions/{id}` | ❌ |
| Delete | `DELETE /solutions/{id}` | ❌ |
| Approve / reject / publish (🔵 cloud-inferred) | `PUT /solutions/{id}/_approve` etc. | ❌ |
| Like / dislike (🔵 cloud-inferred) | `PUT /solutions/{id}/_like` etc. | ❌ |
| List topics | `GET /topics` | ✅ `list_solution_topics` |
| Topic CRUD | various | ❌ |
| Upload attachment | `POST /solutions/{id}/attachments` | ❌ |

---

## Admin / Lookup data

### User management

| Resource | List | Get | Create / Update / Delete |
|---|---|---|---|
| Requesters | ✅ `list_requesters` | ✅ `get_requester` | ❌ |
| Technicians | ✅ `list_technicians` | ✅ `get_technician` | ❌ |
| Users (convert to technician) | — | — | ❌ |

### Reference data (list-only in practice)

| Resource | List | Get | Notes |
|---|---|---|---|
| Groups | ✅ `list_groups` | ❌ | ⚠️ returns empty on this instance |
| Sites | ✅ `list_sites` | ❌ | |
| Departments | ✅ `list_departments` | ❌ | |
| Categories | ✅ `list_categories` | ❌ | |
| Subcategories | ✅ `list_subcategories` | ❌ | |
| Items | ✅ `list_items` | ❌ | |
| Priorities | ✅ `list_priorities` | ❌ | |
| Statuses | ✅ `list_statuses` | ❌ | |
| Urgencies | ✅ `list_urgencies` | ❌ | |
| Announcements | ✅ `list_announcements` | ❌ | |
| Closure codes (🔵 cloud-inferred) | ❌ | ❌ | `/api/v3/closure_codes` |
| Change types (🔵 cloud-inferred) | ❌ | ❌ | `/api/v3/change_types` |
| Change risks (🔵 cloud-inferred) | ❌ | ❌ | `/api/v3/change_risks` |
| Products | ✅ `list_products` | ❌ | confirmed live; supports name / product_type filters |
| Product types | ✅ `list_product_types` | ❌ | `/api/v3/product_types`, confirmed live |

**Not available via API (admin-UI-only in both on-prem and cloud):** roles, shifts, holidays, email settings, SLA/OLA configuration, business rules, custom field definitions, reports, surveys.

---

## Modules with no API surface

These features exist in ServiceDesk Plus but are **not exposed through the REST API v3** in either on-prem or cloud documentation:

- Reports
- SLA / OLA definitions
- Business rules
- Roles
- Shift / holiday calendars
- Email settings
- Satisfaction surveys
- Service catalog / request templates

---

## Cloud-only or unconfirmed modules

These endpoints exist in the cloud API and share the same path structure. Availability on the Spero instance is unconfirmed and requires live testing.

| Module | Endpoint root | Notes |
|---|---|---|
| Announcements | `/api/v3/announcements` | CRUD + follow/unfollow + attachments |
| Checklists | `/api/v3/requests/{id}/checklists` | Per-request; also `/checklist_templates` |
| Request Maintenance | `/api/v3/request_maintenances` | Recurring request automation |
| Change Maintenance | `/api/v3/change_maintenances` | Recurring change automation |
| Technician unavailability | `/api/v3/unavailability` | Mark technician as absent |
| Delegation | `/api/v3/delegation_action` | Work delegation |
| Space management | `/api/v3/space_campuses` + buildings, floors, rooms | Physical location hierarchy |
| Custom modules | `/api/v3/{custom_module_api_name}` | Dynamic — requires knowing the api_plural_name |
| Archive requests | `/api/v3/archive_requests/{id}` | DELETE only |

---

## Contracts & Purchase Orders

> Both endpoints confirmed live on the Spero instance (2026-07-17). Read-only coverage this round.

| Module | MCP coverage |
|---|---|
| Contracts | ✅ `list_contracts`, `get_contract` |
| Purchase Orders | ✅ `list_purchase_orders`, `get_purchase_order` |

---

## Summary

| Module | Tools | Notes |
|---|---|---|
| Requests | 16 | Core CRUD + notes, tasks (add/list), worklogs (add/list), resolution fully covered. Approvals, drafts, attachments, associations not implemented. |
| Problems | 6 | Core CRUD only. No approvals, tasks, worklogs, or note management. |
| Changes | 10 | Core CRUD + list/approve/reject approvals. No task CRUD, worklogs, note management, or approval level management. |
| Releases | 0 | Not implemented. Confirmed in on-prem docs. |
| Projects | 0 | Not implemented. Confirmed in on-prem docs. |
| Assets | 6 | Core CRUD + workstations. No delete. |
| CMDB | 5 | List/get covered. Create/update/relationships blocked on this instance. |
| Solutions | 4 | Read + create. No update/delete or approval workflow. |
| Contracts | 2 | List/get only (read-only this round). |
| Purchase Orders | 2 | List/get only (read-only this round). |
| Admin / Lookup | 16 | List/get only. Includes products + product types. No user/group management. Several lookup types (closure codes, change types, etc.) not implemented. |
| **Total** | **72** | |
