# 💰 tokencost

[![CI](https://github.com/AbdullahTarakji/tokencost/actions/workflows/ci.yml/badge.svg)](https://github.com/AbdullahTarakji/tokencost/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Track and control your LLM API spending across OpenAI, Anthropic, Google, and Mistral — all from the terminal.**

Stop guessing how much your AI calls cost. `tokencost` gives you a CLI, a TUI dashboard, and a transparent HTTP proxy that automatically logs every API call with precise cost breakdowns.

<p align="center">
  <img src="docs/demo.gif" alt="tokencost demo" width="700">
</p>

## ✨ Features

- **📊 Interactive Dashboard** — Real-time TUI with cost charts, model breakdowns, and budget progress bars
- **🔌 Transparent Proxy** — Intercept OpenAI & Anthropic API calls automatically — zero code changes
- **📝 Manual Logging** — Track calls from any provider with a single command
- **💸 Budget Alerts** — Set daily/weekly/monthly limits, get warnings before you overspend
- **🔍 Token Estimation** — Estimate costs before making calls (tiktoken for OpenAI, heuristic for others)
- **📦 Export** — Dump history as CSV or JSON for reporting
- **🎯 Project Tracking** — Tag calls by project, see per-project breakdowns
- **🧠 21 Models** — Built-in pricing for GPT-4o, Claude, Gemini, Mistral, and more

## 📦 Installation

```bash
pip install tokencost
```

Or install from source:

```bash
git clone https://github.com/AbdullahTarakji/tokencost.git
cd tokencost
pip install -e ".[dev]"
```

## 🚀 Quick Start

### Launch the Dashboard

```bash
tokencost
```

Opens an interactive TUI with live cost summaries, model breakdowns, and bar charts.

### Log an API Call

```bash
tokencost log -m gpt-4o -i 1500 -o 500
# ✅ Logged: gpt-4o | 1500→500 tokens | $0.0088 | project=default

tokencost log -m claude-sonnet-4 -i 2000 -o 800 -p my-chatbot
# ✅ Logged: claude-sonnet-4 | 2000→800 tokens | $0.0180 | project=my-chatbot
```

### View Cost Summary

```bash
tokencost summary
# 📊 Summary (today)
#   Calls:  12
#   Tokens: 45,230
#   Cost:   $0.3421

tokencost summary -p week --json
```

### Start the Proxy

Route your API calls through `tokencost` and every request gets logged automatically:

```bash
tokencost proxy --port 8080
```

Then point your API client at `http://localhost:8080`:

```python
import openai
client = openai.OpenAI(base_url="http://localhost:8080/v1")
# All calls are now tracked automatically!
```

### Set Budgets

```bash
tokencost budget set 10.00 -p daily
tokencost budget set 50.00 -p weekly
tokencost budget status
#   daily:   $3.42 / $10.00 (34%) 🟢 OK
#   weekly:  $18.50 / $50.00 (37%) 🟢 OK
```

### Estimate Before You Call

```bash
tokencost estimate "Explain quantum computing in detail" -m gpt-4o
# 📝 Model: gpt-4o
#   Tokens: 6
#   Est. input cost: $0.000015

tokencost estimate ./large-prompt.txt -m claude-sonnet-4
```

### Export Data

```bash
tokencost export --format csv -o costs.csv
tokencost export --format json
```

### List Supported Models

```bash
tokencost models
# Model                     Provider       Input/1M   Output/1M
# ------------------------------------------------------------
# gpt-4o                    openai          $2.500     $10.000
# claude-sonnet-4           anthropic       $3.000     $15.000
# gemini-2.0-flash          google          $0.100      $0.400
# ...
```

## ⚙️ Configuration

`tokencost` uses `~/.config/tokencost/config.yaml`:

```yaml
default_project: default
proxy_port: 8080
budgets:
  daily: 10.0
  weekly: 50.0
  monthly: 200.0
custom_models:
  my-fine-tuned-gpt:
    input: 5.0
    output: 15.0
    provider: openai
```

## 🏗️ Supported Models

| Provider   | Models                                                       |
|------------|--------------------------------------------------------------|
| OpenAI     | gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-4, gpt-3.5-turbo, o1, o1-mini, o3-mini |
| Anthropic  | claude-opus-4, claude-sonnet-4, claude-3.5-sonnet, claude-3.5-haiku, claude-3-haiku |
| Google     | gemini-2.0-flash, gemini-2.0-pro, gemini-1.5-pro, gemini-1.5-flash |
| Mistral    | mistral-large, mistral-small, codestral                      |

Model names are fuzzy-matched — `GPT-4o`, `gpt_4o`, and `gpt4o` all work.

## 🧰 All Commands

| Command          | Description                              |
|------------------|------------------------------------------|
| `tokencost`      | Launch interactive dashboard             |
| `log`            | Manually log an API call                 |
| `summary`        | Show cost summary (today/week/month/all) |
| `proxy`          | Start transparent proxy server           |
| `budget set`     | Set a budget limit                       |
| `budget status`  | Show budget usage                        |
| `estimate`       | Estimate tokens and cost for text/file   |
| `models`         | List supported models with pricing       |
| `export`         | Export data as CSV or JSON               |
| `reset`          | Clear all tracked data                   |
| `version`        | Print version                            |

## 📁 Project Structure

```
tokencost/
├── src/tokencost/
│   ├── cli/          # Click commands
│   ├── config/       # YAML config management
│   ├── dashboard/    # Textual TUI app
│   ├── pricing/      # Model pricing + token estimation
│   ├── proxy/        # HTTP proxy server
│   └── tracker/      # SQLite database + aggregation
├── tests/            # 33 tests
├── docs/             # Architecture docs
└── pyproject.toml
```

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT — see [LICENSE](LICENSE).
