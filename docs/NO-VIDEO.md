# No video in the library

This distribution carries no video or live-action assets. That is a deliberate
weight decision, not an oversight, and this note says where the material went
and how to bring it back.

## What was removed

2,634 MB across 215 files:

| | |
|---|---|
| `film/corpus/videos/` | 19 reference recordings — 2,179 MB, the bulk of it |
| `media/videos/` | 48 hosted demo recordings — 174 MB |
| `archive/rappvision-pipeline/media/plates/base/` | 48 base plates — 111 MB |
| `archive/rappvision-pipeline/media/{broll,audio}/` | b-roll and music beds — 87 MB |
| `film/assets/{broll,audio,stings}/` | the film kit's own footage and beds — 85 MB |
| `film/projects/*/{dist,work}/` | generated films and their intermediates |

Tracked tree: **2,679 MB → 20 MB**.

## Where it went

All of it is on the local branch **`feature/film-and-video`**, which also holds
the seven FY27 films, the film kit that produced them, and the archived
RAPPVision pipeline's assets. Nothing was deleted from history.

```bash
git log --oneline -1 feature/film-and-video
git ls-tree -r feature/film-and-video --name-only | grep '\.mp4$' | wc -l   # 215 incl. audio
git cat-file -e feature/film-and-video:media/videos/ask-hr-agent.mp4        # still there
```

That branch is **local only** — deliberately not pushed. When video comes back,
it comes back from there.

Restore a single file without switching branches:

```bash
git checkout feature/film-and-video -- media/videos/ask-hr-agent.mp4
```

## Why removing files was not enough

This is the part that is easy to get wrong.

**Deleting a file from the tip does not make `git clone` any cheaper.** Every
blob ever committed stays in the pack, and `install.sh` cloned all of it. After
stripping every video the tracked tree was 20 MB and a full clone still pulled
**2.6 GB**.

So `install.sh` and `install.ps1` now clone at **depth 1**, which fetches only
the current tree. Measured on a real clone:

| | working tree | `.git` |
|---|---|---|
| full clone of `main` | 3.0 GB | 2.6 GB |
| depth-1 clone, stripped | **26 MB** | **3.7 MB** |

Removing the assets is what makes a shallow clone small; the shallow clone is
what makes removing them pay. Neither works alone.

### The one path that still needs history

Pinning a version resolves a tag, and a depth-1 clone has neither tags nor the
history to resolve them against. That path — and only that path — buys back what
the shallow clone skipped:

```sh
git fetch --unshallow --quiet
git fetch origin --tags --quiet
```

Verified end to end: a depth-1 clone reports `is-shallow-repository true` with
zero tags; after the unshallow it reports `false` and the release tags resolve.

## What this changed on the surfaces

- `api/v1/onepagers.json` now reports `hosted_videos: 0`. The plumbing already
  keyed on `is_file()`, so it degraded honestly with no code change.
- `solutions.html` no longer promises "the demo recording, playable here rather
  than behind a request for access", and its *Demos hosted* stat and *Has a
  demo* filter are gone rather than left showing zero against an empty choice.
- The film kit under `film/kit/` is **kept**. It is text, it is small, and
  keeping it means `feature/film-and-video` merges back cleanly rather than
  fighting a deleted tree.

## Bringing video back

1. Merge or cherry-pick from `feature/film-and-video`.
2. Decide the hosting question *before* merging. Putting 2.6 GB back into the
   tip puts it back into every future clone, shallow or not. A release asset, a
   separate media repository, or a CDN keeps the library light.
3. If the installer should stay shallow — it should — nothing there needs
   changing.
