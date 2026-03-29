#!/usr/bin/env python
"""
ContentMesh CLI entry point.
Usage: python main.py  OR  crewai run
"""
import sys
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Validate GROQ_API_KEY is set
if not os.getenv("GROQ_API_KEY"):
    print("\n❌ ERROR: GROQ_API_KEY not set in .env")
    print("   Get your free key at: https://console.groq.com")
    print("   Then add to .env:  GROQ_API_KEY=gsk_...\n")
    sys.exit(1)

sys.path.insert(0, os.path.dirname(__file__))

from crew import run_contentmesh

DEFAULT_INPUTS = {
    "topic":            "Announcing our new AI-powered supply chain platform for enterprise manufacturers",
    "audience":         "VP of Operations at manufacturing companies",
    "tone":             "authoritative",
    "locales":          "en, es, fr, de",
    "channels":         "email, linkedin, blog, slack",
    "compliance_rules": "no ROI guarantees, no competitor mentions, no medical claims",
    "recipient_email":  "demo@example.com",
}


def run():
    print("\n🚀 ContentMesh — AI Content Pipeline (powered by Groq)\n")
    print("Model: llama-3.3-70b-versatile")
    print("Running with demo inputs. Edit DEFAULT_INPUTS in main.py to customise.\n")

    inputs = DEFAULT_INPUTS.copy()
    inputs["locales"]          = [l.strip() for l in inputs["locales"].split(",")]
    inputs["channels"]         = [c.strip() for c in inputs["channels"].split(",")]
    inputs["compliance_rules"] = [r.strip() for r in inputs["compliance_rules"].split(",")]

    result = run_contentmesh(inputs)

    if result.get("status") == "rejected":
        print("\n❌ Content Rejected")
        print(f"   Reason:           {result.get('reason')}")
        print(f"   Compliance Score: {result.get('compliance_score')}/100")
    else:
        print("\n✅ Pipeline complete!")
        print(f"   Elapsed:          {result.get('elapsed_seconds')}s")
        print(f"   Compliance score: {result.get('compliance_score')}/100")
        print(f"   Locales:          {', '.join(result.get('locales_generated', []))}")
        print(f"   Channels:         {', '.join(result.get('channels_formatted', []))}")
        print(f"   Violations:       {len(result.get('violations', []))}")
        print(f"\n📊 Engagement Score: {result.get('analytics', {}).get('engagement_score')}")

    output_path = os.path.join(os.path.dirname(__file__), "output.json")
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n📁 Full output written to {output_path}\n")


def train():
    inputs = DEFAULT_INPUTS.copy()
    try:
        n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
        from crew import ContentMeshCrew
        ContentMeshCrew().crew().train(
            n_iterations=n,
            filename=sys.argv[2] if len(sys.argv) > 2 else "training.pkl",
            inputs=inputs,
        )
    except Exception as e:
        raise Exception(f"Training error: {e}")


def replay():
    try:
        from crew import ContentMeshCrew
        ContentMeshCrew().crew().replay(task_id=sys.argv[1])
    except Exception as e:
        raise Exception(f"Replay error: {e}")


def test():
    inputs = DEFAULT_INPUTS.copy()
    try:
        n = int(sys.argv[1]) if len(sys.argv) > 1 else 1
        from crew import ContentMeshCrew
        ContentMeshCrew().crew().test(n_iterations=n, inputs=inputs)
    except Exception as e:
        raise Exception(f"Test error: {e}")


if __name__ == "__main__":
    run()
