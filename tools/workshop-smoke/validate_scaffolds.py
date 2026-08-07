import json, re, sys, pathlib, yaml
ROOT = pathlib.Path("/Users/kodywildfeuer/Documents/GitHub/aibast-agents-library")
CAP = pathlib.Path("/private/tmp/claude-501/-Users-kodywildfeuer-Documents-GitHub-aibast-agents-library/7eb12ce0-32d0-420f-b8c4-eb9929a298e0/scratchpad/captures")
EXEMPLAR = "field_service_dispatch_stack"
issues, ok = {}, []
for man_path in sorted(ROOT.glob("agents/@aibast-agents-library/*_stacks/*/copilot_studio/manifest.json")):
    stack_dir = man_path.parent.parent
    if stack_dir.name == EXEMPLAR: continue
    key = stack_dir.parent.name + "__" + stack_dir.name
    errs = []
    cs = man_path.parent
    try:
        man = json.loads(man_path.read_text())
    except Exception as e:
        issues[key] = [f"manifest unparseable: {e}"]; continue
    for k in ("schema","stack","display_name","instructions","behaviors","knowledge_files","verification"):
        if k not in man: errs.append(f"manifest missing key {k}")
    for rel in man.get("behaviors",[]) + man.get("knowledge_files",[]) + [man.get("instructions","instructions.md")]:
        if not (cs/rel).exists(): errs.append(f"listed file missing: {rel}")
    for b in man.get("behaviors",[]):
        p = cs/b
        if p.exists():
            try:
                d = yaml.safe_load(p.read_text())
                if d.get("kind") != "InlineAgentSkill": errs.append(f"{b}: kind != InlineAgentSkill")
                if not d.get("mcs.metadata",{}).get("componentName"): errs.append(f"{b}: no componentName")
                if "bic:source=blank" not in d.get("content",""): errs.append(f"{b}: missing bic marker")
            except Exception as e: errs.append(f"{b}: yaml error {e}")
    for kf in man.get("knowledge_files",[]):
        p = cs/kf
        if p.exists() and kf.endswith(".md") and "SYNTHETIC" not in p.read_text()[:600]:
            errs.append(f"{kf}: no SYNTHETIC banner")
        if p.exists() and kf.endswith(".mcs.yml"):
            try:
                d = yaml.safe_load(p.read_text())
                if not d.get("mcs.metadata",{}).get("componentName"): errs.append(f"{kf}: sidecar no componentName")
            except Exception as e: errs.append(f"{kf}: sidecar yaml error {e}")
    ins = cs/man.get("instructions","instructions.md")
    if ins.exists() and len(ins.read_text()) < 700: errs.append("instructions.md suspiciously short")
    vs = man.get("verification",[])
    # repaired stacks legitimately gained checks; 9 is the practical ceiling
    if not (3 <= len(vs) <= 9): errs.append(f"verification count {len(vs)}")
    capf = CAP/(key+".json")
    if capf.exists() and vs:
        cap = json.loads(capf.read_text())
        hay = " ".join(o for a in cap["agents"] for o in a["outputs"].values()) + " " + \
              " ".join(a["source"] for a in cap["agents"])
        for i, v in enumerate(vs):
            exp = v.get("expect","")
            nums = re.findall(r"\$?[\d][\d,\.]{2,}%?", exp)
            miss = [n for n in nums if n.rstrip("%").rstrip(".") and n.replace(",","").rstrip("%").rstrip(".") not in hay.replace(",","")]
            if len(miss) > max(1, len(nums)//2):
                errs.append(f"verification[{i}] facts not traceable: {miss[:4]}")
    if errs: issues[key] = errs
    else: ok.append(key)
print(f"OK: {len(ok)}  ISSUES: {len(issues)}")
for k, v in list(issues.items())[:12]:
    print(f"-- {k}: " + " | ".join(v[:4]))
json.dump({"ok": ok, "issues": issues}, open("/private/tmp/claude-501/-Users-kodywildfeuer-Documents-GitHub-aibast-agents-library/7eb12ce0-32d0-420f-b8c4-eb9929a298e0/scratchpad/validation.json","w"))
