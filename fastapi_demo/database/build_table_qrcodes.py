"""生成桌码、可打印页面和清单。

用法：
    # 应用内扫码用的普通二维码（默认，不需要 AppID）
    python database/build_table_qrcodes.py
    python database/build_table_qrcodes.py --out static/qrcodes --clean

    # 微信「扫一扫」直达小程序点单页的小程序码（需要 .env 配好 AppID/Secret）
    python database/build_table_qrcodes.py --mode wechat --env trial --clean

桌码内容约定：MILKTEA:<门店id>:<桌号>
普通二维码：门店/桌号直接写在二维码内容里，小程序内 uni.scanCode 读取。
小程序码：内容放在 scene 参数里，微信扫码后由小程序 onLoad(options.scene) 读取。
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

if str(FASTAPI_DIR) not in sys.path:
    sys.path.insert(0, str(FASTAPI_DIR))

from app.tables import DINING_TABLES, SCENE_PREFIX, scene_of  # noqa: E402



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成四猫茶学园桌码")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="输出目录")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="读取门店名的 SQLite 数据库")
    parser.add_argument("--clean", action="store_true", help="先删除旧的桌码、打印页和清单")
    parser.add_argument(
        "--mode",
        choices=["plain", "wechat"],
        default="plain",
        help="plain=普通二维码（小程序内扫码）；wechat=微信扫一扫直达的小程序码",
    )
    parser.add_argument(
        "--env",
        choices=["release", "trial", "develop"],
        default="trial",
        help="小程序码打开的版本，默认 trial（体验版）；上线打印时改 release",
    )
    parser.add_argument(
        "--page",
        default="pages/menu/index",
        help="扫码后打开的小程序页面（不能以 / 开头）",
    )
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


def clean_outputs(out_dir: Path) -> None:
    for pattern in ("store*_*.png", "store*_*.jpg"):
        for path in out_dir.glob(pattern):
            path.unlink()
    for name in ("print.html", "manifest.csv"):
        target = out_dir / name
        if target.exists():
            target.unlink()


def render_print_page(rows: list[dict], tip: str) -> str:
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
<div class="tip">{html.escape(tip)}</div>
<div class="grid">{''.join(cards)}
</div>
</body>
</html>
"""


def build(
    out_dir: Path,
    db_path: Path,
    clean: bool,
    mode: str = "plain",
    env: str = "trial",
    page: str = "pages/menu/index",
) -> None:
    if mode == "plain":
        try:
            import segno
        except ImportError:
            raise SystemExit("缺少 segno，请先运行：pip install -r requirements.txt")
        tip = "打印后贴在桌面；顾客在小程序里点「扫码点餐」扫描"
    else:
        from app.services.wechat import WeChatError, fetch_wxa_code, image_ext

        env_name = {"release": "正式版", "trial": "体验版", "develop": "开发版"}[env]
        if env == "release":
            tip = "打印后贴在桌面；顾客用微信「扫一扫」直接打开点单页"
        else:
            tip = f"打印后贴在桌面；开发者/体验成员用微信「扫一扫」直接打开{env_name}点单页"

    out_dir.mkdir(parents=True, exist_ok=True)
    if clean:
        clean_outputs(out_dir)

    store_names = load_store_names(db_path)
    rows: list[dict] = []

    for store_id, table_nos in DINING_TABLES.items():
        store_name = store_names.get(store_id, f"门店 {store_id}")
        for table_no in table_nos:
            scene = scene_of(store_id, table_no)
            if mode == "wechat":
                try:
                    image = fetch_wxa_code(scene, page=page, env_version=env)
                except WeChatError as exc:
                    raise SystemExit(f"[FAIL] {scene}：{exc}") from exc
                filename = f"store{store_id}_{table_no}.{image_ext(image)}"
                (out_dir / filename).write_bytes(image)
            else:
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

    (out_dir / "print.html").write_text(render_print_page(rows, tip), encoding="utf-8")

    missing = [row["file"] for row in rows if not (out_dir / row["file"]).is_file()]
    if missing:
        raise SystemExit(f"[FAIL] 有 {len(missing)} 张桌码没生成成功：{missing[:3]}")

    print(f"[OK] 门店 {len(DINING_TABLES)} 个，桌码 {len(rows)} 张（{mode}）")
    print(f"[OK] 输出目录：{out_dir}")
    print(f"[OK] 打印页面：{out_dir / 'print.html'}")
    print(f"[OK] 清单文件：{out_dir / 'manifest.csv'}")
    print(f"[INFO] 内容格式：{SCENE_PREFIX}:<门店id>:<桌号>，例如 {rows[0]['scene']}")
    if mode == "wechat" and env != "release":
        print(f"[INFO] {env} 版本的小程序码只有开发者/体验成员能扫开，普通顾客扫会打不开")


def main() -> None:
    args = parse_args()
    build(args.out, args.db, args.clean, args.mode, args.env, args.page)


if __name__ == "__main__":
    main()
