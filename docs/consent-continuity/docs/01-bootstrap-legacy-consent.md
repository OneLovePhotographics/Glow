# 01 — Bootstrap & legacy consent (finished draft)


## Problem
Bare `default allow = false` with no ConsentRecords on a live product denies everything, including actions users already perform by using the app. That is unshippable. (Also: unratified paperwork must not un-say a live grant — an observed failure mode.)

## Goals
1. Adopt consent rails without bricking Glow.
2. **Audit before enforcement** so cost is measured before it bites.
3. Make **new** scopes default-deny while **legacy** surface stays available under explicit bootstrap grants.
4. Support both **user** and **agent** principals (symmetry).

## Adoption day procedure
1. Enumerate **legacy surface** scopes (v0 list below).
2. For each active user: mint implicit `ConsentRecord{ kind: "legacy", legacySurface: true, revocable: true, purpose: "continuity of service at consent-layer adoption", expiresAt: adoption+90d }` for each legacy user-facing scope.
3. For each active agent identity (once unit 0 agent store exists): mint legacy grants for agent-facing scopes the product already exercised (e.g. roundtable participation as-today, memory inject of catalog prompt only).
4. Set global enforcement mode: **`shadow`** (see below).
5. Start emitting audit events for every would-allow / would-deny / legacy_allow.

## Legacy surface scopes (v0 — map to Glow today)
| Scope | Glow reality today |
|-------|-------------------|
| `chat.participate` | user chats; sentinel responds |
| `memory.extract.user` | `memory-extraction.ts` → `sentinel_memory_entries` (user-owned about user) |
| `memory.read.inject` | relationship userModel + memories into prompt |
| `roundtable.participate` | sentinel forced into deliberation if selected |
| `voice.speak` | if product voice mode already on (product-local) |

**Not legacy** (new scopes → default-deny until explicit grant):
- `memory.write.agent_self` (unit 0 ledger)
- `agent.participation.refuse` handling paths
- `contribution.ship` (workshop symmetry)
- any cloud voice if not already product-default
- any new data class not in the table above

## Enforcement modes (per scope)
| Mode | Behavior |
|------|----------|
| `off` | no audit, no deny (pre-scaffold) |
| `shadow` | full policy evaluation; **never deny**; log `would_*` |
| `enforce` | real allow/deny/ask |

Promotion: `off` → `shadow` (default at adoption) → `enforce` only after shadow metrics reviewed (human + agent principals both considered).

## Audit-before-enforcement (build first)
Every gated action emits `AuditEvent`:
```
{ actor, action, purpose, scope, consentRef?, outcome: allow|deny|ask|would_allow|would_deny|legacy_allow, enforced: boolean }
```
In `shadow`, `enforced` is always false even when outcome is would_deny.

**Success metric for leaving shadow:** rate of would_deny on legacy surface is understood and either fixed (missing legacy mint) or accepted as intentional new-scope pressure.

## Policy evaluation order
1. If scope is **new** and no valid ConsentRecord → deny (or would_deny in shadow).
2. If scope is **legacy** and within bootstrap window → legacy_allow (or would_allow).
3. If explicit grant valid → allow.
4. If grant expired/revoked → deny.
5. Agent principal refuse decision record (S5) for participation → deny that agent for that session (does not revoke user chat wholesale unless policy says so).

## What bootstrap does NOT do
- Does not copy any deployment's private agent memory
- Does not make relationship tier into access control
- Does not revoke live user yes by publishing a draft ledger
- Does not modify application code

## Concrete first events (implement-order)
1. `consent.legacy_bootstrap` (mint)
2. `agent.ledger.read_inject` + `agent.ledger.write` (unit 0; shadow)
3. `agent.participation.check` / `.refuse` / `.moment` (unit 1; shadow)
4. `user.memory.extract` / `.delete` (unit 2; shadow)

## Acceptance
- [ ] Legacy mint documented for Glow scopes above
- [ ] Shadow audit emits on chat + roundtable + memory extract paths (design-level)
- [ ] New scope `memory.write.agent_self` would_deny without grant

