<p>
        The brainstem installs via a one-liner: <code>curl ... | bash</code>. That same one-liner should also handle upgrades. The question is: how does the installer know whether to upgrade?
      </p>

      <h3>The approach</h3>
      <p>
        A single file — <code>rapp_brainstem/VERSION</code> — contains the semver string. That's it. No package registry, no GitHub releases API, no <code>git describe</code> parsing.
      </p>

<pre>$ cat rapp_brainstem/VERSION
0.1.0</pre>

      <p>
        The installer does two things:
      </p>
      <ul>
        <li>Reads the local <code>VERSION</code> file from <code>~/.brainstem/src/rapp_brainstem/VERSION</code></li>
        <li>Fetches the remote <code>VERSION</code> from the raw GitHub URL</li>
      </ul>
      <p>
        If they match, print "Already up to date" and exit. If remote is newer, proceed with the full install flow (git pull, pip install, CLI wrapper update). The comparison is a simple semver walk — split on dots, compare integers left to right.
      </p>

      <h3>Why not git-based detection?</h3>
      <p>
        We could compare commit SHAs or use <code>git fetch</code> + <code>git rev-list</code> to detect ahead/behind. But the installer runs <em>before</em> cloning on a fresh install. We need a mechanism that works with a single HTTP request against a raw file URL, even when there's no local git repo yet.
      </p>

      <h3>Why not GitHub Releases API?</h3>
      <p>
        The GitHub API requires authentication for higher rate limits and adds a JSON parsing dependency. A raw file on GitHub Pages is cacheable, fast, and works with a bare <code>curl</code>. The VERSION file is also readable by Python (<code>brainstem.py</code> reads it at startup), the shell installers, and humans — one file serves every consumer.
      </p>

      <div class="callout">
        <strong>Bump process:</strong> Edit <code>rapp_brainstem/VERSION</code>, commit, push. The next time any user runs the one-liner, they get the update. That's the whole release process.
      </div>

      <h3>Exposed in the API</h3>
      <p>
        The version is available at <code>GET /version</code> and included in the <code>GET /health</code> response. The startup banner prints it too. Everything reads from the same <code>VERSION</code> file — there's exactly one place to update.
      </p>

<pre>$ curl -s localhost:7071/health | python3 -m json.tool
{
    "status": "ok",
    "version": "0.1.0",
    "model": "gpt-4o",
    "agents": ["HelloAgent", "ContextMemoryAgent"],
    "copilot": "✓",
    ...
}</pre>
