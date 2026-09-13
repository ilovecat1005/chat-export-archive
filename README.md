# chat-export-archive

把 ChatGPT 或 Claude 官方匯出的 `conversations.json` 轉成一個排版好的 Markdown 資料夾——按年月分類、一場對話一個檔案、附索引。轉出來的東西離線可讀、可以進 git、之後想餵給其他工具也方便。

只用 Python 標準庫，没有依賴。

## 使用

```bash
python3 archive.py /path/to/conversations.json -o ./chat-archive
```

輸出結構：

```
chat-archive/
├── index.md                  # 全部對話的索引（標題連結、日期、訊息數）
├── 2025/
│   ├── 06/
│   │   ├── Python-pandas-問題.md
│   │   └── MRT-edge-detection.md
│   └── 07/
│       └── ...
```

每個對話檔內含日期、訊息數，訊息以「**我：**／**AI：**」分段。標題重複會自動加編號，檔名會清掉作業系統不允許的字元。

## 怎麼拿到匯出檔

- ChatGPT：設定 → Data controls → Export data
- Claude：設定 → Privacy → Export data

## 已知限制

- 圖片、附件、canvas 等非文字內容不會被輸出（匯出檔裡本來就不含實體檔案）
- 時間以 UTC 記錄
- 只支援官方匯出格式

## 開發

```bash
python3 -m unittest discover -s tests -v
```

## 授權

MIT
