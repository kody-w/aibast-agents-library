"""Mutation-proven tests for the Microsoft AI Academy acceptance gate."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from tools import audit_academy


ROOT = Path(__file__).resolve().parent.parent
PATH_IDS = (
    "start-here",
    "build-agents",
    "serve-customers",
    "run-operations",
    "govern-ai",
    "grow-business",
)
MILESTONE_POINTS = (10, 15, 20, 25, 30, 50)


def _catalog_context():
    catalog = json.loads(
        (ROOT / "solutions" / "catalog.json").read_text(encoding="utf-8")
    )["solutions"]
    registry = json.loads((ROOT / "registry.json").read_text(encoding="utf-8"))
    rows = {row["name"]: row for row in registry["agents"]}
    return catalog, rows


def synthetic_academy():
    catalog, registry = _catalog_context()
    categories = sorted({registry[key]["category"] for key in catalog})
    courses = []
    for index, key in enumerate(catalog):
        row = registry[key]
        slug = (row.get("_demo") or {}).get("slug") or key.rsplit("/", 1)[-1]
        primary = PATH_IDS[1 + index % (len(PATH_IDS) - 1)]
        path_ids = [primary]
        if index < len(PATH_IDS) - 1:
            path_ids.insert(0, "start-here")
        skill_paths = sorted(
            path.relative_to(ROOT).as_posix()
            for path in (
                ROOT / "solutions" / slug / "manual" / "skills"
            ).rglob("SKILL.md")
        )
        courses.append(
            {
                "slug": slug,
                "catalog_key": key,
                "title": row["display_name"],
                "industry_id": row["category"],
                "path_ids": path_ids,
                "primary_path_id": primary,
                "resources": {
                    "quest": f"solutions/{slug}/quest.html",
                    "manual_tutorial": f"solutions/{slug}/manual-tutorial.html",
                    "field_guide": f"solutions/{slug}/field-guide.html",
                    "evidence_report": f"solutions/{slug}/evidence-report.html",
                },
                "skills": [{"path": path} for path in skill_paths],
            }
        )

    paths = []
    for path_id in PATH_IDS:
        paths.append(
            {
                "id": path_id,
                "name": path_id.replace("-", " ").title(),
                "course_slugs": [
                    course["slug"]
                    for course in courses
                    if path_id in course["path_ids"]
                ],
            }
        )
    skill_count = sum(len(course["skills"]) for course in courses)
    return {
        "schema": "aibast-academy/1.0",
        "summary": {
            "courses": len(courses),
            "skills": skill_count,
            "paths": len(paths),
            "industries": len(categories),
            "milestones": len(MILESTONE_POINTS),
            "points": sum(MILESTONE_POINTS),
        },
        "paths": paths,
        "categories": [
            {"id": category, "name": category.replace("_", " ").title()}
            for category in categories
        ],
        "milestones": [
            {
                "id": f"milestone-{index}",
                "name": f"Milestone {index}",
                "points": points,
            }
            for index, points in enumerate(MILESTONE_POINTS, 1)
        ],
        "courses": courses,
    }


def synthetic_academy_html():
    return audit_academy.normalize_source(
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Microsoft AI Academy</title>
  <style>
    .skip-link { position: absolute; }
    a:focus-visible, button:focus-visible, input:focus-visible, select:focus-visible {
      outline: 3px solid currentColor;
    }
    @media (max-width: 48rem) { .course-grid { grid-template-columns: 1fr; } }
    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after { animation-duration: 0s; transition-duration: 0s; }
    }
  </style>
</head>
<body>
  <a class="skip-link" href="#academy-main">Skip to course catalog</a>
  <nav aria-label="Primary">
    <a href="library.html">Library</a>
    <a href="achievements.html">Achievements</a>
    <a href="metrics.html">Metrics</a>
    <a href="docs/rapp-guide.html">Production guide</a>
  </nav>
  <main id="academy-main">
    <h1>Microsoft AI Academy</h1>
    <label for="course-query">Search courses</label>
    <input id="course-query" type="search">
    <label for="path-filter">Learning path</label>
    <select id="path-filter"><option value="">All paths</option></select>
    <button id="reset-filters" type="button">Reset filters</button>
    <div id="loading-state" role="status" aria-live="polite">Loading courses…</div>
    <div id="empty-state" hidden>No courses match these filters.</div>
    <div id="error-state" hidden>Unable to load the Academy catalog.</div>
    <section class="course-grid" aria-label="Academy courses"></section>
  </main>
  <dialog id="course-dialog" aria-labelledby="course-title">
    <h2 id="course-title">Course detail</h2>
    <button id="close-course" type="button" aria-label="Close course detail">Close</button>
  </dialog>
  <script>
    const STORAGE_KEY = 'aibast:achievement-profile:v1';
    const academyState = {};
    let returnFocus = null;

    function sanitizeAchievementProfile(value) {
      const source = value && typeof value === 'object' ? value : {};
      return {
        points: Number.isFinite(source.points) ? Math.max(0, source.points) : 0,
        completed: Array.isArray(source.completed)
          ? source.completed.filter(item => typeof item === 'string')
          : []
      };
    }

    function readAchievementProfile() {
      try {
        const raw = localStorage.getItem(STORAGE_KEY);
        return sanitizeAchievementProfile(raw ? JSON.parse(raw) : {});
      } catch (error) {
        return sanitizeAchievementProfile({});
      }
    }

    const params = new URLSearchParams(window.location.search);
    const urlState = {
      q: params.get('q') || '',
      path: params.get('path') || '',
      industry: params.get('industry') || '',
      progress: params.get('progress') || '',
      sort: params.get('sort') || 'featured'
    };

    function writeUrlState(next) {
      for (const key of ['q', 'path', 'industry', 'progress', 'sort']) {
        if (next[key]) params.set(key, next[key]);
        else params.delete(key);
      }
      history.replaceState(null, '', `${location.pathname}?${params}${location.hash}`);
    }

    function openCourse(slug, trigger) {
      returnFocus = trigger;
      location.hash = `#course/${encodeURIComponent(slug)}`;
      document.getElementById('course-dialog').showModal();
    }

    function closeCourse() {
      document.getElementById('course-dialog').close();
      if (returnFocus && typeof returnFocus.focus === 'function') returnFocus.focus();
    }

    document.addEventListener('keydown', event => {
      if (event.key === 'Escape') closeCourse();
    });
    window.addEventListener('hashchange', () => {
      if (!location.hash.startsWith('#course/')) closeCourse();
    });
    document.getElementById('close-course').addEventListener('click', closeCourse);

    async function loadAcademy() {
      const loading = document.getElementById('loading-state');
      const empty = document.getElementById('empty-state');
      const errorState = document.getElementById('error-state');
      try {
        const response = await fetch('academy.json', { cache: 'no-store' });
        if (!response.ok) throw new Error('Academy request failed');
        const academy = await response.json();
        loading.hidden = true;
        empty.hidden = Array.isArray(academy.courses) && academy.courses.length > 0;
      } catch (error) {
        loading.hidden = true;
        errorState.hidden = false;
      }
    }

    readAchievementProfile();
    writeUrlState(urlState);
    loadAcademy();
  </script>
</body>
</html>
"""
    )


def synthetic_integrations():
    return {
        "index.html": '<nav><a href="academy.html">Academy</a></nav>',
        "library.html": '<nav><a href="academy.html">Academy</a></nav>',
        "achievements.html": '<nav><a href="academy.html">Academy</a></nav>',
        "metrics.html": '<nav><a href="academy.html">Academy</a></nav>',
        "docs/rapp-guide.html": '<nav><a href="../academy.html">Academy</a></nav>',
        "README.md": "[Microsoft AI Academy](academy.html)",
    }


@pytest.fixture(scope="module")
def academy_fixture():
    return (
        synthetic_academy(),
        synthetic_academy_html(),
        synthetic_integrations(),
    )


def run_fixture(data, html, integrations):
    result = audit_academy.AuditResult()
    audit_academy.audit_academy_data(ROOT, data, result)
    audit_academy.audit_academy_html(html, result)
    audit_academy.audit_integration_sources(integrations, result)
    audit_academy.finalize_measurements(result)
    return result.as_dict()


def assert_failure_category(report, category):
    assert report["status"] == "fail", report
    assert category in report["failures"], json.dumps(report, indent=2)


def test_helpers_use_crlf_safe_front_matter_and_safe_relative_urls(tmp_path):
    skill = tmp_path / "SKILL.md"
    skill.write_bytes(
        b"---\r\nname: synthetic-skill\r\ndescription: Safe fixture.\r\n---\r\n\r\n# Skill\r\n"
    )

    source = audit_academy.normalize_source(skill.read_text(encoding="utf-8"))
    metadata = audit_academy.parse_front_matter(source)

    assert metadata == {
        "name": "synthetic-skill",
        "description": "Safe fixture.",
    }
    assert audit_academy.is_safe_repository_url(
        "solutions/example/quest.html#start"
    )
    assert not audit_academy.is_safe_repository_url(
        "https://example.test/collect"
    )
    assert not audit_academy.is_safe_repository_url("../academy.json")
    assert not audit_academy.is_safe_repository_url(
        "solutions/%2e%2e/secrets.txt"
    )


def test_strict_html_helper_rejects_unclosed_structure():
    parser = audit_academy.parse_html(
        "<!doctype html><html><body><main><p>Unclosed</main></body></html>"
    )

    assert parser.errors
    assert any("mismatched" in error or "unclosed" in error for error in parser.errors)


def test_missing_node_is_a_failure_not_a_skip(monkeypatch):
    monkeypatch.setattr(audit_academy.shutil, "which", lambda _name: None)
    result = audit_academy.AuditResult()

    audit_academy.audit_academy_html(synthetic_academy_html(), result)

    assert "javascript" in result.failures
    assert any("never skip" in message for message in result.failures["javascript"])


def test_synthetic_fixture_passes_complete_gate(academy_fixture):
    data, html, integrations = academy_fixture

    report = run_fixture(data, html, integrations)

    assert report["status"] == "pass", json.dumps(report["failures"], indent=2)
    assert report["measurements"]["academy_courses"] == 51
    assert report["measurements"]["academy_skills"] == 229
    assert report["measurements"]["milestone_points"] == 150


def test_mutation_removing_course_fails_catalog_gate(academy_fixture):
    data, html, integrations = copy.deepcopy(academy_fixture)
    data["courses"].pop()

    report = run_fixture(data, html, integrations)

    assert_failure_category(report, "catalog")


def test_mutation_corrupting_milestone_total_fails_points_gate(academy_fixture):
    data, html, integrations = copy.deepcopy(academy_fixture)
    data["milestones"][0]["points"] += 1

    report = run_fixture(data, html, integrations)

    assert_failure_category(report, "milestones")


def test_mutation_missing_skill_path_fails_skill_gate(academy_fixture):
    data, html, integrations = copy.deepcopy(academy_fixture)
    slug = data["courses"][0]["slug"]
    data["courses"][0]["skills"][0]["path"] = (
        f"solutions/{slug}/manual/skills/missing/SKILL.md"
    )

    report = run_fixture(data, html, integrations)

    assert_failure_category(report, "skills")


def test_mutation_broken_javascript_fails_syntax_gate(academy_fixture):
    data, html, integrations = copy.deepcopy(academy_fixture)
    html = audit_academy.normalize_source(html).replace(
        "const academyState = {};",
        "const academyState = {;",
        1,
    )

    report = run_fixture(data, html, integrations)

    assert_failure_category(report, "javascript")


def test_mutation_removed_navigation_link_fails_navigation_gate(academy_fixture):
    data, html, integrations = copy.deepcopy(academy_fixture)
    integrations["index.html"] = "<nav><a href=\"library.html\">Library</a></nav>"

    report = run_fixture(data, html, integrations)

    assert_failure_category(report, "navigation")


def test_mutation_external_script_fails_security_gate(academy_fixture):
    data, html, integrations = copy.deepcopy(academy_fixture)
    html = audit_academy.normalize_source(html).replace(
        "</head>",
        '<script src="https://tracker.example/collect.js"></script>\n</head>',
        1,
    )

    report = run_fixture(data, html, integrations)

    assert_failure_category(report, "security")


def test_repository_passes_microsoft_ai_academy_gate():
    report = audit_academy.audit(ROOT)

    assert report["status"] == "pass", json.dumps(report["failures"], indent=2)
