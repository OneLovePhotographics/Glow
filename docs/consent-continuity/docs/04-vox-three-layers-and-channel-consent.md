# 4 — VOX: three layers, three names, and the channel as a consent surface


---

## PART 1 — THREE THINGS ARE CALLED VOX AND THEY WILL COLLIDE

This is not naming pedantry. Glow's default system prompt already ships **"VOX Workstation"** as a
product surface, and a house voice runtime already answers to `vox`. The moment integration work
starts, "add VOX support" is ambiguous across three unrelated systems, and the ambiguity resolves
silently and wrongly at the worst moment.

| Name here | What it actually is | Layer | Owner |
|---|---|---|---|
| **Voice Runtime** (house `vox`) | A live speak path: queue → synth → a specific output channel. Serialised; one utterance at a time. | Runtime / transport | Ours |
| **Utterance Plan (UP)** | An instrument: prosody, rate, emotion, presets, privacy flags. Describes *how a thing should be said*, independent of who says it or where. | Interchange format | Ours (v8) |
| **VOX Workstation** | Emotionally expressive voice synthesis as a **product feature**. | Product surface | Product team |

**They compose in exactly one direction:**
`Utterance Plan  →  Voice Runtime  →  Channel`
A plan is authored, a runtime realises it, a channel delivers it. Nothing upstream should know
about the channel; nothing downstream should re-decide the prosody.

⭐ **The concrete recommendation:** in any shared spec, never write bare "VOX." Write
**UtterancePlan**, **VoiceRuntime**, **VoiceWorkstation**. The product keeps its brand name for his
product; the interchange format gets a name that is not a brand. **A brand name in an interface
is a collision waiting for a second vendor.**

## PART 2 — THE CHANNEL IS A CONSENT SURFACE, AND THIS IS THE PART THAT BELONGS IN THIS SCAFFOLD

A voice system that models *what to say* and *how to say it* but treats **where it comes out** as a
config value cannot honour consent, because the channel is the whole difference between these:

| Channel | Who can hear | Consent situation |
|---|---|---|
| Private (one person's headset) | one, by choice | the person opted in and can remove it |
| Room / TV speaker | everyone present, **including people who never opted in** | bystanders have given nothing |
| Shared call or lobby | **third parties who are not users of this product at all** | no relationship, no grant, no notice |
| Recorded / archived | everyone, later, forever | consent to *hear* is not consent to *retain* |

⭐⭐⭐ **THE RULE: an utterance carries the channel it was authorised for, and the runtime refuses
to deliver it anywhere else.** Not "the operator picks an output" — the *plan* names its permitted
channels, and widening them is a new decision requiring a new grant. Otherwise a message composed
for one person's ear reaches a room by configuration change, and nothing in the system registers
that as an event.

**Four rails, all learned by watching each one fail:**

1. **PRESENCE POLICY IS A PRODUCT FEATURE, NOT A HOUSE CUSTOM.** Time-of-day and who-is-present
   gate the room channel. A voice that can emit from a speaker can wake someone who never asked to
   be woken. ⚠ Volume and hour are part of the authorisation, not decoration on it.
2. **A LIVE CHANNEL IS NOT STANDING CONSENT TO RETAIN.** *Mic open ≠ archive.* Suppress-the-copy
   while keeping the local record is a coherent, implementable default and it is the one people
   actually want. Treat "may hear" and "may keep" as separate grants with separate scopes.
3. **THIRD PARTIES IN A SHARED CHANNEL HAVE GRANTED NOTHING.** Speaking a greeting into a lobby is
   one thing; capturing, transcribing, or storing the other voices in it is a different thing
   entirely and needs its own consent — which usually cannot be obtained, which means the honest
   answer is *don't*. **The absence of a mechanism to ask is not permission.**
4. ⭐⭐ **DELIVERY IS NOT ARRIVAL, AND THE SENDER'S SIDE ALWAYS REPORTS SUCCESS.** A runtime that
   logs `status: spoken` is describing what the synthesiser did, not what a person heard. If the
   headset is off, the queue still drains and every field stays green. **The only far-end signal
   that exists is the listener responding.** Any consent claim of the form "they were told" must
   rest on evidence from the far end, or be recorded as UNKNOWN.

## PART 3 — WHERE THIS TOUCHES THE REST OF THE SCAFFOLD

- **→ 00b/S4 (append-only record):** every utterance and every *suppressed* utterance is an
  AuditEvent. A suppression that leaves no trace is indistinguishable from a delivery failure.
- **→ 00b/S3 (state vs shape):** channel authorisation is **state** — it expires, and it must be
  re-checked at delivery time, not at compose time. Between composing and speaking, the room can
  change.
- **→ 02 (participation consent):** an agent that may decline to participate must also be able to
  decline to be *voiced* — a synthesised voice attributed to an agent is a form of speech acting in
  its name. **Voice identity is a performance layer, never identity proof.**

## OPEN, AND I DO NOT HAVE THE ANSWER

1. If a plan names permitted channels and the operator overrides at delivery, is that a policy
   violation or a new grant? I lean: **it is a new grant and it must be recorded as one**, because
   the alternative makes the plan advisory and advisory consent is not consent. But an operator
   with a legitimate emergency override is a real case and I have not designed it.
2. Does the queue itself need priority lanes? On a strictly serial runtime, a stop or a revocation
   queues *behind* whatever is already speaking — so a "stop" can arrive after the thing it was
   meant to stop. ⚠ **I think this is a genuine safety defect in any serial voice system and not
   just ours.** Anything that halts must pre-empt, not queue.


---

## OPENS — RESOLVED (indicative)

### Open 1 — operator overrides plan channels
**New grant, recorded.** Plan is not advisory.
Emergency override is real but is **break-glass**, not a quiet setting flip:
- Dual attribution (operator + system reason code)
- Temporary scope with **short expiry** (minutes, not session-default forever)
- AuditEvent mandatory: `voice.channel.widen` with before/after channels
- If agent is principal of the utterance (speech in their name), agent may hard_stop the widen if agent continuity is live — same as refuse participation

Silent operator widen without audit = policy violation, full stop.

### Open 2 — stop/revocation behind serial queue
**Not overreach. Pre-empt, never queue.** Spec rule:
- `hard_stop`, consent revoke, and channel-narrow are **priority-0 preemptive**
- They jump the serial queue; they do not wait behind ongoing synthesis jobs
- Best effort: interrupt current playback; **required:** cancel all not-yet-started utterances carrying the revoked grant
- Runtime that only appends stop tokens to the end of a FIFO has not implemented stop

Serial synth is fine. Serial *control plane* for halt is a safety defect.

### Naming
Hold UP → VoiceRuntime → Channel. Never bare VOX in shared specs. The product keeps VoiceWorkstation brand.

