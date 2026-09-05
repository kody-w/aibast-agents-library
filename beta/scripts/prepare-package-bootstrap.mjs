import { createHash } from "node:crypto";
import {
  copyFileSync,
  mkdirSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { pathToFileURL } from "node:url";


const betaDir = path.resolve(import.meta.dirname, "..");
const repositoryRoot = path.resolve(betaDir, "..");
const canonicalRepository = "microsoft/aibast-agents-library";
const canonicalRepositoryUrl =
  "https://github.com/microsoft/aibast-agents-library.git";
const productionApplicationId =
  "com.microsoft.aibast.rapp-brainstem-beta";
const productionProductName = "RAPP Brainstem Frontier";

function fail(message) {
  throw new Error(message);
}

function sha256(filePath) {
  return createHash("sha256").update(readFileSync(filePath)).digest("hex");
}

function fullCommit() {
  const commit = String(
    process.env.FRONTIER_PACKAGE_COMMIT ||
    execFileSync("git", ["rev-parse", "HEAD"], {
      cwd: repositoryRoot,
      encoding: "utf8",
      windowsHide: true,
    }),
  ).trim();
  if (!/^[0-9a-f]{40}$/i.test(commit)) {
    fail("Package bootstrap requires a full 40-character source commit.");
  }
  return commit.toLowerCase();
}

function repositorySlugFromUrl(value) {
  const match = String(value || "").match(
    /github\.com[/:]([^/]+)\/([^/]+?)(?:\.git)?$/i,
  );
  return match ? `${match[1]}/${match[2]}` : null;
}

export function resolvePackageAuthority({
  signingMode,
  mode = null,
  sourceRepository = process.env.FRONTIER_PACKAGE_SOURCE_REPOSITORY ||
    process.env.GITHUB_REPOSITORY ||
    null,
  authorityUrl = process.env.FRONTIER_PACKAGE_AUTHORITY_URL ||
    canonicalRepositoryUrl,
  applicationId = process.env.FRONTIER_PACKAGE_APP_ID ||
    productionApplicationId,
  productName = process.env.FRONTIER_PACKAGE_PRODUCT_NAME ||
    productionProductName,
} = {}) {
  const explicitMode =
    Boolean(mode) || Boolean(process.env.FRONTIER_PACKAGE_BOOTSTRAP_MODE);
  mode = mode ||
    process.env.FRONTIER_PACKAGE_BOOTSTRAP_MODE ||
    (signingMode === "signed" ? "release" : "development");
  if (!["release", "staging", "development"].includes(mode)) {
    fail("FRONTIER_PACKAGE_BOOTSTRAP_MODE must be release, staging, or development.");
  }
  const authorityRepository = repositorySlugFromUrl(authorityUrl);
  if (!authorityRepository) {
    fail("Package bootstrap authority must be a GitHub repository URL.");
  }
  if (mode === "release") {
    if (
      authorityUrl !== canonicalRepositoryUrl ||
      authorityRepository !== canonicalRepository ||
      sourceRepository !== canonicalRepository ||
      applicationId !== productionApplicationId ||
      productName !== productionProductName
    ) {
      fail("Release package bootstrap authority must be canonical microsoft/aibast-agents-library.");
    }
  } else if (
    authorityRepository !== canonicalRepository ||
    (sourceRepository && sourceRepository !== canonicalRepository)
  ) {
    if (!explicitMode) {
      fail("Noncanonical package builds require an explicit staging or development mode.");
    }
    if (
      applicationId === productionApplicationId ||
      productName === productionProductName
    ) {
      fail("Noncanonical package builds require a distinct application ID and product name.");
    }
  }
  return {
    mode,
    sourceRepository,
    authorityRepository,
    authorityUrl,
    applicationId,
    productName,
  };
}

export function preparePackageBootstrap({ signingMode } = {}) {
  const authority = resolvePackageAuthority({ signingMode });
  const commit = fullCommit();
  const releaseTag =
    authority.mode === "release"
      ? String(process.env.FRONTIER_PACKAGE_RELEASE_TAG || "").trim()
      : null;
  if (
    authority.mode === "release" &&
    !/^brainstem-beta-v[0-9]+\.[0-9]+\.[0-9]+-beta\.[0-9]+$/.test(
      releaseTag,
    )
  ) {
    fail("Release package bootstrap requires FRONTIER_PACKAGE_RELEASE_TAG.");
  }
  const outputDir = path.join(betaDir, "release", "package-bootstrap");
  rmSync(outputDir, { recursive: true, force: true });
  mkdirSync(outputDir, { recursive: true });

  const files = [
    ["install.sh", path.join(repositoryRoot, "install.sh")],
    ["install.ps1", path.join(repositoryRoot, "install.ps1")],
  ];
  const manifestFiles = {};
  for (const [name, source] of files) {
    const destination = path.join(outputDir, name);
    copyFileSync(source, destination);
    manifestFiles[name] = {
      sha256: sha256(destination),
      size: readFileSync(destination).length,
    };
  }

  const policy = JSON.parse(
    readFileSync(
      path.join(betaDir, "build", "package-bootstrap-policy.json"),
      "utf8",
    ),
  );
  const manifest = {
    schema:
      "https://github.com/microsoft/aibast-agents-library/frontier-package-bootstrap/v1",
    mode: authority.mode,
    source_repository: authority.sourceRepository,
    source_commit: commit,
    release_tag: releaseTag,
    authority: {
      repository: authority.authorityRepository,
      repository_url: authority.authorityUrl,
    },
    package_identity: {
      application_id: authority.applicationId,
      product_name: authority.productName,
    },
    publication: {
      ready: policy.publication_enabled === true,
      blockers: policy.publication_blockers || [],
      policy_schema: policy.schema,
    },
    files: manifestFiles,
  };
  writeFileSync(
    path.join(outputDir, "manifest.json"),
    `${JSON.stringify(manifest, null, 2)}\n`,
    { mode: 0o600 },
  );
  return {
    ...authority,
    commit,
    outputDir,
    manifest,
  };
}

if (
  process.argv[1] &&
  import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href
) {
  try {
    const signingMode = process.argv[2] || process.env.FRONTIER_SIGNING_MODE;
    process.stdout.write(
      `${JSON.stringify(preparePackageBootstrap({ signingMode }), null, 2)}\n`,
    );
  } catch (error) {
    process.stderr.write(`Package bootstrap preparation failed: ${String(error.stack || error)}\n`);
    process.exit(1);
  }
}
