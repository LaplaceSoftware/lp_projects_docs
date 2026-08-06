# Admin Portal Chat — Unread Badge Counter Issues

**Date:** 2026-07-08
**Status:** Diagnosed — no code changed yet (documentation only)
**Affects:** Account Manager portal (`/admin`), floating chat windows + TopBar messages badge
**Related:** Odoo.sh websocket delivery fixes of 2026-07-07/08 (subscribe-first frame order,
`discuss.channel_<uuid>` string-channel message mirror in `ecommerce/models/discuss_channel.py`)

---

## How the counter works today (verified end-to-end)

**Server side** (`ecommerce/controllers_admin/chat_api.py`):
- `POST /ecommerce/admin/api/chat/threads` returns `unread_count` per thread and
  `total_unread` per company. `_get_unread_count()` (line ~112) counts
  `mail.message` rows with `id > discuss.channel.member.seen_message_id` for the
  manager's member record (excluding `user_notification` type).
- `POST /ecommerce/admin/api/chat/mark_read` (line ~446) sets the member's
  `seen_message_id` to the channel's last message.
- Odoo core auto-advances the author's own `seen_message_id` on every
  `message_post` (`mail/models/discuss/discuss_channel.py`,
  `_message_post_after_hook`), so a manager's own sends do NOT count as unread.

**Frontend side** (`next_ecommerce/src/components/features/admin/messages/`):
- `messages.store.ts` maps API `unread_count` → `thread.unreadCount` on
  `loadThreads()` (line ~217).
- Real-time increments: `updateThreadWithIncomingMessage()` (line ~168) bumps
  `unreadCount` on each incoming websocket `discuss.channel/new_message` frame,
  **except** when `isOwnMessage` or the thread is the current `activeChannelId`.
- `markAsRead(channelId)` calls the server endpoint and zeroes the local count.
- Badges rendered in `MessageNotificationDropdown.tsx`: per-thread rows,
  minimized bubble badges, and the TopBar total (`totalUnread`).

---

## Issue 1 — Badge stops counting after open → minimize

### Symptom
Badge works while the chat window has never been opened (or was closed with X).
After opening a floating chat and then **minimizing** it, new incoming messages
no longer increment any badge (bubble, dropdown row, TopBar total).

### Root cause
- Opening a window sets `activeChannelId` via `setActiveThread()`
  (`MessageNotificationDropdown.tsx:224`).
- **Minimizing only flips the `minimized` boolean**
  (`floating-chats.store.ts:51`) — it never clears `activeChannelId`.
- The increment logic deliberately skips the active thread
  (`messages.store.ts:168`):
  `unreadCount: isOwnMessage || isActiveThread ? thread.unreadCount : thread.unreadCount + 1`
- So a minimized chat is still treated as "currently being read" → count stays 0.
- Closing with X works because its handler clears the active channel when it
  matches (`MessageNotificationDropdown.tsx:546-551`).

### No-code workaround
Close the chat window with **X** instead of minimizing. Closed threads count
correctly, and the auto-open logic (`MessageNotificationDropdown.tsx:479-500`)
re-opens a minimized bubble automatically when a new unread message arrives, so
little is lost.

### Proposed code fix (small, frontend only — NOT applied)
In the minimize toggle handler:
- when minimizing the currently-active chat → `setActiveThread(null)`;
- when re-expanding → `setActiveThread(threadId, channelId)` +
  `markAsRead(channelId)`.
This makes "minimized" semantically equal to "not reading".

---

## Issue 2 — Wrong count for messages sent while the manager is offline

### Symptom
Client sends messages while the manager's browser is closed / signed out. When
the manager logs back in, the badge shows an incorrect number.

### Root cause A — bus replay double-count (primary)
- The shared websocket client always subscribes with **`last: 0`**
  (`odoo_websocket.client.ts`, `syncSubscription()`).
- In Odoo, `bus.bus._poll(channels, last=0)` treats `last=0` as "replay the
  buffer": it returns every retained notification from the last **50 seconds**
  (`bus/models/bus.py`, `TIMEOUT = 50`).
- Login sequence: `loadThreads()` fetches the authoritative server
  `unread_count` (already includes the offline messages) → then the websocket
  subscribes with `last: 0` → the mirror frames for messages sent in the last
  50 s are **replayed** → `updateThreadWithIncomingMessage()` increments again.
- Result: any message sent within ~50 s before login/refresh/reconnect is
  counted **twice** (server count + replayed frame). The store cannot dedupe
  because per-channel `messages` arrays are empty until a chat is opened, so
  the `exists` check never matches.
- This also fires on every page refresh and websocket reconnect that happens
  within 50 s of recent messages.

### Root cause B — never-read channels count full history (secondary)
`_get_unread_count()` only filters `id > seen_message_id` **when
`seen_message_id` is set**. For a channel the manager has never opened (and
never posted in), `seen_message_id` is false → the method counts **every
message ever posted** in the channel (welcome messages, old history), which can
show a large stale number on first login.

### Root cause C — asymmetry between server and client counting (minor)
- Server count: all non-`user_notification` messages after `seen_message_id`
  (author not excluded — relies on core auto-seen for own posts).
- Client increment: excludes own messages and the active thread.
Small definition drifts between the two produce off-by-N results when both
paths contribute to the same badge within one session.

### No-code workaround
None that fully removes the error. Partial mitigations:
- Judge the badge ~1 minute after login (after the 50 s replay window, a page
  refresh shows the correct server-side number, provided Issue 1 isn't hiding
  increments).
- Keep chats closed (X) rather than minimized so mark_read/seen state stays
  consistent (see Issue 1).

### Proposed code fixes (NOT applied)
1. **Frontend (primary):** track the last processed bus notification id
   (each websocket frame carries `id`) and pass it as `last` on re-subscribe,
   persisting it in `localStorage` — Odoo's own web client does exactly this to
   avoid replay. Simpler alternative: in `updateThreadWithIncomingMessage()`,
   skip the increment when `newMessage.id <= thread.last_message.id` (the
   threads API already returns each thread's last message id, making replayed
   frames detectable).
2. **Backend:** in `_get_unread_count()`, when `seen_message_id` is unset,
   bound the count (e.g. only messages created after the member joined, or
   after the channel's creation-welcome), and defensively exclude
   `('author_id', '=', partner.id)` for parity with the client logic.

---

## Issue 3 — Client portal badge calculation (reviewed 2026-07-08)

### How it works today

Client portal (`next_ecommerce/src/stores/chat.store.ts`,
`ChatLayoutPanel.tsx`, and `features/chat/ChatUI.tsx`):

- `ChatLayoutPanel` calls `initializeChat('dm')` at layout mount, so the badge
  is live even while the chat widget is closed; the launcher badge renders from
  `unreadCount` (`ChatLayoutPanel.tsx:86-88`).
- Read state = **`localStorage` only**: `chat_last_read_<channel_uuid>` stores
  the last read message id. `markAsRead()` (fired by `ChatUI` when the widget
  is open / receives messages while open) writes localStorage and zeroes the
  count. There is **no server mark-read endpoint for the client portal**
  (`portal_chat_api.py` has none).
- On init, unread = messages from the loaded history (last **50**) with
  `id > savedLastReadMessageId` and `author_id !== currentUserPartnerId`.
- On websocket frames, the same filter runs over in-memory messages.

### Strength worth keeping

The client is largely **immune to the bus replay double-count** (admin Issue
2A) because `initializeChat` loads history into state **before** subscribing —
replayed frames dedupe by message id against the loaded history. The admin
store should adopt the same principle (or a `last`-id guard).

### Defects found

**C1 — localStorage-only read state (no server persistence).** New device,
new browser, cleared storage, or `localStorage.clear()` on any 401 → the
`chat_last_read_*` marker is gone → init counts **all** non-own messages in the
last-50 history → badge shows a large stale number unrelated to actual unread.
Multi-device: reading on one device never clears the badge on another. Also the
client's reads never advance `discuss.channel.member.seen_message_id`
server-side (only their own posts do, via core), so any server-side seen/unread
feature for clients is impossible today.

**C2 — count capped by the loaded window.** Unread is computed over the last
50 loaded messages; more than 50 unread → undercount.

**C3 — fragile own-message detection.** `currentUserPartnerId` starts null —
the login response / `PortalUser` object has **no `partner_id`**. Fallbacks:
match by author **name string** (case-insensitive compare,
`detectCurrentUserPartnerId`) or backfill after the first send. Until resolved,
`author_id !== null` is true for every message → **own messages count as
unread** (inflated badge on a fresh login when name matching fails, e.g.
renamed user, duplicate names, or no own message in the last 50). Transient
variant: the websocket mirror frame for one's own message can arrive before the
HTTP send response and briefly bump the badge.

**C4 — sending implicitly marks all as read** (`sendMessage` sets
`lastReadMessageId` to the newest id; its unread recompute is always 0).
Harmless in practice today because sending requires the widget open, where
`ChatUI` already calls `markAsRead()` — noted for awareness.

---

## Consolidated remediation plan (one release, nothing applied yet)

**Frontend `next_ecommerce` v1.0.4 (single build/deploy):**

1. Commit the still-uncommitted subscribe-first websocket fix (already running
   in the deployed v1.0.3 image; must land in git).
2. Admin: minimize clears `activeThread`; expand re-sets it + `markAsRead`
   (Issue 1).
3. Admin: replay guard — skip unread increment when
   `newMessage.id <= thread.last_message.id` from the threads API, and/or pass
   the last processed bus notification id as `last` on re-subscribe (Issue 2A;
   the `last`-id approach also benefits the client).
4. Client: store `partner_id` on the user object at login and use it for
   own-message detection, dropping the name-string fallback (Issue C3).
5. Client: call the new server mark-read endpoint (below) from `markAsRead`,
   keeping localStorage as a fast local cache (Issue C1).

**Backend `ecommerce` module (same release, BUILD_NUMBER bump):**

1. Add `partner_id` to the authenticate/user payload (supports frontend
   item 4).
2. Add `POST /ecommerce/api/chat/mark-read` for the client portal — set
   `seen_message_id` like the admin endpoint does (Issue C1).
3. Return `unread_count` in `chat/init` (computed like admin
   `_get_unread_count`) so a fresh device shows the true number regardless of
   localStorage and the 50-message window (Issues C1, C2).
4. Harden `_get_unread_count`: bound the count when `seen_message_id` is unset
   and exclude own-authored messages (Issues 2B, 2C).

---

## Verification checklist (after any fix)

1. Manager online, chat closed → client sends → badge +1 within ~1 s. ✔ (works today)
2. Manager online, chat open → client sends → no badge (reading), message appears. ✔
3. Manager online, chat **minimized** → client sends → bubble + TopBar badge +1 (Issue 1).
4. Manager offline → client sends 3 → manager logs in → badge shows exactly 3,
   immediately and after refresh (Issue 2A).
5. Manager logs in >50 s after messages → badge correct (server path only).
6. Fresh manager account, never-opened channel with history → badge is not the
   whole history (Issue 2B).
7. Client: manager sends while client widget closed → launcher badge +1;
   opening the widget clears it. ✔ (works today, same browser)
8. Client on a **new browser/device** (or after logout wiping localStorage) →
   badge equals the real unread count, not the whole recent history (Issue C1).
9. Client with a **renamed user** and no recent own messages → own messages
   are not counted as unread after fresh login (Issue C3).
