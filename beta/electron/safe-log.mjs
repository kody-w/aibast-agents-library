import { writeSync } from "node:fs";

const REDACTION = "[REDACTED]";

export function scrubSecrets(value) {
  return String(value ?? "")
    .replace(
      /\b(?:gh[pousr]_[A-Za-z0-9_]{8,}|github_pat_[A-Za-z0-9_]{8,})\b/g,
      REDACTION,
    )
    .replace(
      /\b(Bearer|token)\s+[A-Za-z0-9._~+/-]{8,}/gi,
      `$1 ${REDACTION}`,
    )
    .replace(
      /\b((?:ACCESS_?TOKEN|API_?KEY|CLIENT_?SECRET|GITHUB_TOKEN|GH_TOKEN|PASSWORD|REFRESH_?TOKEN|SECRET)\s*[=:]\s*)[^\s"']+/gi,
      `$1${REDACTION}`,
    )
    .replace(
      /(https?:\/\/)([^/\s:@]+):([^@\s/]+)@/gi,
      `$1${REDACTION}:${REDACTION}@`,
    );
}

export function attachScrubbedLog(stream, logFd) {
  if (!stream) return () => {};
  stream.setEncoding("utf8");
  let pending = "";
  const flushLines = (final = false) => {
    if (final) {
      if (pending) writeSync(logFd, scrubSecrets(pending));
      pending = "";
      return;
    }
    const lines = pending.split(/\n/);
    pending = lines.pop() || "";
    for (const line of lines) {
      writeSync(logFd, `${scrubSecrets(line)}\n`);
    }
  };
  const onData = (chunk) => {
    pending += chunk;
    flushLines(false);
  };
  const onEnd = () => flushLines(true);
  stream.on("data", onData);
  stream.on("end", onEnd);
  return () => {
    stream.off("data", onData);
    stream.off("end", onEnd);
    flushLines(true);
  };
}
