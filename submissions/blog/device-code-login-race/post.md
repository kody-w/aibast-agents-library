<p>
        We shipped an account switcher in v0.5.4. It worked great — unless you
        first signed in with a GitHub account that didn't have Copilot access.
        When you switched to the right account, the UI stayed stuck on
        "Waiting for authorization..." forever. The fix was a six-line architectural
        change, but the bug exposed a pattern worth documenting.
      </p>

      <h3>The setup: two callers, one resource</h3>
      <p>
        The brainstem's device code login flow has two consumers. A <strong>background
        thread</strong> (<code>_bg_poll_loop</code>) polls GitHub so the token gets
        captured even if the browser disconnects. And the <strong>client</strong>
        polls <code>POST /login/poll</code> every 5 seconds so the UI updates when
        auth completes.
      </p>
      <p>
        Both callers invoked the same function: <code>poll_device_code()</code>.
        That function, on success, saves the token and clears the
        <code>_pending_login</code> state. Whoever gets there first wins the token.
        The loser finds <code>_pending_login</code> empty, returns <code>None</code>,
        and tells the client <code>{"status": "pending"}</code>. Forever.
      </p>

      <div class="diagram">Background thread          Client poll (/login/poll)
       │                              │
       ├── poll_device_code() ────┐   │
       │   ✓ got token            │   │
       │   ✓ cleared state ───────┤   │
       │                          │   ├── poll_device_code()
       │                          │   │   ✗ state empty → None
       │                          │   │   returns {"pending"}
       │                          │   │
       │                          │   ├── ...forever
       ▼                          ▼   ▼</div>

      <h3>Why it only showed up on account switch</h3>
      <p>
        On a normal first login, the race exists but is harmless — either caller
        reports success and the UI dismisses. On an account switch, the first
        (wrong) account goes through the full device code flow successfully at
        the GitHub level. GitHub grants a token. But the Copilot token exchange
        fails because the account has no Copilot license. The background thread
        catches this error silently, and the client is left polling an empty
        <code>_pending_login</code> dict.
      </p>
      <p>
        The second login attempt (correct account) hits the same race. If the
        background thread wins — which it reliably does because it's already
        polling at the right interval — the client never sees the result.
      </p>

      <h3>The fix: single-writer pattern</h3>
      <p>
        The solution is to stop having two callers compete for the same resource.
        We introduced a shared <code>_login_result</code> dict. The background
        thread is now the <strong>sole caller</strong> of
        <code>poll_device_code()</code>. When it gets a result — success or
        failure — it writes to <code>_login_result</code>.
      </p>
      <p>
        The <code>/login/poll</code> endpoint no longer calls
        <code>poll_device_code()</code> at all. It just reads
        <code>_login_result</code>. Python's GIL makes dict assignment atomic,
        so no locks are needed.
      </p>

<pre>_login_result = {}  # Written by bg thread only

def _bg_poll_loop():
    token = poll_device_code()
    if token:
        try:
            get_copilot_token()
            _login_result = {"status": "ok", ...}
        except NO_COPILOT_ACCESS:
            _login_result = {"status": "error", ...}

@app.route("/login/poll")
def login_poll():
    if _login_result:          # bg thread wrote something
        return jsonify(_login_result)
    if not _pending_login:     # no flow in progress
        return jsonify({"status": "expired"})
    return jsonify({"status": "pending"})  # still waiting</pre>

      <div class="callout">
        <strong>Pattern:</strong> When a background thread and a request handler
        both need the result of the same operation, don't let them race to call
        it. Have one writer and N readers. The writer owns the function call; the
        readers check a shared result.
      </div>

      <h3>Bonus fixes</h3>
      <ul>
        <li><strong>NO_COPILOT_ACCESS surfaces to the UI.</strong> Previously
        swallowed — the user saw "Authenticated!" then got errors on first chat.
        Now the login overlay shows "username doesn't have Copilot access" with
        "Switch account" and "Sign up for Copilot" links.</li>
        <li><strong>Client poll has a timeout.</strong> 180 attempts at 5-second
        intervals (15 minutes, matching GitHub's device code expiry). No more
        infinite loops.</li>
        <li><strong>Stale Copilot cache cleared on new flow.</strong> Starting a
        fresh device code now wipes <code>.copilot_session</code> and the
        in-memory cache, so a previous account's session can't bleed through.</li>
      </ul>

      <h3>The lesson</h3>
      <p>
        Background threads that "help" by doing the same work as a request
        handler create races that only show up under specific timing. The thread
        was added to capture tokens when the browser disconnects — a real need.
        But it should have been the only writer from day one, with the HTTP
        endpoint as a passive reader. Adding a background optimization to an
        existing request path requires rethinking ownership, not just adding
        another caller.
      </p>
