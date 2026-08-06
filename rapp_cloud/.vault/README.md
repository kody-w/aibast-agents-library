# CommunityRAPP Local Vault

> **This is your personal workspace.** Content here is gitignored — only the folder structure and templates ship with the repo.

## What Is This?

An [Obsidian](https://obsidian.md) vault baked into CommunityRAPP. Open this folder (`.vault/`) as a vault in Obsidian and you get an organized local workspace for all your project-specific content — the stuff that doesn't belong in the community repo.

## Folder Structure

| Folder | Purpose | Examples |
|--------|---------|---------|
| `projects/` | RAPP pipeline project workspaces | Discovery notes, MVP docs, quality gate results |
| `customers/` | Customer-specific context | Meeting notes, org charts, requirements |
| `transcripts/` | Raw call transcripts & recordings | Discovery calls, feedback sessions |
| `demos/` | Customer-specific demo content | Custom demo scripts, screenshots, recordings |
| `transpiled/` | Generated Copilot Studio artifacts | Solution ZIPs, transpiler output |
| `deployments/` | Your deployment configs & logs | Resource names, endpoints, deploy history |
| `scratch/` | Temporary working notes | Ideas, debugging notes, quick captures |

## Quick Start

1. Install [Obsidian](https://obsidian.md) (free)
2. Open Vault → select this `.vault/` folder
3. Start writing — everything stays local

## How It Works

- **Templates** (files starting with `_template_`) are committed to the repo so every community user gets the same starting structure
- **Your actual notes** are gitignored — write freely
- **Folder READMEs** explain what goes where — these are committed too
- The `.obsidian/` config ships with sensible defaults

## Integration with RAPP Pipeline

When you run `transcript_to_agent` or `auto_process`, point output to your vault:

```
# Your RAPP project data lives here, not in the repo root
.vault/projects/acme-corp/
├── inputs/
│   └── discovery_transcript.txt
├── outputs/
│   ├── agent_code.py
│   └── demo.json
└── notes.md
```

## The Rule

> **Committed:** Structure, templates, READMEs, Obsidian config
> **Gitignored:** Everything else — your notes, data, transcripts, output
