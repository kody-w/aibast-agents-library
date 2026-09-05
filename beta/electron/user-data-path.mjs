import path from "node:path";

export function resolveUserDataDirectory(
  value,
  {
    platform = process.platform,
  } = {},
) {
  const requested = String(value ?? "").trim();
  if (!requested) return null;
  if (requested.includes("\0")) {
    throw new Error("BRAINSTEM_BETA_USER_DATA_DIR contains a null byte.");
  }
  const paths = platform === "win32" ? path.win32 : path.posix;
  if (!paths.isAbsolute(requested)) {
    throw new Error(
      "BRAINSTEM_BETA_USER_DATA_DIR must be an absolute non-root path.",
    );
  }
  const normalized = paths.normalize(requested);
  const root = paths.parse(normalized).root;
  const comparable = platform === "win32"
    ? normalized.toLowerCase()
    : normalized;
  const comparableRoot = platform === "win32" ? root.toLowerCase() : root;
  if (comparable === comparableRoot) {
    throw new Error(
      "BRAINSTEM_BETA_USER_DATA_DIR must not be a filesystem root.",
    );
  }
  return normalized;
}
