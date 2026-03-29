# ContentMesh ⚡
### AI Multi-Agent Enterprise Content Pipeline — YAML Config Edition

> Agents and tasks are defined in YAML. The crew is wired in Python using the
> `@CrewBase` decorator pattern — exactly as CrewAI's CLI scaffold generates.

---

## Project Structure

```
contentmesh/
├── src/contentmesh/
│   ├── config/
│   │   ├── agents.yaml        ← All 5 agent definitions (role, goal, backstory)
│   │   └── tasks.yaml         ← All 5 task definitions (description, expected_output, context)
│   ├── tools/
│   │   ├── __init__.py
│   │   └── distributor_tools.py  ← send_email, post_to_slack, log_distribution
│   ├── crew.py                ← @CrewBase class wiring agents + tasks + crew
│   └── main.py                ← CLI entry point (crewai run / python main.py)
├── frontend/
│   └── index.html             ← Full demo dashboard (dark mode, live UI)
├── app.py                     ← FastAPI server (REST API + frontend serving)
├── scripts/
│   └── start.sh               ← One-command startup
├── pyproject.toml             ← CrewAI CLI compatible project config
├── requirements.txt
└── .env.example
```

---

## Quick Start

### Option A — Shell script (recommended)
```bash
cp .env.example .env
# Edit .env → add your ANTHROPIC_API_KEY

chmod +x scripts/start.sh
./scripts/start.sh
```

### Option B — Manual
```bash
cp .env.example .env
# Edit .env → add ANTHROPIC_API_KEY

python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

uvicorn app:app --reload --port 8000
```

Open **http://localhost:8000** in your browser.

> **No API key?** Click **"Load Demo Result"** in the UI — full demo, no key needed.

---

## Run via CrewAI CLI

```bash
pip install crewai
crewai install          # reads pyproject.toml, installs deps
crewai run              # runs src/contentmesh/main.py → writes output.json
```

---

## Agent & Task Config

### agents.yaml — defines all 5 agents
```yaml
content_creator:
  role: Senior Content Strategist
  goal: Create compelling, structured enterprise content...
  backstory: You are an expert B2B content strategist...

compliance_reviewer:
  role: Legal Compliance Reviewer
  goal: Identify and flag all compliance violations...
  backstory: You are a corporate legal compliance officer...

# + localizer, channel_formatter, distribution_agent
```

### tasks.yaml — defines all 5 tasks
```yaml
create_content_task:
  description: >
    Create enterprise-grade content for: {topic}
    Audience: {audience} | Tone: {tone}
    Output valid JSON with title, body, key_messages, cta...
  expected_output: Valid JSON with keys title, body, key_messages...
  agent: content_creator

compliance_review_task:
  description: Review content against rules: {compliance_rules}...
  expected_output: Valid JSON with status, compliance_score, violations...
  agent: compliance_reviewer
  context:
    - create_content_task       # ← receives creator output automatically

# + localize_content_task, format_channels_task, distribute_content_task
```

### crew.py — wires everything with @CrewBase
```python
@CrewBase
class ContentMeshCrew:
    agents_config = "config/agents.yaml"
    tasks_config  = "config/tasks.yaml"

    @agent
    def content_creator(self) -> Agent:
        return Agent(config=self.agents_config["content_creator"], verbose=True)

    @task
    def create_content_task(self) -> Task:
        return Task(config=self.tasks_config["create_content_task"])

    @crew
    def crew(self) -> Crew:
        return Crew(agents=self.agents, tasks=self.tasks, process=Process.sequential)
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/generate` | Run full pipeline |
| `GET` | `/api/demo-result` | Pre-built demo output (no API key needed) |
| `GET` | `/api/stream-progress` | SSE agent progress stream |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Swagger UI |

### Example request
```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Launching our new AI supply chain platform",
    "audience": "VP of Operations at manufacturing companies",
    "tone": "authoritative",
    "locales": ["en", "es", "fr"],
    "channels": ["email", "linkedin", "blog", "slack"],
    "compliance_rules": ["no ROI guarantees", "no competitor mentions"],
    "recipient_email": "demo@yourcompany.com"
  }'
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ Yes | From https://console.anthropic.com |
| `SMTP_HOST` | Optional | Gmail: `smtp.gmail.com` |
| `SMTP_PORT` | Optional | `587` |
| `SMTP_USER` | Optional | Your Gmail address |
| `SMTP_PASS` | Optional | Gmail App Password |
| `SLACK_WEBHOOK` | Optional | Slack Incoming Webhook URL |

Without SMTP/Slack credentials the distribution agent runs in demo mode and simulates delivery.

---

## Impact Metrics

| Metric | Manual | ContentMesh |
|---|---|---|
| Brief → published | 3–5 days | ~90 seconds |
| Locales generated | 1 | 3+ simultaneous |
| Compliance review | 8 hours | 8 seconds |
| Channel variants | 1 per asset | 4 per locale |
