---
name: tab-film
description: >
  Capture a demo film from a live web app safely and cut it to narration. Use for
  any "film this agent / app / portal" ask. Encodes the capture method that works
  on Kody's machine, the three ways desktop capture leaks his private windows,
  and the post-processing step that destroys text. Trigger on film, record,
  showcase video, demo video, capture the screen.
---

# Filming a live web app

## Never use desktop screen capture on this machine

`ffmpeg -f avfoundation -i "2"` grabs **the display**, not a window. It has
leaked private content three separate times in one session:

- Chrome not frontmost → captured VS Code with a session transcript in it
- `open -a "Google Chrome"` → triggered Mission Control, capturing every open
  window at once
- macOS fullscreen → moved Chrome to its own Space, so the capture showed the
  *other* Space (VS Code, Finder, a PowerPoint error dialog)

Fullscreen makes it worse, not better. If a frame is ever captured that contains
anything of Kody's, delete it immediately and say so.

You cannot force fullscreen yourself: `⌃⌘F` sent through the extension does not
reach browser chrome, and `requestFullscreen()` is rejected as untrusted from a
synthetic `click` — though it **does** work when armed on `mousedown`.

## Use the extension's recorder — it is tab-only by construction

`gif_creator` captures the tab viewport. The desktop physically cannot appear.

```
gif_creator start_recording
  → drive the page
gif_creator export (download: true, showClickIndicators/ActionLabels/
                    ProgressBar/Watermark all false, quality 4)
```

**Drive frame capture with `wait` actions, not `screenshot` actions.** Both
produce a frame; only `screenshot` returns an image into your context, and a
50-frame burst of those will exhaust a session. `wait` gives the same frames for
free.

Cap is 50 frames per recording. Export between beats and stitch later.

Then dedupe — a 44-frame export is typically 9–29 distinct states:

```python
prev=None
for f in sorted(glob.glob('q/f*.png')):
    h=hashlib.md5(open(f,'rb').read()).hexdigest()
    if h!=prev: keep.append(f); prev=h
```

## NEVER motion-interpolate text

`minterpolate` with `mi_mode=mci` warps pixels along estimated motion vectors.
Between two frames of *different text* it produces unreadable ghosted soup — it
will try to morph "OPERATING BUDGET" into "CAPITAL BUDGET". Hard cuts, or a
crossfade ≤0.3s. Nothing else. This shipped once and was caught by Kody, not by
the build.

The honest consequence: you cannot manufacture fluid motion from discrete text
states. Frame interpolation only works on continuous motion. If Kody wants true
30fps of a chat streaming, **he records it himself** with ⌘⇧5 while you drive
the page — that is the only route, and it takes him two minutes.

## Audio contract — non-negotiable

- VO bus **+6dB**, voice `en-US-AndrewMultilingualNeural`
- Bed `film/assets/audio/bed-slow-drift.caf` (in-repo; 19.009909s loop with a
  20dB trough 4-6s in — see `film/AUDIO.md`)
- `sidechaincompress=threshold=0.015:ratio=8:attack=25:release=450:makeup=1`
- `alimiter=limit=0.95`
- **NEVER loudnorm**
- Gate: every VO slot mean > **−19dB**; bed-only gaps < **−22dB**

That bed is quiet material (−37dB mean at −16dB gain), so it passes the gate by
20dB while being effectively inaudible. Raise it until it is actually present.

**Every slot must land inside its window.** If a read does not fit, widen the
window or shorten the copy — **never speed up the read**. Over ~2.6 words/sec
reads rushed; check it and name the slot.

### Azure Speech auth

Every Speech resource on this subscription has `disableLocalAuth=true`, so keys
do not exist. Use Entra:

```
Authorization: aad#<resourceId>#<aadToken>
resourceId = $AZURE_SPEECH_RESOURCE_ID/resourceGroups/
             koda-ai/providers/Microsoft.CognitiveServices/accounts/koda-speech
token = az account get-access-token --resource https://cognitiveservices.azure.com
```

## Two cuts, two vocabularies

**Internal** (SEs reviewing the pipeline) may say RAPP Factory, MVP, skills.

**Customer-facing** must not. The customer has never heard of RAPP, the Factory,
RAPPlication, brainstem, egg, MVP, or prototype. Put a **vocabulary gate in the
build script** that hard-fails on those words in narration and card strings — and
know that it cannot see the pixels of captured shots, which is where leakage
actually lives. Check frames by eye.

## The gate

**Watch it.** Extract frames and READ them across the whole timeline. A green
build is not a watched film — this failed twice in one session, once shipping a
smeared unwatchable cut.

Then spawn a **separate blind adversarial reviewer** with the audience brief.
It will find things you cannot, because you know what you intended. Real findings
it caught that the builder missed:

- Internal tool identifiers on screen for 57 of 105 seconds
- Narration claiming success over a frame where the agent visibly failed
- 23 seconds held on one identical frame
- The artifact's own heading sliced in half at the scroll edge
- The user's question never visible despite three "ask it for…" lines
- Invented person names on screen 12s before the synthetic-data disclaimer

Loop until it returns PASS with zero blockers. Then report residual defects
honestly — a known flaw named is fine, a flaw the customer finds is not.

## Related

`/cs-agent-live` to get the agent presentable before you film it.


## The Azure resource id is NOT in this repo, deliberately

It contains a subscription GUID and **this repo is a fork of a public
Microsoft repository**. Never commit it. Supply it at run time:

```
export AZURE_SPEECH_RESOURCE_ID='/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.CognitiveServices/accounts/<account>'
export AZURE_SPEECH_TOKEN=$(az account get-access-token \
  --resource https://cognitiveservices.azure.com --query accessToken -o tsv)
```

`agent.py preflight` fails loudly if either is missing. Local keys are
disabled on these resources — Entra only.
