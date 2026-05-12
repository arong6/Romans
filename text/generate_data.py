#!/usr/bin/env python3
"""扫描 txt 和 audio 目录 -> 按日期配对 -> 嵌入 index.html"""

import json, re
from pathlib import Path

BASE = Path(__file__).parent.resolve()
TXT_DIR = BASE / "txt"
AUDIO_DIR = BASE / "audio"
INDEX_TEMPLATE = BASE / "index.html"
INDEX_TEMPLATE_DEV = BASE / "index.template.html"


def date_key(name: str) -> str:
    m = re.match(r"(\d{4}-\d{2}-\d{2})", name)
    return m.group(1) if m else ""


def extract_title(name: str) -> str:
    rest = re.sub(r"^\d{4}-\d{2}-\d{2}[—一]\s*", "", name)
    rest = re.sub(r"\.(txt|mp3)$", "", rest)
    return rest.strip()


def build_entries() -> list[dict]:
    txt_map, audio_map = {}, {}
    for f in sorted(TXT_DIR.glob("*.txt")):
        k = date_key(f.name)
        if k: txt_map[k] = f
    for f in sorted(AUDIO_DIR.glob("*.mp3")):
        k = date_key(f.name)
        if k: audio_map[k] = f

    entries = []
    for d in sorted(set(txt_map) | set(audio_map)):
        tp, ap = txt_map.get(d), audio_map.get(d)
        if not tp or not ap:
            print(f"⚠ 日期 {d}: 缺少 {'txt' if not tp else 'audio'} 文件")
            continue
        entries.append({
            "date": d,
            "title": extract_title(tp.name),
            "txt_file": tp.name,
            "audio_file": ap.name,
            "content": tp.read_text("utf-8"),
        })
    return entries


def inject_data(html: str, entries: list[dict]) -> str:
    json_str = json.dumps(entries, ensure_ascii=False)
    placeholder = "/* ROM_DATA_PLACEHOLDER */"
    if placeholder not in html:
        raise RuntimeError(f"在 index.html 中未找到占位符 {placeholder}")
    return html.replace(placeholder, json_str)


def main():
    entries = build_entries()

    # 使用开发模板（如果存在），否则用 index.html 自身
    tmpl_path = INDEX_TEMPLATE_DEV if INDEX_TEMPLATE_DEV.exists() else INDEX_TEMPLATE
    html = tmpl_path.read_text("utf-8")
    html = inject_data(html, entries)

    INDEX_TEMPLATE.write_text(html, "utf-8")
    # 同时保留 data.json 供调试参考
    (BASE / "data.json").write_text(
        json.dumps(entries, ensure_ascii=False, indent=2), "utf-8"
    )
    print(f"✅ 已更新 {INDEX_TEMPLATE.name} 和 data.json")
    print(f"   共 {len(entries)} 条记录内嵌")


if __name__ == "__main__":
    main()
