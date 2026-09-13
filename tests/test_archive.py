import json
import tempfile
import unittest
from pathlib import Path

import archive

T = 1750000000.0  # 2025-06-15 UTC 左右

CHATGPT = [
    {
        "title": "Python pandas 問題",
        "create_time": T,
        "mapping": {
            "a": {"message": {"author": {"role": "user"}, "create_time": T, "content": {"parts": ["怎麼合併兩個 dataframe？"]}}},
            "b": {"message": {"author": {"role": "assistant"}, "create_time": T + 10, "content": {"parts": ["用 pd.merge"]}}},
            "s": {"message": {"author": {"role": "system"}, "content": {"parts": ["sys"]}}},
        },
    },
    {
        "title": '推出新產品: 會不會當掉? *測試*',
        "create_time": T + 86400,
        "mapping": {"a": {"message": {"author": {"role": "user"}, "create_time": T + 86400, "content": {"parts": ["想法"]}}}},
    },
    {
        "title": "Python pandas 問題",
        "create_time": T + 172800,
        "mapping": {"a": {"message": {"author": {"role": "user"}, "create_time": T + 172800, "content": {"parts": ["延續上題"]}}}},
    },
]

CLAUDE = [
    {
        "name": "MRT edge detection",
        "created_at": "2025-06-01T08:00:00.123456Z",
        "chat_messages": [
            {"sender": "human", "created_at": "2025-06-01T08:00:00Z", "text": "Canny 還是 Sobel？"},
            {"sender": "assistant", "created_at": "2025-06-01T08:00:30Z", "content": [{"type": "text", "text": "先試 Canny。"}]},
        ],
    }
]


class ArchiveTest(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())

    def test_detect(self):
        self.assertEqual(archive.detect_format(CHATGPT), "chatgpt")
        self.assertEqual(archive.detect_format(CLAUDE), "claude")
        self.assertIsNone(archive.detect_format([{"x": 1}]))

    def test_archive_writes_files_and_index(self):
        count = archive.archive(CHATGPT, self.dir, "ChatGPT")
        self.assertEqual(count, 3)
        index = (self.dir / "index.md").read_text(encoding="utf-8")
        self.assertIn("對話封存索引", index)
        self.assertIn("Python pandas 問題", index)
        files = list(self.dir.rglob("*.md"))
        self.assertEqual(len(files), 4)  # index + 3 conversations
        conv = next(f for f in files if f.name != "index.md" and "pandas" in f.read_text(encoding="utf-8"))
        text = conv.read_text(encoding="utf-8")
        self.assertIn("**我：**", text)
        self.assertIn("pd.merge", text)

    def test_duplicate_titles_get_suffix(self):
        count = archive.archive(CHATGPT, self.dir)
        names = [p.stem for p in self.dir.rglob("*.md") if p.name != "index.md"]
        pandas_named = [n for n in names if "pandas" in n]
        self.assertEqual(len(pandas_named), 2)
        self.assertIn("Python-pandas-問題 (2)", pandas_named)

    def test_unsafe_characters_removed(self):
        count = archive.archive(CHATGPT, self.dir)
        names = [p.stem for p in self.dir.rglob("*.md") if p.name != "index.md"]
        self.assertTrue(any(n.startswith("推出新產品") and ":" not in n and "*" not in n for n in names), names)

    def test_claude_format(self):
        count = archive.archive(CLAUDE, self.dir)
        self.assertEqual(count, 1)
        conv = next(p for p in self.dir.rglob("*.md") if p.name != "index.md")
        text = conv.read_text(encoding="utf-8")
        self.assertIn("Canny", text)
        self.assertIn("2025", text)


if __name__ == "__main__":
    unittest.main()
