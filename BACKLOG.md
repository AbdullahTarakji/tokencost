# BACKLOG — tokencost

## Current Sprint: P0 — Full Feature Build

### Pricing Engine (src/tokencost/pricing/)
- [ ] TC-01: Pricing database — cost per 1M input/output tokens per model
- [ ] TC-02: OpenAI models (gpt-4o, gpt-4o-mini, gpt-4-turbo, o1, o3-mini, etc.)
- [ ] TC-03: Anthropic models (claude-opus-4, claude-sonnet-4, haiku, etc.)
- [ ] TC-04: Google models (gemini-2.0-flash, gemini-2.0-pro, etc.)
- [ ] TC-05: Mistral models (mistral-large, mistral-small, codestral)
- [ ] TC-06: Auto-update pricing from provider APIs/docs
- [ ] TC-07: Custom model pricing via config

### Cost Tracker (src/tokencost/tracker/)
- [ ] TC-08: SQLite database for storing API call records
- [ ] TC-09: Record: timestamp, provider, model, input_tokens, output_tokens, cost, project, tags
- [ ] TC-10: Per-project cost tracking with project tags
- [ ] TC-11: Aggregation queries: daily/weekly/monthly totals, per-model, per-project
- [ ] TC-12: Budget system: set daily/weekly/monthly limits, get alerts
- [ ] TC-13: Export to CSV/JSON

### Proxy Mode (src/tokencost/proxy/)
- [ ] TC-14: HTTP proxy server (intercept OpenAI/Anthropic API calls)
- [ ] TC-15: Parse response headers/body for token usage
- [ ] TC-16: Transparent passthrough — no modification of requests/responses
- [ ] TC-17: Support OpenAI API format (chat completions, embeddings)
- [ ] TC-18: Support Anthropic API format (messages)
- [ ] TC-19: Auto-calculate cost from response token counts

### TUI Dashboard (src/tokencost/dashboard/)
- [ ] TC-20: Rich/Textual-based TUI dashboard
- [ ] TC-21: Summary panel: total cost today/week/month/all-time
- [ ] TC-22: Per-model breakdown table
- [ ] TC-23: Per-project breakdown table
- [ ] TC-24: Daily cost trend (sparkline/bar chart)
- [ ] TC-25: Budget status with progress bars
- [ ] TC-26: Live mode — auto-refresh when proxy logs new calls
- [ ] TC-27: Date range filtering

### CLI Commands (src/tokencost/cli/)
- [ ] TC-28: `tokencost` — launch TUI dashboard
- [ ] TC-29: `tokencost log` — manually log an API call
- [ ] TC-30: `tokencost summary` — print cost summary to stdout
- [ ] TC-31: `tokencost proxy` — start the proxy server
- [ ] TC-32: `tokencost budget set <amount> --period <daily|weekly|monthly>`
- [ ] TC-33: `tokencost budget status` — show budget utilization
- [ ] TC-34: `tokencost export --format csv|json`
- [ ] TC-35: `tokencost estimate <prompt>` — estimate cost without calling API
- [ ] TC-36: `tokencost models` — list supported models with pricing
- [ ] TC-37: `tokencost reset` — clear tracking data
- [ ] TC-38: `tokencost version`

### Config (src/tokencost/config/)
- [ ] TC-39: Config file (~/.tokencost/config.yaml)
- [ ] TC-40: Database location, default project, budget settings
- [ ] TC-41: Custom model pricing overrides

### Token Estimation (src/tokencost/pricing/)
- [ ] TC-42: Estimate tokens from text (tiktoken for OpenAI, approximation for others)
- [ ] TC-43: Pre-call cost estimation

## P1 — Documentation & CI
- [ ] TC-44: README.md with demo GIF
- [ ] TC-45: CONTRIBUTING.md
- [ ] TC-46: CHANGELOG.md
- [ ] TC-47: GitHub Actions CI (lint, test, build)
- [ ] TC-48: GitHub issue templates
- [ ] TC-49: docs/ARCHITECTURE.md
- [ ] TC-50: PyPI packaging (pyproject.toml)
- [ ] TC-51: Demo GIF with VHS

## P2 — Nice to Have
- [ ] TC-52: OpenRouter support
- [ ] TC-53: Groq support
- [ ] TC-54: Webhook notifications for budget alerts
- [ ] TC-55: Web dashboard alternative
- [ ] TC-56: Homebrew tap
