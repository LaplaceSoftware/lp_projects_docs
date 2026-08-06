# Implementation Tasks: Messaging Chatter & Notifications

**Epic**: Portal-Backend Real-Time Communication
**Goal**: Implement visibility flags, notification logic, and API updates to synchronize chat state between the Portal and Odoo Backend.

---

## 📅 Backend Tasks (Odoo)

### 📌 Task 1: Sale Order Visibility Flags, Reset Action & B2B Notebook
**Type**: Task
**Priority**: High
**Description**: 
Add fields to `sale.order` to track unread messages from the portal, implement a mechanism for the Account Manager to mark them as handled, and display these fields in a new notebook page.
**Technical Details**:
- **Model**: `sale.order` (inherit).
- **New Fields**:
  - `portal_messages_count`: Integer, Readonly (default=0). Tracks number of messages sent from portal.
  - `portal_visible`: Boolean, Readonly (default=False). Flag to indicate if the record needs attention (True = Unread Portal Message).
- **New Method / Action**:
  - `action_done_reply()`:
    - Sets `portal_visible = False`.
    - Can be exposed as a button "Reply Done" in the view.
- **View Update**:
  - Add a new `notebook` page or section in `sale.order` form: "B2B E-commerce".
  - Add `portal_visible` and `portal_messages_count` as **ReadOnly** fields in this section.
  - Add "Reply Done" button in the header or near the fields.
**Acceptance Criteria**:
- [ ] Fields `portal_messages_count` and `portal_visible` exist in DB.
- [ ] `action_done_reply` successfully sets `portal_visible` to `False`.
- [ ] "B2B E-commerce" tab appears in Sale Order form with ReadOnly fields.
- [ ] Button "Reply Done" is visible/clickable.

### 📌 Task 2: Account Manager Dashboard Notification
**Type**: Task
**Priority**: Medium
**Description**: 
Enhance the internal user experience by surfacing orders requiring attention via a dashboard notification.
**Technical Details**:
- **Dashboard**:
  - Add a "Notification Card" or Filter in the Account Manager's Dashboard (or List View).
  - **Filter Logic**: `search([('portal_visible', '=', True)])`.
  - Display: List of Orders needing reply.
**Acceptance Criteria**:
- [ ] Account Manager can easily see a list of orders where `portal_visible = True`.

### 📌 Task 3: API Update - Trigger Visibility on Message Send
**Type**: Task
**Priority**: High
**Description**: 
Update the Portal Chat API to automatically flag the record when a Portal User sends a message.
**Technical Details**:
- **Controller**: `PortalChatController` (method `send_message`).
- **Logic**:
  - When `send_message` is called by a Portal User:
    - Identify the related record (e.g., `sale.order` linked to the channel or context). *Note: If the chat is context-aware (on a specific order), update that order.*
    - **Update**:
      - `record.portal_messages_count += 1`
      - `record.portal_visible = True`
- **Context**: Ensure this only triggers for messages *from* the Portal, not internal replies.
**Acceptance Criteria**:
- [ ] Sending a message via API increments `portal_messages_count`.
- [ ] Sending a message via API sets `portal_visible` to `True`.
- [ ] Internal replies do *not* trigger these updates.

---

## 📅 Frontend Tasks (Next.js)

### 📌 Task 4: Wishlist Chat Integration (Draft State)
**Type**: Task
**Priority**: Medium
**Description**: 
Enable the chat interface specifically for the Wishlist page when the portal state is "Draft".
**Technical Details**:
- **Condition**: Check `portal_state == 'draft'`.
- **UI**:
  - If condition met: Render the `ChatComponent`.
  - Pass correct context (likely the current Wishlist/Quotation ID) to `init_chat`.
- **Behavior**:
  - Allow user to send messages regarding the draft items.
  - Ensure real-time updates work as per standard Chat Component.
**Acceptance Criteria**:
- [ ] Chat button/window appears on Wishlist page if state is 'draft'.
- [ ] Chat is hidden or disabled if state is NOT 'draft' (unless otherwise specified).
- [ ] Messages sent from here trigger the backend flags (Task 3).
