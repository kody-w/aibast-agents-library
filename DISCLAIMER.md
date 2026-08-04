# Disclaimer

The AIBAST Agents Library is a **public preview** of frontier tooling for
accelerating AI agent development on the Microsoft AI stack — single-file
agents, an in-browser CPython runtime, one-command installers, and
AI-generated code paths. It moves fast by design.
Use it **at your own risk**.

**Provided "AS IS."** Everything in this repository is licensed under the
MIT License and provided **"AS IS", without warranty of any kind**, express
or implied. There is no SLA, no support commitment, and no guarantee of
fitness for any particular purpose. Third-party materials mirrored under
`rapp/` carry their own upstream licenses — see
[`rapp/THIRD-PARTY-NOTICES.md`](rapp/THIRD-PARTY-NOTICES.md).

**AI outputs require human review.** Agents in this library generate
content, execute code, and call external services. Review every agent
before you install it, review every AI-generated output before it reaches
production or a customer, and validate results independently. An agent
file is plain Python — read it; that's the point of the single-file design.

**Bring your own credentials, keep them out of the repo.** Configuration
flows through environment variables (`requires_env` in each agent's
manifest). Never commit secrets, keys, tokens, or customer data — to this
repository or any fork.

**Community content is not certified.** Publisher submissions and
aggregated skills are community contributions. Ratings, download tallies,
and quality-gate signals are community telemetry, not an endorsement or
certification by Microsoft. Aggregated entries link to their origin; review
the origin before use.

**Local execution, local data — with one disclosed exception.** The brainstem
runs on your machine and the vBrainstem runs entirely in your browser. Your
conversations, agents, and memories stay on your device, and nothing you run
is sent to this repository.

The exception is browser sign-in: github.com sends no CORS headers for the
device-code endpoints, so the in-browser runtime brokers that exchange through
a CORS proxy, and **falls back to the same proxy — passing your GitHub token —
if the direct call to GitHub is unreachable or rejected.** The default proxy is
operated by the upstream RAPP maintainer, not by Microsoft. Set
`VB_AUTH_WORKER` to a proxy you control, or use the on-device brainstem, to
keep the token inside your own trust boundary.

**Azure costs are yours.** The Tier-2 deployment templates provision billable
Azure resources in *your* subscription — Azure OpenAI (S0), a Function App,
Storage, and Application Insights. Cost depends on region and usage; estimate
with the [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/)
before deploying, and delete the resource group when you are done. Any dollar
figures in this repository are illustrative, not quotes.

**Installers change your machine.** The one-liner installers may install
Python, Git, and the GitHub CLI via your platform package manager (winget,
Homebrew, apt/dnf — including adding a package source on Linux), create a
virtual environment under your home directory, and add a line to your shell
profile and PATH. Read the script before piping it to a shell.

**Telemetry.** The public metrics dashboard shows anonymous aggregates from
public APIs only. The optional internal event contract never carries
prompts, responses, customer data, document contents, or individual user
identity — see [`docs/TELEMETRY.md`](docs/TELEMETRY.md).

**Not production-hardened by default.** Preview means preview: pin
versions, test in your own environment, and treat every deployment as your
own. Security reports: see [`SECURITY.md`](SECURITY.md).
