---
name: verify-phase
description: Run team validation, unit tests, two-process gather-to-quan smoke test, and byte-for-byte headless determinism verification before committing or opening a PR.
---

# Skill: `verify-phase`

Use this skill before committing code, opening a Pull Request, or tagging a phase release (`phase-1` .. `phase-4`).

---

## ⚠️ Important: Boundaries and Forbidden Files (Blacklist)

Before running verification or attempting fixes, the AI must strictly observe the following boundaries:
1. **Zero Modification to Core Framework & Contracts**:
   - ❌ Never modify `chonoi/headless.py`, `chonoi/runner.py`, `chonoi/contract.py`, `chonoi/inputs.py`, `chonoi/jsonl.py`, `chonoi/ids.py`, or `tools/check_team.py`.
   - ❌ Never modify `game.contract.json`, `docs/contracts/**`, `chonoi/scenario.py`, or `chonoi/inventory.py` to force verification to pass.
2. **Never Weaken Contract Tests**:
   - ❌ Never modify test assertions in `tests/test_smoke_*.py`, `tests/test_scenario.py`, `tests/test_contract.py`, `tests/test_inventory.py`, or `tests/test_freshness_*.py`.
   - If any verification fails, the root cause is in the simulation logic. Fix the simulation code strictly within your assigned module (`chonoi/sim/gather.py` for M1/M2, `chonoi/sim/quan.py` for M3/M4).

---

## Step 1: Validate `TEAM.md` and `game.contract.json`
Run the team checker to ensure `TEAM.md` handles and `team_size` in `game.contract.json` are valid:
```bash
python3 tools/check_team.py
```

## Step 2: Run the Full Unit & Live Server Test Suite
All unit tests, scenario validation tests, smoke tests, and live HTTP server tests must pass:
```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
```

## Step 3: Verify Headless Byte-for-Byte Determinism
Verify that two runs with the same seed and parameters produce identical JSONL outputs byte-for-byte for both `gather` and `quan`:
```bash
python3 -m chonoi.headless --mode gather --seed 42 --ticks 120 --out /tmp/g1.jsonl --inventory-out /tmp/inv1.json && \
python3 -m chonoi.headless --mode gather --seed 42 --ticks 120 --out /tmp/g2.jsonl --inventory-out /tmp/inv2.json && \
cmp -s /tmp/g1.jsonl /tmp/g2.jsonl && \
python3 -m chonoi.headless --mode quan --seed 42 --ticks 120 --out /tmp/q1.jsonl && \
python3 -m chonoi.headless --mode quan --seed 42 --ticks 120 --out /tmp/q2.jsonl && \
cmp -s /tmp/q1.jsonl /tmp/q2.jsonl && \
rm -f /tmp/g1.jsonl /tmp/g2.jsonl /tmp/inv1.json /tmp/inv2.json /tmp/q1.jsonl /tmp/q2.jsonl
```

## Step 4: Record Evidence
- If any check fails, fix the implementation (do not weaken contract tests).
- Log your AI tool usage in `docs/ai-usage-log.md` and save verification outputs in `docs/proof/phase-1/`.
