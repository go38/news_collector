# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the collector

```bash
# Direct run (requires feedparser)
python3 news_collector.py

# Via shell wrapper (handles venv activation, logging, auto-installs feedparser)
./run_news.sh

# Run and open the report in the browser
./run_news.sh --open

# View the generated report
open reports/latest.html
```

## Dependency

Single external dependency: `feedparser`. Install with `pip install feedparser` or let `run_news.sh` auto-install it. A `.venv/` virtualenv in the project root is auto-activated by the shell script if present.

## Architecture

Everything lives in `news_collector.py` — one file, no framework:

1. **`RSS_SOURCES`** (top of file) — dict with `"english"` and `"chinese"` lists, each entry being `{name, url, category, lang}`. This is the only place to add/remove sources.
2. **`fetch_feed(source)`** → calls `feedparser.parse`, returns list of article dicts. Errors per-source are caught and logged; they don't abort the run.
3. **`fetch_all()`** → iterates all sources in both groups, aggregates results into `{english: [...], chinese: [...], stats: {source_name: count}}`.
4. **`generate_html(data, generated_at)`** → builds a self-contained HTML string with inline CSS (dark theme). Calls `_section_html` for each language group, which calls `_group_by_category` then `_article_card` per article.
5. **`main()`** → orchestrates fetch → generate → write two files: `reports/news_YYYY-MM-DD.html` and `reports/latest.html`.

## Key constants

| Constant | Default | Purpose |
|---|---|---|
| `MAX_ITEMS_PER_SOURCE` | 8 | Articles fetched per RSS feed |
| `REQUEST_TIMEOUT` | 15 | Seconds (passed to feedparser) |
| `REPORT_DIR` | `./reports/` | Output directory |

## Output

- `reports/latest.html` — always overwritten with the newest run
- `reports/news_YYYY-MM-DD.html` — date-stamped archive copy
- `logs/run_TIMESTAMP.log` — created by `run_news.sh`; only the 30 most recent logs are kept

## Adding categories

Add a new category string in `RSS_SOURCES`, then add matching entries to `CATEGORY_ICONS` and `CATEGORY_COLORS` in the HTML generation section so the new category renders with a color and icon.
