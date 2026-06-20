# 📰 Global News Collector

每日自動抓取全球熱門新聞，生成美觀的 HTML 報告，涵蓋中英文媒體。

## 功能

- **多元來源**：BBC、NPR、Al Jazeera、ABC News、BBC 中文、紐約時報中文、自由時報、Yahoo 新聞
- **分類整理**：國際、科技、財經、體育、科學等
- **雙語分區**：中英文各自獨立顯示
- **美觀報告**：深色主題響應式 HTML，手機電腦皆可閱覽
- **容錯設計**：單一來源失敗不影響其他來源
- **自動部署**：GitHub Actions 每日排程執行，自動發布至 GitHub Pages

## 目錄結構

```
news_collector/
├── news_collector.py          # 主程式
├── run_news.sh                # 本機執行腳本
├── README.md                  # 本說明文件
├── .github/
│   └── workflows/
│       └── daily-news.yml     # GitHub Actions 排程設定
├── logs/                      # 執行日誌（自動建立，本機用）
└── reports/                   # HTML 報告輸出
    ├── latest.html            # 最新報告（每次覆蓋）
    └── news_YYYY-MM-DD.html   # 日期存檔
```

## 安裝（本機執行）

### 1. 安裝依賴

```bash
pip install feedparser
```

或使用虛擬環境（推薦）：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install feedparser
```

### 2. 設定執行權限

```bash
chmod +x run_news.sh
```

## 使用方式

### 本機執行

```bash
# 直接執行
python3 news_collector.py

# 使用 shell script（自動記錄日誌、自動安裝依賴）
./run_news.sh

# 執行後自動開啟瀏覽器
./run_news.sh --open
```

### 查看報告

```bash
open reports/latest.html       # macOS
xdg-open reports/latest.html   # Linux
```

## 自動排程

### GitHub Actions（推薦）

專案已內建 `.github/workflows/daily-news.yml`，每天台灣時間 07:00（UTC 23:00）自動執行，並將報告部署至 GitHub Pages。

啟用步驟：

1. 到 GitHub 儲存庫 → **Settings** → **Pages**
2. Source 選擇 **GitHub Actions**
3. 推送程式碼後，Actions 即會自動排程

手動觸發：在 **Actions** 頁面選擇 `Daily News Collection` → **Run workflow**。

---

### 本機排程（替代方案）

#### crontab（macOS / Linux）

```bash
crontab -e
```

加入（請替換為你的實際路徑）：

```cron
0 7 * * * /Users/yourname/Desktop/PlanA/news_collector/run_news.sh >> /Users/yourname/Desktop/PlanA/news_collector/cron.log 2>&1
```

#### launchd（macOS，更穩定）

建立 `~/Library/LaunchAgents/com.newscollector.plist`：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.newscollector</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/yourname/Desktop/PlanA/news_collector/run_news.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>7</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/yourname/Desktop/PlanA/news_collector/launchd.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/yourname/Desktop/PlanA/news_collector/launchd_err.log</string>
</dict>
</plist>
```

```bash
launchctl load ~/Library/LaunchAgents/com.newscollector.plist
```

## 目前 RSS 來源

### English

| 來源 | 分類 |
|---|---|
| BBC News | International |
| NPR News | International |
| Al Jazeera | International |
| ABC News | International |
| BBC Technology | Technology |
| BBC Business | Finance |
| BBC Sport | Sports |
| BBC Science | Science |

### 中文

| 來源 | 分類 |
|---|---|
| BBC 中文 | 國際 |
| 紐約時報中文 | 國際 |
| 自由時報 | 台灣 |
| Yahoo 新聞 | 台灣 |

## 新增或修改新聞來源

編輯 `news_collector.py` 中的 `RSS_SOURCES` 字典：

```python
RSS_SOURCES = {
    "english": [
        {
            "name": "My Source",
            "url": "https://example.com/feed.rss",
            "category": "Technology",   # International / Technology / Finance / Sports / Science
            "lang": "en",
        },
    ],
    "chinese": [
        {
            "name": "我的來源",
            "url": "https://example.com/feed.rss",
            "category": "科技",         # 國際 / 科技 / 財經 / 體育 / 台灣
            "lang": "zh",
        },
    ],
}
```

新增分類時，同步在 `news_collector.py` 的 `CATEGORY_ICONS` 和 `CATEGORY_COLORS` 加入對應設定。

新增來源前，建議先用 feedparser 確認 RSS 能抓到當天文章：

```python
import feedparser
feed = feedparser.parse("https://example.com/feed.rss")
print(len(feed.entries), feed.entries[0].title if feed.entries else "no entries")
```

## 常見問題

**Q: 某個來源顯示 0 articles**
A: 該 RSS 網址可能暫時無法存取，或 URL 已更改。程式會記錄警告但繼續執行，不影響其他來源。

**Q: cron 沒有執行**
A: 確認 crontab 使用絕對路徑，且 `run_news.sh` 有執行權限（`chmod +x`）。可先手動執行 `./run_news.sh` 確認正常。

**Q: 想調整每個來源抓取的則數**
A: 修改 `news_collector.py` 中的 `MAX_ITEMS_PER_SOURCE`（預設 8）。
