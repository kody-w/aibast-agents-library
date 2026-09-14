# Third-party notices

RAPP Brainstem Frontier is distributed under the repository MIT license and uses
the following principal third-party components:

- GitHub Copilot SDK and the unmodified GitHub Copilot CLI platform package,
  obtained through npm and subject to the license and terms included in those
  packages.
- Electron, Chromium, and Node.js, distributed under their respective
  open-source licenses and notices included with the Electron runtime.
- `ffmpeg-static` and `@ffprobe-installer/ffprobe`, used by the source launcher
  for local recording diagnostics.

The source installer obtains these dependencies from their canonical package
registries and retains package integrity hashes in `package-lock.json`.

This beta does not redistribute provider credentials. GitHub authentication
remains owned by GitHub Copilot and RAPP Brainstem.

## Native media binary publication status

The currently resolved macOS ARM64 `ffmpeg-static` binary reports
`--enable-nonfree`. FFmpeg's legal guidance states that a build combining GPL
and nonfree components is not redistributable. The currently resolved FFprobe
binary also reports a different upstream version from FFmpeg.

Accordingly, the Frontier binary release workflow is **fail-closed** and does
not publish any DMG or EXE containing these media binaries. Local source
installation is not an approval to redistribute their bytes.

Binary publication remains blocked until every macOS ARM64, macOS x64, and
Windows x64 FFmpeg/FFprobe binary:

- is the same approved upstream version;
- omits `--enable-nonfree`;
- has a reviewed redistributable license and HTTPS provenance URL; and
- matches a SHA-256 recorded in `build/native-media-policy.json`.

Reference: [FFmpeg legal considerations](https://ffmpeg.org/legal.html).
