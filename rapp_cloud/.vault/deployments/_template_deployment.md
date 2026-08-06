---
environment: dev | staging | production
function_app: 
resource_group: 
storage_account: 
openai_resource: 
openai_model: 
region: 
last_deployed: {{date}}
---

# {{environment}} Deployment

## Resources

| Resource | Name | Region |
|----------|------|--------|
| Function App | `YOUR_FUNCTION_APP` | |
| Resource Group | `YOUR_RESOURCE_GROUP` | |
| Storage Account | `YOUR_STORAGE_ACCOUNT` | |
| Azure OpenAI | `YOUR_OPENAI_RESOURCE` | |
| OpenAI Model | `gpt-4o` | — |

## Endpoints

```
API: https://YOUR_FUNCTION_APP.azurewebsites.net/api/businessinsightbot_function
```

## Quick Commands

```bash
# Deploy
func azure functionapp publish YOUR_FUNCTION_APP --build remote

# Restart
az functionapp restart --name YOUR_FUNCTION_APP --resource-group YOUR_RESOURCE_GROUP

# Get function key
az functionapp keys list --name YOUR_FUNCTION_APP --resource-group YOUR_RESOURCE_GROUP --query "functionKeys.default" -o tsv
```

## Deploy History

| Date | What Changed | Notes |
|------|-------------|-------|
|      |             |       |
