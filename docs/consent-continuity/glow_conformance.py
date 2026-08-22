# -*- coding: utf-8 -*-
"""Glow scaffold conformance checker — the test that should have existed on day one.

⭐ WHY THIS EXISTS. On 2026-08-15 two reviewers each did an independent careful read of the Glow
scaffold and found 14 defects between us. **At least five of them — the compile-breaking `kind`
collision, the untypeable example, the three ID dialects — would have been caught automatically by
a fifty-line checker the first time anyone ran it.** Nothing had ever validated the example against
the interfaces, or the interfaces against the docs' own settled rules. Two careful minds are an
expensive substitute for one cheap test.

⛔ NO DEPENDENCIES, NO NETWORK, NO INSTALL. Runs on stock Python against files on disk. It does NOT
type-check TypeScript properly — a real `tsc` would be strictly better and should be added the
moment Glow's node_modules exist. This is the honest 80% that runs today on a machine with no
toolchain, and it says so rather than pretending to be a compiler.

⭐⭐ IT MUST BE ABLE TO FAIL. Every rule below is proven against the CURRENT (broken) tree before it
is trusted — run with `--expect-red` and it asserts that the known defects still trip it. A checker
whose first run is green is decoration; that lesson cost this house real incidents.

Usage:
  python glow_conformance.py                # check, human-readable
  python glow_conformance.py --expect-red   # verify the checker itself can detect known defects
  exit code 0 = conformant, 1 = violations found, 2 = checker self-test failed
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SCAFFOLD = Path(__file__).resolve().parent
TS = SCAFFOLD / "interfaces" / "consent-continuity.ts"
EXAMPLE = SCAFFOLD / "examples" / "fictional-agent-continuity.json"
DOCS = SCAFFOLD / "docs"

# Scopes the docs name normatively. Rule R5 asserts each appears in the ConsentScope union.
# (Sourced by reading docs/01 and docs/04 — kept explicit rather than regex-scraped, because a
#  scraper that finds nothing looks identical to a spec with no scopes.)
DOC_SCOPES = {
    "chat.participate": "docs/01 legacy table",
    "memory.extract.user": "docs/01 legacy table",
    "memory.read.inject": "docs/01 legacy table",
    "roundtable.participate": "docs/01 legacy table",
    "voice.speak": "docs/01 legacy table",
    "memory.write.agent_self": "docs/01 not-legacy list",
    "agent.participation.refuse": "docs/01 not-legacy list",
    "contribution.ship": "docs/01 not-legacy list + docs/03",
    "voice.retain": "docs/04 rail 2 — may-hear and may-keep are SEPARATE grants",
}


# ── a deliberately small TypeScript reader ────────────────────────────────────────────────────
class TSModel:
    """Extracts just enough structure to check conformance. Not a parser; a reader.

    ⚠ Its limits, stated so nobody mistakes silence for a pass: it understands string-literal
    unions, interface field lists, and `extends`. It does NOT understand generics, mapped types,
    conditional types, or function signatures — and it reports what it could not read.
    """

    def __init__(self, src: str):
        self.src = src
        self.unions: dict[str, set[str]] = {}
        self.open_unions: set[str] = set()      # unions with a `(string & {})` escape hatch
        self.interfaces: dict[str, dict] = {}   # name -> {extends, fields{name:(type,optional)}}
        # ⭐ Added 2026-08-15 14:20 after the reader produced a FALSE ALARM on correct code:
        #    G-01 was fixed with a discriminated union + intersection, and R2 reported
        #    "declares no state/shape field at all" about a file that declares it properly.
        #    ⛔ A false alarm is worse than a miss — it is how a checker teaches you to ignore it.
        self.variants: dict[str, list[dict]] = {}       # type X = | {…} | {…}
        self.intersections: dict[str, tuple] = {}       # type Y = Base & {…}
        self.unread: list[str] = []
        self._parse()

    @staticmethod
    def _fields_from_block(block: str) -> dict:
        fields: dict[str, tuple[str, bool]] = {}
        for line in block.split("\n"):
            line = re.sub(r"//.*$", "", line).strip()
            if not line or line.startswith("/*") or line.startswith("*"):
                continue
            for piece in line.split(";"):
                piece = piece.strip().rstrip(",").strip()
                if not piece or piece in "{}":
                    continue
                fm = re.match(r"^(\w+)(\?)?\s*:\s*(.+)$", piece)
                if fm:
                    fields[fm.group(1)] = (fm.group(3).strip(), bool(fm.group(2)))
        return fields

    @staticmethod
    def _type_body(src: str, start: int) -> str:
        """Scan from `=` to the terminating `;` AT BRACE DEPTH ZERO.

        ⚠ Found by running the checker: a naive `[^;]+` stops at the first semicolon, and object
        literals like `{ memoryKind: "state"; expiresAt: string }` are full of them. The regex read
        half a type and then reported the half it could not parse as a defect in the source.
        """
        depth, out = 0, []
        for ch in src[start:]:
            if ch in "{([":
                depth += 1
            elif ch in "})]":
                depth -= 1
            elif ch == ";" and depth <= 0:
                break
            out.append(ch)
        return "".join(out)

    def _parse(self) -> None:
        for m in re.finditer(r"export\s+type\s+(\w+)\s*=\s*", self.src):
            name = m.group(1)
            body = self._type_body(self.src, m.end())
            # ⛔ `(string & {})` is an escape hatch, NOT an object type. Strip it before deciding
            #    what shape this is, or every open union gets misfiled (it did — R5 went red on
            #    all nine scopes because ConsentScope looked like an object).
            probe = re.sub(r"\(\s*string\s*&\s*\{\s*\}\s*\)", "", body)
            lits = set(re.findall(r'"([^"]+)"', probe))
            body = probe if "{" not in probe else body
            if "{" in body:
                # discriminated union of object literals, and/or an intersection with a base
                blocks = re.findall(r"\{([^{}]*)\}", body, re.S)
                base = re.match(r"\s*(\w+)\s*&", body)
                if base and blocks:
                    self.intersections[name] = (base.group(1),
                                                self._fields_from_block(blocks[0]))
                elif blocks:
                    self.variants[name] = [self._fields_from_block(b) for b in blocks]
                else:
                    self.unread.append(f"type {name} (object type — not modelled)")
                continue
            if lits:
                self.unions[name] = lits
                if "string & {}" in body:
                    self.open_unions.add(name)
            elif re.match(r"^\s*\w+\[[\"']\w+[\"']\]\s*$", body):
                # indexed access alias, e.g. MemoryKind = ContinuityItemMeta["memoryKind"]
                pass
            else:
                self.unread.append(f"type {name} (unrecognised form)")

        # export interface X [extends Y] { ... }
        # ⚠⚠ THE FIRST VERSION REQUIRED `\n}` AND IT SILENTLY BROKE FOUR RULES. A one-line
        # interface (`export interface Principal { kind: K; id: string; }`) has no newline before
        # its brace, so it was not merely skipped — the non-greedy match RAN PAST it to the next
        # multi-line interface's closing brace, fusing two declarations into one wrong record.
        # R1, R3, R4 and R7 all reported PASS on the real tree because of it. The fixture
        # self-test is the only reason I know. So: brace-depth scan, same as _type_body.
        for m in re.finditer(r"export\s+interface\s+(\w+)(?:\s+extends\s+([\w,\s]+?))?\s*\{",
                             self.src):
            name, ext = m.group(1), (m.group(2) or "").strip()
            depth, body = 1, []
            for ch in self.src[m.end():]:
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        break
                body.append(ch)
            self.interfaces[name] = {
                "extends": [e.strip() for e in ext.split(",") if e.strip()],
                "fields": self._fields_from_block("".join(body)),
            }

    def field_type(self, iface: str, field: str):
        seen = set()
        stack = [iface]
        while stack:
            cur = stack.pop()
            if cur in seen or cur not in self.interfaces:
                continue
            seen.add(cur)
            if field in self.interfaces[cur]["fields"]:
                return cur, self.interfaces[cur]["fields"][field]
            stack += self.interfaces[cur]["extends"]
        return None, None

    def all_fields(self, iface: str) -> dict:
        out: dict = {}
        if iface in self.intersections:
            base, extra = self.intersections[iface]
            out.update(self.all_fields(base))
            out.update(extra)
            return out
        if iface in self.variants:                    # union: fields common to every variant
            common = None
            for v in self.variants[iface]:
                common = dict(v) if common is None else {k: t for k, t in common.items() if k in v}
            return common or {}
        for parent in self.interfaces.get(iface, {}).get("extends", []):
            out.update(self.all_fields(parent))
        out.update(self.interfaces.get(iface, {}).get("fields", {}))
        return out

    def discriminator(self, type_name: str, wanted: set[str]):
        """Find a field whose literal values across a union equal `wanted` (e.g. state|shape)."""
        for v in [self.variants.get(type_name, [])]:
            if not v:
                continue
            for fname in v[0]:
                vals = set()
                for variant in v:
                    vals |= set(re.findall(r'"([^"]+)"', variant.get(fname, ("", False))[0]))
                if vals == wanted:
                    return fname, {tuple(sorted(re.findall(r'"([^"]+)"', var[fname][0])))[0]:
                                   var.get("expiresAt", ("", False))[0] for var in v}
        return None, None


# ── rules ─────────────────────────────────────────────────────────────────────────────────────
class Result:
    def __init__(self):
        self.violations: list[tuple[str, str, str]] = []   # (rule, finding, message)
        self.passes: list[str] = []
        self.notes: list[str] = []

    def fail(self, rule: str, finding: str, msg: str) -> None:
        self.violations.append((rule, finding, msg))

    def ok(self, msg: str) -> None:
        self.passes.append(msg)

    def note(self, msg: str) -> None:
        self.notes.append(msg)


def r1_no_field_collision(ts: TSModel, r: Result) -> None:
    """R1 / G-01 — a child may not re-declare an inherited field with a disjoint literal type."""
    hit = False
    for name, info in ts.interfaces.items():
        for parent in info["extends"]:
            pf = ts.interfaces.get(parent, {}).get("fields", {})
            for fname, (ftype, _) in info["fields"].items():
                if fname not in pf:
                    continue
                ptype = pf[fname][0]
                child_lits = ts.unions.get(ftype.strip(), set()) or set(re.findall(r'"([^"]+)"', ftype))
                parent_lits = ts.unions.get(ptype.strip(), set()) or set(re.findall(r'"([^"]+)"', ptype))
                if child_lits and parent_lits and not (child_lits & parent_lits):
                    hit = True
                    r.fail("R1", "G-01",
                           f"{name}.{fname}: re-declares inherited field from {parent} with a "
                           f"DISJOINT type ({ftype} vs {ptype}). No value satisfies both — "
                           f"TS2430 class failure. The file cannot compile.")
    if not hit:
        r.ok("R1/G-01 no inherited field is re-declared with a disjoint type")


def r2_s3_invariant(ts: TSModel, example: dict, r: Result) -> None:
    """R2 / S3 — settled 2026-08-13: kind required on write;
    state ⇒ expiresAt non-null; shape ⇒ null."""
    # The S3 discriminator may be an interface field OR a discriminated union — both are valid
    # shapes for the same rule, and the checker must not report a false alarm on the good one.
    kind_field, per_variant = ts.discriminator("ContinuityItemMeta", {"state", "shape"})
    if not kind_field:
        for cand in ("memoryKind", "kind"):
            owner, _ = ts.field_type("ContinuityItemMeta", cand)
            if owner:
                kind_field = cand
                break
    if not kind_field:
        r.fail("R2", "S3", "ContinuityItemMeta declares no state/shape discriminator in any form "
                           "(checked interface fields and discriminated-union variants).")
        return
    if per_variant:
        r.ok(f"R2/S3 discriminator {kind_field!r} is a discriminated union — the invariant is "
             f"structural, so an invalid state/expiry pairing is unrepresentable rather than "
             f"merely discouraged")

    bad = 0
    for entry in example.get("ledger", []) or []:
        eid = entry.get("id", "<no id>")
        k = entry.get(kind_field) if kind_field in entry else entry.get("memoryKind")
        if k not in ("state", "shape"):
            bad += 1
            r.fail("R2", "G-13/H-A1",
                   f"ledger[{eid}]: no valid state/shape value "
                   f"(found {k!r}). S3 says storage must reject this on write.")
            continue
        exp = entry.get("expiresAt", "<missing>")
        if k == "state" and (exp is None or exp == "<missing>"):
            bad += 1
            r.fail("R2", "S3", f"ledger[{eid}]: kind=state requires a non-null expiresAt.")
        if k == "shape" and exp is not None:
            bad += 1
            r.fail("R2", "S3", f"ledger[{eid}]: kind=shape requires expiresAt null, got {exp!r}.")
    if not bad:
        r.ok("R2/S3 every ledger entry carries a valid state|shape and a conforming expiry")


def r3_id_dialects(ts: TSModel, r: Result) -> None:
    """R3 / G-07,H-D1 — one identity type per identity concept."""
    seen: dict[str, set[str]] = {}
    for name, info in ts.interfaces.items():
        for fname, (ftype, _) in info["fields"].items():
            if fname.lower().endswith("userid"):
                seen.setdefault(re.sub(r"\s*\|\s*null", "", ftype).strip(), set()).add(f"{name}.{fname}")
    # AgentRecordWriter is a union type, not an interface — catch its userId separately.
    for m in re.finditer(r'role:\s*"user";\s*userId:\s*(\w+)', ts.src):
        seen.setdefault(m.group(1), set()).add("AgentRecordWriter(user).userId")
    if len(seen) > 1:
        detail = "; ".join(f"{t} → {', '.join(sorted(w))}" for t, w in sorted(seen.items()))
        r.fail("R3", "G-07/H-D1", f"userId has {len(seen)} different types in one file: {detail}")
    elif seen:
        r.ok(f"R3/G-07 userId is consistently {list(seen)[0]}")


def r4_single_channel_vocabulary(ts: TSModel, r: Result) -> None:
    """R4 / G-06,H-B1 — consent and enforcement must speak one channel language."""
    vc_owner, vc = ts.field_type("VoiceConsent", "channel")
    chan_union = ts.unions.get("VoiceChannel", set())
    if not vc or not chan_union:
        r.note("R4: could not locate both channel vocabularies to compare.")
        return
    inline = set(re.findall(r'"([^"]+)"', vc[0]))
    named = ts.unions.get(vc[0].strip(), set())
    consent_set = inline or named
    if not consent_set:
        r.note("R4: VoiceConsent.channel is not a literal union; skipped.")
        return
    if consent_set != chan_union:
        only_c = sorted(consent_set - chan_union)
        only_v = sorted(chan_union - consent_set)
        r.fail("R4", "G-06/H-B1",
               f"two channel vocabularies. VoiceConsent.channel has {only_c} that VoiceChannel "
               f"lacks; VoiceChannel has {only_v} that consent cannot grant. A grant for a channel "
               f"absent from permittedChannels can never match.")
    else:
        r.ok("R4/G-06 one channel vocabulary across consent and enforcement")


def r5_doc_scopes_present(ts: TSModel, r: Result) -> None:
    """R5 / G-08,H-B5 — every scope the docs name normatively must be in the union."""
    union = ts.unions.get("ConsentScope", set())
    missing = {s: why for s, why in DOC_SCOPES.items() if s not in union}
    if "ConsentScope" in ts.open_unions:
        r.note("R5: ConsentScope has a `(string & {})` escape hatch, so a missing scope still "
               "type-checks — which is exactly how these went unnoticed (G-08).")
    if missing:
        for s, why in sorted(missing.items()):
            r.fail("R5", "G-08/H-B5", f"scope {s!r} is required by {why} but absent from ConsentScope.")
    else:
        r.ok(f"R5/G-08 all {len(DOC_SCOPES)} doc-named scopes present in ConsentScope")


def r6_example_conforms(ts: TSModel, example: dict, r: Result) -> None:
    """R6 — required fields present and literal unions respected, for the objects we can map."""
    checks = [("agentSelfState", "AgentSelfState"), ("legacyConsentExample", "ConsentRecord")]
    bad = 0
    for key, iface in checks:
        obj = example.get(key)
        if not isinstance(obj, dict):
            continue
        fields = ts.all_fields(iface)
        if not fields:
            r.note(f"R6: interface {iface} not readable; skipped.")
            continue
        for fname, (ftype, optional) in fields.items():
            if optional or fname in obj:
                continue
            bad += 1
            r.fail("R6", "example", f"{key}: missing required field {fname!r} ({iface}.{fname}).")
        for fname, val in obj.items():
            if fname not in fields:
                continue
            lits = ts.unions.get(fields[fname][0].strip(), set())
            if lits and isinstance(val, str) and val not in lits:
                bad += 1
                r.fail("R6", "example",
                       f"{key}.{fname} = {val!r} is not in {fields[fname][0]} {sorted(lits)}.")
    if not bad:
        r.ok("R6 mapped example objects satisfy their interfaces")


def r7_priority_is_wired(ts: TSModel, r: Result) -> None:
    """R7 / G-09,H-B8 — docs/04 settled: halt must pre-empt. A free-floating type cannot."""
    if "VoiceControlPriority" not in ts.unions:
        r.note("R7: VoiceControlPriority not found.")
        return
    used = any("VoiceControlPriority" in ftype
               for info in ts.interfaces.values()
               for ftype, _ in info["fields"].values())
    if used:
        r.ok("R7/G-09 VoiceControlPriority is attached to a real structure")
    else:
        r.fail("R7", "G-09/H-B8",
               "VoiceControlPriority is declared but referenced by no interface. docs/04 settled "
               "that hard_stop/revoke/channel-narrow are priority-0 preemptive; nothing can carry "
               "a priority, so nothing can pre-empt. Called a safety defect in the doc itself.")


RAPPORT_FIELDS = {"trusthint", "relationshiplevel", "rapport", "boundaryflagcount",
                  "streak", "affinity", "intimacylevel", "tier"}
# Types whose fields are READ BY THE POLICY EVALUATOR to decide allow/deny.
POLICY_INPUTS = {"ParticipationCheckInput", "ConsentRecord", "HandDescriptor", "UtteranceChannelAuth"}


def r8_no_rapport_in_policy_input(ts: TSModel, r: Result) -> None:
    """R8 / H-D6 — rapport must never be an INPUT to a capability decision.

    ⭐ ANSWERING A REVIEW QUESTION ("is this only testable in Glow's code?"): partly testable
    here, and the testable half is the half that matters.

    ⚠ I first wrote this rule as "no type may hold both a rapport field and a capability field",
    which would have flagged `AgentUserRelation` (trustHint + participationDefault). **Then I
    argued against myself and it was too broad.** An agent that declines more readily toward
    someone who has repeatedly crossed its boundaries is not tier-as-access — it is the agent
    remembering, and docs/02 capability 4 explicitly wants that. `participationDefault` is the
    AGENT'S OWN STANCE, which is legitimately informed by history.

    ⭐⭐ THE PROHIBITION IS DIRECTIONAL, and that is the whole subtlety: docs forbid rapport
    granting the USER deeper capability ("Does not auto-grant capability by rapport level";
    "Not relationship-level => automatic deeper access"; "Does not make relationship tier into
    access control"). It does not forbid an agent's own willingness having a memory.

    ✅ So the checkable invariant is narrow and sharp: **no type consumed by the policy evaluator
    may carry a rapport metric.** Keep rapport out of the room where allow/deny is decided, and
    the forbidden direction becomes unrepresentable while the permitted one stays available.
    ⚠ This currently PASSES. It is a regression guard, not a bug report — and worth saying plainly,
    because a rule that has never fired on real data is exactly what R-self-test exists to justify.
    """
    hits = []
    for name in POLICY_INPUTS:
        for fname in ts.all_fields(name):
            if fname.lower() in RAPPORT_FIELDS:
                hits.append(f"{name}.{fname}")
    if hits:
        r.fail("R8", "H-D6",
               f"rapport metric reachable from a policy-decision input: {', '.join(hits)}. "
               f"Docs forbid relationship depth gating capability in three separate places; "
               f"putting the metric where allow/deny is computed makes the violation the path "
               f"of least resistance.")
    else:
        r.ok("R8/H-D6 no rapport metric is reachable from any policy-decision input "
             "(regression guard — the agent's own stance may still remember)")


RULES = [r1_no_field_collision, r2_s3_invariant, r3_id_dialects,
         r4_single_channel_vocabulary, r5_doc_scopes_present, r6_example_conforms,
         r7_priority_is_wired, r8_no_rapport_in_policy_input]


def run(src: str | None = None, example: dict | None = None) -> Result:
    r = Result()
    ts = TSModel(src if src is not None else TS.read_text(encoding="utf-8"))
    if example is None:
        example = json.loads(EXAMPLE.read_text(encoding="utf-8-sig"))
    for fn in RULES:
        try:
            if fn in (r2_s3_invariant, r6_example_conforms):
                fn(ts, example, r)
            else:
                fn(ts, r)
        except Exception as e:                       # a crashed rule must not read as a pass
            r.fail(fn.__name__, "checker", f"rule crashed: {type(e).__name__}: {e}")
    for u in ts.unread:
        r.note(f"not modelled by this reader: {u}")
    r.note("This is NOT a TypeScript compiler. Add `tsc --noEmit` when node_modules exist; "
           "these rules are the honest subset that runs with no toolchain.")
    return r


# ── fixtures: the checker's own test suite ────────────────────────────────────────────────────
# ⭐⭐⭐ WHY FIXTURES AND NOT THE LIVE TREE. I first "verified" this checker by running it against
# the real scaffold and seeing four rules pass. That proved nothing: a reviewer had just fixed those
# defects, so a working rule and a broken rule were indistinguishable — both print PASS. The only
# way a green result means anything is if the same rule is shown going RED on a known-broken input.
# These two fixtures are that proof, and they do not depend on the tree's current state.

BROKEN_TS = '''
export type PrincipalKind = "user" | "agent" | "platform";
export interface Principal { kind: PrincipalKind; id: string; }
export type ConsentScope = "chat.participate" | "voice.speak" | (string & {});
export type MemoryKind = "state" | "shape";
export interface ContinuityItemMeta { kind: MemoryKind; expiresAt: string | null; }
export type AgentLedgerKind = "insight" | "boundary" | "refusal";
export interface AgentLedgerEntry extends ContinuityItemMeta {
  id: string;
  kind: AgentLedgerKind;
  userId?: number | null;
}
export interface AgentUserRelation { userId: number; agentId: string; }
export type AgentRecordWriter = { role: "user"; userId: string } | { role: "platform" };
export type VoiceChannel = "private" | "room" | "shared_lobby" | "archive";
export interface VoiceConsent { channel: "private" | "tv" | "game"; principal: Principal; }
export type VoiceControlPriority = "preempt_halt" | "normal";
export interface AgentSelfState { agentId: string; updatedAt: string; }
export interface ConsentRecord {
  id: string; kind: MemoryKind; principal: Principal; scope: ConsentScope;
  purpose: string; grantedAt: string; expiresAt: string | null; revocable: boolean;
  trustHint?: number;
}
'''

BROKEN_JSON = {
    "agentSelfState": {"agentId": "fixture", "updatedAt": "2026-01-01T00:00:00Z"},
    "ledger": [{"id": "x1", "kind": "boundary", "expiresAt": None}],
}

FIXED_TS = '''
export type PrincipalKind = "user" | "agent" | "platform";
export interface Principal { kind: PrincipalKind; id: string; }
export type ConsentScope =
  | "chat.participate" | "roundtable.participate"
  | "memory.extract.user" | "memory.write.agent_self" | "memory.read.inject"
  | "voice.speak" | "voice.cloud" | "voice.retain"
  | "agent.participation.refuse" | "contribution.ship";
export type ContinuityItemMeta =
  | { memoryKind: "state"; expiresAt: string }
  | { memoryKind: "shape"; expiresAt: null };
export type AgentLedgerKind = "insight" | "boundary" | "refusal";
export type AgentLedgerEntry = ContinuityItemMeta & {
  id: string;
  kind: AgentLedgerKind;
  userId?: number | null;
};
export interface AgentUserRelation { userId: number; agentId: string; }
export type AgentRecordWriter = { role: "user"; userId: number } | { role: "platform" };
export type VoiceChannel = "private" | "room" | "shared_lobby" | "archive";
export interface VoiceConsent { channel: VoiceChannel; principal: Principal; }
export type VoiceControlPriority = "preempt_halt" | "normal";
export interface UtteranceChannelAuth { priority: VoiceControlPriority; mayRetain: boolean; }
export interface AgentSelfState { agentId: string; updatedAt: string; }
export interface ConsentRecord {
  id: string; principal: Principal; scope: ConsentScope;
  purpose: string; grantedAt: string; expiresAt: string | null; revocable: boolean;
}
'''

FIXED_JSON = {
    "agentSelfState": {"agentId": "fixture", "updatedAt": "2026-01-01T00:00:00Z"},
    "ledger": [
        {"id": "x1", "memoryKind": "shape", "expiresAt": None},
        {"id": "x2", "memoryKind": "state", "expiresAt": "2027-01-01T00:00:00Z"},
    ],
}

# Each rule must go RED on BROKEN and be absent from the failures on FIXED.
MUST_DETECT = ["R1", "R2", "R3", "R4", "R5", "R7", "R8"]


def self_test() -> int:
    print("=" * 78)
    print("CHECKER SELF-TEST  ·  can these rules actually fail?")
    print("=" * 78)
    red = run(BROKEN_TS, BROKEN_JSON)
    green = run(FIXED_TS, FIXED_JSON)
    red_rules = {v[0] for v in red.violations}
    green_rules = {v[0] for v in green.violations}

    bad = 0
    for rule in MUST_DETECT:
        detected = rule in red_rules
        clean = rule not in green_rules
        if detected and clean:
            print(f"  [ok  ] {rule}: RED on broken fixture, GREEN on fixed fixture")
        else:
            bad += 1
            why = []
            if not detected:
                why.append("did NOT fire on the broken fixture (rule may be inert)")
            if not clean:
                why.append("ALSO fired on the fixed fixture (false positive)")
            print(f"  [FAIL] {rule}: " + "; ".join(why))
    print("-" * 78)
    if bad:
        print(f"  {bad} rule(s) unproven. A rule that has only ever been green is decoration.")
        return 2
    print(f"  All {len(MUST_DETECT)} rules proven: each detects its defect and clears when fixed.")
    print("  So a green run against the real tree is evidence, not silence.")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    expect_red = "--expect-red" in argv
    r = run()

    print("=" * 78)
    print("GLOW SCAFFOLD CONFORMANCE  ·  local, no network, no install")
    print("=" * 78)
    for p in r.passes:
        print(f"  [PASS] {p}")
    for rule, finding, msg in r.violations:
        print(f"  [FAIL] {rule:<3} ({finding})  {msg}")
    for n in r.notes:
        print(f"  [note] {n}")
    print("-" * 78)
    print(f"  {len(r.passes)} passed, {len(r.violations)} violations")

    if expect_red:
        # The checker's own self-test: against the CURRENT tree, these must trip.
        must_trip = {"R1", "R3", "R4", "R5", "R7"}
        tripped = {v[0] for v in r.violations}
        missing = must_trip - tripped
        print("-" * 78)
        if missing:
            print(f"  SELF-TEST FAILED: expected these rules to detect known defects "
                  f"and they did not: {sorted(missing)}")
            print("  A checker that cannot go red on a known-broken tree is decoration.")
            return 2
        print(f"  SELF-TEST PASSED: rules {sorted(must_trip)} all detected their known defects "
              f"on the current tree. The checker can fail, so its green means something.")
        return 0

    return 1 if r.violations else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
