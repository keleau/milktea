"""生成桌码 PNG、可打印页面和清单。

用法：
    python database/build_table_qrcodes.py
    python database/build_table_qrcodes.py --out static/qrcodes --clean

桌码内容约定：MILKTEA:<门店id>:<桌号>
前端用 uni.scanCode 扫到字符串后按 ":" 拆开，还原门店和桌号。
"""

from __future__ import annotations

import argparse
import csv
import html
import sqlite3
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

FASTAPI_DIR = Path(__file__).resolve().parent.parent
DEFAULT_OUT = FASTAPI_DIR / "static" / "qrcodes"
DEFAULT_DB = Path(__file__).resolve().parent / "milktea.db"
SCENE_PREFIX = "MILKTEA"

# 门店 id → 桌号；改完重新运行脚本即可
TABLES: dict[int, list[str]] = {
    1: [f"A{i:02d}" for i in range(1, 9)],
    2: [f"B{i:02d}" for i in range(1, 7)],
    3: [f"C{i:02d}" for i in range(1, 9)],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成四猫茶学园桌码")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="输出目录")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="读取门店名的 SQLite 数据库")
    parser.add_argument("--clean", action="store_true", help="先删除旧的桌码、打印页和清单")
    return parser.parse_args()


def load_store_names(db_path: Path) -> dict[int, str]:
    if not db_path.is_file():
        print(f"[WARN] 数据库不存在，门店名用默认值：{db_path}")
        return {}
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("SELECT id, name FROM stores").fetchall()
    finally:
        conn.close()
    return {int(store_id): name for store_id, name in rows}


def scene_of(store_id: int, table_no: str) -> str:
    return f"{SCENE_PREFIX}:{store_id}:{table_no}"


def clean_outputs(out_dir: Path) -> None:
    for path in out_dir.glob("store*_*.png"):
        path.unlink()
    for name in ("print.html", "manifest.csv"):
        target = out_dir / name
        if target.exists():
            target.unlink()


def render_print_page(rows: list[dict]) -> str:
    cards = []
    for row in rows:
        cards.append(
            f"""
        <div class="card">
            <img src="./{html.escape(row['file'])}" alt="{html.escape(row['scene'])}">
            <div class="store">{html.escape(row['store_name'])}</div>
            <div class="table">{html.escape(row['table_no'])} 桌</div>
            <div class="scene">{html.escape(row['scene'])}</div>
        </div>"""
        )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>四猫茶学园 桌码</title>
<style>
    body {{ margin: 0; padding: 24px; font-family: "Microsoft YaHei", sans-serif; background: #fff; }}
    h1 {{ font-size: 22px; text-align: center; margin: 0 0 8px; }}
    .tip {{ text-align: center; color: #777; font-size: 13px; margin-bottom: 24px; }}
    .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 18px; }}
    .card {{ border: 1px dashed #ccc; border-radius: 12px; padding: 14px; text-align: center; break-inside: avoid; }}
    .card img {{ width: 100%; max-width: 180px; height: auto; }}
    .store {{ font-size: 13px; color: #666; margin-top: 6px; }}
    .table {{ font-size: 20px; font-weight: bold; margin: 2px 0; }}
    .scene {{ font-size: 11px; color: #aaa; letter-spacing: 1px; }}
    @media print {{
        body {{ padding: 0; }}
        .tip {{ display: none; }}
        .grid {{ gap: 10px; }}
    }}
</style>
</head>
<body>
<h1>四猫茶学园 桌码</h1>
<div class="tip">打印后贴在桌面；顾客在小程序里点「扫码点餐」扫描</div>
<div class="grid">{''.join(cards)}
</div>
</body>
</html>
"""


def build(out_dir: Path, db_path: Path, clean: bool) -> None:
    try:
        import segno  # noqa: F401
    except ImportError:
        raise SystemExit("缺少 segno，请先运行：pip install -r requirements.txt")

    out_dir.mkdir(parents=True, exist_ok=True)
    if clean:
        clean_outputs(out_dir)

    store_names = load_store_names(db_path)
    rows: list[dict] = []

    for store_id, table_nos in TABLES.items():
        store_name = store_names.get(store_id, f"门店 {store_id}")
        for table_no in table_nos:
            scene = scene_of(store_id, table_no)
            filename = f"store{store_id}_{table_no}.png"
            segno.make(scene, error="m").save(
                out_dir / filename, scale=20, border=4, dark="#000000", light="#ffffff"
            )
            rows.append(
                {
                    "store_id": store_id,
                    "store_name": store_name,
                    "table_no": table_no,
                    "scene": scene,
                    "file": filename,
                }
            )

    with (out_dir / "manifest.csv").open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=["store_id", "store_name", "table_no", "scene", "file"])
        writer.writeheader()
        writer.writerows(rows)

    (out_dir / "print.html").write_text(render_print_page(rows), encoding="utf-8")

    missing = [row["file"] for row in rows if not (out_dir / row["file"]).is_file()]
    if missing:
        raise SystemExit(f"[FAIL] 有 {len(missing)} 张桌码没生成成功：{missing[:3]}")

    print(f"[OK] 门店 {len(TABLES)} 个，桌码 {len(rows)} 张")
    print(f"[OK] 输出目录：{out_dir}")
    print(f"[OK] 打印页面：{out_dir / 'print.html'}")
    print(f"[OK] 清单文件：{out_dir / 'manifest.csv'}")
    print(f"[INFO] 内容格式：{SCENE_PREFIX}:<门店id>:<桌号>，例如 {rows[0]['scene']}")


def main() -> None:
    args = parse_args()
    build(args.out, args.db, args.clean)


if __name__ == "__main__":
    main()
