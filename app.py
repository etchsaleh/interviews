"""Python interview practice app.

Run:  python app.py   then open http://127.0.0.1:5000
"""
from pathlib import Path

import markdown
from flask import Flask, abort, jsonify, render_template, request
from markupsafe import Markup

import mock_api
from problems import ALL_PROBLEMS, BY_ID, CATEGORY_NOTES, CATEGORY_ORDER
from runner import run_solution
from system_design import PROMPTS as DESIGN_PROMPTS

app = Flask(__name__)
app.register_blueprint(mock_api.bp)

HERE = Path(__file__).parent
# Minutes to aim for per difficulty - the real risk in the coding round is running out of time.
TARGET_MINUTES = {"Easy": 10, "Medium": 20, "Hard": 30}
PLAYGROUND = {"id": "playground", "entry": "", "tests": []}


@app.template_filter("md")
def render_markdown(text):
    return Markup(markdown.markdown(text, extensions=["fenced_code", "tables", "toc", "md_in_html"]))


def mock_base_url():
    return request.host_url.rstrip("/") + "/mock"


def public_view(problem):
    """The parts of a problem the browser needs (no solution, no validator)."""
    return {
        "id": problem["id"],
        "title": problem["title"],
        "difficulty": problem["difficulty"],
        "category": problem["category"],
        "tags": problem["tags"],
        "description": problem["description"],
        "needs_base_url": problem.get("needs_base_url", False),
        "java_tip": problem["java_tip"],
        "starter": problem["starter"],
        "followups": problem.get("followups", []),
        "target_minutes": TARGET_MINUTES[problem["difficulty"]],
        "tests": [
            {"input": t["args"], "expected": t.get("expected"), "expected_label": t.get("expected_label")}
            for t in problem["tests"]
        ],
    }


@app.get("/")
def index():
    categories = {c: [p for p in ALL_PROBLEMS if p["category"] == c] for c in CATEGORY_ORDER}
    return render_template("index.html", categories=categories, notes=CATEGORY_NOTES, targets=TARGET_MINUTES)


@app.get("/problem/<problem_id>")
def problem_page(problem_id):
    problem = BY_ID.get(problem_id) or abort(404)
    ids = [p["id"] for p in ALL_PROBLEMS]
    idx = ids.index(problem_id)
    return render_template(
        "problem.html",
        problem=public_view(problem),
        prev_id=ids[idx - 1] if idx > 0 else None,
        next_id=ids[idx + 1] if idx + 1 < len(ids) else None,
        base_url=mock_base_url(),
    )


@app.get("/guide")
def guide():
    return render_template("guide.html", guide_md=(HERE / "GUIDE.md").read_text(encoding="utf-8"))


@app.get("/plan")
def plan():
    return render_template(
        "plan.html",
        plan_md=(HERE / "STUDY_PLAN.md").read_text(encoding="utf-8"),
        categories={c: [p["id"] for p in ALL_PROBLEMS if p["category"] == c] for c in CATEGORY_ORDER},
    )


@app.get("/system-design")
def system_design():
    return render_template(
        "system_design.html",
        guide_md=(HERE / "SYSTEM_DESIGN.md").read_text(encoding="utf-8"),
        prompts=DESIGN_PROMPTS,
    )


@app.get("/playground")
def playground():
    return render_template("playground.html", base_url=mock_base_url())


@app.post("/api/run")
def api_run():
    body = request.get_json(force=True)
    code = body.get("code", "")
    if body.get("id") == "playground":
        return jsonify(run_solution(PLAYGROUND, code))
    problem = BY_ID.get(body.get("id")) or abort(404)
    return jsonify(run_solution(problem, code, base_url=mock_base_url()))


@app.get("/api/solution/<problem_id>")
def api_solution(problem_id):
    problem = BY_ID.get(problem_id) or abort(404)
    return jsonify({"solution": problem["solution"]})


if __name__ == "__main__":
    # threaded=True matters: API problems call back into this same server while /api/run waits.
    app.run(host="127.0.0.1", port=5000, debug=True, threaded=True)
