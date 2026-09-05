import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import {
  DownloadCenterError,
  analyzePackagedDownloads,
  buildBootstrapDownloads,
  claimDownloadCenterInitialization,
  detectArchitecture,
  discoverRelease,
  fetchGitHubJson,
  formatBytes,
  goldenPathUrl,
  initializeDownloadCenter,
  orderDownloadsForPlatform,
  platformRecommendation,
  presentReleaseFailure,
  resolveDownloadContext,
  safeReleaseAssetUrl,
  selectRelease,
  windowsSupportLabel,
} from "../download-center.js";

const betaRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const repository = "octo/frontier";
const tag = "brainstem-beta-v1.2.3";
const commit = "a".repeat(40);

function asset(name, options = {}) {
  const size = Object.hasOwn(options, "size") ? options.size : 4_194_304;
  const state = Object.hasOwn(options, "state") ? options.state : "uploaded";
  const url = Object.hasOwn(options, "url")
    ? options.url
    : `https://github.com/${repository}/releases/download/${tag}/${encodeURIComponent(name)}`;
  return {
    name,
    size,
    state,
    browser_download_url: url,
  };
}

function release(overrides = {}) {
  return {
    id: 20,
    tag_name: tag,
    draft: false,
    prerelease: true,
    published_at: "2026-09-04T20:00:00Z",
    assets: [],
    ...overrides,
  };
}

function jsonResponse(value, { status = 200, headers = {} } = {}) {
  return new Response(JSON.stringify(value), { status, headers });
}

test("repository and optional tag resolution stay fork-aware", () => {
  assert.deepEqual(
    resolveDownloadContext({
      search: "?repo=contoso/frontier-fork&tag=brainstem-beta-v9.1.0",
      hostname: "microsoft.github.io",
      pathname: "/aibast-agents-library/beta/",
    }),
    {
      repository: "contoso/frontier-fork",
      requestedTag: "brainstem-beta-v9.1.0",
    },
  );

  assert.deepEqual(
    resolveDownloadContext({
      search: "",
      hostname: "contoso.github.io",
      pathname: "/frontier-fork/beta/",
    }),
    { repository: "contoso/frontier-fork", requestedTag: null },
  );

  assert.deepEqual(
    resolveDownloadContext({
      search: "?repo=not/a/repository",
      hostname: "contoso.github.io",
      pathname: "/frontier-fork/beta/",
    }),
    { repository: "contoso/frontier-fork", requestedTag: null },
  );
});

test("release selection is deterministic and an explicit tag wins", () => {
  const older = release({
    id: 10,
    tag_name: "brainstem-beta-v1.0.0",
    published_at: "2026-08-01T00:00:00Z",
  });
  const newest = release({
    id: 30,
    tag_name: "brainstem-beta-v1.3.0",
    published_at: "2026-09-03T00:00:00Z",
  });
  const draft = release({
    id: 40,
    tag_name: "brainstem-beta-v2.0.0",
    draft: true,
    published_at: "2026-09-04T00:00:00Z",
  });
  const unrelated = release({
    id: 50,
    tag_name: "v99.0.0",
    published_at: "2026-09-05T00:00:00Z",
  });

  assert.equal(
    selectRelease([older, draft, unrelated, newest]).tag_name,
    newest.tag_name,
  );
  assert.equal(
    selectRelease([newest, older], { requestedTag: older.tag_name }).tag_name,
    older.tag_name,
  );
  assert.equal(selectRelease([draft, unrelated]), null);
});

test("release discovery executes the real API selection and commit validation", async () => {
  const olderTag = "brainstem-beta-v1.0.0";
  const calls = [];
  const releases = [
    release({ tag_name: tag, published_at: "2026-09-04T20:00:00Z" }),
    release({
      id: 10,
      tag_name: olderTag,
      published_at: "2026-08-01T00:00:00Z",
      assets: [asset("Frontier-1.0.0-win-x64.exe", {
        url: `https://github.com/${repository}/releases/download/${olderTag}/Frontier.exe`,
      })],
    }),
  ];
  const fetchImpl = async (url, options) => {
    calls.push({ url, options });
    return calls.length === 1
      ? jsonResponse(releases)
      : jsonResponse({ sha: commit.toUpperCase() });
  };

  const result = await discoverRelease({
    repository,
    requestedTag: olderTag,
    fetchImpl,
  });

  assert.equal(result.tag, olderTag);
  assert.equal(result.version, "1.0.0");
  assert.equal(result.commit, commit);
  assert.equal(result.packagedDownloads.length, 1);
  assert.equal(
    result.goldenPathUrl,
    `https://github.com/${repository}/blob/${olderTag}/beta/GOLDEN_PATH.md`,
  );
  assert.equal(
    calls[0].url,
    `https://api.github.com/repos/${repository}/releases?per_page=30`,
  );
  assert.equal(
    calls[1].url,
    `https://api.github.com/repos/${repository}/commits/${olderTag}`,
  );
  assert.equal(calls[0].options.headers.Accept, "application/vnd.github+json");
});

test("packaged asset classification rejects unsafe or unmeasured files deterministically", () => {
  const validAssets = [
    asset("Frontier-2.0.0-mac-arm64.dmg"),
    asset("Frontier-2.0.0-win-arm64.exe"),
    asset("Frontier-2.0.0-win-x64.exe"),
    asset("Frontier-2.0.0-mac-x64.dmg"),
  ];
  const invalidAssets = [
    asset("Frontier-2.0.0-win-x64-zero.exe", { size: 0 }),
    asset("Frontier-2.0.0-win-x64-missing.exe", { size: undefined }),
    asset("Frontier-2.0.0-win-x64-unsafe.exe", { url: "javascript:alert(1)" }),
    asset("Frontier-2.0.0-win-ia32.exe"),
    asset("Frontier-2.0.0-mac-arm64.dmg", {
      url: `https://github.com/${repository}/releases/download/${tag}/duplicate.dmg`,
    }),
    asset("Frontier-2.0.0-win-x64.exe.blockmap"),
  ];

  const first = analyzePackagedDownloads(
    release({ assets: [...validAssets, ...invalidAssets] }),
    { repository },
  );
  const second = analyzePackagedDownloads(
    release({ assets: [...invalidAssets].reverse().concat([...validAssets].reverse()) }),
    { repository },
  );

  const expectedNames = [
    "Frontier-2.0.0-win-x64.exe",
    "Frontier-2.0.0-win-arm64.exe",
    "Frontier-2.0.0-mac-x64.dmg",
    "Frontier-2.0.0-mac-arm64.dmg",
  ];
  assert.deepEqual(first.downloads.map((item) => item.fileName), expectedNames);
  assert.deepEqual(second.downloads.map((item) => item.fileName), expectedNames);
  assert.equal(first.rejected.length, 5);
  assert.equal(second.rejected.length, 5);
  assert.ok(first.downloads.every((item) => item.size === "4.0 MB"));
  assert.ok(first.downloads.every((item) => item.href.startsWith("https://github.com/")));
});

test("architecture-aware ordering recommends a compatible package before source fallback", () => {
  const { downloads } = analyzePackagedDownloads(
    release({
      assets: [
        asset("Frontier-win-arm64.exe"),
        asset("Frontier-win-x64.exe"),
        asset("Frontier-mac-arm64.dmg"),
      ],
    }),
    { repository },
  );
  const catalog = [
    ...downloads,
    ...buildBootstrapDownloads({
      repository,
      baseUrl: "https://contoso.github.io/frontier/beta/",
    }),
  ];

  assert.deepEqual(
    orderDownloadsForPlatform(catalog, "windows", "arm64").map((item) => item.fileName),
    ["Frontier-win-arm64.exe", "frontier.ps1", "Frontier-win-x64.exe"],
  );
  assert.deepEqual(
    orderDownloadsForPlatform(catalog, "windows", "x64").map((item) => item.fileName),
    ["Frontier-win-x64.exe", "frontier.ps1", "Frontier-win-arm64.exe"],
  );
  assert.deepEqual(
    orderDownloadsForPlatform(catalog, "windows").map((item) => item.fileName),
    ["Frontier-win-x64.exe", "Frontier-win-arm64.exe", "frontier.ps1"],
  );
  assert.deepEqual(
    orderDownloadsForPlatform(catalog, "linux", "arm64").map((item) => item.fileName),
    ["frontier.sh"],
  );

  const unspecified = analyzePackagedDownloads(
    release({ assets: [asset("Frontier-Setup.exe")] }),
    { repository },
  ).downloads;
  assert.deepEqual(
    orderDownloadsForPlatform(
      [...unspecified, ...catalog.filter((item) => item.kind === "bootstrap")],
      "windows",
      "arm64",
    ).map((item) => item.fileName),
    ["Frontier-Setup.exe", "frontier.ps1"],
  );
});

test("Windows ARM64 is only advertised when an ARM64 package exists", () => {
  const x64Only = analyzePackagedDownloads(
    release({ assets: [asset("Frontier-win-x64.exe")] }),
    { repository },
  ).downloads;
  const withArm64 = analyzePackagedDownloads(
    release({
      assets: [
        asset("Frontier-win-x64.exe"),
        asset("Frontier-win-arm64.exe"),
      ],
    }),
    { repository },
  ).downloads;

  assert.equal(windowsSupportLabel(x64Only), "Windows 11 x64");
  assert.doesNotMatch(windowsSupportLabel(x64Only), /ARM64/);
  assert.equal(windowsSupportLabel(withArm64), "Windows 11 x64 or ARM64");
  assert.match(
    platformRecommendation(x64Only, "windows", "arm64"),
    /No ARM64 packaged installer is published/,
  );
});

test("missing and invalid size measurements fail instead of being skipped", () => {
  for (const invalid of [undefined, null, Number.NaN, -1, 0, 1.5, "4096"]) {
    assert.throws(
      () => formatBytes(invalid),
      (error) => error instanceof DownloadCenterError
        && error.code === "INVALID_ASSET_SIZE",
    );
  }

  const result = analyzePackagedDownloads(
    release({ assets: [asset("Frontier-win-x64.exe", { size: undefined })] }),
    { repository },
  );
  assert.equal(result.downloads.length, 0);
  assert.deepEqual(result.rejected, [{
    fileName: "Frontier-win-x64.exe",
    reason: "missing or invalid size",
  }]);
});

test("GitHub rate limits and malformed commit data surface actionable failures", async () => {
  const reset = 1_800_000_000;
  await assert.rejects(
    () => fetchGitHubJson("https://api.github.com/example", {
      operation: "checking a test release",
      fetchImpl: async () => jsonResponse(
        { message: "rate limited" },
        {
          status: 403,
          headers: {
            "x-ratelimit-remaining": "0",
            "x-ratelimit-reset": String(reset),
          },
        },
      ),
    }),
    (error) => {
      assert.equal(error.code, "GITHUB_RATE_LIMIT");
      assert.equal(error.status, 403);
      assert.equal(error.retryAt.toISOString(), new Date(reset * 1000).toISOString());
      assert.match(error.message, /rate limit reached/);
      return true;
    },
  );

  await assert.rejects(
    () => discoverRelease({
      repository,
      fetchImpl: async (url) => url.includes("/releases?")
        ? jsonResponse([release()])
        : jsonResponse({ sha: "short" }),
    }),
    (error) => error instanceof DownloadCenterError
      && error.code === "INVALID_RELEASE_COMMIT",
  );
});

test("release failures are visible while source fallback remains inspectable", () => {
  const elements = Object.fromEntries(
    ["status", "statusDot", "version", "date", "commit", "resolvedDate", "error"]
      .map((name) => [name, { textContent: "", className: "", hidden: true }]),
  );
  presentReleaseFailure(
    elements,
    new DownloadCenterError("GitHub API request failed (HTTP 500)."),
  );
  assert.equal(elements.status.textContent, "Release check unavailable");
  assert.equal(elements.statusDot.className, "status-dot error");
  assert.equal(elements.error.hidden, false);
  assert.match(elements.error.textContent, /HTTP 500/);
  assert.match(elements.error.textContent, /inspectable source bootstraps remain available/);

  const fallback = buildBootstrapDownloads({
    repository,
    baseUrl: "https://contoso.github.io/frontier/beta/",
  });
  assert.deepEqual(
    fallback.map((item) => item.href),
    [
      "https://contoso.github.io/frontier/beta/frontier.ps1",
      "https://contoso.github.io/frontier/beta/frontier.sh",
    ],
  );
  assert.ok(fallback.every((item) => item.command.includes(`RAPP_FRONTIER_REPO="${repository}"`)));
});

test("duplicate initialization exits before listener registration", async () => {
  const root = { dataset: {} };
  assert.equal(claimDownloadCenterInitialization(root), true);
  assert.equal(claimDownloadCenterInitialization(root), false);

  const result = await initializeDownloadCenter({
    documentObject: {
      documentElement: {
        dataset: { downloadCenterInitialized: "true" },
      },
    },
    windowObject: {},
  });
  assert.deepEqual(result, { initialized: false });
});

test("download URLs and DOM wiring reject executable injection surfaces", () => {
  assert.equal(safeReleaseAssetUrl("javascript:alert(1)", repository), null);
  assert.equal(
    safeReleaseAssetUrl(
      `https://evil.example/${repository}/releases/download/${tag}/Frontier.exe`,
      repository,
    ),
    null,
  );
  assert.equal(
    safeReleaseAssetUrl(
      `https://github.com/${repository}/releases/download/${tag}/Frontier.exe`,
      repository,
    ),
    `https://github.com/${repository}/releases/download/${tag}/Frontier.exe`,
  );

  const moduleSource = readFileSync(path.join(betaRoot, "download-center.js"), "utf8");
  const pageSource = readFileSync(path.join(betaRoot, "index.html"), "utf8");
  assert.doesNotMatch(moduleSource, /\binnerHTML\b|insertAdjacentHTML|document\.write/);
  assert.match(pageSource, /<script type="module" src="download-center\.js"><\/script>/);
  assert.doesNotMatch(pageSource, /href="GOLDEN_PATH\.md"/);
  assert.match(pageSource, /id="golden-path-link"/);
  assert.equal(
    goldenPathUrl("contoso/frontier", "brainstem-beta-v2.0.0"),
    "https://github.com/contoso/frontier/blob/brainstem-beta-v2.0.0/beta/GOLDEN_PATH.md",
  );
  assert.equal(
    [...pageSource.matchAll(/src="download-center\.js"/g)].length,
    1,
  );
});

test("architecture detection uses explicit high-entropy data without guessing Apple Silicon", async () => {
  assert.equal(
    await detectArchitecture({
      userAgentData: {
        getHighEntropyValues: async () => ({ architecture: "arm", bitness: "64" }),
      },
    }),
    "arm64",
  );
  assert.equal(
    await detectArchitecture({
      userAgentData: {
        getHighEntropyValues: async () => ({ architecture: "x86", bitness: "64" }),
      },
    }),
    "x64",
  );
  assert.equal(
    await detectArchitecture({
      platform: "MacIntel",
      userAgent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    }),
    null,
  );
});
