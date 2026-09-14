#!/usr/bin/env node

import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import {
  mkdirSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import {
  normalizeGitHubRepositoryUrl,
  validateBootstrapProvenance,
} from "../electron/brainstem-provisioner.mjs";

export const CANONICAL_REPOSITORY =
  "https://github.com/microsoft/aibast-agents-library.git";
export const PRODUCTION_APP_ID =
  "com.microsoft.aibast.rapp-brainstem-beta";
export const PRODUCTION_PRODUCT_NAME =
  "RAPP Brainstem Frontier";
export const NSIS_GUID =
  "48d3a204-a20a-516d-b74f-5ac374e1c8bb";

const dirname = path.dirname(fileURLToPath(import.meta.url));
const betaDir = path.resolve(dirname, "..");
const repositoryRoot = path.resolve(betaDir, "..");
const generatedDir = path.join(betaDir, "build", "generated", "bootstrap");
const commitPattern = /^[0-9a-f]{40}$/;
const releaseTagPattern = /^brainstem-beta-v\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$/;

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

function runGit(args) {
  return execFileSync("git", args, {
    cwd: repositoryRoot,
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
  }).trim();
}

function normalizeSourceRepository(value) {
  const raw = String(value || "").trim();
  if (!raw) return normalizeGitHubRepositoryUrl(runGit(["remote", "get-url", "origin"]));
  if (/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(raw)) {
    return normalizeGitHubRepositoryUrl(`https://github.com/${raw}.git`);
  }
  return normalizeGitHubRepositoryUrl(raw);
}

function resolveMode(explicitMode) {
  const requested = String(
    explicitMode
      || process.env.FRONTIER_PACKAGE_BOOTSTRAP_MODE
      || process.env.BRAINSTEM_BETA_PACKAGE_MODE
      || "development",
  ).trim().toLowerCase();
  if (!["development", "staging", "release"].includes(requested)) {
    throw new Error(
      "FRONTIER_PACKAGE_BOOTSTRAP_MODE must be development, staging, or release.",
    );
  }
  return requested;
}

function resolveCommit(explicitCommit) {
  const commit = String(
    explicitCommit
      || process.env.FRONTIER_PACKAGE_SOURCE_COMMIT
      || process.env.BRAINSTEM_BETA_PACKAGE_COMMIT
      || runGit(["rev-parse", "HEAD"]),
  ).trim().toLowerCase();
  if (!commitPattern.test(commit)) {
    throw new Error(
      "Packaged bootstrap provenance requires a full 40-character commit SHA.",
    );
  }
  const resolved = runGit(["rev-parse", `${commit}^{commit}`]).toLowerCase();
  if (resolved !== commit) {
    throw new Error("The requested package commit is not available locally.");
  }
  const dirty = runGit([
    "status",
    "--porcelain",
    "--untracked-files=no",
    "--",
    "install.sh",
    "install.ps1",
    "beta",
  ]);
  if (dirty) {
    throw new Error(
      "Refusing to package dirty installer or beta sources. Commit the exact "
      + "runtime and bootstrap bytes before building.",
    );
  }
  return commit;
}

function resolveIdentity({ mode, repositoryUrl, appId, productName }) {
  const canonicalSource = repositoryUrl === CANONICAL_REPOSITORY;
  const requestedAppId = String(
    appId || process.env.FRONTIER_PACKAGE_APP_ID || "",
  ).trim();
  const requestedProductName = String(
    productName || process.env.FRONTIER_PACKAGE_PRODUCT_NAME || "",
  ).trim();

  if (mode === "release") {
    if (!canonicalSource) {
      throw new Error(
        `Release package authority must be canonical: ${CANONICAL_REPOSITORY}.`,
      );
    }
    if (
      (requestedAppId && requestedAppId !== PRODUCTION_APP_ID)
      || (requestedProductName && requestedProductName !== PRODUCTION_PRODUCT_NAME)
    ) {
      throw new Error("Release package identity is frozen and cannot be overridden.");
    }
    return {
      applicationId: PRODUCTION_APP_ID,
      productName: PRODUCTION_PRODUCT_NAME,
    };
  }

  if (!canonicalSource) {
    if (!requestedAppId || !requestedProductName) {
      throw new Error(
        "Noncanonical development/staging packages require an explicit "
        + "distinct application ID and product name through "
        + "FRONTIER_PACKAGE_APP_ID and FRONTIER_PACKAGE_PRODUCT_NAME.",
      );
    }
    if (
      requestedAppId === PRODUCTION_APP_ID
      || requestedProductName === PRODUCTION_PRODUCT_NAME
    ) {
      throw new Error(
        "Noncanonical packages must use an identity distinct from production.",
      );
    }
    return {
      applicationId: requestedAppId,
      productName: requestedProductName,
    };
  }

  return {
    applicationId: requestedAppId || PRODUCTION_APP_ID,
    productName: requestedProductName || PRODUCTION_PRODUCT_NAME,
  };
}

export function resolvePackageAuthority({
  mode = "development",
  sourceRepository,
  authorityUrl,
  applicationId,
  productName,
} = {}) {
  const normalizedMode = resolveMode(mode);
  const repositoryUrl = normalizeSourceRepository(
    authorityUrl || sourceRepository,
  );
  const repository = new URL(repositoryUrl).pathname
    .replace(/^\/|\/(?:\.git)?$/g, "")
    .replace(/\.git$/i, "");
  const identity = resolveIdentity({
    mode: normalizedMode,
    repositoryUrl,
    appId: applicationId,
    productName,
  });
  return {
    ...identity,
    authorityRepository: repository,
    authorityUrl: repositoryUrl,
    mode: normalizedMode,
  };
}

export function preparePackageBootstrap(options = {}) {
  const mode = resolveMode(options.mode);
  const provenanceMode = mode === "release" ? "release" : "development";
  const commit = resolveCommit(options.commit);
  const repositoryUrl = normalizeSourceRepository(
    options.repository || process.env.FRONTIER_PACKAGE_SOURCE_REPOSITORY,
  );
  const releaseTag = String(
    options.releaseTag || process.env.FRONTIER_PACKAGE_RELEASE_TAG || "",
  ).trim();
  if (mode === "release" && !releaseTagPattern.test(releaseTag)) {
    throw new Error(
      "Release packaging requires FRONTIER_PACKAGE_RELEASE_TAG="
      + "brainstem-beta-v<semver>.",
    );
  }

  const identity = resolveIdentity({
    mode,
    repositoryUrl,
    appId: options.appId,
    productName: options.productName,
  });

  rmSync(generatedDir, { recursive: true, force: true });
  mkdirSync(generatedDir, { recursive: true });

  const installers = {};
  for (const filename of ["install.sh", "install.ps1"]) {
    const source = execFileSync("git", ["show", `${commit}:${filename}`], {
      cwd: repositoryRoot,
      encoding: null,
      stdio: ["ignore", "pipe", "pipe"],
      maxBuffer: 8 * 1024 * 1024,
    });
    writeFileSync(path.join(generatedDir, filename), source, { mode: 0o755 });
    installers[filename] = { sha256: sha256(source) };
  }

  const manifest = {
    schema: 1,
    product: provenanceMode === "release"
      ? "rapp-brainstem-frontier"
      : "rapp-brainstem-frontier-development",
    mode: provenanceMode,
    commit,
    repositoryUrl,
    sourceRef: mode === "release"
      ? releaseTag
      : String(process.env.BRAINSTEM_BETA_PACKAGE_REF || commit).trim(),
    installers,
    authority: {
      canonical: repositoryUrl === CANONICAL_REPOSITORY,
      requestedMode: mode,
      releaseTag: releaseTag || null,
    },
    packageIdentity: {
      appId: identity.applicationId,
      productName: identity.productName,
      nsisGuid: NSIS_GUID,
    },
  };

  const policy = JSON.parse(
    readFileSync(
      path.join(betaDir, "build", "package-bootstrap-policy.json"),
      "utf8",
    ),
  );
  const policyBlockers = Array.isArray(policy.publication_blockers)
    ? policy.publication_blockers.map((entry) => String(entry))
    : [];
  manifest.publication = {
    ready: policy.publication_enabled === true && policyBlockers.length === 0,
    blockers: policyBlockers,
  };

  validateBootstrapProvenance(manifest);
  writeFileSync(
    path.join(generatedDir, "provenance.json"),
    `${JSON.stringify(manifest, null, 2)}\n`,
    { mode: 0o644 },
  );

  return {
    ...identity,
    bootstrapDirectory: generatedDir,
    manifest,
  };
}

function main() {
  const result = preparePackageBootstrap();
  const written = ["install.sh", "install.ps1", "provenance.json"]
    .map((filename) => {
      const body = readFileSync(path.join(generatedDir, filename));
      return `${filename} (${body.length} bytes)`;
    })
    .join(", ");
  console.log(
    `Prepared ${result.manifest.mode} bootstrap bundle for `
    + `${result.manifest.commit}: ${written}`,
  );
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  try {
    main();
  } catch (error) {
    console.error(`Package bootstrap preparation failed: ${error.message}`);
    process.exit(1);
  }
}
