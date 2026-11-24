"""Brainstem shape test: does another body behave exactly like the Brainstem kernel?

A Brainstem is defined by its shape, not by where its Python runs. This tool records what the
unchanged kernel does with every agent file in one body (installed Python, or Python carried
inside a web page) and compares two records. Same record, same Brainstem.

    python scripts/brainstem_shape.py record  <kernel dir> <agents dir> <out.json> [--run-list <file>]
    python scripts/brainstem_shape.py compare <reference.json> <body.json> [--again <reference2.json>] [--known <list.json>]

record   runs inside the body under test. It loads each agent file through the kernel's own loader,
         keeps the tool description the model would see, and for files named in the run list keeps
         what perform() returns. It also calls /health through the kernel's own app, with no socket.
compare  fails when a tool description, a repeatable perform() answer, or /health differs. An answer
         the reference itself does not repeat (a clock, a random number) is reported, never compared.
         Record the reference before and after the body so a clock that ticks in between is caught.
         --known names agent files that cannot run in this kind of body, each with its reason; they
         are counted and printed, and anything not on the list still fails.
"""
import hashlib, io, json, os, sys, contextlib, traceback


def record(kernel_dir, agents_dir, run_names):
    os.environ["AGENTS_PATH"] = agents_dir
    os.environ.setdefault("PORT", "7071")
    sys.path.insert(0, kernel_dir)
    os.chdir(kernel_dir)
    noise = io.StringIO()
    out = {"python": sys.version.split()[0], "platform": sys.platform, "kernel_import": "ok", "agents": {}}
    try:
        with contextlib.redirect_stdout(noise), contextlib.redirect_stderr(noise):
            import brainstem as kernel
            if hasattr(kernel, "_register_shims"):
                kernel._register_shims()
    except BaseException as e:  # the record must say why, not die
        out["kernel_import"] = f"{type(e).__name__}: {e}"
        out["trace"] = traceback.format_exc()[-1500:]
        return out
    out["kernel_version"] = getattr(kernel, "VERSION", None) or open(os.path.join(kernel_dir, "VERSION")).read().strip()
    for fname in sorted(f for f in os.listdir(agents_dir) if f.endswith("_agent.py") and f != "basic_agent.py"):
        path = os.path.join(agents_dir, fname)
        row = {"sha256": hashlib.sha256(open(path, "rb").read()).hexdigest()}
        try:
            with contextlib.redirect_stdout(noise), contextlib.redirect_stderr(noise):
                loaded = kernel._load_agent_from_file(path)
            row["loaded"] = sorted(loaded)
            row["tools"] = {n: a.to_tool() for n, a in sorted(loaded.items())}
            if fname in run_names:
                row["perform"] = {}
                for n, a in sorted(loaded.items()):
                    try:
                        with contextlib.redirect_stdout(noise), contextlib.redirect_stderr(noise):
                            got = a.perform()
                        row["perform"][n] = {"type": type(got).__name__, "text": got if isinstance(got, str) else repr(got)}
                    except BaseException as e:
                        row["perform"][n] = {"error": f"{type(e).__name__}: {e}"}
        except BaseException as e:
            row["load_error"] = f"{type(e).__name__}: {e}"
        out["agents"][fname] = row
    # the kernel's own doors, with no socket: the same routes a program would call
    try:
        with contextlib.redirect_stdout(noise), contextlib.redirect_stderr(noise):
            c = kernel.app.test_client()
            h = c.get("/health")
            a = c.get("/agents")
        out["health"] = {"status": h.status_code, "keys": sorted((h.get_json() or {}).keys())}
        out["agents_route"] = {"status": a.status_code}
    except BaseException as e:
        out["health"] = {"error": f"{type(e).__name__}: {e}"}
    return out


def record_main(argv):
    kernel_dir, agents_dir, dest = (os.path.abspath(x) for x in argv[1:4])
    run_names = set()
    if "--run-list" in argv:
        run_names = set(open(argv[argv.index("--run-list") + 1]).read().split())
    out = record(kernel_dir, agents_dir, run_names)
    with open(dest, "w") as f:
        json.dump(out, f, indent=1, sort_keys=True, default=str)
    return out


def compare(ref, body, again=None, known=None):
    """Returns (ok, lines). ref/body/again are records made by `record`."""
    lines, bad, known = [], 0, known or {}
    lines.append(f"reference: Python {ref.get('python')} on {ref.get('platform')}; body: Python {body.get('python')} on {body.get('platform')}")
    if body.get("kernel_import") != "ok":
        return False, lines + [f"FAIL the kernel did not load in the body: {body.get('kernel_import')}"]
    if ref.get("python", "").split(".")[:2] != body.get("python", "").split(".")[:2]:
        lines.append("note: the two Pythons are different versions; number formatting and float sums can differ between versions")
    if ref.get("health") != body.get("health"):
        bad += 1
        lines.append(f"FAIL /health differs: {ref.get('health')} vs {body.get('health')}")
    R, B = ref["agents"], body["agents"]
    missing = sorted(set(R) - set(B))
    if missing:
        bad += len(missing)
        lines.append(f"FAIL {len(missing)} agent file(s) not recorded by the body: {missing[:5]}")
    files = sorted(set(R) & set(B))
    tool_diff = [f for f in files if R[f].get("tools") != B[f].get("tools") or R[f].get("load_error") != B[f].get("load_error")]
    lines.append(f"tool descriptions identical: {len(files) - len(tool_diff)} of {len(files)}")
    for f in tool_diff:
        if f in known:
            lines.append(f"known, cannot run in this body: {f} ({known[f]})")
            continue
        bad += 1
        lines.append(f"FAIL {f}: the body loads {B[f].get('loaded')} where the reference loads {R[f].get('loaded')}")
    ran = [f for f in files if "perform" in R[f]]
    if again is None:
        steady, loose = ran, []
        lines.append("note: no second reference record given, so answers that change by themselves are not set aside")
    else:
        steady = [f for f in ran if R[f].get("perform") == again["agents"].get(f, {}).get("perform")]
        loose = [f for f in ran if f not in steady]
    ans_diff = [f for f in steady if R[f]["perform"] != B[f].get("perform") and f not in known]
    bad += len(ans_diff)
    lines.append(f"perform() answers identical: {len(steady) - len(ans_diff)} of {len(steady)} repeatable")
    for f in ans_diff:
        lines.append(f"FAIL {f}: the answer differs from the reference")
    if loose:
        lines.append(f"not compared, the reference does not repeat itself: {len(loose)} ({', '.join(loose[:6])})")
    stale = sorted(f for f in known if f in files and f not in tool_diff and R[f].get("perform") == B[f].get("perform"))
    if stale:
        bad += len(stale)
        lines.append(f"FAIL listed as known but it now matches, take it off the list: {stale}")
    lines.append("SAME SHAPE" if not bad else f"DIFFERENT: {bad} difference(s)")
    return not bad, lines


def main(argv):
    if len(argv) > 4 and argv[1] == "record":
        r = record_main(argv[1:])
        sys.__stdout__.write(f"kernel import: {r['kernel_import']}; agent files recorded: {len(r['agents'])}\n")
        return 0 if r["kernel_import"] == "ok" else 1
    if len(argv) > 3 and argv[1] == "compare":
        again = json.load(open(argv[argv.index("--again") + 1])) if "--again" in argv else None
        known = json.load(open(argv[argv.index("--known") + 1])) if "--known" in argv else None
        ok, lines = compare(json.load(open(argv[2])), json.load(open(argv[3])), again, known)
        print("\n".join(lines))
        return 0 if ok else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
