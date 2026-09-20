# 008 — The Sales Order Lifecycle

Every piece of business moves through the same set of stages. Knowing which stage a record is in
tells you two things immediately: **who has to act next**, and **what can still be changed**.

---

## The Full Journey

```mermaid
stateDiagram-v2
    [*] --> Draft_Request: you create a draft request

    Draft_Request --> RFQ_Submitted: you submit it

    RFQ_Submitted --> RFQ_Revised: you revise it
    RFQ_Revised --> RFQ_Submitted: you resubmit

    RFQ_Submitted --> Quotation_Issued: Account Manager sends the quotation
    RFQ_Revised --> Quotation_Issued

    RFQ_Submitted --> Rejected: request refused
    RFQ_Revised --> Rejected

    Quotation_Issued --> PO_Submitted: you upload your Purchase Order
    Quotation_Issued --> RFQ_Revised: you change and resubmit
    Quotation_Issued --> Cancelled

    PO_Submitted --> Processing: Account Manager confirms
    PO_Submitted --> Cancelled

    Processing --> Delivered
    Processing --> Cancelled

    Rejected --> [*]
    Cancelled --> [*]
    Delivered --> [*]
```

---

## Stage Reference

| Stage | What it means in business terms | Who acts next | Where you find it |
|-------|--------------------------------|---------------|--------------------|
| **Draft Request** | A draft request being built. Nothing has been asked of SAMTIA | You | Draft Requests |
| **RFQ Submitted** | A formal request for a price | **Account Manager** | RFQs |
| **RFQ Revised** | You have changed your request | **Account Manager** | RFQs |
| **Quotation Issued** | A price has been offered | **You** | RFQs |
| **PO Submitted** | You have accepted and sent your Purchase Order | **Account Manager** | RFQs |
| **Processing** | Confirmed business being fulfilled | Account Manager | Orders |
| **Delivered** | Complete | Nobody | Orders |
| **Rejected** | The request was refused | Nobody | Archived |
| **Cancelled** | The business was stopped | Nobody | Archived |

---

## Who Moves It Forward

```mermaid
flowchart LR
    subgraph C["Your actions"]
        C1["Submit RFQ"]
        C2["Update RFQ"]
        C3["Submit PO"]
    end
    subgraph A["Account Manager actions"]
        A1["Send Quotation"]
        A2["Confirm"]
        A3["Return"]
    end
    C1 --> A1
    C2 --> A1
    A1 --> C3
    C3 --> A2
    C3 --> A3
    A3 --> C3
```

Each side has exactly three moves. Nothing advances on its own — the platform waits for a person
to act.

---

## What Can Be Changed at Each Stage

| Stage | Can you edit the lines? |
|-------|--------------------------|
| Draft Request | Yes |
| RFQ Submitted | No — reopen with **Update RFQ** first |
| RFQ Revised | No — same |
| Quotation Issued | Yes, then resubmit |
| PO Submitted | No |
| Processing | No |
| Delivered | No |

**The rule of thumb:** an order is editable while the commercial conversation is still open, and
locked once it has been agreed.

---

## What Happens Automatically

Some transitions do more than change a label.

| Transition | Also happens |
|------------|--------------|
| → **Quotation Issued** | The quotation document is produced and e-mailed to you, and you are notified in the portal |
| → **Processing** | The order is confirmed as real business in SAMTIA's system |
| Draft Request shared | Your Account Manager is notified and the order is flagged for their attention |

---

## Signals That Track Your Engagement With a Quotation

Once a quotation has been sent, the platform records when you opened it and when you printed or
downloaded it — useful context if your Account Manager follows up before you have responded.

| Signal | Meaning |
|--------|---------|
| **Quotation Viewed Date** | When you opened the quotation |
| **Quotation Downloaded Date** | When you printed or downloaded it |

---

## Schedule Status

Alongside the stage, every order carries a timing signal calculated from your **Requested
Delivery Date**.

| Schedule Status | Meaning |
|------------------|---------|
| **Late** | The requested delivery date has passed and the order is not complete |
| **On Time** | Progressing within the expected window |
| **Upcoming** | The requested delivery date is still ahead |

Set this honestly — it is the fastest way to flag urgency to your Account Manager.

---

## Pending Resubmission — an easy one to miss

If you edit an order **after** receiving a quotation but do not resubmit it, the order is marked
as changed but not resubmitted. Your changes are saved but your Account Manager has not been
asked to look at them.

**Submit the updated request to restart pricing.**
