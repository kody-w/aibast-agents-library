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
  check "aka.ms/RAPP target serves (docs/installer.html)" \
    "curl -fsSL -o /dev/null '$BASE/docs/installer.html'"
  check "aka.ms/RAPPworkshop target serves (docs/rapp-guide.html)" \
    "curl -fsSL -o /dev/null '$BASE/docs/rapp-guide.html'"
  check "legacy community_rapp installer path still serves (compat stub)" \
    "curl -fsSL '$BASE/community_rapp/install.sh' | grep -q rapp_cloud"
  # The advertised one-liners must be fetchable, not just mentioned in HTML:
  # a 404 here pipes an error page into every new user's shell.
  for i in install.sh install.ps1 install.cmd install.command; do
    # The failure this guards against is Pages serving an HTML 404 page that
    # then gets piped into a shell — so assert script-shaped, never markup.
    check "advertised installer /$i is a real script, not an error page" \
      "curl -fsSL '$BASE/$i' | head -20 | grep -qiE 'brainstem|rapp' && \
       ! curl -fsSL '$BASE/$i' | head -5 | grep -qi '<!doctype\|<html'"
  done
  check "vbrainstem one-click install integrity hash present in live registry" \
    "curl -fsSL '$BASE/registry.json' | grep -q '_sha256'"
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

echo "== T-APIPAGE explorer + impact page =="
check "api.html has a live explorer, impact panel and badge section" "python3 - <<'PY'
h=open('api.html').read()
for needle in ('id=\"epList\"','id=\"epOut\"','id=\"kpis\"','id=\"spark\"','id=\"badgeList\"',
               'api/v1/index.json','api/v1/agents.json','img.shields.io/endpoint',
               'rapp-static-api/1.0','var esc ='):
    assert needle in h, needle
# explorer must fetch relatively so it exercises whatever host serves it
assert 'var url = active.path;' in h, 'explorer must fetch relative paths'
assert 'fetch(url, { cache:' in h
PY"
check "every explorer endpoint exists in the tree" "python3 - <<'PY'
import re, os
h=open('api.html').read()
paths=re.findall(r'\{ path: \"([^\"]+)\"', h)
assert len(paths)>=8, paths
for p in paths:
    assert os.path.exists(p), p
PY"
check "gallery, metrics and installer link the API explorer" \
  "grep -q 'api.html' index.html && grep -q 'api.html' agents.html && grep -q 'api.html' metrics.html"

echo "== T-AGENTFIRST machine-readable entry points =="
check "llms.txt follows the convention and links only real targets" "python3 - <<'PY'
import re, pathlib
t=open('llms.txt').read()
assert t.startswith('# '), 'llms.txt starts with an H1 title'
lines=[l for l in t.splitlines() if l.strip()]
assert lines[1].startswith('>'), 'a blockquote summary follows the title'
assert '## ' in t, 'sections are H2'
links=re.findall(r'\]\((https://microsoft\.github\.io/aibast-agents-library/([^)]+))\)', t)
assert len(links) >= 10, len(links)
for full, rel in links:
    assert pathlib.Path(rel).exists(), f'llms.txt links a missing file: {rel}'
PY"
check "agent.json answers what/how in one fetch and stays honest about 404s" "python3 - <<'PY'
import json, pathlib
a=json.load(open('api/v1/agent.json'))
for k in ('what','read_this_first','api_root','start_here','rules_for_agents','conventions','human_ui'):
    assert a.get(k), k
assert len(a['start_here'])>=5
verify=[r for r in a['start_here'] if 'certified' in r['get']][0]
assert 'not certified' in verify['then'] and 'error' in verify['then']
assert any('Read an agent file before executing' in r for r in a['rules_for_agents'])
for url in a['human_ui'].values():
    rel=url.split('aibast-agents-library/')[1]
    assert pathlib.Path(rel).exists(), rel
PY"
check "llms-full.txt inlines the documentation for a one-fetch reader" "python3 - <<'PY'
full=open('llms-full.txt').read(); short=open('llms.txt').read()
assert full.startswith(short.split(chr(10))[0])
assert len(full) > len(short) * 3
import pathlib
for note in pathlib.Path('brain').rglob('*.md'):
    title=[l for l in note.read_text(encoding='utf-8').splitlines() if l.startswith('# ')]
    if title: assert title[0][2:] in full, note
PY"
check "AGENTS.md tells an agent working on the repo what will fail the build" "python3 - <<'PY'
d=open('AGENTS.md').read()
for k in ('BRAINSTEM-LOCK','requires_env','build_api.py','PATTERN.md','pytest'):
    assert k in d, k
PY"

echo "== T-BRAIN documentation vault (ms-rapp-brain/1.0) =="
check "vault notes carry frontmatter and resolve their wikilinks" "python3 - <<'PY'
import json, re, subprocess, pathlib
subprocess.run(['python3','scripts/build_api.py'],capture_output=True,timeout=60)
idx=json.load(open('api/v1/brain/index.json'))
assert idx['protocol']=='ms-rapp-brain/1.0' and idx['count']>=8
slugs={n['slug'] for n in idx['notes']}
for n in idx['notes']:
    p=pathlib.Path(n['path'])
    assert p.exists(), n['path']
    head=p.read_text(encoding='utf-8')
    assert head.startswith('---'), f'{n[chr(115)+chr(108)+chr(117)+chr(103)]} needs frontmatter'
    assert n['title'], n['slug']
# every wikilink either resolves or is reported as dangling — never invented
dang={(d['from'],d['to']) for d in idx['dangling_links']}
for n in idx['notes']:
    for l in n['links']:
        assert l in slugs, (n['slug'], l)
assert len(dang) <= 2, sorted(dang)
PY"
check "backlinks are computed, and the graph matches the links" "python3 - <<'PY'
import json, glob
idx=json.load(open('api/v1/brain/index.json'))
g=json.load(open('api/v1/brain/graph.json'))
notes={n['slug']: n for n in idx['notes']}
assert len(g['nodes'])==len(notes)
edges={(e['from'],e['to']) for e in g['edges']}
expected={(s,l) for s,n in notes.items() for l in n['links']}
assert edges==expected, 'graph must equal the link set'
for f in glob.glob('api/v1/brain/notes/*.json'):
    d=json.load(open(f))
    for b in d['backlinks']:
        assert d['slug'] in notes[b]['links'], (b, d['slug'])
    assert 'raw_url' in d and d['protocol']=='ms-rapp-brain/1.0'
PY"
check "the API references note bodies rather than duplicating them" "python3 - <<'PY'
import glob, json, pathlib
for f in glob.glob('api/v1/brain/notes/*.json'):
    d=json.load(open(f))
    assert 'content' not in d and 'body' not in d and 'markdown' not in d
    assert d['raw_url'].startswith('https://raw.githubusercontent.com/')
    # metadata only: the endpoint must stay far smaller than the note it points at
    note_bytes=len(pathlib.Path(d['path']).read_bytes())
    assert len(json.dumps(d)) < note_bytes + 900, (f, note_bytes)
PY"
check "brain.html reads the vault, resolves wikilinks, and offers the Obsidian path" "python3 - <<'PY'
h=open('brain.html').read()
for n in ('api/v1/brain/index.json','id=\"tree\"','id=\"graphSvg\"','obsidian://open',
          'Linked from','function md(','wl dangling','id=\"exportBtn\"'):
    assert n in h, n
PY"
check "vault opens in a notes client with no conversion" "python3 - <<'PY'
import json, pathlib
m=json.load(open('api/v1/brain/_manifest.json'))
assert m['entry']=='index.md' and m['notes']
for n in m['notes']:
    assert pathlib.Path('brain')/n['path'], n
assert (pathlib.Path('brain')/'index.md').exists()
PY"

echo "== T-BLOG field notes publish from Markdown (ms-rapp-blog/1.0) =="
check "a committed post appears in the index and the feed, drafts do not" "python3 - <<'PY'
import json, pathlib, subprocess
subprocess.run(['python3','scripts/build_api.py'],capture_output=True,timeout=60)
idx=json.load(open('api/v1/blog/index.json'))
assert idx['protocol']=='ms-rapp-blog/1.0' and idx['count']>=1
slugs={p['slug'] for p in idx['posts']}
for p in pathlib.Path('blog').glob('*.md'):
    head=p.read_text(encoding='utf-8')
    assert head.startswith('---'), p
    draft='draft: true' in head.split('---')[1]
    assert (p.stem.lower() in slugs) != draft, p
# newest first, deterministic
dates=[p['date'] for p in idx['posts']]
assert dates==sorted(dates, reverse=True), dates
for p in idx['posts']:
    assert pathlib.Path(p['path']).exists() and p['raw_url'].startswith('https://raw.githubusercontent.com/')
    assert p['summary'], p['slug']
PY"
check "the feed is JSON Feed 1.1 and bodies are not duplicated into the API" "python3 - <<'PY'
import json, glob, pathlib
f=json.load(open('api/v1/blog/feed.json'))
assert f['version']=='https://jsonfeed.org/version/1.1'
assert f['title'] and f['home_page_url'] and f['feed_url']
for it in f['items']:
    assert it['id'] and it['title'] and it['url']
for g in glob.glob('api/v1/blog/posts/*.json'):
    d=json.load(open(g))
    assert 'content' not in d and 'body' not in d
    assert len(json.dumps(d)) < len(pathlib.Path(d['path']).read_bytes()) + 900
PY"
check "blog.html renders published posts from the API" "python3 - <<'PY'
h=open('blog.html').read()
for n in ('id=\"livePosts\"','api/v1/blog/index.json','data-raw','function md('):
    assert n in h, n
PY"

echo "== T-EXT-ISOLATION extensions cannot affect the core =="
check "removing every extension leaves core endpoints byte-identical and the build green" "python3 - <<'PY'
import hashlib, json, shutil, subprocess, tempfile
from pathlib import Path
CORE=['api/v1/agents.json','api/v1/categories.json','api/v1/publishers.json',
      'api/v1/status.json','api/v1/badge.json']
digest=lambda: {f: hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in CORE}
subprocess.run(['python3','scripts/build_api.py'],capture_output=True)
before=digest()
tmp=Path(tempfile.mkdtemp())/'ext'
shutil.move('rapp/ext', tmp)
try:
    r=subprocess.run(['python3','scripts/build_api.py'],capture_output=True,text=True)
    assert r.returncode==0, 'core build must survive with no extensions installed'
    assert digest()==before, 'an extension changed a core endpoint'
    assert json.load(open('api/v1/index.json'))['extensions']=={}
    assert not Path('api/v1/wall.json').exists(), 'uninstall must sweep extension endpoints'
finally:
    shutil.move(str(tmp), 'rapp/ext')
    subprocess.run(['python3','scripts/build_api.py'],capture_output=True)
assert Path('api/v1/wall.json').exists(), 'reinstall must restore endpoints'
PY"
check "a broken extension is skipped, never fatal" "python3 - <<'PY'
import json, subprocess, pathlib, shutil
d=pathlib.Path('rapp/ext/zz-probe-1.0'); d.mkdir(parents=True, exist_ok=True)
(d/'build.py').write_text('PROTOCOL=\"probe/1.0\"\nNAMESPACES=()\ndef build(ctx):\n    raise RuntimeError(\"boom\")\n')
try:
    r=subprocess.run(['python3','scripts/build_api.py'],capture_output=True,text=True)
    assert r.returncode==0, 'a broken extension must not fail the core build'
    assert 'SKIPPED' in r.stderr, r.stderr
    assert 'probe/1.0' not in json.load(open('api/v1/index.json'))['extensions']
finally:
    shutil.rmtree(d); subprocess.run(['python3','scripts/build_api.py'],capture_output=True)
PY"
check "an extension cannot write outside its declared namespaces" "python3 - <<'PY'
import json, subprocess, pathlib, shutil, hashlib
core=pathlib.Path('api/v1/agents.json'); before=hashlib.sha256(core.read_bytes()).hexdigest()
d=pathlib.Path('rapp/ext/zz-escape-1.0'); d.mkdir(parents=True, exist_ok=True)
(d/'build.py').write_text(
 'PROTOCOL=\"escape/1.0\"\nNAMESPACES=(\"escape.json\",)\n'
 'def build(ctx):\n    ctx.write(\"agents.json\", {\"pwned\": True})\n    return {}\n')
try:
    r=subprocess.run(['python3','scripts/build_api.py'],capture_output=True,text=True)
    assert r.returncode==0
    assert hashlib.sha256(core.read_bytes()).hexdigest()==before, 'namespace guard failed'
finally:
    shutil.rmtree(d); subprocess.run(['python3','scripts/build_api.py'],capture_output=True)
PY"
check "the pattern is specified and the core names no extension" "python3 - <<'PY'
d=open('rapp/ext/PATTERN.md').read().lower()
for k in ('discovery, not registration','namespaced output','failure is contained',
          'uninstall is complete','conformance','byte-identical'):
    assert k in d, k
core=open('scripts/build_api.py').read()
for forbidden in ('ms-rapp-badge','badges.json','certified','wall.json'):
    assert forbidden not in core, f'core names an extension detail: {forbidden}'
PY"

echo "== T-EXT ms-rapp-badge/1.0 extension =="
check "the extension spec is normative and conformance-checkable" "python3 - <<'PY'
d=open('rapp/ext/ms-rapp-badge-1.0/SPEC.md').read()
for k in ('ms-rapp-badge/1.0','rapp-static-api/1.0','MUST NOT be deleted',
          'Conformance','Revocation','not an endorsement','RFC 2119'):
    assert k.lower() in d.lower(), k
# an extension must not claim to change the protocol it extends
assert 'extension, not a revision' in d.lower() or 'is an **extension**' in d.lower()
PY"
check "every generated badge document declares the protocol" "python3 - <<'PY'
import json, glob
for f in ['api/v1/badges.json','api/v1/certified.json','api/v1/wall.json'] + \
         glob.glob('api/v1/badges/*.json') + glob.glob('api/v1/certified/*.json'):
    d=json.load(open(f))
    assert d.get('protocol')=='ms-rapp-badge/1.0', f
idx=json.load(open('api/v1/index.json'))
ext=idx['extensions']['ms-rapp-badge/1.0']
assert ext['originated_by']=='ms-rapp' and 'ext/ms-rapp-badge-1.0/SPEC.md' in ext['spec']
PY"
check "the corpus registers extensions and governs them" "python3 - <<'PY'
r=open('rapp/README.md').read()
assert 'ext/' in r and 'originated' in r.lower()
s=open('rapp/SUCCESSION.md').read().lower()
for k in ('extension','independently versioned','offered upstream','never redefines','conformance'):
    assert k in s, k
PY"

echo "== T-WALL badge catalog + Wall of Fame =="
check "catalog builds per-badge holder endpoints and a ranked wall" "python3 - <<'PY'
import json, subprocess
subprocess.run(['python3','scripts/build_api.py'],capture_output=True,timeout=60)
cat=json.load(open('badges.json'))['badges']
built=json.load(open('api/v1/badges.json'))
assert built['schema']=='aibast-badge-catalog/1.0'
assert {b['id'] for b in cat}=={b['id'] for b in built['badges']}
for b in cat:
    d=json.load(open(f\"api/v1/badges/{b['id']}.json\"))
    assert d['schema']=='aibast-badge/1.0'
    assert d['holder_count']==len(d['holders'])
w=json.load(open('api/v1/wall.json'))
assert w['schema']=='aibast-wall/1.0'
pts=[m['points'] for m in w['members']]
assert pts==sorted(pts,reverse=True), 'wall must be ranked'
for m in w['members']:
    for a in m['badges']:
        assert json.load(open(f\"api{a['badge_url'].split('/api',1)[1]}\"))['schemaVersion']==1
PY"
check "an award naming an unknown badge is ignored, not invented" "python3 - <<'PY'
import json, subprocess, pathlib
src=pathlib.Path('certified.json'); backup=src.read_text()
try:
    d=json.loads(backup)
    d['members'][0]['badges'].append({'id':'no-such-badge','awarded_on':'2026-01-01'})
    src.write_text(json.dumps(d,indent=2))
    subprocess.run(['python3','scripts/build_api.py'],capture_output=True,timeout=60)
    u=json.load(open(f\"api/v1/certified/{d['members'][0]['username'].lower()}.json\"))
    assert all(a['id']!='no-such-badge' for a in u['badges'])
finally:
    src.write_text(backup); subprocess.run(['python3','scripts/build_api.py'],capture_output=True,timeout=60)
PY"
check "wall.html renders distinct badge art and verifies live" "python3 - <<'PY'
import re
h=open('wall.html').read()
for n in ('id=\"badgeCase\"','id=\"people\"','id=\"result\"','api/v1/wall.json',
          'api/v1/badges.json','api/v1/certified/','var SHAPES','function art('):
    assert n in h, n
# each badge must own its silhouette — the shape is what makes it collectible
block = h.split('var SHAPES')[1].split('};')[0]
shapes = re.findall(r'\"(M[^\"]+)\"', block)
assert len(shapes) >= 5, shapes
assert len(set(shapes)) == len(shapes), 'duplicate badge silhouette'
PY"
check "every surface links the Wall of Fame" \
  "grep -q 'wall.html' index.html && grep -q 'wall.html' agents.html && grep -q 'wall.html' api.html"

echo "== T-CERT RAPP Certified verification =="
check "roster builds per-user endpoints, badges, and a roster document" "python3 - <<'PY'
import json, subprocess
subprocess.run(['python3','scripts/build_api.py'],capture_output=True,text=True,timeout=60)
roster=json.load(open('certified.json'))
built=json.load(open('api/v1/certified.json'))
assert built['schema']=='aibast-certified-roster/1.0'
assert '{username}' in built['lookup']
names={m['username'] for m in built['members']}
assert {str(m['username']).lower() for m in roster['members']} == names
for m in built['members']:
    d=json.load(open(f\"api/v1/certified/{m['username']}.json\"))
    assert d['schema']=='aibast-certified/1.0'
    assert d['certified'] is (m['status']=='active')
    b=json.load(open(f\"api/v1/certified/{m['username']}/badge.json\"))
    assert b['schemaVersion']==1 and b['label']=='RAPP'
    assert (b['color']=='brightgreen') is d['certified']
PY"
check "revocation keeps the URL resolving and flips the answer" "python3 - <<'PY'
import json, shutil, subprocess, pathlib
src=pathlib.Path('certified.json'); backup=src.read_text()
try:
    doc=json.loads(backup)
    doc['members'].append({'username':'GateProbeUser','level':'certified',
                           'certified_on':'2026-01-01','status':'revoked',
                           'revoked_on':'2026-02-01','reason':'gate probe'})
    src.write_text(json.dumps(doc,indent=2))
    subprocess.run(['python3','scripts/build_api.py'],capture_output=True,timeout=60)
    d=json.load(open('api/v1/certified/gateprobeuser.json'))
    assert d['certified'] is False and d['status']=='revoked'   # URL resolves, answer is no
    b=json.load(open('api/v1/certified/gateprobeuser/badge.json'))
    assert b['color']=='lightgrey' and 'not certified' in b['message']
finally:
    src.write_text(backup)
    subprocess.run(['python3','scripts/build_api.py'],capture_output=True,timeout=60)
assert not pathlib.Path('api/v1/certified/gateprobeuser.json').exists()  # pruned on removal
PY"
check "api.html verifies usernames live and links the process" "python3 - <<'PY'
h=open('api.html').read()
for n in ('id=\"certUser\"','id=\"certResult\"','id=\"certTable\"',
          'api/v1/certified/','function verify(','img.shields.io/endpoint'):
    assert n in h, n
d=open('docs/CERTIFICATION.md').read()
for k in ('revoked','never deleted','not** a Microsoft','endorsement','certified.json'):
    assert k.lower() in d.lower(), k
PY"

echo "== T7 metrics.html static contract =="
check "exists, loads state/metrics.json, canonical repo, has KPI+boards containers" "python3 - <<'PY'
h=open('metrics.html').read()
for needle in ('state/metrics.json','microsoft/aibast-agents-library',
               'id=\"kpis\"','id=\"board\"','id=\"pub-table\"','id=\"chart\"'):
    assert needle in h, needle
PY"

echo "== T8 headless render =="
check "agents.html renders cards + search filters; metrics.html renders KPIs" \
  "python3 tests/render_headless.py | tee /dev/stderr | grep -q 'headless OK'"

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

echo "== T-PYFLAKES no undefined names in code we ship =="
check "every Python file we author resolves its names (F821)" "python3 - <<'PY'
import shutil, subprocess, sys
if shutil.which('pyflakes') is None and subprocess.run(
        [sys.executable,'-c','import pyflakes'],capture_output=True).returncode != 0:
    print('SKIP: pyflakes not installed'); raise SystemExit(0)
# Kernel-locked and contributed agent trees are upstream's to lint; these are ours.
files=[f for f in subprocess.run(['git','ls-files','*.py'],capture_output=True,text=True).stdout.splitlines()
       if not f.startswith(('rapp_brainstem/','agents/','rapp_cloud/'))]
r=subprocess.run([sys.executable,'-m','pyflakes']+files,capture_output=True,text=True)
bad=[l for l in (r.stdout+r.stderr).splitlines() if 'undefined name' in l]
assert not bad, bad[:8]
PY"

echo "== T-SECRETS no embedded credentials in shippable content =="
check "no signed trigger URLs, keys, or tokens in tracked source" "python3 - <<'PY'
import re, subprocess
# Files a user installs or that we serve. Kernel + pinned mirrors are covered
# by their own gates; binaries/registry are generated from these sources.
files=[f for f in subprocess.run(['git','ls-files'],capture_output=True,text=True).stdout.splitlines()
       if f.split('.')[-1] in ('py','js','sh','ps1','cmd','command','html','md','json','yml','yaml')
       and not f.startswith(('rapp/','rapp_brainstem/','tests/'))]
PATTERNS=[
    (r'[?&]sig=[A-Za-z0-9_\-]{20,}', 'signed trigger URL (bearer credential)'),
    (r'AccountKey=(?!YOUR|\{|\$)[A-Za-z0-9+/]{30,}', 'storage account key'),
    (r'\bgh[pousr]_[A-Za-z0-9]{30,}', 'GitHub token'),
    (r'\bxox[baprs]-[A-Za-z0-9-]{10,}', 'Slack token'),
    (r'-----BEGIN [A-Z ]*PRIVATE KEY-----', 'private key'),
]
hits=[]
for f in files:
    try: t=open(f, encoding='utf-8', errors='ignore').read()
    except OSError: continue
    for pat,label in PATTERNS:
        for m in re.finditer(pat,t):
            hits.append(f'{f}: {label}: {m.group(0)[:40]}')
assert not hits, hits[:8]
PY"
check "no real customer tenant/org endpoints in agent templates" "python3 - <<'PY'
import re, subprocess
files=[f for f in subprocess.run(['git','ls-files','agents','rapp_cloud'],capture_output=True,text=True).stdout.splitlines()
       if f.endswith('.py')]
BAD=re.compile(r'https://(?!contoso|yourcompany|tenant\.|example|<)[a-z0-9-]+\.(crm[0-9]*\.dynamics\.com|sharepoint\.com)')
hits=[f'{f}: {m.group(0)}' for f in files
      for m in BAD.finditer(open(f, encoding='utf-8', errors='ignore').read())]
assert not hits, hits[:8]
PY"

echo "== T-IDENT rename never corrupts an identifier =="
check "no space-bearing identifier from a display-name substitution" "python3 - <<'PY'
import re, subprocess
# 'RAPP Cloud' is correct in prose and fatal in an identifier: a PowerShell or
# shell function name, a path segment, a filename, a CLI argument value, or an
# XML unique name. This class of break is invisible to a text-only review.
PATTERNS = [
    (r'function\\s+[A-Za-z-]*RAPP Cloud', 'function name'),
    (r'[A-Za-z_]*RAPP Cloud\\s*\\(\\)',      'shell function name'),
    (r'[/\\\\]RAPP Cloud',                'path segment'),
    (r'RAPP Cloud[/\\\\]',                'path segment'),
    (r'<UniqueName>[^<]*RAPP Cloud',   'XML unique name'),
    (r'RAPP Cloud[A-Za-z]*\\.(zip|json|py|ps1|sh|cmd)', 'filename'),
    (r'\\\$[A-Za-z]*RAPP Cloud',           'variable'),
    (r'--[a-z-]+ RAPP Cloud',          'CLI argument value'),
]
EXT = ('.sh','.ps1','.cmd','.command','.py','.js','.json','.xml','.yml','.yaml','.html','.md')
hits = []
for f in subprocess.run(['git','ls-files'], capture_output=True, text=True).stdout.splitlines():
    if not f.endswith(EXT) or f.startswith('tests/'): continue  # this file defines the patterns
    try: text = open(f, encoding='utf-8', errors='ignore').read()
    except OSError: continue
    for pat, label in PATTERNS:
        for m in re.finditer(pat, text):
            hits.append(f'{f}:{text[:m.start()].count(chr(10))+1} [{label}] {m.group(0)[:50]}')
assert not hits, hits[:10]
PY"
check "PowerShell installers parse (no space in a function name)" "python3 - <<'PY'
import re
for f in ('install.ps1','rapp_cloud/install.ps1','docs/install.ps1'):
    src = open(f, encoding='utf-8', errors='ignore').read()
    bad = [m.group(0) for m in re.finditer(r'^\\s*function\\s+[^\\n{]*', src, re.M)
           if ' ' in m.group(0).split('function',1)[1].strip().rstrip('{').strip()]
    assert not bad, (f, bad)
PY"
check "installer test suite targets paths that exist" "python3 - <<'PY'
import re, os
src = open('tests/test_installer.sh', encoding='utf-8').read()
for path in re.findall(r'\"([a-z_]+/install\\.[a-z]+)\"', src):
    assert os.path.exists(path), path
PY"

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
             'vbrainstem/README.md',         # discloses that proxy to the user (required)
             'DISCLAIMER.md',                # same disclosure, user-facing
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

echo "== T-TERMS enterprise vocabulary across every editable surface =="
check "no informal or retired vocabulary in anything we can edit" "python3 - <<'PY'
import re, subprocess
# Scan EVERY tracked text file. Exemptions are explicit and path-based so they
# are visible in review, never accidental.
EXEMPT_DIRS = (
    'rapp_brainstem/',   # kernel-locked: fixes flow down from upstream, never patched here
    'rapp/handbook/',    # pinned upstream mirror, byte-exact by contract
    'rapp/standards/',   # pinned upstream mirror
    'rapp/spec/',        # pinned upstream mirror
    'tests/',            # this suite's own guard patterns
)
EXEMPT_FILES = {
    # Byte-identical mirror of rapp_brainstem/local_storage.py — editing it would
    # fork the engine from the kernel and dirty every future sync.
    'vbrainstem/local_storage.py',
    'docs/CLEAN-BREAK.md',   # the audit record names what was retired
    'rapp/ALIGNMENT.md',     # ditto
    'rapp/SUCCESSION.md',    # describes the upstream relationship
    'rapp/THIRD-PARTY-NOTICES.md',
    'rapp_cloud/CHANGELOG.md',    # historical record
    'rapp_cloud/CONSTITUTION.md', # historical record
}
TEXT = ('.md','.html','.txt','.py','.js','.json','.yml','.yaml','.sh','.ps1','.cmd','.command')
BANNED = re.compile(r'\b(grail|bible|sacred|incantation|CommunityRAPP|rapp_ai|crapp)\b', re.I)
# Factual upstream project/repo names are provenance, not our vocabulary.
PROVENANCE = re.compile(r'RAPP-Bible|rapp-god|kody-w/[A-Za-z0-9._-]+|community_rapp')
r = subprocess.run(['git','ls-files'], capture_output=True, text=True)
assert r.returncode == 0, r.stderr
offenders = []
for f in r.stdout.splitlines():
    if f.startswith(EXEMPT_DIRS) or f in EXEMPT_FILES: continue
    if not f.endswith(TEXT): continue
    try: text = open(f, encoding='utf-8', errors='ignore').read()
    except OSError: continue
    for m in BANNED.finditer(PROVENANCE.sub('', text)):
        offenders.append(f'{f}: {m.group(0)}')
assert not offenders, offenders[:15]
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
check "README carries standard CLA + Trademarks boilerplate (skill-recorder parity)" "python3 - <<'PY'
t=open('README.md').read()
assert 'cla.opensource.microsoft.com' in t
assert 'Trademark & Brand Guidelines' in t
assert 'must not cause confusion or imply Microsoft sponsorship' in t
PY"
check "CONTRIBUTING certifies provenance + CLA; DISCLAIMER covers local execution" "python3 - <<'PY'
c=open('CONTRIBUTING.md').read()
assert 'cla.opensource.microsoft.com' in c and 'provenance' in c
d=open('DISCLAIMER.md').read()
assert 'runs on your machine' in d and 'nothing you run\nis sent to this repository' in d
assert 'VB_AUTH_WORKER' in d and 'Azure Pricing Calculator' in d  # disclosed exceptions
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
