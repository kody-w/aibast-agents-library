import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import {
  copyFileSync,
  mkdirSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import path from "node:path";

import {
  normalizeGitHubRepositoryUrl,
  validateBootstrapProvenance,
} from "../electron/brainstem-provisioner.mjs";

const betaDir = path.resolve(import.meta.dirname, "..");
const repoRoot = path.resolve(betaDir, "..");
const outputDirectory = path.join(betaDir, "build", "generated", "bootstrap");
const COMMIT_PATTERN = /^[0-9a-f]{40}$/i;

function git(args) {
  return execFileSync("git", ["-C", repoRoot, ...args], {
    encoding: "utf8",
    windowsHide: true,
  }).trim();
}

function sha256(filePath) {
  return createHash("sha256").update(readFileSync(filePath)).digest("hex");
}

function resolveCommit() {
  const head = git(["rev-parse", "HEAD"]).toLowerCase();
  const requested = String(
    process.env.BRAINSTEM_BETA_PACKAGE_COMMIT || head,
  ).toLowerCase();
  if (!COMMIT_PATTERN.test(requested)) {
    throw new Error(
      "BRAINSTEM_BETA_PACKAGE_COMMIT must be a full 40-character commit SHA.",
    );
  }
  if (requested !== head) {
    throw new Error(
      `Package provenance ${requested} does not match checkout HEAD ${head}.`,
    );
  }
  const dirty = git(["status", "--porcelain", "--untracked-files=no"]);
  if (dirty) {
    throw new Error(
      "Refusing to package bootstrap provenance from a checkout with tracked changes.",
    );
  }
  return head;
}

function main() {
  const commit = resolveCommit();
  const mode = String(
    process.env.BRAINSTEM_BETA_PACKAGE_MODE || "release",
  ).trim().toLowerCase();
  if (!["development", "release"].includes(mode)) {
    throw new Error(
      "BRAINSTEM_BETA_PACKAGE_MODE must be release or development.",
    );
  }
  const repositoryUrl = normalizeGitHubRepositoryUrl(
    process.env.BRAINSTEM_BETA_PACKAGE_REPOSITORY_URL
      || git(["remote", "get-url", "origin"]),
  );
  const sourceRef = String(
    process.env.BRAINSTEM_BETA_PACKAGE_REF || "main",
  ).trim();
  const installers = {
    "install.sh": path.join(repoRoot, "install.sh"),
    "install.ps1": path.join(repoRoot, "install.ps1"),
  };

  rmSync(outputDirectory, { recursive: true, force: true });
  mkdirSync(outputDirectory, { recursive: true, mode: 0o700 });
  const manifest = {
    schema: 1,
    product: mode === "release"
      ? "rapp-brainstem-frontier"
      : "rapp-brainstem-frontier-development",
    mode,
    commit,
    repositoryUrl,
    sourceRef,
    installers: {},
  };
  for (const [filename, source] of Object.entries(installers)) {
    const destination = path.join(outputDirectory, filename);
    copyFileSync(source, destination);
    manifest.installers[filename] = { sha256: sha256(destination) };
  }
  validateBootstrapProvenance(manifest);
  writeFileSync(
    path.join(outputDirectory, "provenance.json"),
    `${JSON.stringify(manifest, null, 2)}\n`,
    { mode: 0o600 },
  );
  process.stdout.write(
    `Prepared ${mode} Brainstem bootstrap ${commit} from ${repositoryUrl}\n`,
  );
}

main();
