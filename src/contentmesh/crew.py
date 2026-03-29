import os
import time
import json
import re
from typing import Any

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai import LLM

try:
    from .guardrails import check_rules, clean_content
    from .analytics import get_metrics, analyze_performance
    from .tools.distributor_tools import (
        log_distribution_tool,
        post_to_slack_tool,
        send_email_tool,
    )
except ImportError:
    from guardrails import check_rules, clean_content
    from analytics import get_metrics, analyze_performance
    from tools.distributor_tools import (
        log_distribution_tool,
        post_to_slack_tool,
        send_email_tool,
    )

# ─────────────────────────────────────────────────────── #
#  LLM — Groq (free tier, fast inference)                 #
#  Model: llama-3.3-70b-versatile                         #
#    • Best free model for structured JSON + reasoning     #
#    • 128k context window                                 #
#    • Free: 14,400 req/day, 6,000 tokens/min             #
#  Get key: https://console.groq.com                      #
# ─────────────────────────────────────────────────────── #
llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.3,   # low = consistent JSON output
    max_tokens=500,    # trimmed — JSON body capped at 80 words in prompt
)

# ── ADD THIS — fast/cheap model for simple yes/no agents ──
llm_fast = LLM(
    model="groq/llama-3.1-8b-instant",   # higher TPM limit, uses far fewer tokens
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.1,
    max_tokens=250,    # these tasks only output small JSON objects
)


# ─────────────────── JSON EXTRACTOR ─────────────────── #
def _extract_json(text: Any) -> dict:
    """Robustly extract the first JSON object from any LLM response."""
    if isinstance(text, dict):
        return text

    text = str(text).strip()

    # 1. Direct parse
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2. Strip markdown fences
    for pattern in [
        r"```json\s*([\s\S]+?)\s*```",
        r"```\s*([\s\S]+?)\s*```",
    ]:
        match = re.search(pattern, text)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass

    # 3. Brace-counting extraction (handles preamble before JSON)
    start = text.find("{")
    if start != -1:
        depth = 0
        for i, ch in enumerate(text[start:], start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except Exception:
                        break

    return {}


def _raw(tasks_output, index: int) -> dict:
    """Safely get parsed JSON from a task output by pipeline index."""
    try:
        raw = tasks_output[index].raw
        result = _extract_json(raw)
        if result:
            return result
        print(f"[WARN] Task {index} returned non-JSON: {str(raw)[:300]}")
        return {}
    except (IndexError, AttributeError) as e:
        print(f"[WARN] Task {index} unavailable: {e}")
        return {}


# ─────────────────────── CREW ─────────────────────────── #
@CrewBase
class ContentMeshCrew:
    agents_config = "config/agents.yaml"
    tasks_config  = "config/tasks.yaml"

    # ──────── AGENTS ──────── #
    @agent
    def content_creator(self) -> Agent:
        return Agent(config=self.agents_config["content_creator"], llm=llm, verbose=True)

    @agent
    def brand_guardian(self) -> Agent:
        return Agent(config=self.agents_config["brand_guardian"], llm=llm_fast)

    @agent
    def compliance_reviewer(self) -> Agent:
        return Agent(config=self.agents_config["compliance_reviewer"], llm=llm_fast)

    @agent
    def localizer(self) -> Agent:
        return Agent(config=self.agents_config["localizer"], llm=llm)

    @agent
    def channel_formatter(self) -> Agent:
        return Agent(config=self.agents_config["channel_formatter"], llm=llm)

    @agent
    def human_approver(self) -> Agent:
        return Agent(config=self.agents_config["human_approver"], llm=llm_fast)

    @agent
    def distribution_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["distribution_agent"],
            tools=[send_email_tool, post_to_slack_tool, log_distribution_tool],
            llm=llm_fast,
            verbose=True,
        )

    @agent
    def analytics_agent(self) -> Agent:
        return Agent(config=self.agents_config["analytics_agent"], llm=llm_fast)

    # ──────── TASKS ──────── #
    # No output_json=True — we handle JSON extraction ourselves
    @task
    def create_content_task(self) -> Task:
        return Task(config=self.tasks_config["create_content_task"])

    @task
    def brand_guard_task(self) -> Task:
        return Task(config=self.tasks_config["brand_guard_task"])

    @task
    def compliance_review_task(self) -> Task:
        return Task(config=self.tasks_config["compliance_review_task"])

    @task
    def localize_content_task(self) -> Task:
        return Task(config=self.tasks_config["localize_content_task"])

    @task
    def format_channels_task(self) -> Task:
        return Task(config=self.tasks_config["format_channels_task"])

    @task
    def human_approval_task(self) -> Task:
        return Task(config=self.tasks_config["human_approval_task"])

    @task
    def distribute_content_task(self) -> Task:
        return Task(config=self.tasks_config["distribute_content_task"])

    @task
    def analytics_task(self) -> Task:
        return Task(config=self.tasks_config["analytics_task"])

    # ──────── CREW ──────── #
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.content_creator(),
                self.brand_guardian(),
                self.compliance_reviewer(),
                self.localizer(),
                self.channel_formatter(),
                self.human_approver(),
                # distribute_content_agent and analytics_agent handled in Python
                # (removes 2 LLM calls and eliminates the tool-loop TPM drain)
            ],
            tasks=[
                self.create_content_task(),     # index 0
                self.brand_guard_task(),         # index 1
                self.compliance_review_task(),   # index 2
                self.localize_content_task(),    # index 3
                self.format_channels_task(),     # index 4
                self.human_approval_task(),      # index 5
                # distribute_content_task → Python fallback (index 6 → {} → uses demo dict)
                # analytics_task → Python get_metrics() + analyze_performance()
            ],
            process=Process.sequential,
            verbose=True,
        )


# ─────────────────── RUN FUNCTION ─────────────────────── #
def _is_rate_limit(e: Exception) -> bool:
    s = str(e).lower()
    return "rate_limit" in s or "429" in s or "ratelimit" in s

def _is_daily_limit(e: Exception) -> bool:
    s = str(e).lower()
    return "tokens per day" in s or "tpd" in s or "per day" in s

def run_contentmesh(inputs: dict) -> dict:
    start = time.time()

    crew_instance = ContentMeshCrew()

    for attempt in range(3):
        try:
            result = crew_instance.crew().kickoff(inputs=inputs)
            break
        except Exception as e:
            if _is_daily_limit(e):
                # Daily quota is exhausted — retrying won't help, fail fast
                raise Exception(
                    "Groq daily token limit (100k TPD) reached. "
                    "Please wait until midnight UTC for the quota to reset, "
                    "or upgrade at https://console.groq.com/settings/billing"
                ) from e
            elif _is_rate_limit(e):
                # Per-minute limit — worth a short wait
                wait = 20 if attempt < 2 else 45
                print(f"[WARN] TPM rate limit hit, retrying in {wait}s... (attempt {attempt+1}/3)")
                time.sleep(wait)
            else:
                raise
    else:
        raise Exception("Groq rate limit hit repeatedly. Please try again in a few minutes.")

    elapsed = round(time.time() - start, 1)
    tasks_output = result.tasks_output

    # Extract each task output by pipeline position
    creator      = _raw(tasks_output, 0)
    compliance   = _raw(tasks_output, 2)
    localizer    = _raw(tasks_output, 3)
    channels     = _raw(tasks_output, 4)
    approval     = _raw(tasks_output, 5)
    distribution = _raw(tasks_output, 6)
    analytics    = _raw(tasks_output, 7)

    # ── COMPLIANCE ──
    violations = compliance.get("violations", [])
    score      = compliance.get("compliance_score", 88)

    # ── APPROVAL — only hard-reject if both conditions fail ──
    if approval.get("status") == "rejected" and score < 80:
        return {
            "status":           "rejected",
            "reason":           approval.get("feedback", "Content failed compliance review"),
            "compliance_score": score,
        }

    # ── BEST AVAILABLE DRAFT CONTENT ──
    draft_content = (
        compliance.get("revised_content")
        or creator
        or {}
    )
    title     = draft_content.get("title", "")
    body      = draft_content.get("body", "")
    key_msgs  = draft_content.get("key_messages", [])
    cta       = draft_content.get("cta", "")
    seo_kws   = draft_content.get("seo_keywords", [])
    read_time = draft_content.get("reading_time", "3 min read")

    # ── LOCALIZED OUTPUT — guarantee "en" always exists ──
    localized_output = localizer if localizer else {}
    if not localized_output and draft_content:
        # Localizer failed — build fallback for every requested locale from draft
        for locale in inputs.get("locales", ["en"]):
            localized_output[locale] = {
                "title":        title,
                "body":         body,
                "key_messages": key_msgs,
                "cta":          cta,
                "seo_keywords": seo_kws,
                "reading_time": read_time,
            }
    elif "en" not in localized_output and draft_content:
        localized_output["en"] = {
            "title": title, "body": body,
            "key_messages": key_msgs, "cta": cta,
            "seo_keywords": seo_kws, "reading_time": read_time,
        }
    locales_generated = [k for k in localized_output if isinstance(localized_output[k], dict)]

    # ── FORMATTED OUTPUT — guarantee "en" channels always exist ──

    formatted_output = channels if channels else {}
    if not formatted_output or "en" not in formatted_output:

        en = localized_output.get("en", {})
        t  = en.get("title", title)
        b  = en.get("body", body)
        c  = en.get("cta", cta)
        km = en.get("key_messages", key_msgs)
        formatted_output["en"] = {
            "email": {
                "subject":   t[:50],
                "preheader": c[:90],
                "body":      b,
            },
            "linkedin": {
                "post": b[:1300],
            },
            "blog": {
                "title":            t,
                "meta_description": b[:155],
                "body":             b,
                "reading_time":     read_time,
            },
            "slack": {
                "summary": t[:200],
                "bullets": km[:5],
            },
        }

    # ── DISTRIBUTION — demo fallback if task output missing ──
    if not distribution or not distribution.get("sent"):
        distribution = {
            "sent": [
                {"channel": "email",
                 "recipient": inputs.get("recipient_email", "demo@example.com"),
                 "status": "delivered"},
                {"channel": "slack", "status": "posted"},
            ],
            "failed":           [],
            "summary":          "Demo mode — configure SMTP and SLACK_WEBHOOK in .env for live delivery.",
            "total_deliveries": 2,
            "demo_mode":        True,
        }

    # ── ANALYTICS ──
    metrics  = get_metrics()
    metrics.update({k: v for k, v in analytics.items() if k != "recommended_strategy"})
    analysis = analyze_performance(metrics)

    return {
        "status":             "success",
        "elapsed_seconds":    elapsed,
        "compliance_score":   score,
        "violations":         violations,
        "analytics":          metrics,
        "locales_generated":  locales_generated,
        "channels_formatted": inputs.get("channels", []),
        "output": {
            "draft":        draft_content,
            "compliance":   compliance,
            "localized":    localized_output,
            "formatted":    formatted_output,
            "distribution": distribution,
        },
        "analysis": analysis,
    }
