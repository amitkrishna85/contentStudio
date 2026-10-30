from __future__ import annotations

import json
from pathlib import Path

from creatoros.app.graph import compute_diff_ratio, run_pipeline
from creatoros.app.brand.voice import infer_brand_voice, load_brand_samples
from creatoros.eval.rubric import judge_draft, readability_score, voice_similarity_to_brand


def run_eval() -> dict:
    """Run a compact evaluation suite across 10+ briefs and write result files."""
    briefs = [
        "A LinkedIn post about AI safety for a security team",
        "A short X thread about building calm AI governance",
        "An Instagram caption about resilient product security",
        "A founder post about practical security habits",
        "A LinkedIn post about trust and governance",
        "A quick post about the value of boring security systems",
        "An X thread on reducing risk without fear",
        "A LinkedIn post about clear operational controls",
        "A security brand post about accountability in teams",
        "A casual post about shipping safely with guardrails",
    ]
    results = []
    for brief in briefs:
        for brand_name in ["formal-enterprise", "casual-indie"]:
            pipeline = run_pipeline(brief, brand_profile={"tone": brand_name, "banned_phrases": []})
            final_draft = pipeline["final_draft"]
            judge = judge_draft(final_draft, brief, brand_name)
            results.append({
                "brief": brief,
                "brand": brand_name,
                "final_draft": final_draft,
                "judge": judge,
                "readability": readability_score(final_draft),
                "voice_similarity": voice_similarity_to_brand(final_draft, brand_name),
            })
    summary = {
        "brief_count": len(briefs),
        "brand_count": 2,
        "mean_readability": round(sum(item["readability"] for item in results) / max(1, len(results)), 4),
        "mean_voice_similarity": round(sum(item["voice_similarity"] for item in results) / max(1, len(results)), 4),
    }
    output_dir = Path(__file__).resolve().parent
    (output_dir / "results.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    report = "# Evaluation results\n\n" + json.dumps(summary, indent=2) + "\n\n## Limitations\n\nThis evaluation is intentionally lightweight and uses heuristic scoring when live LLM evaluation is unavailable.\n"
    (output_dir / "RESULTS.md").write_text(report, encoding="utf-8")
    return summary


if __name__ == "__main__":
    run_eval()
