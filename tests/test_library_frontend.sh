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
  check "RAPP/1 spec mirror serves" \
    "curl -fsSL '$BASE/rapp/spec/RAPP1-SPEC.md' | head -5 | grep -qi 'RAPP'"
  check "corpus mirror manifest serves" \
    "curl -fsSL '$BASE/rapp/MIRROR-MANIFEST.json' | grep -q 'aibast-corpus-mirror'"
  check "handbook mirror serves" \
    "curl -fsSL '$BASE/rapp/handbook/README.md' -o /dev/null"
  check "disclaimer serves" \
    "curl -fsSL '$BASE/DISCLAIMER.md' | grep -qi 'AS IS'"
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

echo "== T-CLEAN clean break (kody-w refs only in sanctioned places) =="
check "kody-w refs confined to allowlist (tracked + untracked)" "python3 - <<'PY'
import re, subprocess
r=subprocess.run(['git','grep','--untracked','-l','-E','kody-w|kwildfeuer|billwhalen'],
                 capture_output=True,text=True)
assert r.returncode in (0,1), r.stderr   # 0=hits, 1=no hits; anything else = grep itself failed
out=r.stdout.splitlines()
ALLOW_DIRS=('rapp_brainstem/',  # kernel-locked stable content — fixes flow from upstream
            'rapp/',            # pinned corpus mirrors + governance docs discuss upstream by name
            'tests/')           # negative guards in this suite
ALLOW_FILES={'vbrainstem/brainstem_web.py',  # auth CORS proxy, env-overridable (VB_AUTH_WORKER)
             'docs/CLEAN-BREAK.md',          # the audit record itself
             'scripts/corpus_sync.py'}       # addresses the kernel authority file by name
# The staging fork's own identity (kody-w/aibast-agents-library) is a sanctioned
# self-reference: the daily CI stamps whichever repo generated the snapshot, and
# it self-heals to microsoft/* when the workflow runs upstream.
SELF=re.compile(r'kody-w/aibast-agents-library|kody-w\.github\.io/aibast-agents-library')
STRAY=re.compile(r'kody-w|kwildfeuer|billwhalen')
def stray(path):
    t=SELF.sub('', open(path, encoding='utf-8', errors='ignore').read())
    return bool(STRAY.search(t))
bad=[f for f in out if f not in ALLOW_FILES and not f.startswith(ALLOW_DIRS) and stray(f)]
assert not bad, bad
PY"
check "generated state/ and api/ carry no kody-w refs beyond the staging self-reference" "python3 - <<'PY'
import re, subprocess
r=subprocess.run(['git','grep','--untracked','-l','kody-w','--','state/','api/'],capture_output=True,text=True)
assert r.returncode in (0,1), r.stderr
SELF=re.compile(r'kody-w/aibast-agents-library|kody-w\.github\.io/aibast-agents-library')
bad=[f for f in r.stdout.splitlines()
     if 'kody-w' in SELF.sub('', open(f, encoding='utf-8', errors='ignore').read())]
assert not bad, bad
PY"

echo "== T-LOCK brainstem + installers locked =="
check "locked files match BRAINSTEM-LOCK.json and no unlocked file exists in the kernel tree" "python3 - <<'PY'
import hashlib,json,subprocess
from pathlib import Path
lock=json.load(open('rapp/BRAINSTEM-LOCK.json'))
assert len(lock['files'])>=20
for f,h in lock['files'].items():
    assert hashlib.sha256(Path(f).read_bytes()).hexdigest()==h, f
# two-way: an ADDED file in the locked kernel tree (tracked or not) must fail
r=subprocess.run(['git','ls-files','--cached','--others','--exclude-standard','rapp_brainstem'],
                 capture_output=True,text=True)
assert r.returncode==0, r.stderr
extra=set(r.stdout.split())-set(lock['files'])
assert not extra, f'unlocked files in the kernel tree: {sorted(extra)}'
PY"

echo "== T-CORPUS RAPP/1 corpus mirror =="
check "manifest complete, every mirror hash-matches, authority pin self-consistent" "python3 - <<'PY'
import hashlib,json,re
from pathlib import Path
m=json.load(open('rapp/MIRROR-MANIFEST.json'))
assert m['schema']=='aibast-corpus-mirror/1.0'
assert len(m['files'])>=12
for local,e in m['files'].items():
    p=Path(local); assert p.exists(), local
    assert hashlib.sha256(p.read_bytes()).hexdigest()==e['sha256'], local
    assert re.match(r'^[0-9a-f]{7,40}\Z', e['revision']), f'{local}: revision must be a commit sha, not a branch'
    assert e.get('license'), local
# the spec mirror must agree with the mirrored authority pin — the invariant
# that survives every future pin bump
auth=json.load(open('rapp/spec/RAPP1_AUTHORITY.json'))
spec=m['files']['rapp/spec/RAPP1-SPEC.md']
assert spec['sha256']==auth['sha256'], 'spec mirror != authority pin sha256'
assert auth['commit'].startswith(spec['revision'][:7]) or spec['revision'].startswith(auth['commit'][:7]), \
    'spec pin commit != authority commit'
assert hashlib.sha256(open('rapp/spec/RAPP1-SPEC.md','rb').read()).hexdigest()==auth['sha256']
PY"
check "corpus_sync --check passes (local integrity mode)" \
  "python3 scripts/corpus_sync.py --check --local-only"
check "handbook carries upstream LICENSE and NOTICE" \
  "test -f rapp/handbook/LICENSE && test -f rapp/handbook/NOTICE && grep -qi 'BSD' rapp/handbook/LICENSE"

echo "== T-DOCS2 governance + ALM =="
check "SUCCESSION.md covers the kernel→LTS flow" "python3 - <<'PY'
d=open('rapp/SUCCESSION.md').read().lower()
for k in ('kernel','lts','stable release','pin bump','flow down','flow up','never push'):
    assert k in d, k
PY"
check "ALM.md covers rings, builds, gates" "python3 - <<'PY'
d=open('rapp/ALM.md').read().lower()
for k in ('canary','nightly','gate','secret scanning','branch protection','corpus_sync','upstream sync'):
    assert k in d, k
PY"
check "ALIGNMENT.md records current pin + license gaps + shape lock" "python3 - <<'PY'
import json
d=open('rapp/ALIGNMENT.md').read().lower()
auth=json.load(open('rapp/spec/RAPP1_AUTHORITY.json'))
assert auth['commit'][:8] in d, 'ALIGNMENT must cite the CURRENT authority commit'
for k in ('pin','license','rapp-1','shape','0.6.16','freshness'):
    assert k in d, k
PY"
check "CLEAN-BREAK.md documents the auth-worker exception" \
  "grep -q 'VB_AUTH_WORKER' docs/CLEAN-BREAK.md"

echo "== T-TERMS enterprise vocabulary in authored surfaces =="
check "no informal kernel vocabulary in authored prose (provenance names excepted)" "python3 - <<'PY'
import re, glob
AUTHORED = (glob.glob('rapp/*.md') + glob.glob('docs/*.md')
            + ['README.md','CLAUDE.md','rapp/BRAINSTEM-LOCK.json','rapp/MIRROR-MANIFEST.json'])
BAD = re.compile(r'\b(grail|bible|sacred|incantation)\b', re.I)
# factual upstream repo/project names are provenance, not vocabulary
PROVENANCE = re.compile(r'RAPP-Bible|rapp-god|kody-w/[A-Za-z0-9._-]+')
offenders = []
for f in AUTHORED:
    text = PROVENANCE.sub('', open(f, encoding='utf-8').read())
    for m in BAD.finditer(text):
        offenders.append(f'{f}: {m.group(0)}')
assert not offenders, offenders[:12]
PY"

echo "== T-DISCLAIMER frontier-tool posture =="
check "DISCLAIMER.md exists with AS-IS / preview / human-review posture" "python3 - <<'PY'
d=open('DISCLAIMER.md').read()
for k in ('AS IS','public preview','human review','at your own risk','requires_env'):
    assert k.lower() in d.lower(), k
PY"
check "README states MIT for the LTS + third-party carve-out + links disclaimer" "python3 - <<'PY'
d=open('README.md').read()
assert 'MIT' in d and 'THIRD-PARTY-NOTICES' in d and 'DISCLAIMER.md' in d
PY"
check "gallery, metrics, installer, vbrainstem link the disclaimer" "python3 - <<'PY'
for f in ('agents.html','metrics.html','index.html','vbrainstem/README.md'):
    assert 'DISCLAIMER' in open(f).read(), f
PY"

echo "== T-CAT microsoft OSS compliance set (mcscatblog parity) =="
check "standard Microsoft SECURITY.md block present" \
  "grep -q 'BEGIN MICROSOFT SECURITY.MD' SECURITY.md && grep -q 'aka.ms/SECURITY.md' SECURITY.md"
check "Code of Conduct + SUPPORT with canonical Microsoft links" "python3 - <<'PY'
c=open('CODE_OF_CONDUCT.md').read()
assert 'opensource.microsoft.com/codeofconduct' in c and 'opencode@microsoft.com' in c
s=open('SUPPORT.md').read()
assert 'GitHub Issues' in s and 'Discussions' in s and 'Support Policy' in s
PY"
check "CAT footer formula on all three pages" "python3 - <<'PY'
for f in ('index.html','agents.html','metrics.html'):
    t=open(f).read()
    assert 'Microsoft AIBAST. Some rights reserved.' in t, f
PY"

echo "== T-TELEMETRY aibast.tooling.v1 contract =="
check "schema parses, closed contract, all 13 fields" "python3 - <<'PY'
import json
s=json.load(open('schemas/tool-interaction-event.schema.json'))
assert s['additionalProperties'] is False
assert set(s['properties'])=={'eventId','eventName','toolId','toolVersion','correlationId',
 'msxOpportunityId','tpid','actorRole','actorRegion','programId','outcome','durationMs','timestampUtc'}
assert s['properties']['actorRole']['enum']==['TA','SE','GBB','PARTNER','ISD']
assert s['properties']['toolId']['enum']==['RAPP','AIDEATE','LIBRARY','DMT','SOWAGENT']
PY"
check "emitter builds valid events and validates offline (no endpoint, no disk writes)" "python3 - <<'PY'
import sys, os, subprocess, json
sys.path.insert(0,'scripts')
os.environ.pop('AIBAST_TELEMETRY_ENDPOINT',None)
from telemetry import emit, build_event, TelemetryError
before=subprocess.run(['git','status','--porcelain'],capture_output=True,text=True).stdout
e=emit('rapp.prototype.generated', tool_id='RAPP', tool_version='1.0.0',
       correlation_id=None, actor_role='TA', actor_region='AMER',
       program_id='AGENTS', outcome='success', duration_ms=5321)
assert e['eventId'] and e['correlationId'] and e['timestampUtc'].endswith('+00:00') or 'Z' in e['timestampUtc']
assert e['msxOpportunityId'] is None and e['tpid'] is None
after=subprocess.run(['git','status','--porcelain'],capture_output=True,text=True).stdout
assert before==after, 'emitter wrote something into the repo'
PY"
check "emitter rejects prohibited payload fields and bad enums" "python3 - <<'PY'
import sys, os
sys.path.insert(0,'scripts'); os.environ.pop('AIBAST_TELEMETRY_ENDPOINT',None)
from telemetry import build_event, TelemetryError
base=dict(tool_id='RAPP',tool_version='1.0.0',correlation_id=None,actor_role='TA',
          actor_region='AMER',program_id='AGENTS',outcome='success',duration_ms=1)
for bad in ({'prompt':'secret'},{'response':'x'},{'customerData':'x'},{'userEmail':'a@b'},{'documents':'x'}):
    try: build_event('rapp.prototype.generated', **base, **bad); raise SystemExit(f'accepted {bad}')
    except TelemetryError: pass
for field,val in (('actor_role','Kody'),('outcome','meh'),('tool_id','OTHER'),
                  ('tool_version','v1'),('duration_ms',-5)):
    try: build_event('rapp.prototype.generated', **{**base,field:val}); raise SystemExit(f'accepted {field}={val}')
    except TelemetryError: pass
PY"
check "TELEMETRY.md documents the prohibition and the internal-only flow" "python3 - <<'PY'
d=open('docs/TELEMETRY.md').read()
for k in ('AIBAST_TELEMETRY_ENDPOINT','Role, never person','never written into this repository','additionalProperties'):
    assert k in d, k
PY"

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
