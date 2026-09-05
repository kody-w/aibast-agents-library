export function artifactName({ platform, arch, version, mode }) {
  if (!["signed", "unsigned"].includes(mode)) {
    throw new Error(`Unsupported artifact signing mode: ${mode}`);
  }
  const qualifier = mode === "unsigned" ? "-unsigned" : "";
  if (platform === "macos") {
    if (!["x64", "arm64"].includes(arch)) {
      throw new Error(`Unsupported macOS artifact architecture: ${arch}`);
    }
    return `RAPP-Brainstem-Frontier-${version}-macos-${arch}${qualifier}.dmg`;
  }
  if (platform === "windows") {
    if (arch !== "x64") {
      throw new Error(`Unsupported Windows artifact architecture: ${arch}`);
    }
    return `RAPP-Brainstem-Frontier-${version}-windows-${arch}-setup${qualifier}.exe`;
  }
  throw new Error(`Unsupported artifact platform: ${platform}`);
}

export function publisherMatchesApplicationId(applicationId, identity) {
  if (!applicationId || !identity) return false;
  if (applicationId.startsWith("com.microsoft.")) {
    return /\bmicrosoft\b/i.test(identity);
  }
  return true;
}
