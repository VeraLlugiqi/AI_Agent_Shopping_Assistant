# shopping-assistant

Secure multi-agent retail shopping assistant generated with `agents-cli` version `0.5.0`.

This project is designed as a Kaggle Capstone submission. It demonstrates an ADK-based shopping assistant that uses a small multi-agent workflow while preserving security-oriented discount redemption controls.

## Problem Statement

Retail shopping assistants need to answer product, discount, and policy questions without letting user prompts bypass business rules. This project shows how a manager agent can coordinate specialist agents while sensitive actions, such as redeeming a single-use discount code, stay behind validated Python tool logic.

## Solution

The Shopping Manager Agent handles normal shopping help and delegates only the tasks that benefit from specialist behavior:

- discount-code redemption goes to a tool-using Discount Agent
- general store policy questions go to an FAQ Agent

This keeps the architecture simple enough for a Capstone project while clearly demonstrating ADK, multi-agent routing, tool calling, agent skills, and security controls.

## Multi-Agent Architecture

```
Shopping Manager Agent
        |
        +-- Discount Agent
        +-- FAQ Agent
```

- **Shopping Manager Agent** answers ordinary shopping and product questions, then routes specialist requests.
- **Discount Agent** handles discount-code redemption and calls `redeem_discount_code`.
- **FAQ Agent** answers general shopping, return, shipping, sizing, and policy questions.

## Capstone Concepts Demonstrated

- **ADK agent**: the project exports an ADK `app` from `app/agent.py`.
- **Multi-agent workflow**: one manager agent delegates to two specialist agents.
- **Tool calling**: the Discount Agent uses the `redeem_discount_code` Python tool.
- **Agent skill**: the project includes a local STRIDE threat-modeling skill.
- **Security features**: discount redemption validates tool inputs, rejects guest users, enforces single-use codes, and is documented with STRIDE analysis.
- **Security-oriented development**: `.agents/CONTEXT.md`, hooks, pre-commit configuration, Semgrep, and unit tests support safer changes.

## Project Structure

```
shopping-assistant/
├── app/         # Core agent code
│   ├── agent.py               # Main agent logic
│   └── app_utils/             # App utilities and helpers
├── tests/                     # Unit, integration, and load tests
├── GEMINI.md                  # AI-assisted development guide
└── pyproject.toml             # Project dependencies
```

> 💡 **Tip:** Use [Gemini CLI](https://github.com/google-gemini/gemini-cli) for AI-assisted development - project context is pre-configured in `GEMINI.md`.

## Requirements

Before you begin, ensure you have:
- **uv**: Python package manager (used for all dependency management in this project) - [Install](https://docs.astral.sh/uv/getting-started/installation/) ([add packages](https://docs.astral.sh/uv/concepts/dependencies/) with `uv add <package>`)
- **agents-cli**: Agents CLI - Install with `uv tool install google-agents-cli`
- **Google Cloud SDK**: For GCP services - [Install](https://cloud.google.com/sdk/docs/install)


## Quick Start

Install `agents-cli` and its skills if not already installed:

```bash
uvx google-agents-cli setup
```

Install required packages:

```bash
agents-cli install
```

Test the agent with a local web server:

```bash
agents-cli playground
```

For local model access, configure your Gemini credentials through environment variables such as `GOOGLE_API_KEY` or Vertex AI settings. Do not commit API keys or passwords to the repository.

You can also use features from the [ADK](https://adk.dev/) CLI with `uv run adk`.

## Commands

| Command              | Description                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------- |
| `agents-cli install` | Install dependencies using uv                                                         |
| `agents-cli playground` | Launch local development environment                                                  |
| `agents-cli lint`    | Run code quality checks                                                               |
| `agents-cli eval`    | Evaluate agent behavior (generate, grade, analyze, and more — see `agents-cli eval --help`) |
| `uv run pytest tests/test_agent.py` | Run the main agent and tool tests                                                        |

## 🛠️ Project Management

| Command | What It Does |
|---------|--------------|
| `agents-cli scaffold enhance` | Add CI/CD pipelines and Terraform infrastructure |
| `agents-cli infra cicd` | One-command setup of entire CI/CD pipeline + infrastructure |
| `agents-cli scaffold upgrade` | Auto-upgrade to latest version while preserving customizations |

---

## Development

Edit your agent logic in `app/agent.py` and test with `agents-cli playground` - it auto-reloads on save.

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
2. Show the architecture diagram: Shopping Manager, Discount Agent, and FAQ Agent.
3. Demo a normal shopping question handled by the manager.
4. Demo a discount redemption handled by the Discount Agent and Python tool.
5. Mention security controls: Pydantic validation, guest-user rejection, single-use discounts, STRIDE skill, hooks, and tests.

## Deployment

```bash
gcloud config set project <your-project-id>
agents-cli deploy
```

To add CI/CD and Terraform, run `agents-cli scaffold enhance`.
To set up your production infrastructure, run `agents-cli infra cicd`.

## Observability

Built-in telemetry exports to Cloud Trace, BigQuery, and Cloud Logging.
