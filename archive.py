#!/usr/bin/env python3
# chat-export-archive — 把 ChatGPT / Claude 匯出的 conversations.json 轉成長期可讀的 Markdown 封存。
# 只用標準庫。用法：
#   python3 archive.py conversations.json -o ./chat-archive

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def detect_format(data):
    if not isinstance(data, list) or not data:
        return None
    sample = data[:50]
    if any(isinstance(c, dict) and "mapping" in c for c in sample):
        return "chatgpt"
    if any(isinstance(c, dict) and "chat_messages" in c for c in sample):
        return "claude"
    return None


def _ts(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    if isinstance(value, str):
        normalized = re.sub(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\.(\d+)", lambda m: f"{m.group(1)}.{m.group(2)[:3]}", value)
        try:
            return datetime.fromisoformat(normalized.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def parse(data, fmt):
    convs = []
    for raw in data:
        if not isinstance(raw, dict):
            continue
        if fmt == "chatgpt":
            title = (raw.get("title") or "").strip() or "未命名對話"
            created = _ts(raw.get("create_time"))
            messages = []
            for node in (raw.get("mapping") or {}).values():
                m = (node or {}).get("message")
                if not m:
                    continue
                role = (m.get("author") or {}).get("role")
                if role not in ("user", "assistant"):
                    continue
                parts = (m.get("content") or {}).get("parts") or []
                text = "\n".join(p for p in parts if isinstance(p, str)).strip()
                if text:
                    messages.append({"role": role, "text": text})
        else:
            title = (raw.get("name") or "").strip() or "未命名對話"
            created = _ts(raw.get("created_at"))
            messages = []
            for m in raw.get("chat_messages") or []:
                role = {"human": "user", "assistant": "assistant"}.get(m.get("sender"))
                if role is None:
                    continue
                text = (m.get("text") or "").strip()
                if not text:
                    content = m.get("content")
                    if isinstance(content, list):
                        text = "\n".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text").strip()
                if text:
                    messages.append({"role": role, "text": text})
        messages.sort(key=lambda m: 0)
        if messages:
            convs.append({"title": title, "created": created, "messages": messages})
    convs.sort(key=lambda c: c["created"] or datetime.min.replace(tzinfo=timezone.utc))
    return convs


def safe_filename(title, used):
    name = re.sub(r"[\\/:*?\"<>|\x00-\x1f]", "", title).strip().rstrip(".")
    name = re.sub(r"\s+", " ", name)[:60].strip() or "未命名對話"
    base = name
    n = 2
    while name in used:
        name = f"{base} ({n})"
        n += 1
    used.add(name)
    return name


def slug(name):
    return re.sub(r"\s+", "-", name)


def archive(data, out_dir, source=""):
    fmt = detect_format(data)
    if fmt is None:
        raise SystemExit("認不出這個格式。請使用 ChatGPT 或 Claude 官方匯出的 conversations.json。")
    convs = parse(data, fmt)
    out_dir = Path(out_dir)
    used = set()
    index_rows = []
    for conv in convs:
        name = safe_filename(conv["title"], used)
        date = conv["created"]
        sub = out_dir / date.strftime("%Y") / date.strftime("%m") if date else out_dir / "unknown"
        sub.mkdir(parents=True, exist_ok=True)
        rel = sub / f"{slug(name)}.md"
        write_conversation(rel, conv, name, source)
        index_rows.append((date, name, len(conv["messages"]), rel))

    write_index(out_dir, index_rows, source, fmt)
    return len(convs)


def write_conversation(path, conv, name, source):
    lines = [f"# {name}", ""]
    if conv["created"]:
        lines.append(f"> {conv['created'].strftime('%Y-%m-%d %H:%M UTC')}・{len(conv['messages'])} 則訊息" + (f"・來源：{source}" if source else ""))
        lines.append("")
    for msg in conv["messages"]:
        who = "我" if msg["role"] == "user" else "AI"
        lines.append(f"**{who}：**")
        lines.append("")
        lines.append(msg["text"])
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_index(out_dir, rows, source, fmt):
    lines = ["# 對話封存索引", ""]
    lines.append(f"- 共 {len(rows)} 場對話（{'ChatGPT' if fmt == 'chatgpt' else 'Claude'} 匯出）")
    if source:
        lines.append(f"- 來源檔案：{source}")
    lines += ["", "| 對話 | 時間 | 訊息數 |", "| --- | --- | --- |"]
    for date, name, count, rel in reversed(rows):
        when = date.strftime("%Y-%m-%d") if date else "未知"
        relpath = rel.relative_to(out_dir).as_posix()
        lines.append(f"| [{name}]({relpath}) | {when} | {count} |")
    (out_dir / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="把 conversations.json 轉成 Markdown 封存資料夾")
    parser.add_argument("file", help="conversations.json 路徑")
    parser.add_argument("-o", "--out", default="./chat-archive", help="輸出資料夾（預設 ./chat-archive）")
    parser.add_argument("--source", default="", help="註記來源（例如 ChatGPT 或 Claude）")
    args = parser.parse_args()
    with open(args.file, "r", encoding="utf-8") as f:
        data = json.load(f)
    count = archive(data, args.out, args.source or Path(args.file).name)
    print(f"完成：{count} 場對話已寫入 {Path(args.out).resolve()}")


if __name__ == "__main__":
    main()
