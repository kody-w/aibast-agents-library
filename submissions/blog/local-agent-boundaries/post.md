<p>
        The brainstem shipped with a feature that felt magical: paste a GitHub repo URL, toggle agents on, and they'd hot-load into your running server. No restart, no file copying. It worked by fetching <code>manifest.json</code> from the repo, downloading individual <code>*_agent.py</code> files, shimming their imports, and injecting them into the running Python process.
      </p>

      <p>
        We removed all of it in v0.1.0. Here's why.
      </p>

      <h3>The complexity cost</h3>
      <p>
        Remote agent loading touched almost every layer of the system. It required URL normalization (handling <code>github.com/</code>, <code>owner/repo</code>, GitHub Pages URLs), manifest fetching (with three fallback strategies), file downloads, <code>sys.path</code> manipulation, <code>sys.modules</code> shimming, auto-pip-install on import failures, persistent config in <code>.repos.json</code>, restore-on-startup logic, and four HTTP endpoints for the UI to manage it all.
      </p>

      <p>
        That's a lot of surface area for a feature whose primary value — making agents available — can be solved by just dropping a <code>.py</code> file into a folder.
      </p>

      <h3>The statelessness argument</h3>
      <p>
        The brainstem is designed to deploy as an Azure Function. Azure Functions are stateless by design — each invocation starts clean. Caching agents in memory and hot-loading from remote repos assumes a long-lived process. That assumption breaks in production.
      </p>

      <p>
        By making agent loading stateless (fresh discovery every call, no cache, no remote state), we made the brainstem behave identically whether it's running locally on Flask or deployed as a serverless function. Same code path everywhere.
      </p>

      <div class="callout">
        <strong>Design principle:</strong> If it works differently in dev vs prod, it's a bug in the architecture, not a feature.
      </div>

      <h3>What stays</h3>
      <p>
        The import shims (<code>_register_shims</code>) still exist. They're valuable for a different reason: agents written for the Azure deployment import <code>utils.azure_file_storage</code>, and the shims redirect those imports to <code>local_storage.py</code> so the same agent code runs locally without modification. That's a portability feature, not a remote-loading feature.
      </p>

      <p>
        The auto-pip-install logic also stays. If a local agent imports <code>beautifulsoup4</code> and it's not installed, the brainstem installs it and retries. That makes onboarding frictionless — drop in an agent, the brainstem figures out the deps.
      </p>

      <h3>The path forward</h3>
      <p>
        Remote agents will likely return, but as a first-class packaging system rather than a runtime hot-loader. Think: <code>brainstem install github.com/org/agents</code> that clones the repo into your local agents folder, resolves dependencies, and you're done. Install-time, not runtime. Explicit, not magic.
      </p>

      <div class="diagram">agents/
├── hello_agent.py            ← local, loads automatically
├── my_custom_agent.py        ← local, loads automatically
├── context_memory_agent.py   ← local, loads automatically
└── experimental/
    └── converter_agent.py    ← excluded from auto-discovery</div>
