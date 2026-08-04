# Third-party notices — rapp/ corpus mirrors

Files under `rapp/` that are mirrored from upstream RAPP kernel projects are
**third-party materials distributed under their own upstream licenses**, not
under this repository's root MIT grant. Every mirrored file's upstream repo,
pinned revision, SHA-256, and license are recorded in
[`MIRROR-MANIFEST.json`](MIRROR-MANIFEST.json) and verified by
`scripts/corpus_sync.py`.

| Mirror path | Upstream | License | Copyright |
|---|---|---|---|
| `spec/RAPP1-SPEC.md` | kody-w/rapp-1 | No upstream LICENSE yet — redistributed under the author's recorded authorization (see manifest entry); upstream LICENSE is a v1-GA blocker | Upstream author |
| `spec/RAPP1_AUTHORITY.json` | kody-w/rapp-map | MIT | Kody Wildfeuer |
| `spec/ecosystem-spec.json` | kody-w/rapp-god | MIT | Kody Wildfeuer |
| `bible/**` | kody-w/RAPP-Bible | BSD-3-Clause ([bible/LICENSE](bible/LICENSE), [bible/NOTICE](bible/NOTICE)) | Upstream author |
| `standards/PLAYBOOK.md`, `standards/rapp-train-llms.txt` | kody-w/rapp-train | Apache-2.0 ([standards/LICENSE-APACHE-2.0](standards/LICENSE-APACHE-2.0), [standards/NOTICE](standards/NOTICE)) | Wildhaven Homes LLC |
| `standards/rapp-holo-SPEC.md` | kody-w/rapp-holo | Apache-2.0 (same texts) | Wildhaven Homes LLC |
| `standards/rapp-static-api-SPEC.md`, `standards/rapp-static-api-llms.txt` | kody-w/rapp-static-apis | MIT | Kody Wildfeuer |

Files authored in this repository (`README.md`, `SUCCESSION.md`, `ALM.md`,
`ALIGNMENT.md`, `ATTRIBUTION.md`, this file, `MIRROR-MANIFEST.json`,
`BRAINSTEM-LOCK.json`) are covered by the root repository license.
