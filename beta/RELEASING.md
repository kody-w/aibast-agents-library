# Releasing RAPP Brainstem Frontier

Frontier binary releases are built only by
`.github/workflows/frontier-binaries.yml`. The workflow builds on native
platform runners, signs and notarizes in protected jobs, gates the final
installer bytes, attaches them to one existing draft `brainstem-beta-v*`
release, verifies the uploaded bytes, and only then publishes the release.
With GitHub immutable releases enabled, publication locks both the tag and the
assets.

The workflow never creates a release, creates a tag, moves a tag, or replaces
an existing asset. It also refuses to publish binaries unless a hashed and
Sigstore-attested binary manifest allowlists each exact filename, OS,
architecture, SHA-256, platform signing identity, runtime compatibility, and
passing package-gate report. The exact same manifest bytes must appear in the
release body inside the single `rapp-frontier-release-manifest` fence expected
by the Download Center.

> **Current publication blocker:** `ffmpeg-static` resolves an ARM64 FFmpeg 6.0
> binary built with `--enable-nonfree`, and FFprobe resolves a different
> upstream version. FFmpeg documents that nonfree combinations are not
> redistributable. `build/native-media-policy.json` therefore has
> `publication_enabled: false`, and release-mode CI intentionally fails before
> signing or uploading binaries. This pipeline is not release-ready until a
> redistributable checksum-pinned native media matrix is approved.
>
> The atomic bootstrap staging, rollback, cross-process lock, log-redaction,
> and isolated userData contracts now have unit, process, concurrent first-run,
> and native package-gate coverage. `build/package-bootstrap-policy.json` is
> enabled and no longer blocks publication. `build/windows-signing-policy.json`
> still blocks the deprecated electron-builder v26 Azure signing backend. The
> native-media and Windows-signing policies must remain closed until their
> recorded blockers are resolved.

## Supported binary matrix

| Platform | Runner | Asset | Release trust |
| --- | --- | --- | --- |
| macOS Intel | `macos-26-intel` | `RAPP-Brainstem-Frontier-<version>-macos-x64.dmg` | Developer ID, hardened runtime, app + DMG notarization and stapling |
| macOS Apple silicon | `macos-26` | `RAPP-Brainstem-Frontier-<version>-macos-arm64.dmg` | Developer ID, hardened runtime, app + DMG notarization and stapling |
| Windows | `windows-2025` | `RAPP-Brainstem-Frontier-<version>-windows-x64-setup.exe` | Azure Artifact Signing with RFC 3161 timestamping |

The two macOS artifacts are intentionally thin native DMGs. A universal DMG is
not allowed until every embedded executable and native addon has normalized
ARM64 and x64 slices with identical approved provenance.

Windows ARM64 is intentionally not built or advertised. Add it only after the
Electron executable, every `.node`/`.dll`, the Copilot runtime, `ffmpeg`, and
`ffprobe` are all available as ARM64 and the package gate proves their
architecture. A Windows ARM64 runner or an ARM64 Electron target alone is not
enough.

## Native media redistribution gate

`scripts/native-media-gate.mjs` evaluates
`build/native-media-policy.json` twice:

1. release context must show a complete approved macOS ARM64, macOS x64, and
   Windows x64 FFmpeg/FFprobe matrix before protected signing jobs can start;
2. each native package gate hashes and executes its installed FFmpeg/FFprobe
   bytes, rejects `--enable-nonfree`, requires the normalized upstream version,
   and matches the target-specific approval.

Every approval requires a SHA-256, HTTPS source URL, upstream version, reviewed
license, and `redistributable: true`. Missing provenance fails closed. The
current policy deliberately contains no approvals.

Do not enable publication merely by flipping the boolean. Replace or omit the
media binaries, review the license obligations, update
`THIRD-PARTY-NOTICES.md`, and add all target checksums and provenance in one
reviewed change.

Pull requests and ordinary manual dispatches build native, clearly named
`*-unsigned.dmg` and `*-unsigned.exe` Actions artifacts. They are retained for
14 days, include `UNSIGNED-NOT-FOR-DISTRIBUTION.txt` plus a machine-readable
`*.gate.json`, and are never uploaded to a GitHub Release.

## Packaged bootstrap authority and fixture gate

`scripts/prepare-package-bootstrap.mjs` copies the exact committed root
Brainstem `install.sh` and `install.ps1` into `build/generated/bootstrap`
together with `provenance.json`. The provenance binds both installer hashes,
the full source commit, repository URL, source ref, requested packaging mode,
and package identity. Dirty tracked installer or beta sources fail packaging.

Release mode accepts only:

- source authority `microsoft/aibast-agents-library`;
- repository URL
  `https://github.com/microsoft/aibast-agents-library.git`;
- application ID `com.microsoft.aibast.rapp-brainstem-beta`; and
- product name `RAPP Brainstem Frontier`.

A noncanonical authority is allowed only in explicit `staging` or
`development` mode with a distinct application ID and product name. It cannot
silently inherit Microsoft package identity.

Fork workflows must set non-production repository variables
`FRONTIER_STAGING_APP_ID` and `FRONTIER_STAGING_PRODUCT_NAME`. Missing or
Microsoft production values fail instead of producing a mislabeled package.

The unsigned macOS verification gate installs the real DMG into an isolated
Applications directory, starts with no `BRAINSTEM_HOME`, and runs the canonical
first-run/concurrent smoke suite against a controlled immutable fixture. That
suite exercises the actual packaged provisioner, atomic stage activation,
rollback-safe target handling, cross-process lock, credential-canary
redaction, ready-runtime reuse, two concurrent homes/backends, requested versus
actual `app.getPath("userData")`, backend-failure exit, physical
`app.asar.unpacked` Copilot startup, FFmpeg, and FFprobe. No check is optional
or silently skipped.

That local fixture is development evidence only. A sealed signed artifact gate
must not reuse it. Release-mode gates instead run the bundled bootstrap against
the canonical GitHub repository, exact `brainstem-beta-v*` tag, exact
40-character release commit, and commit-pinned runtime version URL, then verify
the installed checkout resolves to that same commit. The signed artifact is
not rewritten with the development fixture: its standard-user first launch
executes the unmodified, hashed bootstrap resource and must reach real
Brainstem readiness before the package gate can pass.

## One-time repository configuration

### GitHub release protection

1. Enable **immutable releases** in repository settings.
2. Create a GitHub environment named `frontier-binary-release`.
3. Create a separate GitHub environment named `windows-production`.
4. Restrict both environments to tags matching `brainstem-beta-v*`.
5. Add required reviewers and prevent self-review where repository policy
   permits it.

The release workflow requires an existing draft prerelease. After publishing,
it verifies that the release API reports `"immutable": true`; if not, it
immediately attempts to return the release to draft and fails. Draft-first
publication follows GitHub's immutable-release guidance: create draft, attach
every asset, then publish.

### Apple secrets

Store these as secrets on the `frontier-binary-release` environment:

| Secret | Exact value |
| --- | --- |
| `MACOS_CERTIFICATE_P12_BASE64` | Base64 of a PKCS#12 containing the **Developer ID Application** certificate and private key |
| `MACOS_CERTIFICATE_PASSWORD` | Password protecting that PKCS#12 |
| `APPLE_API_KEY_P8_BASE64` | Base64 of an App Store Connect **Team API key** `.p8` file |

Store these as environment variables:

| Variable | Exact value |
| --- | --- |
| `MACOS_SIGNING_IDENTITY` | Full Microsoft Developer ID identity; it must contain `Microsoft` and the configured Team ID |
| `APPLE_TEAM_ID` | The 10-character Apple Developer Team ID |
| `APPLE_API_KEY_ID` | App Store Connect API Key ID |
| `APPLE_API_ISSUER_ID` | App Store Connect Team API Key issuer UUID |

The App Store Connect Team API key needs **App Manager** access, as required by
`@electron/notarize`. Do not use an Apple ID password. The workflow materializes
the `.p8` only on the macOS runner and electron-builder creates an ephemeral
keychain for the PKCS#12.

The release configuration deliberately grants only:

- `com.apple.security.cs.allow-jit` to the app and inherited processes; and
- `com.apple.security.device.audio-input` to the main app for explicit voice
  mode.

It does not grant `allow-unsigned-executable-memory` or
`disable-library-validation`. Electron 43 does not need the former, and this
application does not load unsigned third-party libraries into its process.

The package is pinned to the latest tested Electron 43 patch and current
electron-builder 26 patch. Do not jump to Electron 44 or raise the macOS
minimum to 13 as part of release plumbing; that requires its own compatibility
change and evidence.

### Azure Artifact Signing with OIDC

Create a Microsoft Entra application/service principal and a federated
credential for the protected GitHub environment:

| Federated credential field | Value |
| --- | --- |
| Issuer | `https://token.actions.githubusercontent.com` |
| Audience | `api://AzureADTokenExchange` |
| Subject | `repo:<owner>/<repo>:environment:windows-production` |

Repositories using GitHub's post-July-2026 immutable OIDC subject format must
use the owner/repository-ID form shown by their GitHub OIDC settings instead.

Assign the service principal exactly one runtime Azure role:

```text
Artifact Signing Certificate Profile Signer
```

Scope it to the certificate profile, not the resource group or subscription:

```text
/subscriptions/<subscription-id>/resourceGroups/<resource-group>/providers/Microsoft.CodeSigning/codeSigningAccounts/<account>/certificateProfiles/<profile>
```

`Contributor`, `Owner`, and `Artifact Signing Identity Verifier` are setup-time
human/admin roles and are not required by the release workload identity.

Store these non-secret identifiers as `windows-production` environment
variables:

| Variable | Exact value |
| --- | --- |
| `AZURE_CLIENT_ID` | Entra application/client ID |
| `AZURE_TENANT_ID` | Entra tenant ID |
| `AZURE_SUBSCRIPTION_ID` | Subscription containing the signing profile |
| `AZURE_ARTIFACT_SIGNING_ENDPOINT` | Regional endpoint such as `https://eus.codesigning.azure.net` |
| `AZURE_ARTIFACT_SIGNING_ACCOUNT_NAME` | Artifact Signing account name |
| `AZURE_ARTIFACT_SIGNING_CERTIFICATE_PROFILE_NAME` | Public-trust certificate profile name |
| `AZURE_ARTIFACT_SIGNING_PROFILE_TYPE` | Exactly `PublicTrust` |
| `WINDOWS_SIGNING_SUBJECT` | Exact Microsoft Authenticode subject returned by `Get-AuthenticodeSignature` |

These production values are intentionally absent from the repository. Do not
invent placeholder account, profile, endpoint, tenant, subscription, client,
or publisher values.

There is no Azure client secret, certificate blob, or long-lived cloud
credential. `azure/login` exchanges GitHub's job-scoped OIDC token for a
short-lived Azure token. electron-builder then uses Azure CLI authentication
to sign every generated `.exe`, `.dll`, and native `.node` file, including
unpacked `ffmpeg`, `ffprobe`, and the NSIS uninstaller. The workflow uses
electron-builder's Azure backend instead of post-signing only the final
installer so executable payloads and the generated uninstaller are signed
before NSIS embeds them.

The locked builder currently exposes Azure signing through the deprecated
electron-builder v26 `WindowsAzureSigningConfiguration` / `azureSignOptions`
schema. `build/windows-signing-policy.json` therefore keeps Windows
publication disabled. Migrating to a supported backend requires a separate
surgical dependency/configuration change, full native Windows tests, and an
updated recorded backend schema; do not flip the policy around the deprecated
path.

The configured application ID is
`com.microsoft.aibast.rapp-brainstem-beta`. Both packaging and manifest gates
reject non-Microsoft signing identities for that namespace. A fork signing
under another publisher must first change the bundle/application ID to an
honest reverse-DNS namespace owned by that publisher.

The NSIS contract is exactly one per-user x64 installer named
`RAPP-Brainstem-Frontier-<version>-windows-x64-setup.exe`, with:

- application ID and AUMID `com.microsoft.aibast.rapp-brainstem-beta`;
- uninstall GUID `48d3a204-a20a-516d-b74f-5ac374e1c8bb`;
- `asInvoker`, stable shortcuts/uninstall identity, and no app-data deletion;
- `warningsAsErrors=true`; and
- `runAfterFinish=false`, so installation never races an unobserved first-run
  bootstrap.

No `.blockmap`, `latest.yml`, or other updater metadata is published. Initial
SmartScreen warnings may still occur; signing is not documented as a
SmartScreen-free guarantee.

Windows packaging runs only on a native x64 Windows runner after a fresh
`npm ci`. `dist:win:x64` rejects every non-Windows or non-x64 host. Both
unsigned verification and future signed release gates create a temporary local
non-administrator account and run the installed NSIS application, bundled
bootstrap, Copilot startup, FFmpeg, FFprobe, and Brainstem readiness checks
under that standard-user token. An elevated-only pass is rejected.

## Prepare a release commit

Update `VERSION`, `package.json`, and both package-lock version fields to the
same semantic prerelease version, then run:

```sh
cd beta
mkdir -p release/.ci-tmp
TMPDIR="$PWD/release/.ci-tmp" npm ci --no-audit --no-fund
TMPDIR="$PWD/release/.ci-tmp" npm run check
TMPDIR="$PWD/release/.ci-tmp" npm test
```

On a native development Mac, an unsigned DMG and its full package gate can also
be exercised locally:

```sh
FRONTIER_SIGNING_MODE=unsigned npm run dist:mac
npm run package:gate
```

This local artifact is named `*-unsigned.dmg`; never attach it to a release.
The gate mounts the DMG, copies the app into an isolated Applications
directory and executes that installed app bundle. The canonical package
first-run gate rewrites only the unsigned development copy with its immutable
fixture, restores the original bytes afterward, and runs the 26-check
missing-runtime, already-ready, concurrent-userData, redaction, Copilot/media,
readiness, failure, and shutdown contract. Windows unsigned verification runs
in the workflow because NSIS standard-user installation, real commit-pinned
bootstrap, launch, readiness, and uninstall require a native Windows runner.

Wait for repository preflight and the unsigned `Frontier Binaries` pull-request
jobs to pass.

## Create the immutable tag and one draft release

Use a component-qualified annotated tag:

```sh
version="0.1.0-beta.7"
release_commit="<full-40-character-commit>"
tag="brainstem-beta-v$version"

git tag -a "$tag" "$release_commit" -m "RAPP Brainstem Frontier v$version"
git push fork "$tag"
```

Never move or reuse a published tag. Create exactly one draft prerelease before
dispatching CI:

```sh
gh release create "$tag" \
  --repo <owner>/<repo> \
  --verify-tag \
  --draft \
  --prerelease \
  --latest=false \
  --title "RAPP Brainstem Frontier v$version" \
  --notes-file "<reviewed-release-notes-file>"
```

This is the only release-creation step. It is performed once by the release
manager, not by parallel build jobs.

## Build, attach, verify, and publish

Dispatch the workflow from a trusted branch that contains the release
workflow:

```sh
gh workflow run frontier-binaries.yml \
  --repo <owner>/<repo> \
  --ref "$tag" \
  -f publish_release=true \
  -f release_tag="$tag"
```

Running the workflow at the tag is required: it binds the protected environment
deployment and the provenance `source-ref` to `refs/tags/<tag>` rather than to a
mutable branch.

At present this command is expected to fail at the native-media and Windows
signing policy gates. Those failures are publication controls, not release
incidents.

Release mode fails closed unless all of the following are true:

- the source version exactly matches the requested tag;
- the remote tag is annotated and resolves to the checked-out commit;
- the final published release reports GitHub immutability (otherwise the
  workflow attempts to return it to draft and fails);
- exactly one matching draft prerelease already exists;
- both native macOS builds use the configured Developer ID identity;
- `forceCodeSigning` is true, the bundle ID is compatible with the publisher,
  and no signed item is ad-hoc;
- the app and DMG have secure timestamps, return notarization status
  `Accepted`, have their notary logs inspected, are stapled, and pass
  `codesign`, `spctl`, and `hdiutil` verification;
- the Windows payload, installer, and installed uninstaller have valid,
  timestamped signatures from `WINDOWS_SIGNING_SUBJECT`;
- packaged app contents, architecture, `ffmpeg`, `ffprobe`, actual DMG/NSIS
  install and platform launch all pass;
- the installed app starts a real isolated routed Brainstem whose `/health`,
  frontend, and `/models` endpoints become ready, then stops it cleanly;
- all three assets receive GitHub/Sigstore build provenance attestations;
- each package-gate JSON report says every check passed and is hashed;
- the binary manifest contains only the exact three allowed assets and records
  their nonzero byte size, download URL, OS/architecture, SHA-256, verified
  signing identity, runtime compatibility, exact release commit, and
  gate-report URL/digest;
- the manifest uses `rapp-brainstem-frontier-release-manifest/v1`, and the
  draft release body contains exactly one
  `rapp-frontier-release-manifest` fence byte-for-byte equivalent to the signed
  manifest asset;
- duplicate names, unknown files, uninstallers, missing URLs, zero-size files,
  a mismatched tag, or anything other than a full 40-character source commit
  make manifest generation fail;
- the binary manifest itself is in `SHA256SUMS` and has a verified Sigstore
  attestation;
- uploaded release assets are byte-identical to the gated artifacts; and
- `SHA256SUMS`, every binary/report/manifest attestation, and the downloaded
  manifest policy all pass.

Only the staging and final publication jobs have `contents: write`. Staging
uploads missing draft assets without `--clobber`; a same-name asset with
different bytes aborts. Native macOS ARM64/x64 jobs then redownload the DMGs and
rerun `hdiutil`, code-signing, timestamp, notarization, Gatekeeper, media, and
architecture checks. A Windows job redownloads and revalidates SHA-256 and
Authenticode. Only after those read-only jobs pass does the final job publish
the existing draft and assert the GitHub API reports `"immutable": true`.

The release includes:

```text
RAPP-Brainstem-Frontier-<version>-macos-arm64.dmg
RAPP-Brainstem-Frontier-<version>-macos-arm64.dmg.gate.json
RAPP-Brainstem-Frontier-<version>-macos-x64.dmg
RAPP-Brainstem-Frontier-<version>-macos-x64.dmg.gate.json
RAPP-Brainstem-Frontier-<version>-windows-x64-setup.exe
RAPP-Brainstem-Frontier-<version>-windows-x64-setup.exe.gate.json
RAPP-Brainstem-Frontier-<version>-windows-x64-setup.exe.spdx.json
<each binary>.sigstore.json
RAPP-Brainstem-Frontier-<version>-binary-manifest.json
RAPP-Brainstem-Frontier-<version>-binary-manifest.json.sigstore.json
SHA256SUMS
```

If a job fails, the release remains a draft. Correct the credential,
notarization, signing, or packaging problem and rerun the workflow. The
workflow preserves already-attached identical bytes and never replaces a
different asset. If a failed draft contains a different or invalid partial
asset, inspect it and remove that draft asset explicitly before rerunning; do
not use `--clobber`.

## Binary update channel

Source checkouts and packaged applications are different update domains.
`Update and Restart` may refresh a managed source checkout, but it cannot
replace code sealed inside a packaged `app.asar`.

Packaged builds therefore declare
`frontierDistributionChannel=binary-release-manifest-v1` and set
`frontierSourceCheckoutUpdaterCompatible=false`. At runtime, `app.isPackaged`
blocks the source-checkout updater and explains that a packaged update must use
the binary channel.

The binary channel's machine-readable authority is the single
`rapp-frontier-release-manifest` JSON fence in the release body. CI requires it
to equal the separately attached and Sigstore-attested
`RAPP-Brainstem-Frontier-<version>-binary-manifest.json` before publication.
The Download Center may expose a `.dmg` or `.exe` only when:

1. the manifest schema, release tag, 40-character commit, and version match;
2. one manifest entry exactly matches the requested filename, OS, and
   architecture;
3. the GitHub release API reports one uploaded, nonempty asset with a safe
   browser URL and a `sha256:` digest matching that entry;
4. the binary is nonempty and its size and SHA-256 match that
   entry;
5. the gate report is nonempty and its URL and SHA-256 match that entry;
6. the recorded platform signing identity and runtime compatibility match
   policy; and
7. the gate status is `passed`.

The protected publication workflow additionally verifies `SHA256SUMS`, every
binary/report/manifest attestation, the exact fenced/body equality, and the
same Download Center validator immediately before changing the draft to
published. A future in-app updater must perform equivalent signature and
attestation verification locally.

There is no in-place `app.asar` mutation or fallback to the source updater.
Until a manifest-verifying in-app installer exists, packaged users install the
next immutable allowlisted release asset through the Download Center.

The manifest also carries `source_fallback.commit`,
`source_fallback.resolves_latest=false`, commit-pinned installer URLs, and
platform commands that set `BRAINSTEM_BETA_COMMIT` to the same 40-character
commit displayed for the release. The Download Center must render those
manifest commands rather than a bootstrap that re-resolves “latest.”

Manifest assets are sorted by deterministic filename, and `SHA256SUMS` is
written in an explicit stable order covering every binary, gate report,
Sigstore bundle, and the manifest itself.

## Consumer verification

After download:

```sh
sha256sum -c SHA256SUMS
gh attestation verify \
  RAPP-Brainstem-Frontier-<version>-macos-arm64.dmg \
  --repo <owner>/<repo>
gh attestation verify \
  RAPP-Brainstem-Frontier-<version>-binary-manifest.json \
  --bundle RAPP-Brainstem-Frontier-<version>-binary-manifest.json.sigstore.json \
  --repo <owner>/<repo>
```

On macOS:

```sh
mkdir frontier-verify-mount
hdiutil attach RAPP-Brainstem-Frontier-<version>-macos-arm64.dmg \
  -nobrowse -readonly -mountpoint "$PWD/frontier-verify-mount"
codesign --verify --deep --strict --verbose=4 \
  "$PWD/frontier-verify-mount/RAPP Brainstem Frontier.app"
xcrun stapler validate RAPP-Brainstem-Frontier-<version>-macos-arm64.dmg
spctl --assess --type open --context context:primary-signature --verbose=4 \
  RAPP-Brainstem-Frontier-<version>-macos-arm64.dmg
hdiutil detach "$PWD/frontier-verify-mount"
rmdir frontier-verify-mount
```

On Windows:

```powershell
signtool.exe verify /pa /all /v /tw `
  .\RAPP-Brainstem-Frontier-<version>-windows-x64-setup.exe
Get-AuthenticodeSignature `
  .\RAPP-Brainstem-Frontier-<version>-windows-x64-setup.exe |
  Format-List Status,SignerCertificate,TimeStamperCertificate
```

## Primary references

- [Electron code signing](https://www.electronjs.org/docs/latest/tutorial/code-signing)
- [electron-builder macOS notarization](https://www.electron.build/docs/features/code-signing/notarization/)
- [electron-builder Windows code signing](https://www.electron.build/docs/features/code-signing/code-signing-win/)
- [`@electron/notarize`](https://github.com/electron/notarize)
- [Apple notarization workflow](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution)
- [Azure Artifact Signing integrations](https://learn.microsoft.com/azure/artifact-signing/how-to-signing-integrations)
- [Azure Artifact Signing roles](https://learn.microsoft.com/azure/artifact-signing/tutorial-assign-roles)
- [GitHub OIDC for Azure](https://docs.github.com/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-azure)
- [GitHub immutable releases](https://docs.github.com/code-security/concepts/supply-chain-security/immutable-releases)
