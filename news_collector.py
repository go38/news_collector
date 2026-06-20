#!/usr/bin/env python3
"""
Global News Collector
Fetches top news from RSS feeds and generates a beautiful HTML report.
"""

import feedparser
import os
import sys
import logging
from datetime import datetime, timezone
from pathlib import Path
from html import escape
import time
import re

# ── Configuration ──────────────────────────────────────────────────────────────

RSS_SOURCES = {
    "english": [
        {
            "name": "BBC News",
            "url": "http://feeds.bbci.co.uk/news/rss.xml",
            "category": "International",
            "lang": "en",
        },
        {
            "name": "Reuters",
            "url": "https://feeds.reuters.com/reuters/topNews",
            "category": "International",
            "lang": "en",
        },
        {
            "name": "Al Jazeera",
            "url": "https://www.aljazeera.com/xml/rss/all.xml",
            "category": "International",
            "lang": "en",
        },
        {
            "name": "AP News",
            "url": "https://rsshub.app/apnews/topics/ap-top-news",
            "category": "International",
            "lang": "en",
        },
        {
            "name": "BBC Technology",
            "url": "http://feeds.bbci.co.uk/news/technology/rss.xml",
            "category": "Technology",
            "lang": "en",
        },
        {
            "name": "BBC Business",
            "url": "http://feeds.bbci.co.uk/news/business/rss.xml",
            "category": "Finance",
            "lang": "en",
        },
        {
            "name": "BBC Sport",
            "url": "http://feeds.bbci.co.uk/sport/rss.xml",
            "category": "Sports",
            "lang": "en",
        },
        {
            "name": "BBC Science",
            "url": "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
            "category": "Science",
            "lang": "en",
        },
    ],
    "chinese": [
        {
            "name": "BBC 中文",
            "url": "https://feeds.bbci.co.uk/zhongwen/trad/rss.xml",
            "category": "國際",
            "lang": "zh",
        },
        {
            "name": "紐約時報中文",
            "url": "https://cn.nytimes.com/rss/",
            "category": "國際",
            "lang": "zh",
        },
        {
            "name": "自由時報",
            "url": "https://news.ltn.com.tw/rss/all.xml",
            "category": "台灣",
            "lang": "zh",
        },
        {
            "name": "聯合新聞網",
            "url": "https://udn.com/rssfeed/news/2/0?ch=news",
            "category": "台灣",
            "lang": "zh",
        },
    ],
}

MAX_ITEMS_PER_SOURCE = 8
REPORT_DIR = Path(__file__).parent / "reports"
REQUEST_TIMEOUT = 15

# ── Logging ────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Fetching ───────────────────────────────────────────────────────────────────


def fetch_feed(source: dict) -> list[dict]:
    """Fetch and parse a single RSS feed. Returns list of article dicts."""
    url = source["url"]
    name = source["name"]
    try:
        log.info(f"Fetching {name} ...")
        feed = feedparser.parse(url, request_headers={"User-Agent": "NewsCollector/1.0"})

        if feed.bozo and not feed.entries:
            log.warning(f"  {name}: feed parse error – {feed.bozo_exception}")
            return []

        articles = []
        for entry in feed.entries[:MAX_ITEMS_PER_SOURCE]:
            title = _clean(getattr(entry, "title", ""))
            summary = _clean_summary(getattr(entry, "summary", getattr(entry, "description", "")))
            link = getattr(entry, "link", "")
            published = _parse_date(entry)

            if not title or not link:
                continue

            articles.append(
                {
                    "title": title,
                    "summary": summary,
                    "link": link,
                    "published": published,
                    "source": name,
                    "category": source["category"],
                    "lang": source["lang"],
                }
            )

        log.info(f"  {name}: {len(articles)} articles")
        return articles

    except Exception as exc:
        log.error(f"  {name}: failed – {exc}")
        return []


def fetch_all() -> dict:
    """Fetch all sources and return grouped results."""
    results = {"english": [], "chinese": [], "stats": {}}

    for group, sources in [("english", RSS_SOURCES["english"]), ("chinese", RSS_SOURCES["chinese"])]:
        for source in sources:
            articles = fetch_feed(source)
            results[group].extend(articles)
            results["stats"][source["name"]] = len(articles)
            time.sleep(0.3)  # be polite

    return results


# ── Helpers ────────────────────────────────────────────────────────────────────

_TAG_RE = re.compile(r"<[^>]+>")
_SPACES_RE = re.compile(r"\s+")


def _clean(text: str) -> str:
    text = _TAG_RE.sub("", text)
    return _SPACES_RE.sub(" ", text).strip()


def _clean_summary(text: str) -> str:
    text = _clean(text)
    if len(text) > 280:
        text = text[:277] + "..."
    return text


def _parse_date(entry) -> str:
    now = datetime.now(timezone.utc)
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                dt = datetime(*t[:6], tzinfo=timezone.utc)
                if (now - dt).days <= 7:
                    return dt.strftime("%Y-%m-%d %H:%M UTC")
            except Exception:
                pass
    return ""


def _group_by_category(articles: list[dict]) -> dict:
    grouped = {}
    for a in articles:
        cat = a["category"]
        grouped.setdefault(cat, []).append(a)
    return grouped


# ── HTML Generation ────────────────────────────────────────────────────────────

CATEGORY_ICONS = {
    # English
    "International": "🌍",
    "Technology": "💻",
    "Finance": "📈",
    "Sports": "⚽",
    "Science": "🔬",
    # Chinese
    "國際": "🌍",
    "科技": "💻",
    "財經": "📈",
    "體育": "⚽",
    "台灣": "🇹🇼",
}

CATEGORY_COLORS = {
    "International": "#3b82f6",
    "Technology": "#8b5cf6",
    "Finance": "#10b981",
    "Sports": "#f59e0b",
    "Science": "#06b6d4",
    "國際": "#3b82f6",
    "科技": "#8b5cf6",
    "財經": "#10b981",
    "體育": "#f59e0b",
    "台灣": "#ef4444",
}


def _article_card(article: dict) -> str:
    cat_color = CATEGORY_COLORS.get(article["category"], "#6b7280")
    icon = CATEGORY_ICONS.get(article["category"], "📰")
    title = escape(article["title"])
    summary = escape(article["summary"])
    source = escape(article["source"])
    published = escape(article["published"])
    link = escape(article["link"])
    category = escape(article["category"])

    return f"""
        <article class="card">
            <div class="card-meta">
                <span class="badge" style="background:{cat_color}20;color:{cat_color};border:1px solid {cat_color}40">
                    {icon} {category}
                </span>
                <span class="source">{source}</span>
                {f'<span class="time">🕐 {published}</span>' if published else ''}
            </div>
            <h3 class="card-title">
                <a href="{link}" target="_blank" rel="noopener noreferrer">{title}</a>
            </h3>
            {f'<p class="card-summary">{summary}</p>' if summary else ''}
            <a class="read-more" href="{link}" target="_blank" rel="noopener noreferrer">Read more →</a>
        </article>"""


def _section_html(title: str, flag: str, articles: list[dict], lang_class: str) -> str:
    if not articles:
        return ""

    grouped = _group_by_category(articles)
    categories_html = ""

    for cat, items in grouped.items():
        icon = CATEGORY_ICONS.get(cat, "📰")
        color = CATEGORY_COLORS.get(cat, "#6b7280")
        cards = "\n".join(_article_card(a) for a in items)
        categories_html += f"""
        <div class="category-section">
            <h2 class="category-title" style="border-left:4px solid {color}">
                {icon} {escape(cat)}
                <span class="count" style="background:{color}20;color:{color}">{len(items)}</span>
            </h2>
            <div class="cards-grid">
                {cards}
            </div>
        </div>"""

    return f"""
    <section class="lang-section {lang_class}" id="{lang_class}">
        <div class="section-header">
            <h1 class="section-title">{flag} {escape(title)}</h1>
            <span class="total-count">{len(articles)} articles</span>
        </div>
        {categories_html}
    </section>"""


def generate_html(data: dict, generated_at: datetime) -> str:
    date_str = generated_at.strftime("%B %d, %Y")
    datetime_str = generated_at.strftime("%Y-%m-%d %H:%M UTC")
    en_articles = data["english"]
    zh_articles = data["chinese"]
    total = len(en_articles) + len(zh_articles)

    stats_items = ""
    for src, count in data["stats"].items():
        status = "ok" if count > 0 else "fail"
        stats_items += f'<span class="stat-item {status}">{escape(src)}: {count}</span>\n'

    en_section = _section_html("English News", "🌐", en_articles, "english")
    zh_section = _section_html("中文新聞", "🀄", zh_articles, "chinese")

    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Global News — {date_str}</title>
    <style>
        *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

        :root {{
            --bg: #0f172a;
            --surface: #1e293b;
            --surface2: #273449;
            --border: #334155;
            --text: #f1f5f9;
            --text-muted: #94a3b8;
            --accent: #38bdf8;
            --radius: 12px;
            --shadow: 0 4px 24px rgba(0,0,0,0.3);
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang TC",
                         "Microsoft JhengHei", sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            min-height: 100vh;
        }}

        /* ── Header ── */
        header {{
            background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0f172a 100%);
            border-bottom: 1px solid var(--border);
            padding: 2rem 1.5rem 1.5rem;
            text-align: center;
            position: sticky;
            top: 0;
            z-index: 100;
            backdrop-filter: blur(10px);
        }}
        .header-title {{
            font-size: clamp(1.5rem, 4vw, 2.5rem);
            font-weight: 800;
            background: linear-gradient(135deg, #38bdf8, #818cf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: -0.02em;
        }}
        .header-sub {{
            color: var(--text-muted);
            font-size: 0.875rem;
            margin-top: 0.25rem;
        }}
        .header-stats {{
            display: flex;
            justify-content: center;
            gap: 1.5rem;
            margin-top: 0.75rem;
            flex-wrap: wrap;
        }}
        .header-stat {{
            color: var(--text-muted);
            font-size: 0.8rem;
        }}
        .header-stat strong {{ color: var(--accent); }}

        /* ── Nav ── */
        nav {{
            background: var(--surface);
            border-bottom: 1px solid var(--border);
            padding: 0.5rem 1.5rem;
            display: flex;
            gap: 0.5rem;
            justify-content: center;
            flex-wrap: wrap;
        }}
        nav a {{
            color: var(--text-muted);
            text-decoration: none;
            padding: 0.35rem 0.9rem;
            border-radius: 20px;
            font-size: 0.85rem;
            border: 1px solid transparent;
            transition: all 0.2s;
        }}
        nav a:hover {{
            color: var(--accent);
            border-color: var(--accent);
            background: rgba(56,189,248,0.08);
        }}

        /* ── Layout ── */
        main {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem 1rem;
        }}

        /* ── Section ── */
        .lang-section {{ margin-bottom: 3rem; }}
        .section-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1.5rem;
            padding-bottom: 0.75rem;
            border-bottom: 2px solid var(--border);
        }}
        .section-title {{
            font-size: 1.5rem;
            font-weight: 700;
        }}
        .total-count {{
            background: var(--surface2);
            color: var(--text-muted);
            font-size: 0.8rem;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
        }}

        /* ── Category ── */
        .category-section {{ margin-bottom: 2rem; }}
        .category-title {{
            font-size: 1.1rem;
            font-weight: 600;
            padding: 0.5rem 1rem;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            background: var(--surface);
            border-radius: 8px;
        }}
        .count {{
            font-size: 0.75rem;
            padding: 0.15rem 0.5rem;
            border-radius: 20px;
            font-weight: 500;
            margin-left: auto;
        }}

        /* ── Cards Grid ── */
        .cards-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 1rem;
        }}

        /* ── Card ── */
        .card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 1.1rem;
            transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
            display: flex;
            flex-direction: column;
            gap: 0.6rem;
        }}
        .card:hover {{
            transform: translateY(-2px);
            box-shadow: var(--shadow);
            border-color: #4a6080;
        }}
        .card-meta {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            flex-wrap: wrap;
        }}
        .badge {{
            font-size: 0.72rem;
            padding: 0.2rem 0.55rem;
            border-radius: 20px;
            font-weight: 600;
            white-space: nowrap;
        }}
        .source {{
            color: var(--text-muted);
            font-size: 0.78rem;
            font-weight: 500;
        }}
        .time {{
            color: var(--text-muted);
            font-size: 0.75rem;
            margin-left: auto;
        }}
        .card-title {{
            font-size: 0.95rem;
            font-weight: 600;
            line-height: 1.4;
        }}
        .card-title a {{
            color: var(--text);
            text-decoration: none;
            transition: color 0.2s;
        }}
        .card-title a:hover {{ color: var(--accent); }}
        .card-summary {{
            color: var(--text-muted);
            font-size: 0.82rem;
            line-height: 1.55;
            flex: 1;
        }}
        .read-more {{
            color: var(--accent);
            text-decoration: none;
            font-size: 0.8rem;
            font-weight: 500;
            transition: opacity 0.2s;
            align-self: flex-start;
        }}
        .read-more:hover {{ opacity: 0.7; }}

        /* ── Source Stats ── */
        .stats-section {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 1rem 1.25rem;
            margin-bottom: 2rem;
        }}
        .stats-title {{
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-bottom: 0.5rem;
            font-weight: 600;
        }}
        .stats-grid {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem;
        }}
        .stat-item {{
            font-size: 0.75rem;
            padding: 0.2rem 0.6rem;
            border-radius: 20px;
        }}
        .stat-item.ok {{ background: rgba(16,185,129,0.15); color: #34d399; }}
        .stat-item.fail {{ background: rgba(239,68,68,0.15); color: #f87171; }}

        /* ── Footer ── */
        footer {{
            text-align: center;
            padding: 2rem 1rem;
            color: var(--text-muted);
            font-size: 0.8rem;
            border-top: 1px solid var(--border);
        }}

        /* ── Responsive ── */
        @media (max-width: 640px) {{
            header {{ padding: 1.25rem 1rem 1rem; position: static; }}
            .cards-grid {{ grid-template-columns: 1fr; }}
            .header-stats {{ gap: 1rem; }}
            nav {{ padding: 0.5rem 0.75rem; }}
            .time {{ display: none; }}
        }}

        /* ── Scrollbar ── */
        ::-webkit-scrollbar {{ width: 6px; }}
        ::-webkit-scrollbar-track {{ background: var(--bg); }}
        ::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: #4a6080; }}
    </style>
</head>
<body>

<header>
    <div class="header-title">📰 Global News Digest</div>
    <div class="header-sub">{datetime_str}</div>
    <div class="header-stats">
        <span class="header-stat">Total <strong>{total}</strong> articles</span>
        <span class="header-stat">English <strong>{len(en_articles)}</strong></span>
        <span class="header-stat">中文 <strong>{len(zh_articles)}</strong></span>
    </div>
</header>

<nav>
    <a href="#english">🌐 English News</a>
    <a href="#chinese">🀄 中文新聞</a>
    <a href="#sources">📊 Sources</a>
</nav>

<main>
    {en_section}
    {zh_section}

    <section id="sources">
        <div class="stats-section">
            <div class="stats-title">📊 Source Status</div>
            <div class="stats-grid">
                {stats_items}
            </div>
        </div>
    </section>
</main>

<footer>
    Generated by News Collector · {datetime_str}
    · <a href="https://github.com" style="color:inherit">GitHub</a>
</footer>

</body>
</html>"""


# ── Main ───────────────────────────────────────────────────────────────────────


def main():
    log.info("=== News Collector starting ===")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    data = fetch_all()
    total = len(data["english"]) + len(data["chinese"])
    log.info(f"Collected {total} articles total")

    if total == 0:
        log.error("No articles collected. Check network and RSS URLs.")
        sys.exit(1)

    now = datetime.now(timezone.utc)
    html = generate_html(data, now)

    dated_path = REPORT_DIR / f"news_{now.strftime('%Y-%m-%d')}.html"
    latest_path = REPORT_DIR / "latest.html"

    dated_path.write_text(html, encoding="utf-8")
    latest_path.write_text(html, encoding="utf-8")

    log.info(f"Report saved: {dated_path}")
    log.info(f"Report saved: {latest_path}")
    log.info("=== Done ===")


if __name__ == "__main__":
    main()
