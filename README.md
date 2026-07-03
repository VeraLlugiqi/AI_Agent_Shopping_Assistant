# Secure Multi-Agent Shopping Assistant

This project is a Kaggle Capstone submission for the 5-Day AI Agents course. It demonstrates a secure shopping assistant built with Google ADK, a small multi-agent workflow, tool calling, Pydantic validation, and security documentation.

## Problem Statement

Retail shopping assistants need to answer product, discount, and policy questions without allowing user prompts to bypass business rules. Discount redemption is sensitive because a user should not be able to redeem invalid codes, reuse single-use codes, or claim a discount as a guest account.

## Solution

The assistant uses a manager agent that handles normal shopping requests and delegates specialized tasks to smaller agents:

- discount-code redemption goes to the Discount Agent
- general store policy questions go to the FAQ Agent

Sensitive discount logic is implemented in a Python tool, not only in the prompt. This keeps business rules testable and easier to secure.

## Multi-Agent Architecture

```text
Shopping Manager Agent
        |
        +-- Discount Agent
        +-- FAQ Agent
```

- **Shopping Manager Agent** answers ordinary shopping questions and routes specialist requests.
- **Discount Agent** handles discount redemption and calls `redeem_discount_code`.
- **FAQ Agent** answers return, shipping, sizing, and policy questions.

## Capstone Concepts Demonstrated

- **ADK agent**: the project exports an ADK `app` from `app/agent.py`.
- **Multi-agent workflow**: one manager agent delegates to two specialist agents.
- **Tool calling**: the Discount Agent uses the `redeem_discount_code` Python tool.
- **Pydantic validation**: discount tool input is validated with `DiscountRedemptionRequest`.
- **Agent skill**: the project includes a local STRIDE threat-modeling skill.
- **Security features**: discount redemption rejects guest users, validates input, enforces single-use codes, and is documented with STRIDE analysis.
- **Testing and documentation**: the project includes pytest tests, README documentation, and a threat model.

## Project Structure

```text
shopping-assistant/
+-- app/
|   +-- agent.py               # Main ADK agent, sub-agents, tool, and app export
|   +-- fast_api_app.py         # Optional FastAPI wrapper for serving the agent
|   +-- app_utils/              # Telemetry and shared Pydantic types
+-- tests/
|   +-- test_agent.py           # Main project tests
|   +-- unit/                   # Unit-test scaffold
|   +-- integration/            # Optional integration-test scaffold
|   +-- eval/                   # Optional evaluation scaffold
+-- .agents/
|   +-- CONTEXT.md              # Local secure coding guidance
|   +-- skills/                 # Local agent skill files
+-- threat_model.md             # STRIDE threat model
+-- Dockerfile                  # Optional container runtime
+-- pyproject.toml              # Python dependencies and tool config
+-- uv.lock                     # Locked dependency versions
+-- README.md
```

## Requirements

- Python 3.11+
- `uv`
- Google ADK / agents-cli dependencies from `pyproject.toml`
- Gemini API key only if you want live model responses in ADK Playground

## Quick Start

Install dependencies:

```bash
uv sync
```

Run the main tests:

```bash
uv run pytest tests/test_agent.py
```

Run the agent in ADK Playground:

```bash
uv run adk web . --host 127.0.0.1 --port 8000 --session_service_uri memory:// --artifact_service_uri memory://
```

Then open:

```text
http://127.0.0.1:8000
```

For live model responses, set a Gemini API key before starting the playground:

```powershell
$env:GOOGLE_API_KEY="YOUR_API_KEY"
```

Do not commit API keys, passwords, or local `.env` files.

## Example User Prompts

```text
Can you recommend a gift for someone who likes running and has a $75 budget?
```

```text
I want to redeem WELCOME50. My registered user ID is user_123.
```

```text
What should I know before returning an online order?
```

## Suggested 5-Minute Demo Flow

1. Explain the retail shopping problem and why tool-protected agents are useful.
2. Show the architecture: Shopping Manager Agent, Discount Agent, and FAQ Agent.
3. Show `app/agent.py`, including the agents, Pydantic model, and discount tool.
4. Run `uv run pytest tests/test_agent.py`.
5. Show security artifacts: `.agents/CONTEXT.md`, the STRIDE skill, and `threat_model.md`.
6. If Gemini quota is unavailable, explain that live model calls require active Gemini API quota, while the code, tests, architecture, and documentation are included in the repository.

## Deployment

Deployment is not required for the Capstone. The included `Dockerfile` is provided as an optional container runtime if the agent is later deployed.
