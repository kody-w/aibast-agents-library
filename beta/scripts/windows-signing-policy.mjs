import { readFileSync } from "node:fs";
import path from "node:path";

const betaDir = path.resolve(import.meta.dirname, "..");
const defaultPolicyPath = path.join(
  betaDir,
  "build",
  "windows-signing-policy.json",
);

function fail(message) {
  throw new Error(message);
}

export function loadWindowsSigningPolicy(filePath = defaultPolicyPath) {
  const policy = JSON.parse(readFileSync(filePath, "utf8"));
  if (
    policy?.schema !==
      "https://github.com/microsoft/aibast-agents-library/frontier-windows-signing-policy/v1"
    || typeof policy.publication_enabled !== "boolean"
    || typeof policy.current_backend_schema !== "string"
    || !["approved", "blocked-deprecated-v26"].includes(
      policy.backend_approval,
    )
    || (
      policy.approved_backend_schema !== null
      && typeof policy.approved_backend_schema !== "string"
    )
    || policy.required_environment !== "windows-production"
    || policy.required_profile_type !== "PublicTrust"
    || policy.client_secret_allowed !== false
  ) {
    fail("Windows signing policy is malformed.");
  }
  return policy;
}

export function evaluateWindowsSigningPolicy(policy) {
  const blockers = [];
  if (policy?.publication_enabled !== true) {
    blockers.push(policy?.publication_blocker || "publication is disabled");
  }
  if (
    policy?.backend_approval !== "approved"
    || !policy?.approved_backend_schema
    || policy.approved_backend_schema !== policy.current_backend_schema
  ) {
    blockers.push(
      `signing backend ${policy?.current_backend_schema || "unknown"} is not approved`,
    );
  }
  if (
    policy?.client_secret_allowed !== false
    || policy?.required_environment !== "windows-production"
    || policy?.required_profile_type !== "PublicTrust"
  ) {
    blockers.push("OIDC/Public Trust production policy is incomplete");
  }
  return {
    publicationReady: blockers.length === 0,
    blockers,
  };
}

function expectedText(expected, name) {
  const value = String(expected?.[name] || "").trim();
  if (!value) fail(`Protected Windows signing value ${name} is required.`);
  return value;
}

export function validateWindowsSigningEvidence(signing, policy, expected) {
  const readiness = evaluateWindowsSigningPolicy(policy);
  if (!readiness.publicationReady) {
    fail(`Windows signing policy is blocked: ${readiness.blockers.join(" | ")}`);
  }
  const independent = {
    endpoint: expectedText(expected, "endpoint"),
    account: expectedText(expected, "account"),
    certificateProfile: expectedText(expected, "certificateProfile"),
    publisherSubject: expectedText(expected, "publisherSubject"),
    profileType: expectedText(expected, "profileType"),
  };
  if (independent.profileType !== "PublicTrust") {
    fail("Protected Windows signing profile type must be PublicTrust.");
  }
  let endpoint;
  try {
    endpoint = new URL(independent.endpoint);
  } catch {
    fail("Protected Windows signing endpoint is invalid.");
  }
  if (
    endpoint.protocol !== "https:"
    || !endpoint.hostname.endsWith(".codesigning.azure.net")
  ) {
    fail("Protected Windows signing endpoint must use codesigning.azure.net.");
  }
  if (
    signing?.backend_schema !== policy.current_backend_schema
    || signing.backend_schema !== policy.approved_backend_schema
    || signing?.endpoint !== independent.endpoint
    || signing?.account !== independent.account
    || signing?.certificate_profile !== independent.certificateProfile
    || signing?.identity !== independent.publisherSubject
    || signing?.profile_type !== independent.profileType
    || signing?.file_digest !== "SHA256"
    || signing?.timestamp_digest !== "SHA256"
    || signing?.timestamp_url !== "http://timestamp.acs.microsoft.com/"
  ) {
    fail("Windows signing evidence does not match independently protected policy.");
  }
  return independent;
}
