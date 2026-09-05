import { createHash } from "node:crypto";
import {
  existsSync,
  mkdirSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";


function fail(message) {
  throw new Error(message);
}

function requiredEnvironment(name) {
  const value = String(process.env[name] || "").trim();
  if (!value) fail(`${name} is required for notarization.`);
  return value;
}

function sha256(filePath) {
  return createHash("sha256").update(readFileSync(filePath)).digest("hex");
}

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    encoding: "utf8",
    maxBuffer: 20 * 1024 * 1024,
    timeout: 30 * 60 * 1000,
    windowsHide: true,
    ...options,
  });
  if (result.status !== 0) {
    fail(
      `${command} ${args.join(" ")} failed: ` +
      `${String(result.stderr || result.stdout || result.error || "").trim()}`,
    );
  }
  return result;
}

function authorizationArguments() {
  return [
    "--key",
    requiredEnvironment("APPLE_API_KEY"),
    "--key-id",
    requiredEnvironment("APPLE_API_KEY_ID"),
    "--issuer",
    requiredEnvironment("APPLE_API_ISSUER"),
  ];
}

function codeSignature(appPath) {
  const result = run("codesign", ["-d", "--verbose=4", appPath]);
  const output = `${result.stdout || ""}\n${result.stderr || ""}`;
  const field = (name) =>
    new RegExp(`^${name}=(.+)$`, "im").exec(output)?.[1]?.trim() || null;
  return {
    identifier: field("Identifier"),
    team_id: field("TeamIdentifier"),
    cdhash: field("CDHash"),
    timestamp: field("Timestamp"),
    authorities: [
      ...output.matchAll(/^Authority=(.+)$/gim),
    ].map((match) => match[1].trim()),
    ad_hoc: /Signature=adhoc/i.test(output),
  };
}

function bundleIdentifier(appPath) {
  return run("plutil", [
    "-extract",
    "CFBundleIdentifier",
    "raw",
    "-o",
    "-",
    path.join(appPath, "Contents", "Info.plist"),
  ]).stdout.trim();
}

export async function notarizeTarget(targetPath, evidencePath) {
  if (process.platform !== "darwin") {
    fail("Apple notarization must run on macOS.");
  }
  const resolvedTarget = path.resolve(targetPath);
  const resolvedEvidence = path.resolve(evidencePath);
  if (!existsSync(resolvedTarget)) fail(`Notarization target is missing: ${resolvedTarget}`);
  mkdirSync(path.dirname(resolvedEvidence), { recursive: true });

  const extension = path.extname(resolvedTarget).toLowerCase();
  const targetType = extension === ".dmg" ? "dmg" : "app";
  const submissionPath =
    targetType === "dmg"
      ? resolvedTarget
      : `${resolvedEvidence}.submission.zip`;
  if (targetType === "app") {
    rmSync(submissionPath, { force: true });
    run(
      "ditto",
      [
        "-c",
        "-k",
        "--sequesterRsrc",
        "--keepParent",
        path.basename(resolvedTarget),
        submissionPath,
      ],
      { cwd: path.dirname(resolvedTarget) },
    );
  }

  const submittedSha256 = sha256(submissionPath);
  const submission = run("xcrun", [
    "notarytool",
    "submit",
    submissionPath,
    ...authorizationArguments(),
    "--wait",
    "--output-format",
    "json",
  ]);
  let submissionResult;
  try {
    submissionResult = JSON.parse(submission.stdout.trim());
  } catch {
    fail(`notarytool submit returned invalid JSON: ${submission.stdout}`);
  }
  if (
    submissionResult.status !== "Accepted" ||
    !submissionResult.id
  ) {
    fail(`Apple notarization was not Accepted: ${submission.stdout}`);
  }

  const logPath = `${resolvedEvidence}.log.json`;
  rmSync(logPath, { force: true });
  run("xcrun", [
    "notarytool",
    "log",
    submissionResult.id,
    logPath,
    ...authorizationArguments(),
  ]);
  const notarizationLog = JSON.parse(readFileSync(logPath, "utf8"));
  const blockingIssues = (notarizationLog.issues || []).filter(
    (issue) => String(issue.severity || "").toLowerCase() === "error",
  );
  if (
    notarizationLog.status !== "Accepted" ||
    notarizationLog.sha256?.toLowerCase() !== submittedSha256 ||
    blockingIssues.length
  ) {
    fail(`Apple notarization log is not clean: ${JSON.stringify(notarizationLog)}`);
  }

  run("xcrun", ["stapler", "staple", "-v", resolvedTarget]);
  run("xcrun", ["stapler", "validate", "-v", resolvedTarget]);
  run("codesign", ["--verify", "--deep", "--strict", "--verbose=4", resolvedTarget]);

  const signature = codeSignature(resolvedTarget);
  if (signature.ad_hoc || !signature.timestamp) {
    fail("Notarized target is ad-hoc signed or lacks a secure timestamp.");
  }
  const evidence = {
    schema:
      "https://github.com/microsoft/aibast-agents-library/frontier-notarization/v1",
    target: {
      type: targetType,
      name: path.basename(resolvedTarget),
      submitted_sha256: submittedSha256,
      stapled_sha256: targetType === "dmg" ? sha256(resolvedTarget) : null,
      bundle_id: targetType === "app" ? bundleIdentifier(resolvedTarget) : null,
      code_signature: signature,
    },
    submission: {
      id: submissionResult.id,
      status: submissionResult.status,
    },
    log: {
      name: path.basename(logPath),
      sha256: sha256(logPath),
      status: notarizationLog.status,
      issues: notarizationLog.issues || [],
    },
    stapled: true,
  };
  writeFileSync(resolvedEvidence, `${JSON.stringify(evidence, null, 2)}\n`, {
    mode: 0o600,
  });
  if (targetType === "app") rmSync(submissionPath, { force: true });
  return evidence;
}

export default async function notarizeSignedApp(context) {
  if (process.env.FRONTIER_SIGNING_MODE !== "signed") return;
  const evidencePath = requiredEnvironment(
    "FRONTIER_NOTARIZATION_APP_EVIDENCE",
  );
  const appPath = path.join(
    context.appOutDir,
    `${context.packager.appInfo.productFilename}.app`,
  );
  await notarizeTarget(appPath, evidencePath);
}
