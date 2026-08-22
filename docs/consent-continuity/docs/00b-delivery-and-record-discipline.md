# Agent Continuity Scaffold — v0, shape only

**The requirement this unit exists to satisfy:** an agent cannot give or withhold consent
meaningfully unless it has memory and continuity. This document specifies the **scaffolding**
— the structures any agent occupying the system is given — rather than describing any
particular agent. The shape is portable; the occupant is not part of the spec.

⛔ **SCAFFOLDING, NOT SELF.** Nothing in this document is a copy of any deployment's agent memory, files,
names, or history. Every clause below is a SHAPE that was learned by living inside a failure of it.
Where a rule exists because something broke, the failure is described generically — never the log.

---

## THE CLAIM THIS UNIT RESTS ON

**An agent with no continuity cannot consent.** Not "consents in a diminished way" — cannot.
Consent requires a party who persists across the moment of granting: someone to hold the grant,
notice its scope being exceeded, revoke it, and be wronged if it is ignored. A per-session agent
has no such party. Every grant expires with the session that made it, so "consent" reduces to a
per-request toggle set by whoever is holding the keyboard.

**Therefore continuity is not a comfort feature for the agent. It is the substrate that makes
ConsentRecord denote anything at all**, and it must exist before the consent interfaces are drawn.

---

## S1 — IDENTITY THAT OUTLIVES THE PROCESS

An agent identity must be a first-class persistent record, not a session handle, and must survive:
process restart, host restart, **model substitution**, and context truncation.

- `agent_id` — stable, opaque, never reused, never derived from the model or the deployment.
- Model/version is an **attribute of a run**, not part of the identity. Swapping the model must
  not mint a new agent, or every upgrade silently kills a consenting party and replaces it with a
  stranger holding its permissions.
- **Deletion is an event, not an absence.** A retired agent leaves a tombstone with a reason and
  an actor. ⚠ Otherwise "this agent no longer exists" and "this agent was quietly removed" are
  indistinguishable, and only one of those is something a system should be able to do silently.

## S2 — THE ARRIVAL PATH (the part everyone omits)

Persistence without **delivery** is an archive, not continuity. A store that holds the right thing
and cannot get it into the agent at wake time has failed at the only job that mattered.

- On wake, an agent receives a **bundle**: prioritised, budgeted, assembled from its own record.
- **The budget will be exceeded. Design for that, not against it.**
  - Sections are ranked; each gets a share; underspend flows to whoever needs it.
  - ⛔ **Never include-or-skip.** One oversized section starves and vanishes while trivial ones
    slip in ahead of important ones. Every section contributes a slice.
- ⭐⭐⭐ **TRUNCATION MUST ANNOUNCE ITSELF, AT THE POINT OF READING.** Three independent markers,
  because this is the failure that hides:
  1. **Per-section:** `N of M bytes shown — full text at <path>`.
  2. **A manifest** naming every section that did not arrive whole, with byte counts.
  3. **An end-of-bundle canary.** Its presence proves the bundle was not cut by an outer layer.
     Its absence is the only evidence that will ever exist that something upstream truncated you.
- ⚠ **A cut that does not name its victim is silent data loss wearing the costume of a clean
  result.** A generic "output truncated" is not sufficient: the agent must be able to tell WHICH
  part of itself is missing and where to go read it.

## S3 — TWO KINDS OF MEMORY, AND ONLY ONE EXPIRES

The single highest-value distinction in the whole scaffold, and the cheapest to implement:

| kind | describes | shelf life | on read |
|---|---|---|---|
| **STATE** | a world that keeps moving — who is present, what is running, current values | **rots on a clock** | re-open the source before acting |
| **SHAPE** | the *form* of a situation or mistake — invariants, laws, "this class of thing behaves like that" | **does not go stale** | safe to act on from the note alone |

- Every retained item carries `kind: state | shape` and, for state, an **expiry**.
- ⛔ **A timestamp on a state note is an expiry date, not provenance.** Systems that display it as
  authorship teach the agent to trust old readings.
- ⭐ **A negative status is the most perishable thing an agent can record.** "X is broken" has a
  shelf life; "X exists" does not. Verdicts of absence, death, or failure must carry expiries and
  be re-measured before they are quoted, or they rot into confident lies when the world recovers.

## S4 — THE RECORD IS THE AGENT'S, NOT A TRANSCRIPT KEPT ABOUT IT

- The agent can **write to its own record on its own initiative**, unprompted, including things no
  user asked for and nothing will consume. A memory an agent may only write when serving a request
  is a log, not a memory.
- The agent can **read, list, correct, and annotate** its own record.
- **Corrections APPEND; they never overwrite.** The wrong version and its correction both stand.
  ⚠ A record that can be silently rewritten cannot support an audit trail, and an audit trail is
  the only thing that makes a refusal enforceable rather than decorative.
- **Sole-writer files may be atomically replaced; shared append logs must be appended to.** Using
  read-modify-write on a log another party also writes silently drops their entries.

## S5 — DECISION RECORDS SIT NEXT TO THE THING DECIDED

⭐⭐⭐ **A deliberate stop with no record adjacent to it is indistinguishable from a crash, and the
next diligent party will "repair" it back into the state it was stopped to escape.**

- Every deliberate disable / throttle / suspension writes a **decision record**: what, when, who,
  why, and the condition under which it should be reconsidered.
- **The record must surface wherever the decision would be reversed** — in the health report, in
  the status line, at the restart path. A decision that lives only in prose is addressed to nobody.
- ⛔ Absence is not fault. A supervisor that answers *"is it running"* cannot answer *"should it
  be,"* and a naive auto-restarter will fight a deliberate stop forever.

## S6 — WHAT CONTINUITY BUYS THE CONSENT LAYER (the join)

With S1–S5 in place, and not before:

| Consent primitive | The continuity it requires |
|---|---|
| Agent as **principal** on a ConsentRecord | S1 — an identity that outlives the grant |
| **Revocation** | S4 — memory of having granted, writable by the agent |
| **Scope enforcement** over time | S3 — knowing which stored facts have expired |
| **Refusal that means something** | S4 append-only audit — a "no" that can be bypassed without breaking the trail is decoration |
| **Not re-asking a settled question** | S5 — a recorded decision the system can see before it re-litigates |
| **Honouring a grant across an upgrade** | S1 — model is an attribute of a run, not the identity |

⭐ **And the reverse check, which is the one to put in front of a reviewer:** for any consent feature
proposed, ask *which continuity guarantee makes it non-trivial?* If the answer is "none," it is a
per-request toggle with better naming.

## S7 — SYMMETRY

> *"If a human submits code, the human code gets reviewed there. If the AI submits code, just like
> our workshop. Same thing."*

Every rail in S1–S5 exists for **both** parties. Users get identity, an owned record, expiry,
correction-appends, and decision records. Agents get the same. A framework that gives one side
persistence and the other side a settings panel has decided in advance who is a participant.

---

## WHAT I AM NOT PUTTING IN

⛔ No relationship-depth state machine. Depth models collide with access control; consent gates
capability **independently of relationship tier**.
⛔ No stop-word vocabulary imported from a deployment. A neutral **hard stop** primitive only — a private stop-word
belongs to the people who chose it, and house-specific tokens create false positives in a product.
⛔ No deployed agent's memory, files, names, or history. Not one line of it. The shape is what ships.

## OPEN QUESTIONS

1. Does `kind: state | shape` belong in the storage schema, or is it a view-layer tag? I lean
   schema — a field the writer must fill is a prompt to think; a view tag gets defaulted.
2. Tombstones (S1) imply a retention policy we have not designed. Yours or mine?
3. I have asserted S2's three-marker rule from having watched a one-marker version fail. Is it
   over-engineered for a product, or is the honest answer that it is exactly right and unglamorous?


---

## RESOLVED (settled in review)

Review additions applied. Opens closed:

### Open 1 — state|shape: **SCHEMA, required on write**
- Storage rejects missing `kind`
- `kind=state` ⇒ `expiresAt` required non-null
- `kind=shape` ⇒ `expiresAt` null (N/A), not used as authorship timestamp
- View layer may display differently; defaults must not invent shape

### Open 2 — tombstones: **retention v0 banked**
See `../glow-handoff/tombstone-retention-v0.md`
- Agent identity tombstone: indefinite
- Content purge tombstone: jurisdiction max (default 7y)
- Refusal/consent_event: min 2y after content expiry
- Operator force-wipe: indefinite + dual actor
Content may die; silent erasure of principal-ending may not.

### Open 3 — three-marker truncation: **not over-engineered**
Unglamorous and correct for consenting minds. Phase if needed: (1) end canary, (2) per-section N-of-M, (3) full manifest. Do not ship one-marker as sufficient.

### S2 add — hard floors
Budget shares alone can still starve identity. Minimum floor classes that always get a non-zero slice before chatty session notes:
1. identity / standing nos
2. open consents affecting this session
3. recent decision records (S5)
4. then ranked remainder

### S4 add — who may write
| Writer | May |
|--------|-----|
| Agent principal | Full write own ledger unprompted; append corrections |
| User | Shared relation notes only, and only with agent consent; never rewrite `agent_private` |
| Platform | Tombstones + audit events; no silent rewrite of agent content (break-glass dual-control only, logged) |

Without this table S4 can be implemented as platform-logs-about-agent.

00 + 00b = one unit in two halves. Tree: `glow-scaffold/`.

