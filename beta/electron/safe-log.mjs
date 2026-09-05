import { writeSync } from "node:fs";

const REDACTION = "[REDACTED]";
const SENSITIVE_KEYS = new Set([
  "accesstoken",
  "apikey",
  "authorization",
  "clientsecret",
  "githubtoken",
  "ghtoken",
  "password",
  "refreshtoken",
  "secret",
  "token",
]);

function sensitiveKey(key) {
  return SENSITIVE_KEYS.has(
    String(key || "").toLowerCase().replace(/[^a-z0-9]/g, ""),
  );
}

function scrubText(value) {
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
      /(["']?(?:ACCESS_?TOKEN|API_?KEY|CLIENT_?SECRET|GITHUB_TOKEN|GH_TOKEN|PASSWORD|REFRESH_?TOKEN|SECRET|TOKEN)["']?\s*[=:]\s*)("(?:\\.|[^"])*"|'(?:\\.|[^'])*'|[^\s,}]+)/gi,
      (_match, prefix, assigned) => {
        const quote = assigned.startsWith('"')
          ? '"'
          : assigned.startsWith("'")
            ? "'"
            : "";
        return `${prefix}${quote}${REDACTION}${quote}`;
      },
    )
    .replace(
      /(https?:\/\/)([^/\s:@]+):([^@\s/]+)@/gi,
      `$1${REDACTION}:${REDACTION}@`,
    );
}

export function sanitizeTelemetryValue(value, key = "") {
  if (sensitiveKey(key) && value !== null && value !== undefined) {
    return REDACTION;
  }
  if (Array.isArray(value)) {
    return value.map((item) => sanitizeTelemetryValue(item));
  }
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([childKey, childValue]) => [
        childKey,
        sanitizeTelemetryValue(childValue, childKey),
      ]),
    );
  }
  return typeof value === "string" ? scrubText(value) : value;
}

export function scrubSecrets(value) {
  const text = String(value ?? "");
  const trimmed = text.trim();
  if (trimmed) {
    try {
      const parsed = JSON.parse(trimmed);
      const leading = text.slice(0, text.indexOf(trimmed));
      const trailing = text.slice(text.indexOf(trimmed) + trimmed.length);
      return `${leading}${JSON.stringify(sanitizeTelemetryValue(parsed))}${trailing}`;
    } catch {}
  }
  return scrubText(text);
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
