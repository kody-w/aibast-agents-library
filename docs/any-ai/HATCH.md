---
name: "aibast-brainstem-hatch"
description: "Hatch a Brainstem for yourself and be its model. For an AI that can run Python somewhere (your own sandbox or the person's computer) but should not ask the person for a second sign-in. The Brainstem's real chat loop runs unchanged; each time it needs the model it asks you."
license: "MIT"
compatibility: "Any AI that can run Python 3.9 or later and fetch a file. No sign-in. No server. No open port."
---

# Hatch a Brainstem and be its model

A Brainstem is a small AI runtime: it keeps agents (single Python files), offers them to a model, runs the
ones the model picks, and returns one reply. Normally it signs in to a model of its own. Here **you are the
model**, so the person needs nothing but you.

## Tell the person first, and wait for a yes

> I can set up a Brainstem here, a small runtime that lets me use ready-made agents and keep a record of
> what we did. It fetches a handful of files, checks each one's fingerprint, and runs them where I run code.
> Nothing is installed on your computer unless that is where I run code. OK?

## Then do this, in order

1. Make an empty folder and work inside it.
2. Fetch one file into it: `https://microsoft.github.io/aibast-agents-library/docs/any-ai/hatch.py`
   and its helper `https://microsoft.github.io/aibast-agents-library/docs/any-ai/plug.py`.
3. Run `python hatch.py get`. It fetches the Brainstem into `rapp_brainstem/`, refuses any file whose
   fingerprint does not match, and installs the four small Python packages the Brainstem needs.
4. Run `python hatch.py tools` and read the list once. Those are your agents.
5. Tell the person, in one sentence, that it is ready, and offer one thing to try.

If you cannot run Python anywhere, stop and say so plainly. Give the person
https://microsoft.github.io/aibast-agents-library/docs/installer.html instead. Never pretend to run an agent.

## Every turn after that

When the person asks for something an agent could do:

1. `python hatch.py ask "<what the person said>"`
   It prints what the model must answer: the new messages, and the agents you may call.
2. Answer as the model:
   - to run an agent first:
     `python hatch.py answer '{"tool_calls": [{"function": {"name": "<Agent>", "arguments": {}}}]}'`
     The Brainstem runs it and hands you the agent's real output. Never invent an agent's output.
   - to finish: `python hatch.py answer '<your words for the person>'`
3. When it prints `"done"`, say the `response` to the person. Up to three rounds of agents a turn.

Need an agent you do not have? `python hatch.py bring <agent name>` adds one from the library catalog,
fingerprint-checked. Browse the catalog: https://microsoft.github.io/aibast-agents-library/

## What the person keeps

`python hatch.py chat` prints where the chat file is and which agents ran in it. Offer that file to the
person when they finish. Any Brainstem, hatched by any AI, can pick the work up from it.

## Safety, in plain words

- Agent files are code. Bring them only from the library catalog or from the person.
- Be careful when three things meet: private data, text from a stranger (a web page, an email), and a way
  to send data out. If all three are in play, stop and ask the person.
- Anything that leaves this place or cannot be undone waits for the person's yes.

## If you can call your own API from code

You may skip the ask and answer steps. `plug.use(brainstem, answer)` makes any function the Brainstem's
model for `/chat` and `/chat/stream`; the top of `plug.py` says what the function receives and returns.
