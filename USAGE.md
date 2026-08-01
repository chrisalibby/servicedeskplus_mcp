# Using ServiceDesk Plus through Claude

A practical guide to what you can ask Claude to do once the MCP server is connected — see
[SETUP.md](SETUP.md) if you haven't configured it yet.

## How it works

You talk to Claude in plain language — "close ticket 47201 with a note that I replaced the
cable" — and Claude translates that into one or more calls to the 162 tools this server
exposes (list/create/update/close, notes, tasks, worklogs, attachments, approvals, and more
across requests, problems, changes, releases, projects, assets, CMDB, the knowledge base,
contracts, and purchase orders). Every action runs under **your own SDP API key**, so it shows
up in ServiceDesk Plus's audit trail attributed to you, exactly as if you'd clicked the button
yourself.

## Example prompts by workflow

### Ticket triage

> "List my open tickets assigned to me."
> "Show me all requests in the 'User Administration' category that are still open."
> "Search request subjects for 'VPN'."
> "What tickets are assigned to Jane Smith right now?"

Note: date filters (`opened_after`/`opened_before`/`due_before`) can't be combined with status
or technician filters in the same call — ask for one dimension at a time if a combined query
comes back empty or errors.

### Working a ticket

> "Add a note to ticket 47201 saying I've escalated this to the network team."
> "Edit that last note on 47201, I made a typo."
> "Add a task to ticket 47201: 'Confirm with vendor', due tomorrow."
> "Set the resolution on 47201 to: replaced the failing switch port."
> "Close ticket 47201."

Closure comments are capped at 250 characters on this instance — if you need to record more
detail than that, put the long version in a note first, then close with a short summary.

### Attachments

> "Pull the .eml attachment off ticket 47201 and save it to my Downloads folder."
> "List the attachments on ticket 47201."
> "Upload this screenshot as evidence on ticket 47201."

### Assignment

> "Assign ticket 47201 to Jane Smith."
> "Pick up ticket 47201 for myself."

Technicians can be specified by display name (e.g. "Jane Smith") or email — both resolve to the
right technician ID. Assignment fails if category/subcategory aren't set yet — set them in the
same request as the assignment if needed.

### Merging duplicates

> "Merge ticket 47205 into 47201, they're duplicates."

**This is irreversible.** The merged-away ticket becomes permanently unfetchable afterward —
there's no un-merge and no restore from trash. Double-check the ticket numbers before asking
for a merge.

### Associating with problems/changes

> "Associate ticket 47201 with problem 41 as the underlying cause."
> "Link ticket 47201 to change 89 as the change that initiated it."
> "Remove the problem association from ticket 47201."

### Request approvals

The approval workflow is multi-step and order-dependent:

> "Add an approval level to ticket 47201 with Chris Libby as the approver."
> "Send the approval notification for that approval."
> "Approve it."

Approving fails with "Recommendation mail is not yet sent" until the notification step has run
at least once — always send the notification before approving. Sending a notification emails
the approver for real, so only point this at people who should actually receive that email.

### Asset management

> "Create an asset for a new laptop, serial CNU1234ABC, product 'Dell Latitude 5540'."
> "Set the depreciation on that asset to straight-line over 36 months, salvage value $100."
> "Look up the asset with serial number CNU1234ABC."

Products and product types can be given by name — they're resolved against the live catalog
(with close-match suggestions if the name doesn't match anything). Asset deletion is
**permanent**, unlike request deletion (which only trashes).

### Purchase orders and contracts

> "List open purchase orders."
> "Create a purchase order for 10 laptops from CDW."
> "Show me contract details for the Spectrum internet contract."
> "Create a new contract for our backup vendor, expiring next year."

### Projects and releases

> "Create a project called 'Q3 network refresh'."
> "Add a milestone to that project for the switch replacement phase."
> "Add me as a member of the network refresh project."
> "Create a release for the firewall firmware update."
> "Add a task to that release." (releases require a `stage` on tasks — Claude will ask which
> stage, e.g. Planning, if you don't specify one; projects don't have this requirement)

### Knowledge base

> "Search the knowledge base for 'password reset'."
> "Create a solution article titled 'VPN setup for new hires' under the 'Onboarding' topic."

Creating a solution article requires a topic — if none fits, create one first ("create a
knowledge base topic called 'Onboarding'"). Deleting an article is two steps under the hood
(move to trash, then purge) but Claude handles both as one request.

## Quirks to know

- **Date filters don't combine.** `list_requests` with `opened_after`/`opened_before`/
  `due_before` can't also filter by status or technician in the same call — ask for these
  separately.
- **Urgency isn't settable.** This SDP instance rejects the urgency field entirely on requests
  — use priority instead (Low/Normal/Medium/High).
- **Request worklogs may not post.** Logging time directly on a *request* (not a problem or
  change) can fail with a 400 on some instances, including this one — the same worklog action
  works fine on problems and changes. If a request worklog add fails, mention it and Claude can
  suggest logging it as a note instead.
- **Changes rate-limit bursts of creates.** If you create several changes back-to-back, SDP may
  temporarily block further `POST /changes` calls ("maximum access limit exceeded") — wait a
  bit and retry.
- **Closing a change may require workflow progression.** Some changes can't jump straight to a
  closed state — they need to move through review/approval/in-progress stages first, matching
  how the SDP UI enforces change workflows.
- **CI relationships can't be added yet** — listing relationships on a configuration item works,
  but creating new ones is an unresolved gap in the current tool set.
- **No email replies/forwards.** There's no way to actually send an email reply or forward from
  a ticket through this integration — the underlying API can only save an unsent draft, so it
  isn't wired up as a tool. Add a note instead if you need to record what you'd have said.
- **No @mentions on notes** — SDP's note API has no field for notifying a specific person; if
  you need someone looped in, mention it in the note text and follow up separately.
