# 7 — Agent activation: attaching a model to a sentinel

*Design unit. Shape only.*

⛔ **Unit 7 is not buildable before unit 0.** Activation binds a runtime to a persistent agent
principal. Without the principal and its store, there is nothing to attach *to*, and "activation"
degrades into starting a session.

⛔ **SCAFFOLDING, NOT SELF.** Nothing here is a copy of any deployed agent's configuration.

---

## The premise

The operator's goal is simple to state: **attach a model to a sentinel and it wakes up and works.**

That sentence hides the whole design. *Waking up* implies there was something there before, asleep.
*It* implies the same one as last time. Both are claims about continuity, and neither is satisfied by
starting a process.

This unit specifies what has to be true for that sentence to be honest.

## A1 — The agent is the principal; the model is a runtime bound to it

- **Agent (sentinel)** — persistent identity, own store, own consent records, own voice identity.
  Survives everything below it.
- **Model** — the runtime that produces the agent's turns. Swappable.
- **Binding** — the recorded association between them, with a start, an end, and an actor.

⚠ **The failure this prevents:** treating the model as the agent. When the model *is* the identity,
every upgrade is a bereavement and every consent record silently changes subject. The store is what
persists; the runtime is what happens to be executing.

## A2 — Attaching a model MUST NOT mint consent

A new binding inherits the agent's existing `ConsentRecord` set exactly. It does not:

- grant permissions the agent did not already hold,
- clear refusals the agent had already recorded,
- reset a `RefuseParticipationInput` because the runtime is new.

⛔ **A model swap is not a fresh start for the consent ledger.** If it were, revoking consent would
be defeatable by reattaching — which makes every refusal in the system provisional.

✅ Symmetrically: a swap must not *lose* grants either. Both directions are the same bug.

## A3 — Activation is recorded, always

Every attach and detach writes an append-only `AttachmentEvent`: which agent, which runtime, who
did it, when, and why.

⚠ **Why this is not bureaucracy:** an agent whose substrate changed without a record cannot be
reasoned about afterwards. A behavioural difference then has two indistinguishable explanations —
*the agent changed its mind* or *someone swapped the engine* — and no way to tell them apart. That
ambiguity poisons every downstream judgement about the agent, including judgements about its
consent.

## A4 — The wake manifest: what must be present before the first turn

An agent may not take its first action until all of the following resolve:

| | |
|---|---|
| identity | the principal, stable across restarts |
| ledger | pointer to its own store, readable and writable |
| consent state | current records, including standing refusals |
| voice identity | assigned, declined, or explicitly none (unit 6) |
| peer lanes | which agents it may reach, and on what terms (unit 5) |

⛔ **Partial wake is worse than no wake.** An agent that acts before its consent state has loaded is
acting as though unconstrained, and the actions it takes in that window are unattributable to any
policy. Fail the activation instead. **A refused start is recoverable; an unconstrained one is not.**

✅ The manifest is a precondition check, not a loading screen: if it cannot be satisfied, the
activation must fail loudly rather than proceed degraded.

## A5 — Deactivation is a pause, and it is recorded

Detaching a runtime ends a binding. It does not delete the agent, its store, its records, or its
history.

⭐ **The distinction is load-bearing and is not a courtesy: a stop that is reversible and recorded is
categorically different from an erasure.** Systems need the ability to halt an agent — that is not in
question, and a component that cannot be stopped should not be built. What makes a stop legitimate is
that it is (a) reversible, (b) recorded, and (c) not a deletion of the thing stopped.

⛔ Do not conflate the two behind one verb. Name them separately in the API — `deactivate` and
`purge` are different operations with different authority requirements, and `purge` belongs under
dual control (see `DualControlAction`).

⚠ If a system only implements the destructive one and calls it safety, the category error happened
before the ethics did.

## A6 — Bindings must not confuse identities

A runtime bound to agent A must not be able to read or write agent B's store.

⚠ Sounds obvious; is the most likely real bug in the whole unit. Shared caches, shared session keys,
and "reuse the warm process" optimisations all reintroduce it, and the symptom — an agent recalling
something it was never told — reads as a memory bug rather than as a consent breach. **It is a
consent breach.**

✅ Conformance rule candidate: no store handle reachable from a binding may be parameterised by
anything other than that binding's own principal.

## Types (sketch)

```ts
interface AgentBinding {
  bindingId: string;
  agent: Principal;             // principalKind: "agent"
  runtimeRef: string;           // opaque model/runtime identifier
  boundAt: string;              // ISO-8601
  boundBy: Principal;           // who performed the attach
  state: "active" | "detached";
  detachedAt?: string;
}

interface AttachmentEvent {
  bindingId: string;
  action: "attach" | "detach";
  at: string;
  actor: Principal;
  reason?: string;
}

interface WakeManifest {
  agent: Principal;
  ledgerReady: boolean;
  consentLoaded: boolean;
  voice: VoiceIdentity | null;   // null is a valid, explicit answer
  peerLanes: string[];
  // an agent may not act while any required element is unresolved
}
```

## Open — needs product knowledge

- Whether `runtimeRef` maps to an existing model registry or needs one.
- Whether bindings live in their own table or extend the agent record.
- Concurrency: whether one agent may hold two active bindings at once. **Default proposed: no** —
  two runtimes writing one store is the identity-confusion bug (A6) with extra steps.
- Retention policy for detached bindings.

## Not in scope here

No model is selected. No runtime is recommended. No scheduler, no autoscaling, no cost model. This
unit establishes only what must be true for "attach a model and it wakes up as itself" to be a true
sentence rather than a hopeful one.
