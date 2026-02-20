# Architecture

## Components

```
┌─────────────────────────────────────────────────┐
│                   CLI (Click)                    │
│  log │ summary │ proxy │ budget │ estimate │ ... │
└──────────┬──────────────────────────┬────────────┘
           │                          │
     ┌─────▼─────┐            ┌──────▼──────┐
     │  Tracker   │            │  Dashboard  │
     │  (SQLite)  │◄───────── │  (Textual)  │
     └─────┬──────┘            └─────────────┘
           │
     ┌─────▼──────┐     ┌──────────────┐
     │ Aggregator  │     │    Proxy     │
     │ (summaries) │     │  (aiohttp)   │──► OpenAI/Anthropic APIs
     └─────┬──────┘     └──────┬───────┘
           │                    │
     ┌─────▼────────────────────▼──────┐
     │         Pricing Engine          │
     │  models.py │ estimator.py       │
     │  21 models │ fuzzy match        │
     │  tiktoken  │ len/4 fallback     │
     └────────────────────────────────┘
```

## Data Flow

1. **Manual logging**: CLI → Pricing → Tracker (SQLite)
2. **Proxy logging**: HTTP request → Proxy intercepts → Pricing → Tracker
3. **Dashboard**: Aggregator reads Tracker → renders TUI
4. **Estimation**: Text → tiktoken/heuristic → Pricing → cost

## Storage

- **Database**: `~/.local/share/tokencost/costs.db` (SQLite)
- **Config**: `~/.config/tokencost/config.yaml` (YAML)

## Key Design Decisions

- **SQLite over files**: Structured queries, aggregation, no parsing overhead
- **Fuzzy model matching**: Developers use inconsistent model names
- **tiktoken + fallback**: Precise for OpenAI, `len/4` approximation for others
- **Transparent proxy**: Zero code changes in existing apps — just change `base_url`
