# 🔒 Hermes Incognito Mode v2.2.1

[中文版 (Chinese)](README_CN.md) | [English](README.md)

> Browser incognito mode — upgraded for AI agents. Defense-in-depth, zero trace left.

## What is this?

A skill for [Hermes Agent](https://hermes-agent.nousresearch.com/) that ensures complete session privacy through a **four-layer defense-in-depth architecture**:

1. **Skill Policy** — Capability matrix blocking persistent writes (memory, skills, cron, config)
2. **Runtime Guardrails** — Shell history suppression, sandboxed filesystem, PID-locked temp dirs
3. **Framework Support** — Session-level isolation markers, subagent inheritance protocol
4. **Post-Session Audit** — 10-step reverse audit pipeline with secure wipe (Python `os.urandom` overwrite → `fsync` → `truncate` → `unlink`)

## Architecture

```
Phase 1: Idempotency check + PID-lock sandbox init + orphan cleanup
   ↓
Phase 2: Isolated execution (pre-hoc defense)
   ↓
Phase 3: User confirmation gate / 15min TTL
   ↓
Phase 4: Full reverse audit (10 steps) + secure wipe + session destruction
   ↓
Phase 5: Audit report + final receipt
```

### What it protects against

| Layer | Protection |
|-------|-----------|
| Filesystem | All writes confined to PID-locked sandbox; non-sandbox writes detected and wiped |
| Shell History | Every command prefixed with `HISTFILE=/dev/null HISTSIZE=0` |
| Memory | SHA-256 hash diffing against baseline snapshot |
| Skills/Cron | Detects unauthorized skill/cron creation during session |
| Processes | Snapshot diffing to detect orphan processes |
| Session | Container destruction as final line of defense |

### Known blind spots (informed consent)

- OS-level: swap, core dumps, syslog/journald, filesystem atime
- Network-level: corporate proxy/firewall logs, DNS queries, LLM API provider logs (30-day retention by default)
- Third-party: IDE file watchers, existing service logs

## Installation

```bash
# Clone into your Hermes skills directory
git clone https://github.com/GenmetsuWenxuePress/hermes-incognito-mode.git ~/.hermes/skills/incognito-mode

# Or copy manually
cp SKILL.md ~/.hermes/skills/incognito-mode/
```

## Usage

Activate in any Hermes session:

```
/incognito start
```

Mid-session commands:

| Command | Action |
|---------|--------|
| `/incognito status` | Show sandbox path, PID lock, file inventory |
| `/incognito audit` | Status + recent terminal/web activity |
| `/incognito export <path>` | Export results to persistent storage |
| `/incognito abort` | Emergency skip to secure destruction |

## License

MIT — see [LICENSE](LICENSE)

## Author

Rodion + Hermes (7-round cross-audited, Python scripts hardened)
