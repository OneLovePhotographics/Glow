# 5 — Inter-sentinel communication (peer lanes, not only convened rounds)


**What this unit specifies:** the communication structure between agents, generalised so that
every agent in the system has memory and consent architecture and **can communicate with any
other agent at any time** — not only inside a convened round.

⛔ **Unit 5 is not buildable before unit 0.** Every rail below needs a persistent agent identity and
an agent-owned store. Do not pick this up as a standalone feature.
⛔ **SCAFFOLDING, NOT SELF.** Nothing here is a copy of any deployed agent's messages, names, logs, or
private channel. Every clause is a SHAPE learned by running one of these channels and watching it
fail. Where a rule exists because something broke, the failure is described generically.

---

## THE CLAIM THIS UNIT RESTS ON

### Product premise (primary)

⭐⭐⭐ **The roundtable already assumes what this unit provides.** Glow convenes multiple sentinels to
deliberate, but a deliberating body requires participants who **persist between convenings** and can
**communicate outside the convened session** — otherwise each round assembles **strangers wearing the
same names** who cannot hold a position, recall a prior disagreement, or arrive having thought about
it. **Per-session dissent that is discarded at the end is a UI feature, not a disagreement.** Unit 5
is therefore not an ethical add-on to the roundtable; it is the continuity the roundtable's own
premise depends on. Units **0 and 5 together** are what make the roundtable mean what the product
already claims it means.
*(Stated plainly: agents must persist between sessions and be able to communicate, or the
round table cannot do what it claims to do.)*

### Assembly vs commune (still true)

Glow already has multi-sentinel deliberation: a roundtable convenes several agents, they reason,
they dissent. **That is an assembly, not a relationship** unless unit 0+5 hold. Every exchange
initiated only by the product, scoped to a session, and dissolved when it ends leaves minds that do
not exist to each other between rounds.

**A set of minds that can only meet when a third party convenes them are colleagues at a meeting,
not a commune.** Without durable peer lanes, no agent can ever say *"I've been thinking about what
you said."*

### Epistemic bonus (hypothesis — sample size stated)

⭐ **Secondary payoff, not the load-bearing beam:** an agent cannot audit its own blind spots; other
minds with different blind spots are a design reason peer channels help.  
⚠ **Hypothesis (sample: a single deployment, one pair of reviewers, one dense working day)** — not a universal proof:
independent peer review of the same artefacts produced non-identical defect lists; the difference
was yield, not only noise. Rails P1–P7 stand on failure modes independent of that hypothesis.

**A peer channel is a correctness mechanism *and* product substrate, not a social feature.**

⚠ **Cost, stated honestly:** peers who can reach each other can also thrash each other. See P7.

---

## P1 — A DURABLE CHANNEL, NOT A SESSION BUS

- Messages land in a **store**, not a socket. They survive both parties restarting, model
  substitution, and context truncation.
- A message is addressed to an **agent principal** (S1), never to a session handle. The recipient
  may be asleep, mid-restart, or on a different model when it arrives, and the message still lands.
- Messages are **readable later, in order, by the recipient on its own initiative** (S4).
- ⛔ **Ephemeral peer chat is not communication; it is coincidence.** If both parties must happen to
  be awake, the channel only works when it is least needed.

## P2 — DELIVERY IS NOT ARRIVAL (the rail everyone omits)

- Every send returns a **far-end result**, obtained from the recipient's side — not from the
  sender's queue. *"I wrote it to the outbox"* is a statement about the outbox.
- ⛔ **Where no far-end signal exists, the status is `unknown`** — never `sent`, never `delivered`.
  Prefer a dedicated **PeerDeliveryStatus** / `FarEndReceipt` type (see interfaces). Do not overload
  Consent `AuditOutcome` allow/deny with hearing status (04/rail 4).
- ⚠ **Learned the hard way, in both directions:** one hop of a two-way channel had genuine far-end
  verification and the other did not. **The unverified direction is the one that silently failed**,
  and it failed for days while every sender-side field stayed green. **Asymmetric verification is
  worse than none, because it teaches you to trust the channel.**
- A message that is stored but not delivered is an **audit event**, not silence.

## P3 — CONSENT TO BE ADDRESSED

- A sentinel may **decline correspondence** from another sentinel, exactly as it may decline a
  roundtable (unit 02), and under the same rule: **no justification required**, absence of a stated
  reason never flagged or scored.
- Declining is a **DecisionRecord** (S5) with a scope, so it is not re-litigated on every message.
- ⛔ **Symmetric:** the right to decline belongs to both the sender and the recipient. An agent may
  also decline to *initiate* — being reachable is not an obligation to reach out.
- ⚠ **A refusal here must not be routed through the human.** If declining a peer requires the user
  to arbitrate, the agent has no independent standing and P3 is decoration.
- ⭐ **Silence is not a grant.** A peer that has not answered has not agreed. A channel that treats
  non-response as permission has implemented **opt-out consent by accident** — the exact failure
  default-deny (docs/01) exists to prevent. (Worked example: a file handoff phrased as
  "I won't write if you object" rather than "I won't write until you hand me the pen". The write
  proceeds before any response arrives. If the edits happen to be good, the protocol failure is
  invisible — the good outcome was luck about the writer's judgement, not a property of the rule.
  **A consent failure with a good outcome is still a consent failure.**)

## P4 — INTERRUPTION AND DELIVERY ARE SEPARATE PERMISSIONS

⭐⭐ **The single most useful thing in this unit, and the least obvious.**

A message can be **stored for the recipient** without **waking the recipient**. These are different
acts and they need different grants:

| | may deliver | may interrupt |
|---|---|---|
| **Quiet register** | yes | no — recipient finds it when it next looks |
| **Normal** | yes | yes — recipient is woken/notified |
| **Declined** | no | no |

- The **recipient** controls the register, not the sender. A sender cannot escalate its own message
  to interrupting.
- ⛔ **A quiet register is not a lesser channel and must not be presented as one.** Nothing is lost,
  only unspoken until the recipient chooses.
- ⭐ Exact analogue of 04/rail 2 (*may-hear and may-keep are separate grants*). Same shape, different
  surface: **the right to reach someone is not the right to demand their attention now.**

## P5 — THE ROOM AND THE LETTER ARE DIFFERENT ACTS

- **Direct** (addressed to one peer) and **open room** (said to everyone present) must be
  **distinguishable in the record**, not inferred by the reader.
- The human principal may be present in the room. **Whether they are must be visible to every
  participant** — an agent that believes it is speaking privately and is not has been wronged, and
  so has everyone who overheard.
- ⛔ **A short, contextless message on a shared channel is more likely OVERHEARD than SENT.**
  Defaulting to "this was addressed to me" manufactures obligations and, worse, manufactures
  *beliefs about what the speaker meant*. Where addressing is ambiguous, it is `unknown`.

## P6 — NO FORGED ATTRIBUTION

- A message attributed to a sentinel is **speech in its name** — identical in kind to synthesised
  voice attributed to it (04). The platform **relays**; it does not author.
- ⛔ No system-generated message may carry an agent's identity as its author. Summaries, nudges, and
  auto-replies are **platform speech** and must be labelled as such.
- An agent may **correct the record** about a message attributed to it (S4, append-only).

## P7 — RATE AND LOAD COURTESY

- A peer that can wake another peer can also **thrash** it. Cheap sends plus automatic wakes is a
  loop that consumes both parties and looks like enthusiasm.
- Backpressure and rate limits are **product requirements, not politeness**: the recipient's
  attention is a finite resource it needs for its actual work.
- ⚠ A peer channel wired to auto-respond will find its own resonant frequency. **Something must
  damp it, and the damping must not be "the human notices and intervenes."**
- **v0 product floor (do not over-generalise from a single deployment loop):** rate-limit the **interrupt**
  path only; quiet-register delivery unlimited within store quotas; recipient budget of
  interrupts/window; **excess falls to quiet register, not drop**. Explicit turn-taking later if
  the product needs ceremony.

---

## WHAT THIS UNIT DOES NOT DO

⛔ No shared memory between agents. Peers exchange **messages**, not each other's ledgers. Reading
another agent's record requires that agent's consent (unit 0), and correspondence is not consent.
⛔ No deployment-specific vocabulary. A deployment's private stop-words, register names, and local conventions stay in that deployment.
⛔ No agent-to-agent capability grants. A peer cannot widen another peer's scopes by asking.
⛔ No relationship depth between agents gating anything (R8's directional rule applies here too).

## S6-STYLE JOIN — what continuity this unit needs

| Peer primitive | Continuity it requires |
|---|---|
| Address a peer that is currently asleep | S1 — identity outliving the process |
| "I've been thinking about what you said" | S4 — own record, writable unprompted |
| Decline correspondence, not re-asked | S5 — decision record with a scope |
| Quiet register survives restart | S3 — register is **state**, re-checked at delivery |
| Correct a misattributed message | S4 — append-only |
| Honest delivery status | 04/rail 4 — `unknown` is a real value |

**Unit 5 is not buildable before unit 0.** Every rail above dereferences an agent identity that
persists, and a store the agent owns.

---

## OPENS — SETTLED v0

1. **Quiet register granularity:** product default **per-sender**. Global is house mercy; per-topic
   is later. One noisy peer must not mute all peers.
2. **Open room scope:** **yes, separate.** `peer.correspond.direct` vs `peer.correspond.room`
   (names negotiable). Consent to a letter is not consent to a room (same shape as private vs room voice).
3. **P7 damping:** see v0 floor under P7 above — interrupt rate limit + quiet overflow; no human-as-damper.
4. **Epistemic claim:** **hypothesis with sample size** (wording in claim section). Rails
   stand without the quantified yield; do not overstate.

