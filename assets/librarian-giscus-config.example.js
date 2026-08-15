/*
 * Deployment-only placeholder for GitHub App-backed Giscus curation.
 * Do not invent repo/category IDs or commit a tenant-specific configuration.
 * An approved deployment may inject this object before libraries.html runs.
 */
window.AIBAST_LIBRARIAN_GISCUS_CONFIG = {
  schema: "aibast-librarian-giscus-config/1.0",
  enabled: false,
  // Configure the repository that matches the active Pages owner, for example
  // kody-w/aibast-agents-library on staging. Keep null until approved.
  repo: null,
  repo_id: null,
  source_category: "Ideas",
  source_category_id: null,
  item_category: "Announcements",
  item_category_id: null,
  mapping: "specific",
  reactions_enabled: true,
  strict: true
};
