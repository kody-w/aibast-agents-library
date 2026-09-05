const path = require("node:path");
const { spawnSync } = require("node:child_process");
const { existsSync } = require("node:fs");

function required(name) {
  const value = String(process.env[name] || "").trim();
  if (!value) throw new Error(`${name} is required for Artifact Signing.`);
  return value;
}

function quote(value) {
  return `'${String(value).replace(/'/g, "''")}'`;
}

module.exports = async function artifactSigningHook(configuration) {
  const filePath = path.resolve(configuration.path);
  const signingRoot = path.resolve(required("FRONTIER_SIGNING_ROOT"));
  const relative = path.relative(signingRoot, filePath);
  if (
    !relative
    || relative.startsWith("..")
    || path.isAbsolute(relative)
    || ![".exe", ".dll", ".node"].includes(path.extname(filePath).toLowerCase())
  ) {
    throw new Error(`Refusing to sign file outside validated input: ${filePath}`);
  }
  const moduleRoot = path.resolve(required("FRONTIER_ARTIFACT_SIGNING_MODULE_ROOT"));
  if (!existsSync(moduleRoot)) {
    throw new Error(`Validated ArtifactSigning module root is missing: ${moduleRoot}`);
  }
  const invoke = [
    "Invoke-ArtifactSigning",
    `  -Endpoint ${quote(required("AZURE_ARTIFACT_SIGNING_ENDPOINT"))}`,
    `  -CodeSigningAccountName ${quote(required("AZURE_ARTIFACT_SIGNING_ACCOUNT_NAME"))}`,
    `  -CertificateProfileName ${quote(required("AZURE_ARTIFACT_SIGNING_CERTIFICATE_PROFILE_NAME"))}`,
    `  -Files ${quote(filePath)}`,
    "  -FileDigest SHA256",
    "  -TimestampRfc3161 'http://timestamp.acs.microsoft.com/'",
    "  -TimestampDigest SHA256",
  ].join(" `\n");
  const script = [
    "$ErrorActionPreference = 'Stop'",
    `$env:PSModulePath = ${quote(moduleRoot)} + ';' + $env:PSModulePath`,
    "Import-Module ArtifactSigning -RequiredVersion 0.1.8 -Force",
    invoke,
  ].join("\n");
  const result = spawnSync("powershell.exe", [
    "-NoLogo",
    "-NoProfile",
    "-NonInteractive",
    "-Command",
    script,
  ], {
    encoding: "utf8",
    maxBuffer: 20 * 1024 * 1024,
    timeout: 10 * 60 * 1000,
    windowsHide: true,
  });
  if (result.status !== 0) {
    throw new Error(
      `Artifact Signing failed for ${filePath}: `
      + String(result.stderr || result.stdout || result.error || "").trim(),
    );
  }
};
