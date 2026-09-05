# Releasing RAPP Brainstem Frontier

RAPP Brainstem Frontier follows Skill Recorder's source-only release pattern:

1. Publish an immutable annotated tag after the staging commit passes.
2. Record the full release commit and installer hashes in the GitHub Release.
3. Do not attach locally assembled Electron applications to the source release.
4. Test the installer against the exact commit from a clean isolated home.

## 1. Prepare and validate

Update `VERSION`, `package.json`, and `package-lock.json` to the same semantic
prerelease version, then run:

```sh
npm ci --no-audit --no-fund
npm run check
npm test
npm run prepare:bootstrap
```

Wait for the repository preflight workflow on the release commit to pass.

`prepare:bootstrap` must run from a clean tracked checkout. It writes a
generated package resource that binds `install.sh`, `install.ps1`, the GitHub
repository, and the full checkout commit. `npm run dist:mac` runs this step
automatically. Release mode accepts only the canonical Microsoft repository.
For explicit fork-only development artifacts, set
`BRAINSTEM_BETA_PACKAGE_MODE=development`; those artifacts receive a distinct
development provenance identity and are not release candidates.

Binary packaging is optional and is not required for a source-only release. If
you intentionally prepare a macOS preview artifact, run `npm run dist:mac` and
review it separately. Do not attach a locally assembled application to the
source-only GitHub Release.

The package gate launches with isolated `HOME`, `USERPROFILE`,
`BRAINSTEM_HOME`, and Frontier state directories. It starts with no target
runtime, substitutes a controlled immutable installer fixture, verifies staged
activation and sanitized logs, then requires the routed Brainstem worker to
pass the compatibility/agent-load gate before the smoke process may exit zero.
Packaged update UX must continue directing users to a new signed package; the
source-checkout updater is not a binary updater.
The gate also executes the Copilot platform binary from
`app.asar.unpacked`; a logical ASAR path is not acceptable evidence.

Windows publication is x64 NSIS only. The installer must remain per-user,
non-elevating, launch after install, and preserve both Electron profile data and
the external shared `BRAINSTEM_HOME` during uninstall. Windows CI must exercise
a clean standard-user first launch and wait for the compatible Brainstem
readiness gate before signing or publishing. ARM64 source bootstrap is expected
to fail with the explicit x64 guidance until one complete architecture stack is
supported.

## 2. Create the immutable tag

Use a component-qualified tag because this repository ships more than one
versioned product:

```sh
version="0.1.0-beta.1"
release_commit="<full-40-character-commit>"
tag="brainstem-beta-v$version"
git tag -a "$tag" "$release_commit" -m "RAPP Brainstem Frontier v$version"
git push fork "$tag"
```

Never move or reuse a published tag. Publish a new prerelease version instead.

## 3. Calculate installer hashes

Calculate hashes from the exact release commit's Git blobs:

```sh
node -e 'const {execFileSync}=require("node:child_process");const {createHash}=require("node:crypto");const commit=process.argv[1];if(!/^[0-9a-f]{40}$/i.test(commit))throw new Error("full release commit SHA required");for(const file of ["beta/install.cmd","beta/install.sh"]){const data=execFileSync("git",["cat-file","blob",commit+":"+file]);console.log(createHash("sha256").update(data).digest("hex")+"  "+file)}' "$release_commit"
```

## 4. Publish the source-only prerelease

Release notes must include:

- the version and full release commit;
- SHA-256 values for `beta/install.cmd` and `beta/install.sh`;
- user-visible changes and known beta limitations;
- commit-pinned Windows and macOS/Linux install commands;
- a clear statement that the release is source-only.

Publish after preparing a temporary notes file outside the repository:

```sh
gh release create "$tag" \
  --repo kody-w/aibast-agents-library \
  --verify-tag \
  --prerelease \
  --title "RAPP Brainstem Frontier v$version" \
  --notes-file "<release-notes-file>"
```

## 5. Test the published commit

Use a clean temporary `HOME` and disable launch during installation:

```sh
repo="kody-w/aibast-agents-library"
commit="<full-40-character-commit>"
curl -fsSL "https://raw.githubusercontent.com/$repo/$commit/beta/install.sh" \
  | HOME="<isolated-home>" \
    BRAINSTEM_BETA_HOME="<isolated-home>/.brainstem/beta-launcher" \
    BRAINSTEM_BETA_REPO_URL="https://github.com/$repo.git" \
    BRAINSTEM_BETA_COMMIT="$commit" \
    BRAINSTEM_BETA_NO_LAUNCH=1 bash
```

Confirm the launcher checkout and the shared Brainstem checkout both resolve to
the release commit, then launch the installed Electron application and verify
the Brainstem health endpoint.
