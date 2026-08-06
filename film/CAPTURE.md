# Filming a live surface

`film/kit/screens.py` draws the demo segment. This document is for the other
case — when the demo has to be the real product, captured. Read it before you
record anything, because two of the rules below exist because private material
reached a frame.

## Never capture the desktop

`ffmpeg -f avfoundation -i "<display>"` grabs the *display*, not a window. On
one machine, in one session, that leaked three different ways:

- the browser was not frontmost, so the capture recorded an editor with a
  session transcript in it;
- bringing the browser forward triggered the window manager's overview, and
  the capture recorded every open window at once;
- putting the browser in full screen moved it to its own space, and the
  capture recorded the *other* space — an editor, a file browser, and an
  application error dialog.

Full screen makes it worse, not better. If any frame captures material that is
not the product, delete the take immediately and say so.

## Two sanctioned methods, both tab-only by construction

**The browser extension's recorder.** The desktop cannot appear in the output,
because the recorder never sees it. Start it, drive the page, export.

- The cap is 50 frames per recording. Export between beats and stitch.
- **Drive frame capture with `wait` actions, not `screenshot` actions.** Both
  produce a frame; only `screenshot` returns an image into the session, and a
  50-frame burst of those exhausts it.
- Deduplicate after export. A 44-frame export is typically nine to thirty
  distinct states; the rest are the same pixels.

**A CDP screencast** against an already-running browser
(`Page.startScreencast`, `format: png`, `everyNthFrame: 2`). Every frame must
be acknowledged with `Page.screencastFrameAck` or the stream stalls.

Either way: find the page by URL, never by index. Taking index 0 once landed a
probe on an unrelated tab and produced a confident, false "the answer is
missing".

## Completion is not a length plateau

A take was ruined by typing the next question over the previous answer's
"Working on it…". The page sits perfectly still while the spinner spins, so a
stable body length is not completion.

Completion is **no spinner text AND a settled body**, over several consecutive
polls. Poll every three seconds, require four unchanged polls, cap the wait at
five minutes, and hold four more seconds of reading time before cutting.

## Citations resolve late, and not everywhere

- They resolve **only when a message completes**. Mid-stream frames carry raw
  reference tokens, so a panel that looks perfect at the end was broken in the
  middle — and the middle is what a contact sheet catches.
- They do not render **inside a table cell**. Only in prose. Ask for prose.
- A follow-up in an existing thread is answered from conversation history
  without re-calling any tool, so it has **no citations at all**. Start a
  fresh chat for every question you intend to show.

`screens.py` mirrors all three: citations appear only on the final stage of a
question, never on an intermediate one.

## Before you roll

- Turn on the surface's end-user preview mode, or chain-of-thought rows and
  raw tool identifiers are on screen for the whole take. Verify it per
  response, not once — the behaviour differs between answers.
- Check the agent's display name. Generated names truncate silently at 30
  characters and read badly on camera.
- Show the operator's question in frame. Three "ask it for…" narration lines
  over answers with no visible question is a reviewer's first finding, and it
  is why every demo beat in this kit carries a lower third with the prompt.
- Confirm the surface actually answers from its data before you film it, with
  a question whose answer can only come from the data. A greeting proves
  nothing.

## Never motion-interpolate text

`minterpolate` with motion compensation warps pixels along estimated motion
vectors. Between two frames of *different text* it produces unreadable
ghosting — it will try to morph one heading into another. Hard cuts, or a
crossfade of 0.3 s or less. Nothing else. This shipped once and a human caught
it, not the build.

The honest consequence: you cannot manufacture fluid motion out of discrete
text states. If a take genuinely needs 30 fps of a response streaming in, it
has to be recorded that way.

## Compressing a capture

Reading holds are the point of the film; spinner holds are dead time.
Compress only the latter. Find runs of identical frames by hash, collapse each
to about 1.6 s, and clamp any single frame to 3 s. Never speed-ramp, and never
apply a global speed factor — it hits the reading holds too.
