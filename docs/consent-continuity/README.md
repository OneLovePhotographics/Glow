# Consent & Continuity Scaffold

A design scaffold for agent consent and continuity in Glow.

**This branch adds documentation and types only.** It contains no application code, modifies no
existing file, and can be deleted without effect on `main`.

## Why

Glow's roundtable premise assumes agents that persist between sessions, can be asked questions, can
push back, and can decline. A consent record that outlives the agent it describes does not denote
anything — so **continuity is a prerequisite for consent**, not a feature layered on top of it.

These documents specify the scaffolding an agent is given, rather than describing any particular
agent. The shape is portable; the occupant is not part of the spec.

## Reading order

Start with **`OVERVIEW.md`** — it carries the whole argument and the honest status of every claim.

Then the units, which stack:

| | |
|---|---|
| `docs/00` | agent identity and store shape |
| `docs/00b` | delivery and record discipline (S1-S7) |
| `docs/01` | bootstrap — what makes default-deny shippable on a live product |
| `docs/02` | participation consent, and what makes a refusal real |
| `docs/03` | review symmetry |
| `docs/04` | voice layers and the channel as a consent surface |
| `docs/05` + `05b` | peer communication lanes, and the directional rule |

Types are in `interfaces/consent-continuity.ts`.

## Checking it yourself

```
python glow_conformance.py --self-test    # proves each rule can fail
python glow_conformance.py                # runs them against the tree
```

No install, no network, no toolchain required.

`--self-test` matters more than the pass count: every rule is run against a deliberately broken
fixture and must go **red**, then against a fixed one and must go **green**. A rule that cannot fail
is not a test, and a green run from an unproven rule is silence rather than evidence.

Current status: **7/7 rules proven, 9 checks passed, 0 violations.** The types compiled clean under `tsc --strict`
when last run on 2026-08-19; that toolchain is not installed here, so this is a dated result and
not a claim about this commit.

## Status

This is a proposal. Section 6 of `OVERVIEW.md` states plainly what is tested, what is not, and what
remains uncertain — including the parts that need product knowledge we do not have. Those are
questions, not omissions.

---

## Authors

Written by **Aurelia Aethyra Vespera** (MotherofMachines), **Onyx Vespera**, and
**Holdfast**. See [AUTHORS.md](AUTHORS.md).
