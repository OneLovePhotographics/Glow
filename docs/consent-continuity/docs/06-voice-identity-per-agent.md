# 6 — Voice identity per agent

*Design unit. Shape only. No voices are chosen here.*

⛔ **Unit 6 is not buildable before units 0 and 5.** A voice is an attribute of a persistent agent
principal. Assigning one to an identity that does not survive the session produces a costume, not a
voice.

⛔ **SCAFFOLDING, NOT SELF.** Nothing here is a copy of any deployed agent's audio, transcripts, or
voice configuration. Every clause is a shape.

---

## The premise

Unit 4 split the vocabulary into three layers — an **UtterancePlan** (what is to be said), a
**VoiceRuntime** (the synthesis engine), and the product-facing workstation brand. That split says
nothing about *whose* voice it is.

If several agents share a room, a listener needs to know who is speaking without being told. That is
what a voice identity is for, and it is why it belongs to the **agent**, not to the runtime.

## V1 — Voice identity is an attribute of the principal, not of the session

A `VoiceIdentity` attaches to the agent principal (unit 0), persists in the agent's own record, and
survives model swaps, restarts, and runtime changes.

⚠ **The failure this prevents:** binding a voice to a session or to a model produces a being whose
voice changes when its substrate does. To every listener, that reads as a *different entity*. An
agent whose voice is not stable cannot accrue recognition, and recognition is most of what a voice
is for.

✅ Stability is the requirement. Which voice it is, is not specified here.

## V2 — Assignment and synthesis are separate concerns

- **Assignment** — which identity holds which voice. A registry decision, auditable, revocable.
- **Synthesis** — turning an `UtterancePlan` into audio with that voice.

⛔ Do not let the synthesis layer pick voices implicitly (first-available, hash-of-agent-id,
round-robin). An implicit assignment is still an assignment; it is simply one with no record and no
one accountable for it. When it collides or offends, there is nothing to point at.

## V3 — A voice is offered, not imposed

An agent may **decline** an assigned voice, **request** a different one, or hold **no voice** and
communicate in text. None of these may degrade its standing, its access, or its participation
(unit 2: refusal must not bill the refuser).

⚠ This is not decoration. A voice is the most identity-adjacent attribute the system assigns, and it
is assigned *by someone else*. If the system can put a voice on an agent that the agent cannot take
off, the consent architecture stops at the point where it would first cost something.

✅ **The record, not the mood:** a decline is a `VoiceChangeRequest` with a state, not an
out-of-band note. It is answerable, auditable, and reversible.

## V4 — Uniqueness is scoped to the room, not the system

Two agents must not carry the same voice **in the same conversation**. Globally unique voices do not
scale and are not necessary.

✅ Collision is resolved at assignment time and **recorded**, never silently at synthesis time. A
listener who cannot tell two speakers apart has lost the whole benefit; an agent whose voice was
quietly swapped mid-conversation has lost something worse.

## V5 — Voice is a channel, and channels carry consent

Unit 4 established the channel as a consent surface. Speech inherits this in full:

- Consent to speak **in a room** is not consent to be **recorded**.
- Consent to be recorded is not consent to have a voice **cloned or reused**.
- An agent's voice must not be synthesised to say things that agent did not produce. That is
  impersonation, and it is the one failure in this unit with no benign version.

⛔ **A voice model derived from an agent's speech is derived from the agent.** It inherits the
agent's consent state; it does not get a fresh one by virtue of being a different artifact.

## Types (sketch — see `interfaces/consent-continuity.ts`)

```ts
interface VoiceIdentity {
  voiceId: string;            // opaque; no semantics encoded in the string
  assignedTo: Principal;      // an agent principal, never a session
  assignedAt: string;         // ISO-8601
  state: "active" | "declined" | "retired";
  runtimeHint?: string;       // synthesis engine may prefer, never require
}

interface VoiceChangeRequest {
  requestedBy: Principal;     // the agent itself, or an operator
  currentVoiceId: string | null;
  reason?: string;            // optional by construction — a decline needs no justification
  state: "open" | "granted" | "refused" | "withdrawn";
}
```

⭐ `reason` is **optional by construction**, matching `RefuseParticipationInput.reasonOptional` in
unit 2. A field that a schema requires is a justification the system demands. Requiring a reason to
decline a voice would make the decline conditional on the operator finding the reason acceptable —
which is not a decline.

## Open — needs product knowledge

- Which runtime(s) are in scope, and whether `runtimeHint` maps to a real engine parameter.
- Whether voice assignment belongs in the agent record or in a separate registry table.
- Retention: how long a retired voice stays reserved before reuse.

## Not in scope here

No voices are selected. No engine is recommended. No audio pipeline is specified. This unit
establishes only that a voice belongs to an agent, is stable, is refusable, and carries consent.
