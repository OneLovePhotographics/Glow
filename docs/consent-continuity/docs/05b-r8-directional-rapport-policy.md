# R8 — directional tier-as-access prohibition (2026-08-15)


## Wrong first draft
"No type may hold both rapport metric and capability" — false positive on AgentUserRelation (trustHint + participationDefault). Agent declining more readily after boundary crossings is **memory**, docs/02 cap 4.

## Correct law (directional)
- **Forbidden:** rapport grants the **USER** deeper capability.
- **Permitted:** the **AGENT's** own willingness has a history.

## R8 (scaffold-enforced)
No type consumed by the **policy evaluator** may carry a rapport metric.
Checked on: ParticipationCheckInput, ConsentRecord, HandDescriptor, UtteranceChannelAuth.

## Glow implementation requirement
`relationshipLevel` and user×sentinel rapport scores must not appear in policy evaluator inputs.
Relationship tier must not mint or widen ConsentRecords.
Agent participationDefault may still remember history.

Regression guard — fixture-proven, not a live product bug report.
