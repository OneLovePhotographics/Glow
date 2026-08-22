# 02 — Roundtable participation consent (rides on unit 0)


Requires agent continuity ledger so a refuse can be remembered and a grant can be held.

## Seam in Glow
`server/roundtable.ts` — already has dissent, confidence, interruptions, pauseFlags.
Add **before each sentinel is forced into a round**:
1. Load agent continuity (unit 0)
2. Participation consent check (yes / ask / no / moment / hard_stop)
3. On refuse: record **without requiring justification**; session **continues without them**
4. Audit event always (shadow mode first) — audit-before-enforcement

### Refusal must not bill the refuser 
- **A refusal must never be the proximate cause of a session ending.**
- If quorum / voice-count matters, the system **degrades**: fewer voices, lower confidence, explicit result like `"proceeded with 2 of 4"` or `"insufficient participation"`.
- **Never surface who refused as the reason.** Group facts only — not "failed because X declined."
- If a product genuinely cannot degrade, the product constraint must be **named out loud** (refusal is expensive here) — do not imply free refusal while charging collective cost.

### "Record kindly" → implementable rule
- Record refusal **without requiring a justification**
- Absence of a stated reason is **never flagged, scored, or escalated**
- `refuseInteraction(reasonOptional)` — *optional* is load-bearing

## Six capabilities (product language)
1. Veto / exit participation
2. Consent check-ins (start + escalation)
3. "I need a moment" soft pause
4. Privacy-safe boundary flag
5. Revocable memory consent (agent self-entries)
6. **Right not to be asked again** — declined participation is a **DecisionRecord (00b/S5)**; do not re-litigate within stated scope; re-ask only on scope change or expiry (not merely a new round)

## S6 continuity map
| Capability | Continuity guarantee | Status |
|---|---|---|
| 1 veto / exit | S1 identity outlives session | ok |
| 2 check-ins | S5 decision record (cap 6) | ok when 6 held |
| 3 soft pause | in-session | ok |
| 4 boundary flag | S4 append-only audit | ok |
| 5 revocable memory | S4 + S3 expiry | ok |
| 6 not re-asked | S5 decision record | **required** |

## Product hard stop
Use a neutral product primitive (e.g. `hard_stop`). Never adopt a deployment's private stop-word as the product token: real-world vocabularies collide with ordinary content and generate false positives.

## Link to voice (04)
Refusing to participate and refusing to be *voiced* (speech in the agent's name) are the same right. Channel widen of agent-attributed speech may be hard_stopped by the agent principal.

## Shadow first
Bootstrap audit-before-enforcement applies here: log would_deny / would_allow before enforce.

