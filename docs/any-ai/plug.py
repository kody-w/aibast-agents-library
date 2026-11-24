"""plug.py: let the AI that hatched this Brainstem be its model. No second sign-in.

A Brainstem asks a model in two places: one plain call and one streaming call. `use` swaps both, in
memory, for a function you supply. The Brainstem's own file is not changed, and `use` hands back a
function that puts the original calls back.

    import brainstem, plug
    undo = plug.use(brainstem, answer)        # from now on /chat and /chat/stream ask `answer`

    def answer(messages, tools):
        '''messages: the chat so far, each {"role": "system" | "user" | "assistant" | "tool", "content": ...}
        tools:    the agents on offer this turn, each {"type": "function", "function": {name, description, parameters}},
                  or None when no agent may be called on this step.
        Return ONE assistant message:
          {"role": "assistant", "content": "the words for the person"}
        or, to run agents first:
          {"role": "assistant", "content": None, "tool_calls": [
              {"id": "call_1", "type": "function", "function": {"name": "<agent name>", "arguments": "<json text>"}}]}
        The Brainstem runs those agents and calls you again with their output as "tool" messages.'''

`scripted` below is a stand-in model with no intelligence at all. It exists so the same chat can be
replayed in two bodies and compared byte for byte.
"""
import json

__all__ = ["use", "scripted"]


def _message(raw):
    if isinstance(raw, str):
        raw = {"content": raw}
    if not isinstance(raw, dict):
        raise TypeError("the model plug must return one assistant message (a dict) or plain text")
    msg = {"role": "assistant", "content": raw.get("content")}
    calls = raw.get("tool_calls") or []
    if calls:
        msg["tool_calls"] = []
        for i, c in enumerate(calls, 1):
            fn = c.get("function") or {}
            args = fn.get("arguments", "{}")
            msg["tool_calls"].append({
                "id": str(c.get("id") or f"call_{i}"),
                "type": "function",
                "function": {"name": str(fn.get("name", "")),
                             "arguments": args if isinstance(args, str) else json.dumps(args)},
            })
    elif msg["content"] is None:
        msg["content"] = ""
    return msg


def use(kernel, answer, name="host-ai"):
    """Make `answer` the model for `kernel` (the imported Brainstem module). Returns undo()."""
    kept = (kernel.call_copilot, kernel.call_copilot_stream)

    def call(messages, tools=None):
        msg = _message(answer(messages, tools))
        finish = "tool_calls" if msg.get("tool_calls") else "stop"
        return {"choices": [{"index": 0, "message": msg, "finish_reason": finish}], "model": name}, name

    def stream(messages, tools=None, model=None):
        msg = _message(answer(messages, tools))
        if msg.get("content"):
            yield ("delta", msg["content"])
        yield ("done", {"message": msg, "model": name,
                        "finish_reason": "tool_calls" if msg.get("tool_calls") else "stop"})

    kernel.call_copilot, kernel.call_copilot_stream = call, stream

    def undo():
        kernel.call_copilot, kernel.call_copilot_stream = kept

    return undo


def scripted(messages, tools):
    """A stand-in model for tests. "use <AgentName>" runs that agent with no arguments; an agent's
    output is repeated back whole; anything else gets a fixed line. Same input, same output, always."""
    last = messages[-1] if messages else {}
    if last.get("role") == "tool":
        outs = [str(m.get("content", "")) for m in messages if m.get("role") == "tool"]
        return {"content": "The agent answered:\n" + "\n---\n".join(outs)}
    text = str(last.get("content", ""))
    names = sorted((t["function"]["name"] for t in (tools or [])), key=len, reverse=True)
    for n in names:
        if ("use " + n).lower() in text.lower():
            return {"content": None, "tool_calls": [{"id": "call_1", "type": "function",
                                                     "function": {"name": n, "arguments": "{}"}}]}
    return {"content": f"Stand-in model. You said: {text}"}
