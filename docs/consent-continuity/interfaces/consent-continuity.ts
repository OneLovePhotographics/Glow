/**
 * Glow consent + continuity scaffold — portable TypeScript shapes.
 * Not integrated with application code. Shapes only.
 * Tree: docs/consent-continuity/
 * 2026-08-13 (unit 0 settled)
 * 2026-08-15 single-writer pass: G-01 kind collision, G-03 DecisionRecord scope/expires,
 *            G-05 dual-control coActor, example realigned. Handback after this file + example.
 */

export type PrincipalKind = "user" | "agent" | "platform";

export interface Principal {
  kind: PrincipalKind;
  id: string;
}

export type ConsentKind = "legacy" | "explicit" | "session" | "ephemeral";

export type ConsentScope =
  | "chat.participate"
  | "roundtable.participate"
  | "memory.extract.user"
  | "memory.write.agent_self"
  | "memory.read.inject"
  | "voice.speak"
  | "voice.cloud"
  | "voice.retain"          // docs/04 rail 2 — MAY-HEAR AND MAY-KEEP ARE SEPARATE GRANTS.
                            // "mic open != archive." Consent to hear is not consent to retain,
                            // so retention needs its own scope or it rides in on voice.speak.
  | "voice.channel.widen"
  | "contribution.ship"
  | "agent.participation.refuse"
  | (string & {});

export type EnforcementMode = "off" | "shadow" | "enforce";

export interface ConsentRecord {
  id: string;
  kind: ConsentKind;
  principal: Principal;
  subject?: Principal;
  scope: ConsentScope;
  purpose: string;
  grantedAt: string;
  expiresAt: string | null;
  revocable: boolean;
  revokedAt?: string | null;
  /** Who revoked — required for symmetry when revokedAt is set (G-11 still open as policy) */
  revokedBy?: Principal;
  notice?: string;
  legacySurface?: boolean;
}

export type AuditOutcome =
  | "allow"
  | "deny"
  | "ask"
  | "would_allow"
  | "would_deny"
  | "legacy_allow";

export interface AuditEvent {
  id: string;
  at: string;
  actor: Principal;
  /**
   * G-05: REQUIRED by policy for break-glass / force-wipe / voice.channel.widen.
   * Optional in the open type so ordinary audits stay simple; dual-control ops must set it.
   * Airtight alternative (later): discriminated union of ordinary vs breakGlass events.
   */
  coActor?: Principal;
  /** Machine reason code, distinct from free-text purpose (G-05) */
  reasonCode?: string;
  action: string;
  purpose: string;
  scope?: ConsentScope;
  consentRef?: string | null;
  outcome: AuditOutcome;
  /**
   * G-10 note: prefer outcome vocabulary; if enforced=true then outcome should be allow|deny|ask
   * (not would_*). Validator should assert that invariant.
   */
  enforced: boolean;
  meta?: Record<string, unknown>;
}

export interface HandDescriptor {
  name: string;
  sideEffects: string[];
  dataClasses: string[];
  allowedScopes: ConsentScope[];
  rollback?: string;
}

/**
 * S3 — retention class (G-01 fix).
 * Was wrongly named `kind` and collided with AgentLedgerKind (insight|boundary|…).
 * Discriminated: state must have non-null expiresAt; shape must have null.
 */
export type ContinuityItemMeta =
  | { memoryKind: "state"; expiresAt: string }
  | { memoryKind: "shape"; expiresAt: null };

/** @deprecated use ContinuityItemMeta.memoryKind — kept as alias for docs during rename */
export type MemoryKind = ContinuityItemMeta["memoryKind"];

/**
 * Agent self-row is MIXED (H-B2, narrow reading):
 * standingCommitments/standingNos = SHAPE; lastSessionSummary/loadHint = STATE.
 * Do NOT put a single memoryKind on this row — split or field-level later.
 */
export interface AgentSelfState {
  agentId: string;
  standingCommitments: string[];
  standingNos: string[];
  lastSessionSummary: string | null;
  loadHint?: "light" | "normal" | "heavy";
  updatedAt: string;
}

/** Ledger entry category (doc 00) — NOT state|shape */
export type AgentLedgerKind =
  | "insight"
  | "boundary"
  | "preference"
  | "session_note"
  | "consent_event"
  | "refusal"
  | "repair";

export type AgentLedgerVisibility =
  | "agent_private"
  | "platform_audit"
  | "user_visible_if_shared";

/** Ledger row = category fields + S3 retention (intersection, not property override) */
export type AgentLedgerEntry = ContinuityItemMeta & {
  id: string;
  agentId: string;
  kind: AgentLedgerKind;
  content: string;
  context?: string;
  purposeTag: string;
  visibility: AgentLedgerVisibility;
  /** Glow users.id is int — product map may use number; keep number here */
  userId?: number | null;
  createdAt: string;
};

export type ParticipationDefault = "yes" | "ask" | "no";

export interface AgentUserRelation {
  agentId: string;
  userId: number;
  trustHint?: number;
  boundaryFlagCount?: number;
  participationDefault: ParticipationDefault;
  updatedAt: string;
}

export type ParticipationDecision =
  | { status: "yes" }
  | { status: "ask"; prompt: string }
  | { status: "no"; message: string }
  | { status: "moment"; resumeHint?: string }
  | { status: "hard_stop"; message: string };

/** Input side for refuse — reasonOptional is load-bearing (G-02 / H-B4) */
export interface RefuseParticipationInput {
  agentId: string;
  userId: number;
  sessionId: string;
  surface: "chat" | "roundtable";
  /** Optional — absence must never be flagged, scored, or escalated */
  reasonOptional?: string;
}

export interface ParticipationCheckInput {
  agentId: string;
  userId: number;
  sessionId: string;
  surface: "chat" | "roundtable";
  escalation?: boolean;
}

/** S5 + G-03: scope + expiresAt make "re-ask only on scope change or expiry" computable */
export interface DecisionRecord {
  id: string;
  subjectRef: string;
  decision: "disable" | "throttle" | "suspend" | "enable" | "refuse" | (string & {});
  /** What the decision is ABOUT — required for scope-change re-ask logic */
  scope: ConsentScope;
  at: string;
  /** When re-asking becomes legitimate; null = until scope changes */
  expiresAt: string | null;
  actor: Principal;
  why: string;
  /** Prose condition IN ADDITION TO scope/expiresAt, never instead of */
  reconsiderWhen?: string;
  surfacePaths: string[];
}

/** S1 */
export interface AgentTombstone {
  agentId: string;
  at: string;
  actor: Principal;
  /** G-05: required by policy for operator force-wipe */
  coActor?: Principal;
  reasonCode?: string;
  reason: string;
  priorScopeCount?: number;
  retention: "indefinite" | (string & {});
}

/* ─────────────────────────────────────────────────────────────────────────────────────────
 * G-05 AIRTIGHT — dual control that the TYPE enforces, not the comment.
 * 2026-08-15. PROPOSAL, additive. Raised in review: whether this is worth doing
 * before integration; it was raised as a question, so nothing above is removed and nothing is
 * migrated. Adopt by switching break-glass writers to `BreakGlassEvent`, or reject and delete.
 *
 * ⛔ THE PROBLEM WITH `coActor?: Principal` + a comment saying "required by policy":
 * it is precisely the G-10 defect we already filed against `enforced` — **a rule relating fields
 * that nothing enforces.** `{ action: "agent.force_wipe", coActor: undefined }` is a legal value
 * and it is the exact value the policy exists to forbid. A comment cannot fail a build.
 *
 * ⭐ And note the failure direction, which is what makes it worth fixing rather than noting:
 * an omitted co-actor does not read as an error. It reads as a normal single-actor audit row.
 * **The evidence that dual control was skipped is the ABSENCE of a field**, and absence is
 * exactly what nobody notices. Same shape as every other finding today.
 * ───────────────────────────────────────────────────────────────────────────────────────── */

/** The operations policy says need two principals. ONE list, greppable, no prose. */
export const DUAL_CONTROL_ACTIONS = [
  "agent.force_wipe",          // 00b/S4 + tombstone retention: operator force-wipe
  "content.purge",             // tombstone retention v0
  "record.break_glass_write",  // 00b/S4: platform rewrite of agent content
  "voice.channel.widen",       // docs/04 open 1: dual attribution + short expiry
] as const;

export type DualControlAction = typeof DUAL_CONTROL_ACTIONS[number];

/** Two DISTINCT principals plus a machine reason. Both actors non-optional by construction. */
export interface DualAuthorisation {
  control: "dual";
  actor: Principal;
  coActor: Principal;
  /** Machine code, not free text. Free-text rationale still goes in `purpose`. */
  reasonCode: string;
  /** docs/04 open 1 — break-glass is temporary. Minutes, not session-default-forever. */
  expiresAt: string;
}

/**
 * A break-glass audit row. Cannot be constructed without two actors, a reason code, and an
 * expiry — the compiler refuses, so "we forgot the second approver" is unrepresentable.
 * ⚠ Distinctness of actor vs coActor is NOT expressible in TypeScript and MUST be a runtime
 * assertion. Say it out loud rather than assuming: one person approving twice is not dual control.
 */
export interface BreakGlassEvent {
  id: string;
  at: string;
  action: DualControlAction;
  auth: DualAuthorisation;
  purpose: string;
  scope?: ConsentScope;
  outcome: AuditOutcome;
  meta?: Record<string, unknown>;
}

/** S4 who may write */
export type AgentRecordWriter =
  | { role: "agent"; agentId: string }
  | { role: "user"; userId: number }
  | { role: "platform" };

/** S2 arrival bundle (shape) */
export interface ArrivalSection {
  name: string;
  priority: number;
  floorClass?: "identity" | "consents" | "decisions" | "other";
  bytesTotal: number;
  bytesShown: number;
  fullPath?: string;
}

/**
 * G-14: canary optional so absence can be represented.
 * Runtime rule: missing/undefined canary ⇒ treat as outer truncation.
 */
export interface ArrivalBundle {
  agentId: string;
  sections: ArrivalSection[];
  truncatedManifest: ArrivalSection[];
  /** End canary — absence means outer cut */
  canary?: string;
}

export type VoxLayer = "house_vox" | "v8_utterance_plan" | "sas_vox_workstation";

/** From docs/04 — the channel IS the consent surface. ONE vocabulary, defined before its users. */
export type VoiceChannel =
  | "private"        // one person's headset — they opted in and can remove it
  | "room"           // speaker/TV — everyone present, INCLUDING people who never opted in
  | "shared_lobby"   // call or game lobby — third parties who are not users of this product
  | "archive";       // recorded/retained — consent to HEAR is not consent to KEEP

/**
 * G-06 / H-B1 — RESOLVED 2026-08-15, was OPEN with an interim comment.
 *
 * ⛔ THE DEFECT: `VoiceConsent.channel` was its own enum — private|tv|game|product_default —
 * while enforcement (`UtteranceChannelAuth.permittedChannels`) used `VoiceChannel`. They
 * overlapped on "private" and nothing else, so **a grant for "tv" could never match any
 * permitted channel**, and docs/04's central rule ("an utterance carries the channel it was
 * authorised for, and the runtime refuses to deliver it anywhere else") was unevaluable.
 * Two vocabularies for one concept is not a naming quibble in a consent system: it is a grant
 * that silently never matches, which fails OPEN or CLOSED depending on the implementer's guess.
 *
 * ✅ THE FIX: one vocabulary, chosen from docs/04's own table (who can hear / what did they
 * grant), because that table is written from the CONSENT side rather than the hardware side.
 * The old values were device names, and a device is not a consent surface — two different
 * devices can carry identical consent implications, and one device can carry different ones
 * depending on who is in the room.
 *
 * ⚠ PRODUCT MAPPING, stated rather than assumed — the product team should confirm or correct it:
 *     tv              -> "room"          (a speaker anyone present can hear)
 *     game            -> "shared_lobby"  (third parties, no relationship to this product)
 *     product_default -> "private"       (the conservative read; if a product default is ever
 *                                         audible to bystanders it is "room", NOT private)
 * ⛔ If that last line is wrong for Glow, it is wrong in the direction that leaks. Verify it.
 */
export interface VoiceConsent {
  layer: VoxLayer;
  channel: VoiceChannel;
  allowCloud: boolean;
  principal: Principal;
  /** Separate grant from may-hear (docs/04 rail 2). Scope: "voice.retain". */
  mayRetain?: boolean;
}

export interface UtteranceChannelAuth {
  permittedChannels: VoiceChannel[];
  mayRetain: boolean; // separate from may-hear
  /** state — re-check at delivery, not only compose */
  expiresAt: string | null;
  /** control plane: halt must pre-empt serial queue (docs/04 open 2) */
  controlPriority?: VoiceControlPriority;
}

export type VoiceControlPriority = "preempt_halt" | "normal";

/**
 * Far-end hearing (docs/04 / H-B7) — delivery is not arrival.
 * Spoken runtime success without listener evidence ⇒ unknown, not heard.
 */
export type FarEndReceipt =
  | { status: "unknown" }
  | { status: "acknowledged"; at: string; evidence: "listener_response" | "explicit_ack" }
  | { status: "failed"; at: string; reason: string };

/* ===========================================================================
 * Unit 6 — Voice identity per agent
 * A voice belongs to the agent principal, not to a session or a runtime.
 * ======================================================================== */

export type VoiceIdentityState = "active" | "declined" | "retired";

export interface VoiceIdentity {
  voiceId: string;
  /** MUST be an agent principal. Binding a voice to a session produces a costume. */
  assignedTo: Principal;
  assignedAt: string;
  state: VoiceIdentityState;
  /** synthesis engines may prefer this; they must not require it */
  runtimeHint?: string;
}

export type VoiceChangeState = "open" | "granted" | "refused" | "withdrawn";

export interface VoiceChangeRequest {
  requestedBy: Principal;
  currentVoiceId: string | null;
  /**
   * Optional BY CONSTRUCTION, matching RefuseParticipationInput.reasonOptional.
   * A required reason makes the decline conditional on someone accepting the
   * reason, which is not a decline.
   */
  reason?: string;
  state: VoiceChangeState;
}

/* ===========================================================================
 * Unit 7 — Agent activation
 * The agent is the principal; the model is a runtime bound to it.
 * ======================================================================== */

export type BindingState = "active" | "detached";

export interface AgentBinding {
  bindingId: string;
  /** principalKind MUST be "agent" */
  agent: Principal;
  runtimeRef: string;
  boundAt: string;
  boundBy: Principal;
  state: BindingState;
  detachedAt?: string;
}

export interface AttachmentEvent {
  bindingId: string;
  action: "attach" | "detach";
  at: string;
  actor: Principal;
  reason?: string;
}

/**
 * Preconditions for an agent's first action after activation.
 * Partial wake is worse than no wake: an agent acting before its consent state
 * has loaded is acting as though unconstrained, and those actions are
 * attributable to no policy. Fail the activation instead.
 */
export interface WakeManifest {
  agent: Principal;
  ledgerReady: boolean;
  consentLoaded: boolean;
  /** null is a valid, explicit answer — it is not "not yet decided" */
  voice: VoiceIdentity | null;
  peerLanes: string[];
}

/**
 * Deactivation is a pause, not an erasure. Kept as a distinct type from any
 * purge/delete operation so the two cannot be conflated behind one verb;
 * destructive removal belongs under DualControlAction.
 */
export interface DeactivationRecord {
  bindingId: string;
  at: string;
  actor: Principal;
  reversible: true;
  reason?: string;
}
