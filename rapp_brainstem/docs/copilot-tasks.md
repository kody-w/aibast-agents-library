# Private, transport-neutral Copilot tasks

`agents/copilot_cli_agent.py` has two separate interfaces:

* The existing **local** `CopilotCLIAgent.perform(dispatch/result/list)` interface
  remains compatible, including its legacy autonomous permission policy. Never
  expose it directly to a remote channel.
* The **private portal adapter** below does not use that interface. It is an
  import-safe, standard-library Python API and JSON CLI. It does not import
  Brainstem, discover agents, start a channel reader, send messages, or read a
  message database or global FlightRecorder history.

The adapter reuses `~/.brainstem/copilot_jobs`. Old jobs are left unchanged and are
not remotely enumerable: without a recorded owner/thread binding, ownership
cannot safely be inferred.
Catalog scans may inspect bounded current-user regular legacy JSON to identify
its schema, including old mode-0644 metadata. Such nonportal records are skipped
without rewriting them. Actual portal metadata must still be private mode-0600;
a record is never treated as legacy merely to bypass that validation.

## Authority and deployment

The caller must be an existing, trusted local transport handler. It must verify
the incoming sender and canonical chat **before** constructing `actor`. Never
let a model supply an actor, policy configuration, approval token, executable,
destination, or arbitrary CLI flags. This adapter is not an authentication
boundary against other processes with the same operating-system account.

Install only this extension file and its existing `basic_agent.py` dependency in
an approved source location. Do not call `/health`, `/chat`, or `/api/agent` to
invoke it: discovery can activate unrelated installed channel agents. Do not
start another iMessage watcher or reactivate a legacy service.

The private configuration is supplied by absolute path, must be a regular file
owned by the current user, and must have mode `0600`. Example with **synthetic**
identities (replace locally; do not commit real identifiers):

```json
{
  "version": 1,
  "jobs_dir": "/absolute/private/home/.brainstem/copilot_jobs",
  "staging_root": "/absolute/private/inbound-staging",
  "copilot_path": "/absolute/path/to/the/installed/copilot",
  "authorized": [
    {"sender": "+15550100101", "chat": "synthetic-canonical-chat"}
  ],
  "profiles": {
    "read-only": {"available_tools": ["view", "glob", "rg"]},
    "workspace-write": {
      "available_tools": ["view", "glob", "rg", "apply_patch"],
      "allow_tools": ["write"]
    }
  },
  "approval_ttl_seconds": 600,
  "max_runtime_seconds": 900,
  "max_attachment_bytes": 33554432,
  "max_total_attachment_bytes": 67108864,
  "max_artifact_bytes": 33554432,
  "max_output_bytes": 8388608
}
```

Phone handles normalize to E.164, ignoring spaces, parentheses and hyphens.
Email handles are case-folded. Chat identifiers are trimmed but otherwise exact
and case-sensitive. Use the transport's canonical identifier consistently;
never infer an owner from a display name, text prefix, or a different chat.

Profiles explicitly list available tools. An empty list permits no tools.
Additional optional fields are `allow_tools`, `deny_tools`, `add_dirs`, and
`allow_urls`. Only explicitly configured `shell(command)`/`write(path)` grants
and explicit HTTPS URLs are supported. Shell is denied when there is no explicit
shell grant; writes and URL access likewise default to denied. Unknown fields,
wildcard tool availability, and blanket shell grants are rejected.

Every job runs in its own private `workspace/`. Additional absolute directories
are a deliberate local policy choice and are included in approval binding.
They may not expose task state, inbound staging, or the configuration. Copilot's
`--add-dir` also trusts that directory's extension configuration; do not add
untrusted repositories. CLI path/tool permissions are **not an OS sandbox**,
especially when a local operator explicitly grants shell commands.

The worker pins `gpt-6-astra`, disables remote export, built-in MCP servers,
custom instructions, shell startup files and automatic updates, and supplies
explicit `--available-tools`, `--allow-tool`, `--deny-tool`, and path flags.
It never uses `--allow-all`, `--allow-all-tools`, `--allow-all-paths`,
`--allow-all-urls`, or `--yolo` through the portal path.
The trusted task boundary also renders the effective tool grants/denials,
working directory, added directories, and allowed URLs, derived from those
same enforced arguments. It excludes account configuration, actor data,
approval tokens and other job/configuration fields. Keep permission rules and
URL grants themselves nonsecret. This summary is guidance, not additional
authority: the CLI remains the enforcement boundary.

For shell tasks the worker is told to use only explicitly named approved
programs, prefer separate permitted invocations, and avoid unapproved preflight
or cleanup commands. It should leave intermediate files rather than request
broader permissions. For example, grants for `say`, `ffmpeg`, and `ffprobe` do
not grant `test` or `rm`; rejection of an unnecessary compound step must not be
interpreted as a blanket loss of the approved shell capabilities.

Each job has a fresh `COPILOT_HOME` inside its existing job directory, preventing
inherited permissive settings, plugins, hooks, and session state. Two explicitly
selected authentication modes preserve that isolation:

* Default `{"auth":{"mode":"environment"}}`: supported GitHub authentication
  environment variables (`COPILOT_GITHUB_TOKEN`, `GH_TOKEN`, `GITHUB_TOKEN`)
  may be provisioned by the trusted launch context. Values are never written
  by the adapter or returned in status. A selected classic `ghp_` PAT is rejected
  as `auth_unsupported` before invoking Copilot; classic PATs are not supported.
* To reuse the operator's **existing Copilot OAuth/keychain account**, locally
  pin its **nonsecret** account reference in the private portal configuration:

  ```json
  {
    "auth_account": {
      "host": "https://github.com",
      "login": "synthetic-account"
    }
  }
  ```

  The operator supplies the already-known host/login locally, never from an
  incoming message or model. Only these two strings are accepted; extra fields
  such as tokens or permissions are rejected. No main Copilot configuration,
  settings, or external account file is read. The worker writes only the pinned
  reference into a fresh private `copilot-state/config.json`, with exactly
  these two top-level fields:

  ```json
  {
    "lastLoggedInUser": {"host":"https://github.com","login":"synthetic-account"},
    "loggedInUsers": [{"host":"https://github.com","login":"synthetic-account"}]
  }
  ```

  Copilot itself resolves the OAuth token from its system credential store
  using host/login. The adapter never invokes a keychain token-export command,
  reads a keychain token, or reads/copies the parent configuration, `authTokens`,
  `copilotTokens`, permissions, settings, hooks, or plugins. In this mode inherited
  GitHub token/host overrides are removed from the worker environment so an
  unrelated classic `gh` PAT cannot take precedence. The chosen account is
  hash-bound into task approval; changing the local pin requires a new
  submission and fresh approval. Parent authentication is never modified.

  The earlier experimental `auth.source_config` option is rejected. Replace
  that block with `auth_account`; do not configure both. This avoids any general
  configuration read or copy, even when its account references are nonsecret.

This metadata selection is verified against the installed Copilot CLI 1.0.87
schema (`UserAuthInfo` keeps the token in the runtime secret store, keyed by
host/login). That CLI rejects `--user`; this adapter does not invent that flag.
Unsupported metadata fails closed. Missing/inaccessible keychain credentials
remain an explicit CLI authentication failure—never a reason to copy secret
values, perform a new login automatically, or widen permissions. An installation
using plaintext credential fallback cannot use this metadata-only path.

If the CLI cannot authenticate or rejects a permission, its nonzero exit is a
durable failure, not permission to retry with broader access. Live
authentication/inference must be checked separately during authorized
integration; fake-worker tests prove neither.

## JSON/CLI contract

From an approved source directory:

```bash
python3 agents/copilot_cli_agent.py --portal-config /absolute/private/portal.json
```

Write exactly one JSON object on stdin and close stdin. One JSON object is
returned on stdout; exit `0` means the adapter operation succeeded, and exit `1`
means `{"ok":false,"error":{"code":"...","message":"..."}}`. A successful `result`
operation can describe a **failed task**: inspect `job.status` and
`result.exit_code`, not only the operation's `ok`.

The equivalent import-safe API is:

```python
from agents.copilot_cli_agent import PortalTaskStore

store = PortalTaskStore("/absolute/private/portal.json")
reply = store.handle(request_object)
```

Every request has:

```json
{"op":"list","actor":{"sender":"+15550100101","chat":"synthetic-canonical-chat"}}
```

Operations:

| Operation | Additional fields | Result |
|---|---|---|
| `submit` | `request_id`, `prompt`, `profile`; optional `attachments`, `artifact_paths` | `job`, one-use `approval`, `duplicate` |
| `approve` | `job_id`, `approval_token` | queued `job`; never starts a second worker for a used approval |
| `list` | optional `limit` (1–100), `before` (previous job ID) | this actor/thread's `jobs`, `next_before` |
| `status` | `job_id`; optional `stdout_offset`, `stderr_offset`, `event_offset`, `limit` (4–65536 bytes) | `job`, incremental `stdout`, `stderr`, `events`, cursors, `worker_active` |
| `result` | same as `status` | additionally terminal `result`, or `null` while pending/running |
| `cancel` | `job_id` | cancelled/cancelling `job`; idempotent once terminal |
| `recover` | optional `job_id` | reconcile this thread's job(s); never rerun a task or signal a stored PID |

`request_id` is a transport event/idempotency identifier, not a task instruction.
It is preserved in the private metadata and returned in `job.request_id` for
ingress reconciliation. `job.job_id` and `job.status` are stable field names.
Concurrent identical submissions return the same job and still-live approval.
Reusing it for different content is an explicit `idempotency_conflict`.
`submit` is always inert. Its approval expires in 1–3600 seconds, according to
the finite local configuration, and is bound to job, owner/thread, exact prompt,
attachment content hashes, output declarations, and permission policy.
Wrong-thread, changed, expired, or replayed approval cannot start execution.
There is no `approved: true` shortcut.

Keep the approval token in the trusted transport's private pending-approval
record, outside model context. Map a human's explicit confirmation to the
corresponding token and exact job; a numbered reply must be bound to the correct
pending list in the same verified thread. Status and list never return tokens.

### Attachments and artifacts

An attachment is a staged file reference, not inline/base64 content:

```json
{
  "path": "/absolute/private/inbound-staging/synthetic-note.txt",
  "name": "synthetic-note.txt",
  "mime": "text/plain",
  "size_bytes": 24,
  "sha256": "<optional lowercase SHA-256>"
}
```

Omit size/hash when unavailable; otherwise they must match the actual file.
The adapter snapshots bounded regular files into the job's `inputs/`, computes
hashes, and verifies them again before approval/execution. Maximum 16 inputs.
Missing/incomplete files are errors for the transport to stage/retry before
submission. Symlinks (including parent components), traversal, hardlinks,
executable modes/content, and active executable/installer/link types are refused.
No media conversion, automatic extraction, or interpretation occurs.
Photo, audio and video **file transport is not content understanding**. Audio is
not automatically transcribed; video is not automatically decoded, summarized,
or streamed continuously. Any transcription, frame extraction, or media analysis
needs an actually available tool, an explicitly approved capability profile,
and a separate verified result. Do not advertise those abilities merely because
an attachment was accepted.

`artifact_paths` is an explicit list of at most 16 relative paths inside the
job's `workspace/`, included in the approval. For example `["report.txt"]`.
It is also returned as `job.artifact_paths` for the transport's approval preview.
Only these files can be emitted. The worker never mines generated text for
paths. Outputs undergo the same regular-file, confinement and size checks,
then are copied to private `artifacts/` using unique job-prefixed basenames.
Returned records include stable ID, path, name, byte count and SHA-256.
They also include `mime` (filename-derived, or `application/octet-stream`);
this is descriptive metadata, not a reason to skip transport validation.
One missing/unsafe requested artifact makes the task fail explicitly; partial
artifact batches are not published.

The transport must verify the record/hash before sending, bind the send to the
original approved chat, and maintain its own existing durable delivery/outbox
state. Adapter artifact existence is not proof of native submission, delivered
status, or actual receipt/opening on a phone.
Native transports can report an exception after accepting an attachment that
subsequently delivers. Reconcile after exceptions as well as successful calls,
using the authorized chat, unique artifact basename/part identity, and bounded
post-send window. A caption's GUID is not the attachment's delivery receipt.
Keep unresolved sends `unknown`; never blindly resend. Native media processing
may change byte counts or encoding, so the manifest hash attests the emitted
pre-send file, not byte-identical delivery of the native attachment.

### Explicit per-task output requests

The existing transport, not this runtime, owns command parsing. The minimal
command-room convention is:

```text
RAPP <task>                         → artifact_paths: []
RAPP file report.txt | <task>       → artifact_paths: ["report.txt"]
```

The file command accepts one explicit safe basename from the user, not a path
invented by a model. The transport checks its bounded basename and passive
media/document extension allowlist, rejects absolute paths, traversal,
executables, destinations and CLI/profile flags, and shows the filename in
the task's normal one-use approval preview. There is no fixed mandatory report
file for ordinary text tasks.

The permission profile stays locally configured: declaring a filename does not
grant new tools or paths. The worker is explicitly instructed to create every
declared file at that exact name inside its current isolated workspace. A missing
capability must be reported for a new, explicitly approved task under an already
configured suitable profile; no automatic escalation or invented output path
is allowed.

Screenshots and short clips can be returned as attachments when explicitly
requested, approved, and produced by actually available permitted tools.
iMessage is not a continuous interactive desktop livestream, and accepting an
output filename does not make a capture or media-generation tool available.

### Progress, recovery, and cancellation

States are `pending_approval`, `queued`, `running`, `cancelling`, then
`succeeded`, `failed`, `cancelled`, `expired`, or `interrupted`.

Logs remain `out.log` and `stderr.log`; supervisor diagnostics are `worker.log`.
`meta.json` and `result.json` are private, atomically replaced and fsynced.
Process-safe `flock` locks serialize mutations. A held `.worker.lock`, not PID
existence, establishes worker ownership. Each JSON invocation can exit while
the separately supervised worker continues.
New jobs are fully initialized under a private `.initializing-<job_id>` name
before atomic directory publication. Catalogs ignore that uncommitted namespace.
A killed initializer can leave a private uncommitted directory for local
inspection/cleanup, but cannot expose a half-created task or poison other
history. Older incomplete or unreadable records are handled individually during
list/recovery rather than making every thread's history unavailable.

Progress cursors count **bytes**; event cursors count sequence numbers. Stable
event IDs are `<job_id>:<sequence>`. Feed these to the transport's existing
outbox deduplication, persist its cursors, and do not create another responder.
The final response is bounded to 65,536 characters with `response_truncated`;
full bounded/retained logs can be paged. CLI output exceeding its configured
bound fails the task; retained diagnostic files may exceed the threshold by
the final in-flight write before the worker stops it.

Cancellation is a durable request. Only the dedicated supervising worker
signals its owned CLI child process group; remote operations never kill persisted PIDs.
The worker retains the leader's identity using `waitid(..., WNOWAIT)` and the
default `SIGCHLD` policy. Some macOS Python builds (including Homebrew 3.12)
omit the Python `os.waitid` wrapper despite the OS supporting it. On 64-bit
Darwin, the adapter then binds the public libSystem `waitid` API using the
documented `siginfo_t` layout and the same non-reaping flags. No SDK installation,
helper daemon, PID-existence approximation, or early reaping is used. Unsupported
ABIs fail closed before launching the CLI.
It does not reap the leader when TERM makes it exit:
after a bounded grace period it still escalates KILL to TERM-ignoring members
of the same owned group, and only then reaps the leader. A normally exited CLI
also has leftover owned-group members stopped before committing its result.
After reaping, the worker only probes for group disappearance; it never sends
another destructive signal to a possibly reused group.

If cleanup cannot be established, the task is an explicit failed
`process_cleanup_incomplete`, `execution_may_continue` is true, and no artifact
batch is published. Neither cancellation nor confirmed group cleanup rolls
back earlier effects or constitutes a full-machine sandbox. A missing worker
is reconciled from a committed result or marked `interrupted`, with unknown
exit code and `execution_may_continue` when appropriate. No unsafe PID-based
cleanup or automatic execution replay is attempted. A queued launch that loses
its supervisor is reconciled after a 10-second startup allowance. Run `recover`
on watcher restart and periodically while awaiting completions.

The runtime has no implicit permission profile. Configure the existing
transport's local default profile to a key in `profiles` (for example
`read-only`), and configure its default `artifact_paths` list locally (`[]` is
valid). Neither value should be selected by arbitrary remote message fields.
`staging_root` is an independent absolute directory chosen by the transport,
not a requirement to stage inside the job store. Task history remains readable
if that staging directory or the Copilot executable is later unavailable.

Useful error codes are:

* `forbidden`: the verified sender/chat pair is not configured.
* `not_found`: unknown task or a task belonging to another configured thread.
* `approval_required`, `approval_expired`, `approval_used`, `approval_changed`:
  missing/wrong token, finite expiry, consumed token, or changed bound inputs.
* `policy_denied`: an unconfigured permission profile.
* `auth_selector_invalid`, `auth_unsupported`: invalid locally pinned account
  metadata, or an unsupported classic PAT.
* `worker_launch_failed`: the supervisor could not be launched (operation error).
* `worker_unavailable`: the Copilot executable is unavailable (terminal result).
* `worker_lost`: ownership disappeared; terminal `interrupted`, never replayed.
* `process_cleanup_incomplete`: owned-group cleanup is unconfirmed; execution
  may continue and requires local inspection rather than an automatic retry.
* `cli_failed`, `timeout`, `output_limit`, `empty_result`: explicit CLI outcomes.
* `artifact_missing`: a declared file was not created.
* `artifact_rejected`: a declared file failed confinement/type/size validation.

Operation errors have `{ok:false,error:{code,message}}`. Terminal task errors
appear in `job.error` and `result.error`, even when querying the result itself
returns `ok:true`.

## Hermetic validation

From `rapp_brainstem/`, use an existing environment with `pytest` installed:

```bash
mkdir -p .test-artifacts
PYTHONDONTWRITEBYTECODE=1 TMPDIR="$PWD/.test-artifacts" \
  python3 -m pytest tests/test_copilot_tasks.py -q -p no:cacheprovider \
  --basetemp=.test-artifacts/pytest
```

The tests launch actual worker subprocesses and harmless fake CLI executables,
using only synthetic sender identities, prompts, and project-local files.
They do not invoke Copilot inference, a Brainstem endpoint, native messaging,
or any private history. Real transport receipt remains a separate, explicitly
authorized integration check.
