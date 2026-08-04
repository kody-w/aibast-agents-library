#!/usr/bin/env bash
# Test cases for the Agent Library front-end + metrics + aggregator.
#
#   bash tests/test_library_frontend.sh          # local (pre-push) suite
#   bash tests/test_library_frontend.sh live URL # live suite against a Pages base URL
#
# Written BEFORE the build (plan-first); every deliverable must turn its
# section green before shipping.

set -u
cd "$(dirname "$0")/.."
PASS=0; FAIL=0
ok()   { PASS=$((PASS+1)); echo "  ✓ $1"; }
bad()  { FAIL=$((FAIL+1)); echo "  ✗ $1"; }
check(){ if eval "$2" >/dev/null 2>&1; then ok "$1"; else bad "$1"; fi; }

MODE="${1:-local}"

if [ "$MODE" = "live" ]; then
  BASE="${2:?usage: test_library_frontend.sh live https://host/path}"
  echo "== T10 live: $BASE =="
  for p in agents.html metrics.html registry.json state/metrics.json state/aggregated.json state/discussion_ratings.json; do
    check "GET /$p is 200" "curl -fsSL -o /dev/null '$BASE/$p'"
  done
  check "agent .py serves over Pages" \
    "curl -fsSL '$BASE/agents/@aibast-agents-library/art-generator.py' | grep -q __manifest__"
  check "agents.html references registry.json" \
    "curl -fsSL '$BASE/agents.html' | grep -q 'registry.json'"
  check "metrics.html references state/metrics.json" \
    "curl -fsSL '$BASE/metrics.html' | grep -q 'state/metrics.json'"
  check "index.html still serves installer one-liner" \
    "curl -fsSL '$BASE/index.html' | grep -q 'install.sh | bash'"
  check "index.html links to the library" \
    "curl -fsSL '$BASE/index.html' | grep -q 'agents.html'"
  check "api/v1/index.json serves with endpoint directory" \
    "curl -fsSL '$BASE/api/v1/index.json' | grep -q rapp-static-api"
  check "per-agent API endpoint serves" \
    "curl -fsSL '$BASE/api/v1/agents/aibast-agents-library/art-generator.json' | grep -q manifest"
  check "api/v1/agents.json is CORS-open" \
    "curl -fsSIL '$BASE/api/v1/agents.json' | grep -qi 'access-control-allow-origin'"
  check "vbrainstem serves" \
    "curl -fsSL '$BASE/vbrainstem/' | grep -q vbrainstem-boot"
  check "vbrainstem reads the aibast library, not RAR" \
    "! curl -fsSL '$BASE/vbrainstem/vbrainstem-boot.js' | grep -q 'kody-w/RAR'"
  echo; echo "live: $PASS passed, $FAIL failed"; exit $((FAIL>0))
fi

echo "== T1 registry data contract =="
check "registry.json parses, 100+ agents, all have category+_file" "python3 - <<'PY'
import json
r=json.load(open('registry.json'))
a=r['agents']
assert len(a)>=100, len(a)
assert all('category' in x and '_file' in x and 'description' in x for x in a)
assert r['stats']['categories']>=14
PY"

echo "== T2 discussion_ratings.py =="
check "syntax OK" "python3 -c \"import ast;ast.parse(open('scripts/discussion_ratings.py').read())\""
check "fetch without token is non-fatal (exit 0)" \
  "env -u GITHUB_TOKEN -u GH_TOKEN python3 scripts/discussion_ratings.py fetch"
check "title regex accepts dashed aibast slugs" "python3 - <<'PY'
import importlib.util
s=importlib.util.spec_from_file_location('dr','scripts/discussion_ratings.py')
m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
assert m.is_agent_title('@aibast-agents-library/art-generator')
assert m.is_agent_title('@some-user/my_agent')
assert not m.is_agent_title('not a title')
assert not m.is_agent_title('@bad/UPPER Case')
PY"

echo "== T3 crawl_skills.py (aggregator, index-only) =="
check "dry-run indexes cat-agent-skills, refs normalized, no content mirrored" "python3 - <<'PY'
import json,subprocess
p=subprocess.run(['python3','scripts/crawl_skills.py','--dry-run','--only','cat-agent-skills'],
                 capture_output=True,text=True,timeout=60)
assert p.returncode==0, p.stderr
snap=json.loads(p.stdout)
skills=snap['skills']
assert len(skills)>0
for s in skills:
    assert s['ref'].startswith('@cat-agent-skills/')
    assert isinstance(s['front_page_score'],int)
    assert 'url' in s and s['url']
    for banned in ('body','content','source_code','files'):
        assert banned not in s, banned
PY"
check "gate verdicts dominate front_page_score" "python3 - <<'PY'
import importlib.util
s=importlib.util.spec_from_file_location('cs','scripts/crawl_skills.py')
m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
raw={'source_signal':{'downloads':100000,'rating':5,'featured':True}}
gated={'source_signal':{}}
v={'converted':True,'gates':{'quality':{'passed':True},'usability':{'passed':True},'effectiveness':{'passed':True}}}
assert m.front_page_score(gated,v) > m.front_page_score(raw,None)
PY"

echo "== T4 build_metrics.py =="
check "runs tokenless and writes contract-shaped state/metrics.json" "python3 - <<'PY'
import json,subprocess,os
env=dict(os.environ); env.pop('GITHUB_TOKEN',None); env.pop('GH_TOKEN',None)
p=subprocess.run(['python3','scripts/build_metrics.py'],capture_output=True,text=True,timeout=120,env=env)
assert p.returncode==0, p.stderr
m=json.load(open('state/metrics.json'))
t=m['totals']
for k in ('downloads','clones','cdn_hits','agents','publishers','categories','upvotes','tracked_downloads'):
    assert k in t, k
assert isinstance(m['daily'],list)
for b in ('most_downloaded','most_upvoted','categories','publishers'):
    assert b in m['leaderboards'], b
reg=json.load(open('registry.json'))
assert t['agents']==reg['stats']['total_agents']
assert m['aggregated']['total']>=0
PY"
check "history accumulates and dedupes by date" "python3 - <<'PY'
import json
h=json.load(open('state/metrics_history.json'))
dates=[d['date'] for d in h['daily']]
assert len(dates)==len(set(dates))
PY"

echo "== T5 metrics workflow =="
check "metrics.yml valid YAML with discussions+contents write, cron, all 3 scripts" "python3 - <<'PY'
import yaml
w=yaml.safe_load(open('.github/workflows/metrics.yml'))
assert w['permissions']['contents']=='write'
assert w['permissions']['discussions']=='write'
trig=w.get('on') or w.get(True)
assert 'schedule' in trig and 'workflow_dispatch' in trig
steps=str(w)
for s in ('crawl_skills.py','discussion_ratings.py','build_metrics.py'):
    assert s in steps, s
PY"

echo "== T6 agents.html static contract =="
check "exists, fetches registry.json relatively, has search/chips/viewer/publish/aggregated" "python3 - <<'PY'
h=open('agents.html').read()
for needle in (\"registry.json\",'id=\"agentSearch\"','id=\"industryChips\"',
               'id=\"codeModal\"','id=\"publish\"','id=\"aggregated\"',
               'state/discussion_ratings.json','function esc'):
    assert needle in h, needle
assert 'kody-w.github.io/AI-Agent-Templates' not in h
PY"
check "escapes untrusted registry strings before innerHTML" \
  "grep -q 'esc(' agents.html"

echo "== T7 metrics.html static contract =="
check "exists, loads state/metrics.json, canonical repo, has KPI+boards containers" "python3 - <<'PY'
h=open('metrics.html').read()
for needle in ('state/metrics.json','microsoft/aibast-agents-library',
               'id=\"kpis\"','id=\"board\"','id=\"pub-table\"','id=\"chart\"'):
    assert needle in h, needle
PY"

echo "== T8 headless render =="
check "agents.html renders cards + search filters; metrics.html renders KPIs" \
  "python3 tests/test_render_headless.py"

echo "== T9 index.html link integrity (additive only) =="
check "installer one-liners unchanged" "python3 - <<'PY'
h=open('index.html').read()
assert 'curl -fsSL https://microsoft.github.io/aibast-agents-library/install.sh | bash' in h
assert 'irm https://raw.githubusercontent.com/microsoft/aibast-agents-library/main/install.ps1 | iex' in h
assert 'href=\"install.command\"' in h
PY"
check "index links to agents.html and metrics.html" "python3 - <<'PY'
h=open('index.html').read()
assert 'agents.html' in h and 'metrics.html' in h
PY"

echo "== T-API static api (rapp-static-api/1.0) =="
check "build_api runs and endpoints parse with correct counts" "python3 - <<'PY'
import json,subprocess
p=subprocess.run(['python3','scripts/build_api.py'],capture_output=True,text=True,timeout=60)
assert p.returncode==0, p.stderr
reg=json.load(open('registry.json'))
idx=json.load(open('api/v1/index.json'))
assert idx['spec']=='rapp-static-api/1.0'
ag=json.load(open('api/v1/agents.json'))
assert ag['count']==reg['stats']['total_agents']
assert all(a['raw_url'].startswith('https://raw.githubusercontent.com/microsoft/') for a in ag['agents'])
det=json.load(open('api/v1/agents/aibast-agents-library/art-generator.json'))
assert det['manifest']['name']=='@aibast-agents-library/art-generator'
st=json.load(open('api/v1/status.json'))
assert st['ok'] and st['agents']==reg['stats']['total_agents']
b=json.load(open('api/v1/badge.json'))
assert b['schemaVersion']==1
json.load(open('api/v1/categories.json')); json.load(open('api/v1/publishers.json'))
PY"
check "stable-write: rebuild produces zero changes" \
  "python3 scripts/build_api.py | grep -q '(0 file(s) changed)'"
check ".nojekyll present for Pages byte-exact serving" "test -f .nojekyll"

echo "== T-VB vbrainstem port =="
check "core files present" "python3 - <<'PY'
import os
for f in ('index.html','vbrainstem-boot.js','vbrainstem-worker.js','brainstem_web.py',
          'local_storage.py','soul.md','VERSION','README.md','agents/basic_agent.py'):
    assert os.path.exists('vbrainstem/'+f), f
PY"
check "no RAR endpoints remain anywhere in the port" \
  "! grep -rq 'kody-w/RAR' vbrainstem/"
check "library + tracking point at aibast" "python3 - <<'PY'
boot=open('vbrainstem/vbrainstem-boot.js').read()
assert 'raw.githubusercontent.com/microsoft/aibast-agents-library/main/registry.json' in boot
idx=open('vbrainstem/index.html').read()
assert \"RAR_TRACK_REPO = 'microsoft/aibast-agents-library'\" in idx
assert 'cdn.jsdelivr.net/gh/microsoft/aibast-agents-library@' in idx
PY"
check "brainstem_web.py parses" \
  "python3 -c \"import ast;ast.parse(open('vbrainstem/brainstem_web.py').read())\""

echo "== T-docs publisher + aggregation =="
check "PUBLISHING.md covers @username default + both output formats" "python3 - <<'PY'
d=open('docs/PUBLISHING.md').read()
for needle in ('@<your-github-username>','__manifest__','skill.md','agent.py'):
    assert needle in d, needle
PY"
check "AGGREGATION.md covers gates + conversion + dedupe surfacing" "python3 - <<'PY'
d=open('docs/AGGREGATION.md').read()
for needle in ('quality','usability','effectiveness','skill.md','agent.py','front_page_score','sources.json'):
    assert needle.lower() in d.lower(), needle
PY"
check "publisher issue form parses" \
  "python3 -c \"import yaml;yaml.safe_load(open('.github/ISSUE_TEMPLATE/publisher-application.yml'))\""

echo; echo "local: $PASS passed, $FAIL failed"
exit $((FAIL>0))
