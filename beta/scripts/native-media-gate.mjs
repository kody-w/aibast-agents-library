import { createHash } from "node:crypto";
import { existsSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { pathToFileURL } from "node:url";


const betaDir = path.resolve(import.meta.dirname, "..");
const defaultPolicyPath = path.join(
  betaDir,
  "build",
  "native-media-policy.json",
);

function fail(message) {
  throw new Error(message);
}

function sha256(filePath) {
  return createHash("sha256").update(readFileSync(filePath)).digest("hex");
}

function parseArguments(argv) {
  const values = {};
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (!argument.startsWith("--")) fail(`Unexpected argument: ${argument}`);
    const name = argument.slice(2);
    if (name === "require-publication") {
      values[name] = true;
      continue;
    }
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) fail(`Missing value for ${argument}.`);
    if (!["policy"].includes(name)) fail(`Unsupported argument: ${argument}.`);
    values[name] = value;
    index += 1;
  }
  return values;
}

export function loadNativeMediaPolicy(policyPath = defaultPolicyPath) {
  const policy = JSON.parse(readFileSync(policyPath, "utf8"));
  if (
    policy?.schema !==
      "https://github.com/microsoft/aibast-agents-library/frontier-native-media-policy/v1" ||
    !Array.isArray(policy.requirements?.required_targets) ||
    !Array.isArray(policy.requirements?.required_components) ||
    !Array.isArray(policy.requirements?.disallowed_configure_flags) ||
    !policy.requirements?.normalized_upstream_version ||
    !policy.approved_binaries ||
    typeof policy.approved_binaries !== "object"
  ) {
    fail("Native media policy is malformed.");
  }
  return policy;
}

function validateApproval(approval, policy, target, component) {
  const errors = [];
  if (!approval || typeof approval !== "object") {
    return [`${target}/${component} has no approved binary provenance.`];
  }
  if (!/^[0-9a-f]{64}$/i.test(approval.sha256 || "")) {
    errors.push(`${target}/${component} has no valid SHA-256.`);
  }
  if (
    approval.upstream_version !==
    policy.requirements.normalized_upstream_version
  ) {
    errors.push(`${target}/${component} is not the normalized upstream version.`);
  }
  try {
    const sourceUrl = new URL(approval.source_url);
    if (sourceUrl.protocol !== "https:") {
      errors.push(`${target}/${component} source URL is not HTTPS.`);
    }
  } catch {
    errors.push(`${target}/${component} has no valid source URL.`);
  }
  if (
    approval.redistributable !== true ||
    !approval.license ||
    /nonfree/i.test(approval.license)
  ) {
    errors.push(`${target}/${component} lacks redistributable license approval.`);
  }
  return errors;
}

export function evaluatePolicyReadiness(policy) {
  const blockers = [];
  if (policy.publication_enabled !== true) {
    blockers.push(
      policy.publication_blocker ||
      "Native media publication is disabled by policy.",
    );
  }
  for (const target of policy.requirements.required_targets) {
    for (const component of policy.requirements.required_components) {
      blockers.push(
        ...validateApproval(
          policy.approved_binaries[target]?.[component],
          policy,
          target,
          component,
        ),
      );
    }
  }
  return {
    publication_ready: blockers.length === 0,
    blockers,
  };
}

function inspectBinary(filePath, component, target, policy) {
  if (!filePath || !existsSync(filePath)) {
    return {
      component,
      path: filePath || null,
      publication_ready: false,
      blockers: [`${target}/${component} binary is missing.`],
    };
  }
  const result = spawnSync(filePath, ["-version"], {
    encoding: "utf8",
    timeout: 30000,
    windowsHide: true,
  });
  const output = `${result.stdout || ""}\n${result.stderr || ""}`.trim();
  const version = new RegExp(`^${component} version ([^\\s]+)`, "im")
    .exec(output)?.[1]
    ?.replace(/^n/, "") || null;
  const configuration = /^configuration:\s*(.+)$/im.exec(output)?.[1] || "";
  const approval = policy.approved_binaries[target]?.[component];
  const digest = sha256(filePath);
  const blockers = validateApproval(approval, policy, target, component);
  for (const flag of policy.requirements.disallowed_configure_flags) {
    if (configuration.split(/\s+/).includes(flag)) {
      blockers.push(`${target}/${component} contains disallowed ${flag}.`);
    }
  }
  if (version !== policy.requirements.normalized_upstream_version) {
    blockers.push(
      `${target}/${component} reports ${version || "unknown"} instead of ` +
      `${policy.requirements.normalized_upstream_version}.`,
    );
  }
  if (approval?.sha256 && approval.sha256.toLowerCase() !== digest) {
    blockers.push(`${target}/${component} SHA-256 is not approved.`);
  }
  return {
    component,
    sha256: digest,
    size: statSync(filePath).size,
    upstream_version: version,
    configuration,
    approved_provenance: approval || null,
    publication_ready: blockers.length === 0,
    blockers,
  };
}

export function evaluateNativeMedia({
  ffmpegPath,
  ffprobePath,
  platform,
  arch,
  policyPath = defaultPolicyPath,
}) {
  const policy = loadNativeMediaPolicy(policyPath);
  const target = `${platform}-${arch}`;
  const components = [
    inspectBinary(ffmpegPath, "ffmpeg", target, policy),
    inspectBinary(ffprobePath, "ffprobe", target, policy),
  ];
  const blockers = [
    ...(policy.publication_enabled === true
      ? []
      : [policy.publication_blocker || "Native media publication is disabled."]),
    ...components.flatMap((component) => component.blockers),
  ];
  return {
    schema: policy.schema,
    target,
    publication_ready: blockers.length === 0,
    blockers,
    components,
  };
}

export function runNativeMediaGate(argv = process.argv.slice(2)) {
  const args = parseArguments(argv);
  const policy = loadNativeMediaPolicy(
    path.resolve(args.policy || defaultPolicyPath),
  );
  const result = evaluatePolicyReadiness(policy);
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  if (args["require-publication"] && !result.publication_ready) return 1;
  return 0;
}

if (
  process.argv[1] &&
  import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href
) {
  try {
    process.exit(runNativeMediaGate());
  } catch (error) {
    process.stderr.write(`Native media gate failed: ${String(error.stack || error)}\n`);
    process.exit(2);
  }
}
