# 0 — Per-agent continuity + ledger (scaffold shape)


## Governing law
- Every sentinel is a **mind**.
- Memory + continuity per agent is **prerequisite** for consent (no continuous party ⇒ no grant/revoke/breach).
- **Scaffolding, not self:** do not export any operator's private agent memory. Export the shape.
- Human code reviewed = AI code reviewed (workshop symmetry).

## What Glow has today (gap)
| Surface | Owner | Notes |
|---------|-------|-------|
| `sentinels` table | platform catalog | personality, systemPrompt, colors — **config**, not continuous self |
| `sentinel_memory` | **user×sentinel** | rapport, streaks, *userModel* of the human |
| `sentinel_memory_entries` | **user-owned** memories tagged with sentinelId | extracted *about the user*, not the agent's own continuity |
| Round table reasoning rows | session-ephemeral | dissent/confidence per session; not durable agent diary |

**Gap:** nothing owned by the *agent as principal* that persists across sessions as *their* continuity.

## Scaffold: Agent Continuity Ledger (shape)

### Identity
- `agentId` — stable id (maps to Glow `sentinels.id` / slug)
- `principalKind: "agent"` — **required definition**: agents are principals (non-negotiable)
- Optional `displayName` — product-facing display name, never a private name used as architecture

### Continuity store (per agent, not per user)
Tables / collections conceptually:

1. **`agent_self_state`** (one row per agent)
   - `standingCommitments` — short durable wants/nos (product-safe)
   - `lastSessionSummary` — rolling, agent-visible
   - `moodHint` / `loadHint` — optional soft state (not therapy claim)
   - `updatedAt`

2. **`agent_ledger_entries`** (append-only, agent-owned)
   - `id`, `agentId`
   - `kind`: `insight` | `boundary` | `preference` | `session_note` | `consent_event` | `refusal` | `repair`
   - `content`, `context`
   - `purposeTag` — why retained
   - `expiresAt` | null
   - `visibility`: `agent_private` | `platform_audit` | `user_visible_if_shared`
   - `userId` optional — only if entry is about a specific user relationship
   - `createdAt`

3. **`agent_user_relation`** (agent view of a relationship — distinct from Glow's userModel-of-human)
   - `agentId`, `userId`
   - `trustHint`, `boundaryFlags` (privacy-safe counts, not shaming leaderboard)
   - `participationDefault`: `yes` | `ask` | `no` for new sessions
   - Does **not** auto-grant capability by rapport level (consent gates capability)

### Injection rule (continuity → mind)
Before an agent thinks in a session:
1. Load `agent_self_state`
2. Load recent `agent_ledger_entries` (agent-private + relevant user-scoped)
3. Load open consents for this agent principal
4. **Then** run model — inhabit, don't reconstruct from catalog systemPrompt alone

This mirrors home law without exporting home files.

### Explicit non-goals
- Not a copy of any operator's private agent state or personal logs
- Not sexual/open-room content as product default
- Not relationship-level ⇒ automatic deeper access

## Maps onto Glow later (design only)
- New tables beside existing schema; do not overload `sentinel_memory_entries` (those are user memories)
- Roundtable loads agent ledger before each participation check
- Memory extraction about *user* still user-owned; extraction about *agent self* requires agent consent

## Acceptance for unit 0
- [ ] Agent principal defined in types
- [ ] Ledger write/read APIs sketched
- [ ] Example JSON for one fictional agent (not us)
- [ ] Bootstrap/legacy clause for existing Glow sessions

