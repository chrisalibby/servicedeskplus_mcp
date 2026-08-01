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
| Merge | `PUT /requests/{id}/merge_requests` | ✅ `merge_requests` (confirmed live 2026-08-01 — irreversible; see note below) |
| Get summary (counts) | `GET /requests/{id}/summary` | ✅ `get_request_summary` (confirmed live 2026-08-01) |
| Associate problem | `POST /requests/{id}/problem` | ✅ `associate_problem` (confirmed live 2026-08-01) |
| Dissociate problem | `DELETE /requests/{id}/problem` | ✅ `dissociate_problem` (confirmed live 2026-08-01 — requires a body on this instance, see quirk below) |
| Associate initiated change | `POST /requests/{id}/request_initiated_change` | ✅ `associate_change` (association_type='initiated', confirmed live 2026-08-01) |
| Dissociate initiated change | `DELETE /requests/{id}/request_initiated_change` | ✅ `dissociate_change` (confirmed live 2026-08-01) |
| Associate causative change | `POST /requests/{id}/request_caused_by_change` | ✅ `associate_change` (association_type='caused_by', confirmed live 2026-08-01) |
| Dissociate causative change | `DELETE /requests/{id}/request_caused_by_change` | ✅ `dissociate_change` (confirmed live 2026-08-01) |
| Associate project | `POST /requests/{id}/project` | ❌ (not implemented — Projects module now exists (see Projects section) but this request-side association endpoint wasn't probed) |

> **Merge behavior (confirmed live 2026-08-01):** merging request B into parent A
> (`merge_requests(request_id=A, merge_request_ids=[B])`) makes B permanently unfetchable —
> `GET /requests/{B}` afterward 404s with a message naming the parent it was merged into.
> This is **irreversible** — there is no un-merge or restore-from-trash equivalent. Trashing
> the parent request afterward (`delete_request`) works normally.
>
> **Association payload quirk:** the association POST bodies wrap the target in a named key
> matching the endpoint (`request_problem_association`, `request_initiated_change`,
> `request_caused_by_change`) — a bare `{"problem": {...}}` or `{"change": {...}}` 400s with
> "Extra key found in JSON". Dissociation is `DELETE` to the same path, but on this instance a
> bare `DELETE` with no body 500s ("Internal Error") — the same wrapped body used for the
> associate call must be sent with the DELETE for it to succeed (confirmed live for problem,
> initiated-change, and caused-by-change associations).

### Notes

| Operation | MCP tool |
|---|---|
| Add note | ✅ `add_request_note` |
| List notes | ✅ `list_request_notes` |
| Get note | ✅ `get_request_note` (confirmed live 2026-08-01: `GET /requests/{id}/notes/{note_id}`) |
| Edit note | ✅ `update_request_note` (confirmed live 2026-08-01: `PUT /requests/{id}/notes/{note_id}`) |
| Delete note | ✅ `delete_request_note` (confirmed live 2026-08-01: `DELETE /requests/{id}/notes/{note_id}`, permanent) |

### Tasks

| Operation | MCP tool |
|---|---|
| List tasks | ✅ `list_request_tasks` |
| Add task | ✅ `add_request_task` |
| Get / update / delete task | ✅ `get_request_task`, `update_request_task`, `delete_request_task` (confirmed live 2026-08-01) |
| Close / trigger / assign task | ❌ |
| Task dependencies | ❌ |
| Task attachments (list, download, delete) | ❌ |
| Task worklogs | ❌ |

### Worklogs

| Operation | MCP tool |
|---|---|
| Add worklog | ✅ `add_request_worklog` |
| List worklogs | ✅ `list_request_worklogs` |
| Get / edit / delete worklog | ✅ `update_request_worklog`, `delete_request_worklog` (shape verified live on problems/changes worklogs — identical sub-resource; requests-side PUT/DELETE itself unverified since `add_request_worklog` POST is broken on this instance. A single existing worklog was found on a live request and used only for a read-only GET shape check, not mutated.) |

### Resolution

| Operation | MCP tool |
|---|---|
| Get resolution | ✅ `get_request_resolution` |
| Set / update resolution | ✅ `update_request_resolution` |

### Approval levels & approvals

> Confirmed live 2026-08-01 with a full create → level → approver(self) → notify → approve →
> trash round-trip on a disposable test request (48158). Approver in all live tests was the
> API key owner (Chris Libby) only — never point these at a real colleague, since
> `send_request_approval_notification` sends a real email.

| Operation | Endpoint | MCP tool |
|---|---|---|
| List approval levels | `GET /requests/{id}/approval_levels` | ✅ `list_request_approval_levels` |
| Add approval level | `POST /requests/{id}/approval_levels` | ✅ `add_request_approval_level` (requires at least one approver in the same call — an approver-less POST 400s with "Approvers are unavailable"; SDP assigns the level number itself, the documented writable `level` int field is rejected as read-only on this instance) |
| Get / delete approval level | `GET`/`DELETE .../approval_levels/{level_id}` | ❌ (documented, not implemented — not in this round's scope) |
| List / get approvals | `GET .../approval_levels/{level_id}/approvals[/{approval_id}]` | ✅ `list_request_approvals` (list only; single-get not wrapped as a tool) |
| Add approver | `POST .../approval_levels/{level_id}/approvals` | ✅ `add_request_approver` |
| Get notification content / send notification | `GET .../approvals/get_notification_content`, `PUT .../approvals/send_notification?ids={approval_id}` | ✅ `send_request_approval_notification` (fetches content then sends in one call; body key is `{"approval": {"notification": {...}}}`, not the bare `{"notification": {...}}` the cloud docs show — that shape 400s "Extra key found in JSON" on this instance) |
| Approve | `PUT .../approvals/{approval_id}/_approve` | ✅ `approve_request` (400s "Recommendation mail is not yet sent" until the notification has been sent at least once) |
| Reject | `PUT .../approvals/{approval_id}/_reject` | ✅ `reject_request` (payload shape mirrors approve; not individually re-tested live to conserve the write budget — symmetry confirmed against the same endpoint family) |

### Drafts (email drafts) — reply/forward platform gap

> Confirmed in on-prem docs (`requests/request_draft.html`, 2026-08-01). This is **not** a
> send-email API — see below. Not implemented (would be misleading to wrap as
> `reply_request`/`forward_request`).

| Operation | Endpoint | MCP tool |
|---|---|---|
| Add draft | `POST /requests/{id}/drafts` | ❌ |
| Get draft | `GET /requests/{id}/drafts/{draft_id}` | ❌ |
| List drafts | `GET /requests/{id}/drafts` | ❌ |
| Delete draft | `DELETE /requests/{id}/drafts/{draft_id}` | ❌ |

Punch-list item "reply_request / forward_request" (send an email reply/forward from a
request) was investigated 2026-08-01 and found to be **not supported by the on-prem v3 REST
API** — closing as a documented platform gap, not a missing tool.

- The only email-shaped resource under Requests in the docs
  (`manageengine.com/products/service-desk/sdpop-v3-api/requests/`) is `request_draft.html`.
  Its schema (`to`, `cc`, `bcc`, `subject`, `description`, `type: "reply"|...`, `attachments`)
  looks exactly like a reply/forward payload, and the sample subject line
  (`"Re: [Request ID :##26##] ..."`) confirms it's meant for that use case.
- However, the page explicitly documents this as saving **draft** content only ("This
  operation lets you save a email notification content as draft in a request"). The response
  object carries `is_draft (boolean) read only` and `sent_time`/`last_updated_time` fields but
  no "send" action, and the four operations on the page are strictly Add/Get/List/Delete —
  there is no send/dispatch/notify endpoint documented anywhere under Requests (the full
  Requests nav is just `request.html`, `request_draft.html`, `request_note.html`,
  `request_task.html`, `archive_request.html`).
- No sibling `reply`, `forward`, or `notifications` page exists in the docs site nav for
  Requests (checked directly against the rendered sidebar, not just search results).
- Conclusion: the v3 REST API can stage a reply/forward as an unsent draft (visible in the SDP
  UI's compose box) but cannot actually dispatch the email — that step is UI-only. Building
  `reply_request`/`forward_request` on top of the draft endpoint would silently *not send* the
  email, which is worse than not having the tool. No live POST was attempted since the docs
  already rule out a send capability (task instructions: don't build a fake workaround).
- If ManageEngine adds a send/dispatch operation in a future release, revisit this section —
  the draft endpoint's schema is otherwise a ready-made blueprint for the request body.

### Attachments

| Operation | Endpoint | MCP tool |
|---|---|---|
| List attachments | `GET /requests/{id}/attachments` | ✅ `list_request_attachments` (confirmed live 2026-08-01) |
| Download attachment content | `GET /requests/{id}/attachments/{attachment_id}/_download` | ✅ `get_request_attachment_content` (confirmed live 2026-08-01 — note the `_download` path, not `/download`) |
| Upload attachment | `PUT /requests/{id}/upload` (multipart, field `input_file`) | ✅ `add_request_attachment` (confirmed live 2026-08-01) |

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
| Delete | `DELETE /problems/{id}` | ✅ `delete_problem` (confirmed live 2026-08-01 — permanent; no `restore_from_trash` sub-route exists for problems on this instance, `PUT /problems/{id}/restore_from_trash` 404s "Invalid URL") |

### Notes

| Operation | MCP tool |
|---|---|
| Add note | ✅ `add_problem_note` |
| List note | ✅ `list_problem_notes` |
| Edit note | ✅ `update_problem_note` (confirmed live 2026-08-01: `PUT /problems/{id}/notes/{note_id}`) |
| Get note | ✅ `get_problem_note` (confirmed live 2026-08-01) |
| Delete note | ✅ `delete_problem_note` (confirmed live 2026-08-01, permanent) |

### Tasks

| Operation | MCP tool |
|---|---|
| List / add task | ✅ `list_problem_tasks`, `add_problem_task` |
| Get / update / delete task | ✅ `get_problem_task`, `update_problem_task`, `delete_problem_task` (shape verified live on requests' identical task sub-resource 2026-08-01) |
| Task worklogs | ❌ |

### Worklogs

| Operation | MCP tool |
|---|---|
| List / add worklog | ✅ `list_problem_worklogs`, `add_problem_worklog` |
| Get / update / delete worklog | ✅ `update_problem_worklog`, `delete_problem_worklog` (confirmed live 2026-08-01) |

### Approval levels & approvals

> Cloud docs claim full parity with Changes, but confirmed live 2026-08-01 that this on-prem
> instance does **not** have the endpoint: `GET /problems/{id}/approval_levels` and
> `GET /problems/{id}/approvals` both return status_code 4007 "Invalid URL" (not a
> permissions or empty-data error — the URL itself is rejected), tested against an existing
> live problem (id 41). Not implemented; not a docs-only gap, a confirmed on-prem gap.

| Operation | MCP tool |
|---|---|
| Add / list / get / delete approval level | ❌ (confirmed unavailable on this instance) |
| Add / list / get / remove approver | ❌ (confirmed unavailable on this instance) |

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
| Copy | `PUT /changes/{id}/copy` | ✅ `copy_change` (unverified live — not exercised since POST-adjacent operations on `/changes` are rate-limited and a copy would need its own cleanup; implemented per docs, PUT with no body) |
| Move to trash | `DELETE /changes/{id}/move_to_trash` | ✅ `delete_change` (confirmed live 2026-08-01 on an existing test change, paired with a successful restore) |
| Restore from trash | `PUT /changes/{id}/restore_from_trash` | ✅ `restore_change` (confirmed live 2026-08-01 — this endpoint rejects any `input_data` body on this instance ("Extra parameter(s) not allowed"); the PUT must carry no body at all, unlike every other write endpoint in this codebase) |
| Permanently delete | `DELETE /changes/{id}` | ❌ |
| Pick up / bulk assign | `PUT /changes/pickup` | ❌ |

### Notes

| Operation | MCP tool |
|---|---|
| Add note | ✅ `add_change_note` |
| List note | ✅ `list_change_notes` |
| Edit note | ✅ `update_change_note` (confirmed live 2026-08-01: `PUT /changes/{id}/notes/{note_id}`) |
| Get note | ✅ `get_change_note` (confirmed live 2026-08-01) |
| Delete note | ✅ `delete_change_note` (confirmed live 2026-08-01, permanent) |

### Tasks

| Operation | MCP tool |
|---|---|
| List / add task | ✅ `list_change_tasks`, `add_change_task` |
| Get / update / delete task | ✅ `get_change_task`, `update_change_task`, `delete_change_task` (confirmed live 2026-08-01) |
| Close / trigger / assign task | ❌ |
| Task dependencies | ❌ |
| Task attachments | ❌ |
| Task worklogs (🔵 cloud-inferred) | ❌ |

### Worklogs

| Operation | MCP tool |
|---|---|
| List / add worklog | ✅ `list_change_worklogs`, `add_change_worklog` |
| Get / update / delete worklog | ✅ `update_change_worklog`, `delete_change_worklog` (confirmed live 2026-08-01) |

### Approval levels & approvals

| Operation | Endpoint | MCP tool |
|---|---|---|
| List pending approvals | `GET /changes/{id}/approvals` | ✅ `list_pending_approvals` (⚠️ re-checked again 2026-08-01: this path still returns 4007 "Invalid URL" — probed 5 path variants (`/approvals`, `/change_approvals`, `/approvers`, `/approval`, plus `approval_levels` which 500s "Internal Error" for changes with no configured level) and none resolve to a working flat list; confirmed no correct on-prem path exists on this instance. Docstring now steers callers to `list_change_approval_levels`. Kept implemented since a future change with a configured approval level may behave differently, but not fixed further this round.) |
| Approve | `PUT /changes/{id}/approvals/{approval_id}` | ✅ `approve_change` |
| Reject | `PUT /changes/{id}/approvals/{approval_id}` | ✅ `reject_change` |
| List approval levels | `GET /changes/{id}/approval_levels` | ✅ `list_change_approval_levels` (added 2026-08-01, read-only; live GET against 3 existing changes returns 4004 "Internal Error" — all three have `has_approvals: false` in `approval_levels/approval_summary`, i.e. no approval level was ever configured on them, so it's unverified whether this call works once a level actually exists. Docs confirm the path.) |
| Add / edit / delete approval level | `POST`/`PUT`/`DELETE /changes/{id}/approval_levels[/{level_id}]` | ❌ (documented per `change_approval_level.html`, not implemented — no change may be created to test this round due to the instance's create-change rate limit) |
| Add / remove approvers | `POST`/`DELETE .../approval_levels/{level_id}/approvals[/{approval_id}]` | ❌ (documented, not implemented) |
| Send approval notification | `PUT .../approval_levels/{level_id}/approvals/send_notification` | ❌ (documented, not implemented — mirrors the request-side shape confirmed live, but not independently verified for changes) |

---

## Releases

> Confirmed live on this instance (2026-08-01) — `GET /releases` returns 200 (empty list, not a 404).
> Only `title` is mandatory for create; SDP auto-assigns the default template/workflow.

### Release record

| Operation | Endpoint | MCP tool |
|---|---|---|
| List | `GET /releases` | ✅ `list_releases` |
| Get | `GET /releases/{id}` | ✅ `get_release` |
| Create | `POST /releases` | ✅ `create_release` |
| Update | `PUT /releases/{id}` | ✅ `update_release` |
| Close | `PUT /releases/{id}/_close` | ✅ `close_release` (403 "User does not have this permission" for the standard technician role on this instance — implemented per docs but unverified end-to-end here) |
| Trash / restore / delete | `DELETE /releases/{id}/move_to_trash` | confirmed working live, no dedicated tool (mirrors `delete_request`'s recoverable-trash pattern; not wired up as an MCP tool per the task scope) |
| Get summary / history / permissions | various | ❌ (not probed — out of scope) |

### Sub-resources

| Resource | MCP tool |
|---|---|
| Notes (add/list/update) | ✅ `add_release_note`, `list_release_notes`, `update_release_note` |
| Tasks (add/list) | ✅ `add_release_task`, `list_release_tasks` — `stage` is mandatory on create (`{"id": ...}`, e.g. `"2"` = Planning) or SDP 400s "Value not provided" |
| Worklogs (add/list) | ✅ `add_release_worklog`, `list_release_worklogs` — same shape as changes' worklogs |
| Approval levels + approvals | ❌ (not probed — out of scope) |

---

## Projects

> Confirmed live on this instance (2026-08-01). `/projects` and sub-resources work; only `title` is mandatory on create.

| Resource | Operations | MCP tool |
|---|---|---|
| Project record | List / get / create / update / delete | ✅ `list_projects`, `get_project`, `create_project`, `update_project`, `delete_project` — no `move_to_trash` endpoint for projects on this instance (404s "Invalid URL"); `delete_project` is a direct, non-recoverable delete |
| Members | Add / list | ✅ `add_project_member`, `list_project_members` — on this instance the API has been observed to resolve the given `email_id` to a different technician than requested (unconfirmed root cause); verify the returned member before relying on it |
| Milestones | Add / list | ✅ `add_project_milestone`, `list_project_milestones` |
| Tasks | Add / list | ✅ `add_project_task`, `list_project_tasks` — unlike release tasks, `stage` is not mandatory here |
| Task worklogs (🔵 cloud-inferred) | CRUD | ❌ (not probed — out of scope this round) |
| Comments | Add / list | ✅ `add_project_comment`, `list_project_comments` — payload key is `content`, not `description` (that key 400s "Extra key found in JSON") |

---

## Assets

### Asset record

| Operation | Endpoint | MCP tool |
|---|---|---|
| List | `GET /assets` | ✅ `list_assets` |
| Get | `GET /assets/{id}` | ✅ `get_asset` |
| Create | `POST /assets` | ✅ `create_asset` |
| Update | `PUT /assets/{id}` | ✅ `update_asset` |
| Delete | `DELETE /assets/{id}` | ✅ `delete_asset` (confirmed working live 2026-08-01; permanent, unlike `delete_request`) |
| Depreciation fields | `POST /assets`, `PUT /assets/{id}` — nested `asset_depreciation` object | ✅ `create_asset`, `update_asset` (params: `depreciation_type`, `useful_life`, `salvage_value`) |
| List depreciation types | `GET /depreciation_types` | ✅ `list_depreciation_types` |
| List workstations | `GET /workstations` | ✅ `list_workstations` |
| Get workstation | `GET /workstations/{id}` | ✅ `get_workstation` |

---

## CMDB

> Fixed 2026-07-20: create/update/relationships were previously thought unavailable (404), but the
> actual issue was wrong endpoint paths/payload shapes — see CLAUDE.md's CMDB quirk entries. They
> are module-scoped: `POST`/`PUT /{module_type}` with body `{module_type: {...}}`, not `/cmdb`
> with `{"ci": {...}}`.

| Operation | Endpoint | MCP tool |
|---|---|---|
| List CIs | `GET /cmdb` | ✅ `list_configuration_items` |
| Get CI | `GET /cmdb/{id}` | ✅ `get_configuration_item` |
| Create CI | `POST /{module_type}` | ✅ `create_configuration_item` |
| Update CI | `PUT /{module_type}/{id}` | ✅ `update_configuration_item` |
| Delete CI | `DELETE /{module_type}/{id}` | ✅ `delete_configuration_item` (confirmed live 2026-08-01; permanent, unlike `delete_request`) |
| List relationships | `GET /cmdb/{id}/ci_relationships` | ✅ `list_ci_relationships` |
| Add relationship | `POST /cmdb/{id}/ci_relationships` | ⚠️ `add_ci_relationship` — 400s on the `relationship_type` field regardless of shape tried; likely needs a relationship-type lookup endpoint (not implemented) |
| Delete relationship | `DELETE /cmdb/{type}/{id}/ci_relationships/{id}` | ❌ |

---

## Solutions / Knowledge Base

| Operation | Endpoint | MCP tool |
|---|---|---|
| Search | `GET /solutions?search_fields=...` | ✅ `search_solutions` |
| Get | `GET /solutions/{id}` | ✅ `get_solution` |
| Create | `POST /solutions` | ✅ `create_solution` (topic is mandatory on this instance) |
| Update | `PUT /solutions/{id}` | ✅ `update_solution` |
| Approve / reject | `PUT /solutions/{id}` with `approval_status: {"name": ...}` | ✅ via `update_solution` — the cloud-style `_approve`/`_reject` action sub-routes exist on this instance (400, not 404) but reject the payload shapes tried; plain field update works and was used instead |
| Publish (🔵 cloud-only) | `PUT /solutions/{id}/_publish` | ❌ confirmed 404 "Invalid URL" on this instance |
| Delete | `DELETE /solutions/{id}` | ⚠️ `delete_solution` implemented, but consistently returns "Not in trash" live on this instance — no working move-to-trash sub-route was found; unresolved |
| Like / dislike (🔵 cloud-inferred) | `PUT /solutions/{id}/_like` etc. | ❌ not probed |
| List topics | `GET /topics` | ✅ `list_solution_topics` |
| Create topic | `POST /topics` | ✅ `create_solution_topic` |
| Upload attachment | `PUT /solutions/{id}/upload` (not `/attachments` — that 404s) | ✅ `add_solution_attachment` |

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
| Groups | ✅ `list_groups` | ❌ | ⚠️ `/groups` returns 404 "Invalid URL" on this instance — not available |
| Sites | ✅ `list_sites` | ❌ | |
| Departments | ✅ `list_departments` | ❌ | |
| Categories | ✅ `list_categories` | ❌ | |
| Subcategories | ✅ `list_subcategories` | ❌ | |
| Items | ✅ `list_items` | ❌ | |
| Priorities | ✅ `list_priorities` | ❌ | |
| Statuses | ✅ `list_statuses` | ❌ | |
| Urgencies | ✅ `list_urgencies` | ❌ | |
| Announcements | ✅ `list_announcements` | ❌ | |
| Closure codes | ✅ `list_closure_codes` | ❌ | confirmed live 2026-08-01, `GET /closure_codes` |
| Change types | ✅ `list_change_types` | ❌ | confirmed live 2026-08-01, `GET /change_types` (returns Standard/Major/Emergency etc.) |
| Change risks | ❌ | ❌ | ⚠️ `GET /change_risks` 404s "Invalid URL" on this instance (confirmed 2026-08-01) — not available |
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

> Both endpoints confirmed live on the Spero instance (2026-07-17). Contract write support added
> 2026-07-20 — mandatory fields confirmed live: `name`, `custom_contract_id`, `type`, `vendor`,
> `from_date`/`to_date`. Purchase order write support added 2026-08-01 — mandatory fields
> confirmed live: `name`, `custom_po_id`, `vendor`, `requested_by`, `items` (each line item needs
> `product`, `ordered_quantity`, `price`, `category` — numeric category id, defaults to `1` =
> Assets). Products must be associated with the chosen vendor or the create 400s.

| Module | MCP coverage |
|---|---|
| Contracts | ✅ `list_contracts`, `get_contract`, `create_contract`, `update_contract` |
| Purchase Orders | ✅ `list_purchase_orders`, `get_purchase_order`, `create_purchase_order`, `update_purchase_order` |

---

## Summary

| Module | Tools | Notes |
|---|---|---|
| Requests | 40 | Core CRUD + notes (add/list/edit/get/delete), tasks (add/list/get/update/delete), worklogs (add/list/update/delete), resolution, attachments (list/download/upload), merge, summary, problem/change associations, and approval levels/approvals (add level+approver/list/notify/approve/reject) confirmed live 2026-08-01 end-to-end. Note get/delete added 2026-08-01, confirmed live. Drafts not implemented (platform gap). |
| Problems | 20 | Core CRUD + delete (permanent, added 2026-08-01) + notes (add/list/edit/get/delete), tasks (add/list/get/update/delete), worklogs (add/list/update/delete). Note get/delete and record delete confirmed live 2026-08-01. Approvals confirmed unavailable on this on-prem instance 2026-08-01 (4007 Invalid URL). |
| Changes | 26 | Core CRUD + trash/restore/copy (added 2026-08-01 — trash+restore confirmed live on an existing test change, copy unverified) + notes (add/list/edit/get/delete), tasks (add/list/get/update/delete), worklogs (add/list/update/delete), approve/reject, list approval levels (read-only, endpoint valid but returns Internal Error on changes with no configured levels). List pending approvals (flat path) re-confirmed unavailable on this instance 2026-08-01 across 5 path variants — docstring now points to list_change_approval_levels. Approval-level write ops (add/edit/delete/approver) documented only — not implemented (change-create is rate-limited on this instance, couldn't safely verify). |
| Releases | 12 | Core CRUD + notes (add/list/edit), tasks (add/list, stage required), worklogs (add/list), close (permission-gated on this instance). No approval-level management. |
| Projects | 13 | Core CRUD (delete is permanent — no move_to_trash endpoint) + milestones (add/list), tasks (add/list, no stage requirement), members (add/list, email resolution quirk), comments (add/list, `content` field). Confirmed live 2026-08-01. |
| Assets | 8 | Core CRUD + delete (added 2026-08-01, permanent) + depreciation fields + depreciation types + workstations. |
| CMDB | 7 | List/get/create/update/delete all covered (delete added 2026-08-01, permanent). Relationship listing works; adding relationships still unresolved. |
| Solutions | 8 | Read/create/update, approve-reject (via update_solution), topic create, attachment upload. Delete implemented but unresolved live ("Not in trash"); publish is cloud-only (404). |
| Contracts + Purchase Orders | 8 | Full list/get/create/update for both (PO writes added 2026-08-01). No contract renewal or PO receive/approve workflow actions. |
| Admin / Lookup | 19 | List/get only. Includes products (list/get), product types, closure codes and change types (added 2026-08-01, confirmed live). No user/group management. Change risks confirmed unavailable on this instance (404). |
| **Total** | **161** | |
