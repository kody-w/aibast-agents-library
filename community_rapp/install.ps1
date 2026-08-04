# COMPATIBILITY STUB — this path is preserved so existing links keep working.
# The Tier-2 cloud installer now lives at rapp_cloud/install.ps1 (RAPP Cloud).
Write-Host "[community_rapp] This installer has moved to rapp_cloud/ (RAPP Cloud). Continuing with the current installer..."
irm https://raw.githubusercontent.com/microsoft/aibast-agents-library/main/rapp_cloud/install.ps1 | iex
