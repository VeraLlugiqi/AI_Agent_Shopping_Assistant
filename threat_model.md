# STRIDE Threat Model: Shopping Assistant

## Scope

This threat model covers the local ADK shopping-assistant project files:

- `app/agent.py`
- `pyproject.toml`
- `.agents/CONTEXT.md`
- `.pre-commit-config.yaml`
- `.agents/hooks.json`
- `.agents/scripts/validate_tool_call.py`

## System Overview

The project defines an ADK retail shopping assistant backed by a Gemini model. A Shopping Manager Agent handles ordinary shopping help and delegates specialist tasks to a Discount Agent and FAQ Agent. The Discount Agent can call `redeem_discount_code(discount_code, user_id)` to redeem one of two single-use discount codes stored in process memory: `WELCOME50` and `SUMMER20`.

Local security controls include project guidance in `.agents/CONTEXT.md`, pre-commit hooks for whitespace and Semgrep scanning, and an agent tool-use hook that invokes `.agents/scripts/validate_tool_call.py` before `run_command` usage.

## System Boundaries

| Boundary | Trusted Side | Untrusted / Less Trusted Side | Notes |
|---|---|---|---|
| User prompt to LLM agent | ADK app and Python code | Retail customer input and prompt content | User text may attempt prompt injection or unauthorized tool use. |
| LLM to Python tool | `redeem_discount_code` implementation | Model-selected tool arguments | Tool arguments should be treated as untrusted even when selected by the model. |
| Runtime process to in-memory store | Python process memory | Concurrent requests, restarts, model calls | Redemption state is mutable and not durable. |
| Local repo to developer tooling | Repository configuration | Local machine environment and installed binaries | Pre-commit uses `language: system`, so behavior depends on local installed commands. |
| Agent hook to shell command validator | `validate_tool_call.py` | Hook JSON payload and requested command line | Validator only blocks a small denylist of command substrings. |
| Model configuration to external Gemini API | ADK model client | External model service and network path | Model credentials are expected from the runtime environment, not source code. |

## Entry Points

| Entry Point | File | Trust Level | Security-Relevant Behavior |
|---|---|---|---|
| Chat/user messages to the ADK agent | `app/agent.py` | Untrusted | User prompts can influence shopping advice and tool invocation. |
| `redeem_discount_code(discount_code, user_id)` | `app/agent.py` | Untrusted arguments | Redeems single-use discounts based on caller-provided code and user ID. |
| Gemini model initialization | `app/agent.py` | Sensitive configuration | Uses ADK/Gemini runtime credential configuration; no API key is committed in source. |
| Pre-commit hooks | `.pre-commit-config.yaml` | Local developer-controlled | Runs whitespace checks and `semgrep --config auto` on selected source files. |
| Agent PreToolUse hook | `.agents/hooks.json` | Local agent-control plane | Runs command validator before `run_command`. |
| Command validator stdin JSON | `.agents/scripts/validate_tool_call.py` | Untrusted hook input | Parses tool args and blocks only a narrow destructive-command denylist. |
| Dependency install/update | `pyproject.toml` | Supply-chain boundary | Pulls runtime and dev dependencies, including security tools. |

## Data Stores

| Data Store | File / Location | Data | Sensitivity | Notes |
|---|---|---|---|---|
| Discount store | `app/agent.py` `_DISCOUNT_STORE` | Discount code names, percent values, `redeemed_by` user ID | Medium | Process-local and mutable; reset on restart. |
| Gemini credentials | Runtime environment | API key or Vertex AI credentials | High | Credentials must remain outside source code and be supplied by the local or deployment environment. |
| ADK session/event state | Runtime-managed by ADK | Conversation history and tool calls | Medium to High | Not explicitly configured here; may contain user IDs or shopping data. |
| Hook configuration | `.agents/hooks.json` | Hook matcher and command | Medium | Controls whether local command validation is invoked. |
| Security policy guidance | `.agents/CONTEXT.md` | Secure coding rules | Low to Medium | Advisory unless enforced by hooks/tests/review. |
| Pre-commit configuration | `.pre-commit-config.yaml` | Hook definitions | Medium | Local controls can be bypassed or misconfigured. |
| Dependency metadata | `pyproject.toml` | Package names and version ranges | Medium | Affects supply-chain risk and security tooling availability. |

## STRIDE Findings

### Spoofing

| ID | Threat | Risk | Evidence | Recommended Mitigations |
|---|---|---|---|---|
| S-1 | User identity for discount redemption is self-attested. Any caller can provide any non-empty `user_id` and redeem a code for that identity. | High | `redeem_discount_code` only checks that `user_id` is a non-empty string. | Bind redemptions to authenticated session identity from the ADK/runtime context instead of accepting `user_id` as a free-form tool argument. Validate the caller against a registered-user service before redemption. |
| S-2 | The model can be prompted to call the redemption tool with attacker-chosen arguments. | Medium | User prompts influence tool use; tool arguments cross the LLM-to-code boundary. | Treat all model-selected arguments as untrusted. Add schema validation, authorization checks, and confirmation for discount redemption. |
| S-3 | Local command hook trust depends on matching only `run_command`. Similar tooling or renamed command paths may bypass validation. | Medium | `.agents/hooks.json` has matcher `run_command` only. | Ensure all shell-capable tools used by the agent are covered by hook matchers. Prefer an allowlist of approved commands over a narrow denylist. |

### Tampering

| ID | Threat | Risk | Evidence | Recommended Mitigations |
|---|---|---|---|---|
| T-1 | In-memory discount redemption state can be modified by any code running in the same process and is not protected by concurrency controls. | Medium | `_DISCOUNT_STORE` is a module-level mutable dictionary. | Move redemption state to a transactional store with atomic compare-and-set semantics. Use locks or database uniqueness constraints to prevent race-condition double redemption. |
| T-2 | Discount code validation still allows broad alphanumeric-like values before checking the in-memory store. | Low | `DiscountRedemptionRequest` validates type, trims input, limits length, and normalizes casing before lookup. | Consider adding an explicit allowlist pattern for discount-code characters if new code formats are introduced. |
| T-3 | Hook validator command parsing is substring-based and can be bypassed with alternate destructive commands, aliases, encoded commands, or command composition. | High | `validate_tool_call.py` checks only `rm -rf /`, `mkfs`, `del /s /q C:\`, and `format C:`. | Replace denylist matching with an allowlist parser for permitted commands and arguments. Reject shell metacharacters and encoded commands unless explicitly required. |
| T-4 | Pre-commit hooks use `language: system`, so a developer's local PATH can alter which binaries run. | Medium | `.pre-commit-config.yaml` uses local repo hooks with system entries. | Pin hook repositories and versions where possible. For local hooks, verify executable paths or run tools in a controlled environment. |

### Repudiation

| ID | Threat | Risk | Evidence | Recommended Mitigations |
|---|---|---|---|---|
| R-1 | Discount redemption has no durable audit trail. Users can deny redeeming a code, and operators cannot reliably investigate. | High | `redeem_discount_code` mutates memory and returns a response but does not log transaction metadata. | Log redemption attempts with timestamp, authenticated user ID, code, result, request/session ID, and source channel. Protect logs from tampering and avoid logging secrets. |
| R-2 | Failed or blocked command validation is only printed to stderr/stdout and may not be centrally retained. | Medium | `validate_tool_call.py` prints approval/block decisions and exits. | Emit structured audit events for blocked commands, including command hash, requester/session metadata, and policy reason. |
| R-3 | Pre-commit failures are local and can be bypassed with `--no-verify`. | Medium | `.pre-commit-config.yaml` is local-only enforcement. | Run the same checks in CI as required status checks. Preserve Semgrep and hook logs as build artifacts. |

### Information Disclosure

| ID | Threat | Risk | Evidence | Recommended Mitigations |
|---|---|---|---|---|
| I-1 | Gemini credentials could be leaked if a future developer commits local secrets. | Medium | `app/agent.py` does not hardcode an API key; credentials are expected from the runtime environment. | Keep credentials in environment variables, local secret stores, or Secret Manager. Add secret scanning in CI before publishing. |
| I-2 | Repeat redemption attempts disclose the `redeemed_by` user ID of the original redeemer. | Medium | The already-redeemed error returns `"redeemed_by": discount["redeemed_by"]`. | Do not return another user's identifier to callers. Return a generic already-redeemed message and write user details only to protected audit logs. |
| I-3 | Tool responses may expose internal discount state details to the LLM conversation. | Low | Tool returns code, discount percent, and redemption status directly. | Keep tool responses minimal. Separate user-facing messages from internal diagnostic fields. |
| I-4 | Semgrep `--config auto` may send code metadata or require external registry access depending on Semgrep configuration and environment. | Low | `.pre-commit-config.yaml` uses `semgrep --config auto`. | Confirm Semgrep data-sharing settings. Use pinned local rulesets for sensitive projects or CI environments with restricted egress. |

### Denial of Service

| ID | Threat | Risk | Evidence | Recommended Mitigations |
|---|---|---|---|---|
| D-1 | No rate limiting exists for discount redemption attempts. Attackers can brute-force codes or flood tool calls. | Medium | `redeem_discount_code` has no throttling or attempt counter. | Add per-user, per-session, and per-IP rate limits. Track failed redemption attempts and temporarily lock out abusive callers. |
| D-2 | Concurrent redemption calls may race against the in-memory single-use check. | Medium | Check and mutation of `_DISCOUNT_STORE` are not atomic. | Use a database transaction, row lock, or atomic update to enforce single-use redemption under concurrency. |
| D-3 | LLM calls and retry settings can amplify cost under prompt flooding. | Medium | Gemini retry options allow 3 attempts; no request quotas are shown. | Add request quotas, timeouts, budget controls, and abuse monitoring around agent invocation. |
| D-4 | Pre-commit Semgrep `--config auto` may slow or fail commits when network or registry access is unavailable. | Low | Pre-commit invokes Semgrep auto config locally. | Pin a local ruleset for offline operation or document network requirements for developer environments. |

### Elevation of Privilege

| ID | Threat | Risk | Evidence | Recommended Mitigations |
|---|---|---|---|---|
| E-1 | Unauthenticated users can perform a privileged business action: redeeming a discount. | High | The tool only requires a supplied `user_id`; no authentication or registration lookup is implemented. | Require authenticated runtime identity and verify registration before tool execution. Remove `user_id` as a user-controlled field where possible. |
| E-2 | Prompt injection can attempt to override agent instructions and trigger unauthorized tool calls. | Medium | Agent instructions ask for user ID but tool enforcement is limited to non-empty strings. | Enforce authorization in code, not only in prompts. Add before-tool callbacks or tool wrappers for policy checks. |
| E-3 | The command validation hook may give a false sense of shell safety while allowing many dangerous commands outside the denylist. | High | Validator blocks only four destructive patterns. | Implement least-privilege command execution: command allowlists, sandboxed execution, no shell by default, and explicit human approval for risky operations. |
| E-4 | Local security policies in `.agents/CONTEXT.md` remain advisory for future tools unless enforced by tests, hooks, or CI. | Medium | The discount tool uses Pydantic validation, but there is no automated policy check requiring the same pattern for new tools. | Add automated checks for tool schema patterns and fail CI when tools do not use approved validation helpers. |

## Key Risks Summary

| Risk | Level | Why It Matters |
|---|---|---|
| Self-attested `user_id` for redemption | High | Enables spoofing and unauthorized use of single-use discounts. |
| Runtime Gemini credential handling | Medium | Credentials are no longer hardcoded, but local setup still depends on secure environment configuration. |
| Narrow denylist command validator | High | Dangerous shell commands can bypass policy with alternate syntax. |
| No redemption audit trail | High | Business-critical transactions cannot be reliably investigated. |
| Mutable non-atomic in-memory discount store | Medium | Causes race conditions, reset-on-restart behavior, and weak integrity. |
| Pre-commit-only security enforcement | Medium | Local hooks are bypassable and environment-dependent. |

## Recommended Mitigation Roadmap

### Immediate

- Remove `redeemed_by` from user-visible already-redeemed responses.
- Keep strict Pydantic input schemas for discount redemption arguments.
- Keep Gemini credentials out of source code and document environment-based setup.
- Expand command validation from a denylist to an allowlist for approved commands.

### Near Term

- Bind redemption to authenticated session identity instead of caller-provided `user_id`.
- Add durable, tamper-resistant audit logging for redemption attempts and command-hook decisions.
- Add rate limiting and failed-attempt tracking around discount redemption.
- Run pre-commit-equivalent security checks in CI, not only on local developer machines.

### Longer Term

- Move discount state to a persistent transactional data store with atomic single-use redemption.
- Centralize policy enforcement in reusable tool wrappers or ADK callbacks.
- Replace local system pre-commit hooks with pinned hook repositories or containerized tooling.
- Add security regression tests for identity spoofing, repeat redemption, and validator bypass cases.

## Residual Risk

The current implementation is appropriate for a local security lab and intentionally includes at least one simulated secret for testing. It should not be used in production without authenticated identity, durable transactional storage, audit logging, secret management, and stronger command-execution controls.
