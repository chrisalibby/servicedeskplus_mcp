# API Coverage — ServiceDesk Plus MCP

Maps the SDP On-Premise REST API v3 surface against the tools currently exposed by this MCP server.

Legend: ✅ covered · ❌ not covered · ⚠️ instance limitation (endpoint exists in API but returns errors on `sdp.example.com`)

---

## Requests

### Request record

| Operation | API endpoint | MCP tool |
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
| Get summary | `GET /requests/{id}/summary` | ❌ |
| Associate problem | `POST /requests/{id}/problem` | ❌ |
| Associate change | `POST /requests/{id}/request_initiated_change` | ❌ |
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
| Get task | ❌ |
| Update task | ❌ |
| Delete task | ❌ |
| Close / trigger task | ❌ |
| Task dependencies | ❌ |

### Worklogs

| Operation | MCP tool |
|---|---|
| Add worklog | ✅ `add_request_worklog` |
| List worklogs | ✅ `list_request_worklogs` |
| Get worklog | ❌ |
| Edit worklog | ❌ |
| Delete worklog | ❌ |

### Resolution

| Operation | MCP tool |
|---|---|
| Get resolution | ✅ `get_request_resolution` |
| Set / update resolution | ✅ `update_request_resolution` |

---

## Problems

### Problem record

| Operation | API endpoint | MCP tool |
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
| List / get / edit / delete | ❌ |

### Tasks & Worklogs

| Operation | MCP tool |
|---|---|
| All task operations | ❌ |
| All worklog operations | ❌ |

---

## Changes

### Change record

| Operation | API endpoint | MCP tool |
|---|---|---|
| List | `GET /changes` | ✅ `list_changes` |
| Get | `GET /changes/{id}` | ✅ `get_change` |
| Create | `POST /changes` | ✅ `create_change` |
| Update | `PUT /changes/{id}` | ✅ `update_change` |
| Close | `PUT /changes/{id}/close` | ✅ `close_change` (⚠️ requires correct workflow state) |
| Move to trash | `DELETE /changes/{id}/move_to_trash` | ❌ |
| Permanently delete | `DELETE /changes/{id}` | ❌ |
| Copy | `PUT /changes/{id}/copy` | ❌ |

### Notes

| Operation | MCP tool |
|---|---|
| Add note | ✅ `add_change_note` |
| List / get / edit / delete | ❌ |

### Tasks

| Operation | MCP tool |
|---|---|
| List tasks | ✅ `list_change_tasks` |
| Add / get / update / delete task | ❌ |
| Close / trigger task | ❌ |
| Task dependencies | ❌ |

### Worklogs

| Operation | MCP tool |
|---|---|
| All worklog operations | ❌ |

### Approvals

| Operation | MCP tool |
|---|---|
| List pending approvals | ✅ `list_pending_approvals` |
| Approve | ✅ `approve_change` |
| Reject | ✅ `reject_change` |
| Add / remove approvers | ❌ |
| Approval level CRUD | ❌ |

---

## Releases

> The Releases module has a full API surface (CRUD, notes, worklogs, tasks, approvals — same pattern as Changes). No MCP tools are currently implemented for this module.

| Category | MCP coverage |
|---|---|
| Release records | ❌ |
| Notes | ❌ |
| Tasks | ❌ |
| Worklogs | ❌ |
| Approvals | ❌ |

---

## Projects

> Projects have CRUD plus members, milestones, and tasks. No MCP tools are currently implemented.

| Category | MCP coverage |
|---|---|
| Project records | ❌ |
| Members | ❌ |
| Milestones | ❌ |
| Tasks | ❌ |

---

## Assets

### Asset record

| Operation | API endpoint | MCP tool |
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

| Operation | API endpoint | MCP tool |
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

| Operation | API endpoint | MCP tool |
|---|---|---|
| Search solutions | `GET /solutions?search_fields=...` | ✅ `search_solutions` |
| Get solution | `GET /solutions/{id}` | ✅ `get_solution` |
| Create solution | `POST /solutions` | ✅ `create_solution` |
| Update solution | `PUT /solutions/{id}` | ❌ |
| Delete solution | `DELETE /solutions/{id}` | ❌ |
| List topics | `GET /topics` | ✅ `list_solution_topics` |

---

## Contracts & Purchase Orders

> These modules are documented in the cloud API and follow the same v3 pattern. Neither is implemented in this MCP server. Availability on the Spero instance is unconfirmed.

| Module | MCP coverage |
|---|---|
| Contracts | ❌ |
| Purchase Orders | ❌ |

---

## Admin / Lookup data

| Resource | List | Get | Create / Update / Delete |
|---|---|---|---|
| Requesters | ✅ `list_requesters` | ✅ `get_requester` | ❌ |
| Technicians | ✅ `list_technicians` | ✅ `get_technician` | ❌ |
| Groups | ✅ `list_groups` | ❌ | ❌ |
| Sites | ✅ `list_sites` | ❌ | ❌ |
| Departments | ✅ `list_departments` | ❌ | ❌ |
| Categories | ✅ `list_categories` | ❌ | ❌ |
| Subcategories | ✅ `list_subcategories` | ❌ | ❌ |
| Items | ✅ `list_items` | ❌ | ❌ |
| Priorities | ✅ `list_priorities` | ❌ | ❌ |
| Statuses | ✅ `list_statuses` | ❌ | ❌ |
| Urgencies | ✅ `list_urgencies` | ❌ | ❌ |
| Announcements | ✅ `list_announcements` | ❌ | ❌ |

---

## Summary

| Module | Tools implemented | Notes |
|---|---|---|
| Requests | 16 | Core CRUD + notes, tasks, worklogs, resolution fully covered |
| Problems | 6 | Core CRUD only; no tasks, worklogs, or note management |
| Changes | 10 | Core CRUD + approvals; no tasks CRUD, worklogs, or note management |
| Releases | 0 | Not implemented |
| Projects | 0 | Not implemented |
| Assets | 6 | Core CRUD + workstations; no delete |
| CMDB | 5 | List/get covered; create/update/relationships blocked on this instance |
| Solutions | 4 | Read + create; no update/delete |
| Contracts | 0 | Not implemented; instance availability unconfirmed |
| Purchase Orders | 0 | Not implemented; instance availability unconfirmed |
| Admin / Lookup | 14 | List/get only; no user/group management |
| **Total** | **66** | |
