# NeverDown

**Autonomous Incident Detection, Analysis, and Remediation System**

NeverDown is a production-grade system that autonomously detects CI/CD failures, analyzes root causes using LLMs, generates fixes, verifies them in isolated sandboxes, and opens pull requests for human review.

## 🔒 Security First

- **Zero Secret Exposure**: All secrets are redacted before reaching LLMs
- **Read-Only Production**: System never writes to production environments
- **Sandbox Execution**: All code runs in isolated Docker containers
- **Human-in-the-Loop**: PRs are never auto-merged

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        NeverDown Pipeline                        │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────┤
│   Agent 0   │   Agent 1   │   Agent 2   │   Agent 3   │ Agent 4 │
│  Sanitizer  │  Detective  │  Reasoner   │  Verifier   │Publisher│
│             │             │             │             │         │
│ • Redact    │ • Parse     │ • LLM       │ • Docker    │ • Create│
│   secrets   │   logs      │   analysis  │   sandbox   │   PR    │
│ • Entropy   │ • Git       │ • Generate  │ • Run       │ • Never │
│   detection │   history   │   patch     │   tests     │   merge │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker
- PostgreSQL

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/neverdown.git
cd neverdown

# Install dependencies
pip install -e ".[dev]"

# Copy environment configuration
cp .env.example .env
# Edit .env with your configuration

# Start with Docker Compose
docker-compose up -d
```

### Configuration

Key environment variables:

| Variable | Description |
|----------|-------------|
| `GITHUB_TOKEN` | GitHub personal access token |
| `LLM_API_KEY` | Anthropic or OpenAI API key |
| `LLM_PROVIDER` | `anthropic` or `openai` |
| `DATABASE_URL` | PostgreSQL connection string |

## 📡 API Usage

### Create Incident Manually

```bash
curl -X POST http://localhost:8000/api/v1/incidents \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Build failure in production",
    "source": "manual",
    "severity": "high",
    "repository": {
      "url": "https://github.com/org/repo",
      "branch": "main"
    },
    "logs": "Traceback (most recent call last):\n  File \"app.py\", line 42...\nTypeError: ..."
  }'
```

### GitHub Webhook Integration

Configure a webhook at `https://your-domain/api/v1/webhooks/github` with:
- Events: `workflow_run`, `check_run`
- Secret: Your `GITHUB_WEBHOOK_SECRET`

## 🔧 Agent Details

### Agent 0: Sanitizer
- Scans for 15+ secret patterns (AWS, GitHub, Stripe, etc.)
- Shannon entropy detection for unknown secrets
- Creates sanitized shadow repository
- Halts if too many secrets found

### Agent 1: Detective
- Multi-format log parsing (Python, JavaScript, JSON)
- Git history analysis with blame integration
- Failure categorization (name_error, timeout, etc.)
- Confidence-scored file localization

### Agent 2: Reasoner
- Prompt engineering for root cause analysis
- Supports Anthropic Claude and OpenAI GPT
- Generates unified diff patches
- Confidence thresholding

### Agent 3: Verifier
- Isolated Docker sandbox execution
- No network access, memory limits
- Multi-framework test detection (pytest, jest, unittest)
- Automated test result parsing

### Agent 4: Publisher
- Creates fix branches
- Generates comprehensive PR descriptions
- Adds appropriate labels
- **Never auto-merges**

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_sanitizer.py -v
```

## 📁 Project Structure

```
NeverDown/
├── agents/
│   ├── agent_0_sanitizer/    # Secret detection & redaction
│   ├── agent_1_detective/    # Failure analysis
│   ├── agent_2_reasoner/     # LLM-powered fix generation
│   ├── agent_3_verifier/     # Sandbox testing
│   └── agent_4_publisher/    # GitHub PR creation
├── api/
│   ├── routes/               # FastAPI endpoints
│   └── middleware/           # Auth, rate limiting, logging
├── config/                   # Settings & security rules
├── database/                 # Models & repositories
├── models/                   # Pydantic schemas
├── services/                 # Git & orchestration
└── tests/                    # Test suite
```

## 🔐 Security Patterns Detected

- AWS Access Keys & Secrets
- GitHub Tokens (PAT, OAuth)
- JWT Tokens
- Database URLs (PostgreSQL, MySQL, MongoDB)
- Stripe Keys
- Slack Tokens
- GCP API Keys
- RSA/SSH Private Keys
- Generic API keys & passwords
- High-entropy strings

## 📜 License

MIT License - See [LICENSE](LICENSE) for details.

---

**⚠️ Important**: This system assists with bug fixing but all changes require human review before merging.
