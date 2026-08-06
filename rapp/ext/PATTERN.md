# The ms-rapp extension pattern

**How this distribution adds capability without ever standing in the way of a
kernel update.**

Status: normative for every ms-rapp expansion. Governance (how an extension is
versioned and offered upstream) is in [SUCCESSION.md](../SUCCESSION.md).
First implementation: [`ms-rapp-badge/1.0`](ms-rapp-badge-1.0/SPEC.md).

---

## 1. The problem this solves

An LTS distribution that adds features by editing shared files slowly becomes
a fork: every kernel sync turns into a merge negotiation, and the cost of
staying current rises until it stops happening. The distribution then either
freezes or diverges. Both are failure.

So the rule is not "add carefully." The rule is **the core must not know that
any particular extension exists.**

## 2. The pattern, borrowed from the kernel

RAPP/1 already answers this twice, and this pattern is those two answers
applied to the distribution:

- *"New capability is a new agent behind `/chat`, never a sibling REST route"*
  (RAPP/1 §8). Capability arrives at an established extension point, never as
  a new limb on the core surface.
- *"Unrecognized members **MUST** be ignored, never refused"* (RAPP/1 §8).
  Not knowing about something is never an error.

The brainstem itself is the working example: `agents/*_agent.py` are
discovered from a directory, self-register, and are reloaded per request. No
file lists them. Adding one is dropping it in; removing one is deleting it.

**An ms-rapp extension is that same shape, one level up.**

## 3. The contract

An extension is a single directory: `rapp/ext/<protocol>-<major>.<minor>/`.

| File | Required | Purpose |
|---|---|---|
| `SPEC.md` | ✅ | The normative specification, with a conformance section. |
| `build.py` | ⬜ | The builder, if the extension emits endpoints. |
| anything else | ⬜ | Fixtures, tests, notes — scoped to this directory. |

`build.py` MUST expose:

```python
PROTOCOL   = "ms-rapp-<name>/<major>.<minor>"   # what it declares in output
NAMESPACES = ("thing.json", "thing/")           # every path it may write
def build(ctx) -> dict: ...                     # returns its index.json entry
```

`ctx` is the only surface the core offers: `ctx.load(path, default)`,
`ctx.write(rel, doc)`, `ctx.prune(rel_dir, keep)`, plus `ctx.agents`,
`ctx.generated`, `ctx.pages_base`. There is no core object to reach through.

## 4. The rules

1. **Discovery, not registration.** The core globs `rapp/ext/*/build.py`. No
   file anywhere names an extension. Adding one is a directory; removing one
   is `rm -r`.
2. **Namespaced output.** An extension may only write inside its declared
   `NAMESPACES`. The host refuses anything else, so an extension can never
   collide with a core endpoint or with another extension.
3. **Failure is contained.** An extension that is missing, broken, or throws
   is reported and skipped. The core API still builds and still exits 0. A
   broken expansion must never be able to break the distribution.
4. **Uninstall is complete.** The previous `index.json` records each
   extension's namespaces, so removing the directory makes the next build
   sweep the endpoints it used to own. Nothing keeps serving after removal.
5. **Extensions never touch kernel content.** Anything under `rapp_brainstem/`,
   the installers, or the pinned mirrors in `rapp/spec|handbook|standards` is
   out of bounds — those are covered by `BRAINSTEM-LOCK.json` and the corpus
   manifest, and a kernel sync must be able to replace them wholesale.
6. **Every generated document declares its `protocol`,** so a consumer can
   tell distribution-originated data from core data at a glance.
7. **The core stays ignorant.** If you find yourself adding a name, a count,
   or a branch to shared code on an extension's behalf, the design is wrong —
   move it behind `ctx`.

## 5. Why this survives a kernel sync

A kernel sync replaces kernel files. Under this pattern an extension owns:

- its own directory (not kernel content),
- its own output namespace (not core endpoints),
- its own version line (not RAPP/1's).

The intersection with a kernel sync is therefore **empty by construction**, not
by care. That is the property worth having: it does not depend on anyone
remembering it during a merge.

## 6. Conformance

An extension conforms if:

- [ ] It lives entirely in one `rapp/ext/<name>-<ver>/` directory.
- [ ] It ships a `SPEC.md` with a conformance section.
- [ ] `build.py` (if present) exposes `PROTOCOL`, `NAMESPACES`, `build(ctx)`.
- [ ] It writes only inside its declared namespaces.
- [ ] Removing its directory leaves every core endpoint **byte-identical** and
      the build exiting 0 — verified, not asserted (see the `T-EXT-ISOLATION`
      section of `tests/test_library_frontend.sh`).
- [ ] Removing its directory removes its endpoints.
- [ ] Its generated documents carry `protocol`.
- [ ] It modifies no kernel file and no pinned mirror.
