# Connectors and Tools Audit

| Capability | Used for | Notes |
|---|---|---|
| Bash, Python 3.12 venv, uv | All development, data and ML work | — |
| Network to Hugging Face | Dataset download | Needed a dedicated environment allowlist (`huggingface.co`, `us.aws.cdn.hf.co` and related hosts), approved by the user |
| GitHub (git push) | Version control on branch `claude/hopeful-noether-t6vfi7` | No pull request created |
| Google Drive connector | Searched for the HW PDFs (not found); the PDFs were later uploaded to the session | Read-only search |
| Playwright + Chromium (preinstalled) | Real-browser UX validation and screenshots | — |
| Other MCP connectors (Gmail, Figma, Vercel and others) | Not used | Irrelevant to the task |

No transaction data was sent to any external service. No paid service was used.
