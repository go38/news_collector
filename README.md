# 📰 Global News Collector

每日自動抓取全球熱門新聞，生成美觀的 HTML 報告，涵蓋中英文媒體。

## 功能

- **多元來源**：BBC、Reuters、CNN、AP、BBC 中文、紐約時報中文、自由時報、聯合新聞網
- **分類整理**：國際、科技、財經、體育、科學等
- **雙語分區**：中英文各自獨立顯示
- **美觀報告**：深色主題響應式 HTML，手機電腦皆可閱覽
- **容錯設計**：單一來源失敗不影響其他來源

## 目錄結構

```
news_collector/
├── news_collector.py   # 主程式
├── run_news.sh         # 執行腳本
├── README.md           # 本說明文件
├── logs/               # 執行日誌（自動建立）
└── reports/            # HTML 報告輸出
    ├── latest.html     # 最新報告（每次覆蓋）
    └── news_YYYY-MM-DD.html
```

## 安裝

### 1. 安裝依賴

```bash
pip install feedparser
```

或使用虛擬環境（推薦）：

```bash
cd news_collector
python3 -m venv .venv
source .venv/bin/activate
pip install feedparser
```

### 2. 設定執行權限

```bash
chmod +x run_news.sh
```

## 使用方式

### 直接執行

```bash
# 執行並產生報告
python3 news_collector.py

# 使用 shell script（含日誌記錄）
./run_news.sh

# 執行後自動開啟瀏覽器
./run_news.sh --open
```

### 查看報告

```bash
open reports/latest.html       # macOS
xdg-open reports/latest.html   # Linux
```

## 排程設定（每天早上 7:00 自動執行）

### macOS / Linux — crontab

```bash
# 編輯排程
crontab -e
```

加入以下行（請換成你的實際路徑）：

```cron
0 7 * * * /Users/yourname/Desktop/PlanA/news_collector/run_news.sh >> /Users/yourname/Desktop/PlanA/news_collector/cron.log 2>&1
```

確認排程已加入：

```bash
crontab -l
```

### macOS — launchd（更穩定，推薦）

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

載入排程：

```bash
launchctl load ~/Library/LaunchAgents/com.newscollector.plist
```

手動觸發測試：

```bash
launchctl start com.newscollector
```

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
        # ...
    ],
    "chinese": [
        {
            "name": "我的來源",
            "url": "https://example.com/feed.rss",
            "category": "科技",         # 國際 / 科技 / 財經 / 體育 / 台灣
            "lang": "zh",
        },
        # ...
    ],
}
```

## 常見問題

**Q: 某個來源顯示 0 articles**
A: 該 RSS 網址可能暫時無法存取，或 URL 已更改。程式會記錄警告但繼續執行，不影響其他來源。

**Q: cron 沒有執行**
A: 確認 crontab 路徑為絕對路徑，且 run_news.sh 有執行權限 (`chmod +x`)。可先手動執行 `./run_news.sh` 確認正常。

**Q: 想調整每個來源抓取的則數**
A: 修改 `news_collector.py` 中的 `MAX_ITEMS_PER_SOURCE`（預設 8）。
