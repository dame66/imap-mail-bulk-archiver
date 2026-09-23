# -*- coding: utf-8 -*-
"""
IMAP Mail Bulk Archiver · 通用邮箱批量归档工具

============================================================
用途
============================================================
- 通过 IMAP 协议 · 批量下载邮箱里所有邮件 · 保存为 .eml
- 生成 _index.csv 索引(uid / date / from / subject / size)
- **只读连接** · 不改邮箱任何状态
- **断点续传** · 已下载 uid 跳过 · 重跑不重复

============================================================
支持的邮箱
============================================================
Gmail / Outlook / Yahoo / QQ / 163 / 126 / yeah / 新浪 / 搜狐 /
阿里云 / Foxmail / iCloud / Yandex / Zoho / Hostinger / 腾讯企业邮 · 15+ 种
其它 IMAP 邮箱 · 在 providers.json 里加一条就行

============================================================
用法
============================================================
方式 A · 命令行:
    python main.py --provider gmail --user me@gmail.com --password xxx
    python main.py --provider qq --user me@qq.com --password <授权码> --all

方式 B · .env(推荐 · 密码不进命令行历史):
    复制 .env.example → .env · 填入
    python main.py

参数:
    --provider   邮箱服务(gmail/qq/163/outlook/...) · 或 --host 自定义
    --user       邮箱地址
    --password   密码 / 授权码 / 应用专用密码
    --host       自定义 IMAP 服务器(替代 --provider)
    --port       端口(默认 993)
    --folder     指定文件夹(默认 INBOX)
    --all        下载所有文件夹
    --list       只列文件夹 · 不下载
    --out        自定义输出目录
    --resume     断点续传当天目录
    --batch      每批 FETCH 数量(默认 100 · 慢邮箱调 50)

输出:
    输出/<YY.M.D>/<文件夹名>/*.eml
    输出/<YY.M.D>/<文件夹名>/_index.csv
"""
from __future__ import annotations

import argparse
import csv
import email
import email.header
import imaplib
import json
import os
import re
import sys
import time
from datetime import date
from email.message import Message
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_ENV = SCRIPT_DIR / ".env"
DEFAULT_PROVIDERS = SCRIPT_DIR / "providers.json"
DEFAULT_OUT_ROOT = Path.cwd() / "输出"


def load_env(path: Path) -> dict:
    if not path.exists():
        return {}
    env = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def load_providers(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8")).get("providers", {})


def today_folder() -> str:
    d = date.today()
    return f"{d.year % 100}.{d.month}.{d.day}"


def next_out_dir(root: Path, base: str) -> Path:
    if not (root / base).exists():
        return root / base
    n = 2
    while (root / f"{base}_{n}").exists():
        n += 1
    return root / f"{base}_{n}"


def latest_out_dir(root: Path, base: str):
    if not (root / base).exists():
        return None
    latest = root / base
    n = 2
    while (root / f"{base}_{n}").exists():
        latest = root / f"{base}_{n}"
        n += 1
    return latest


def sanitize(name: str) -> str:
    """IMAP 文件夹名 → 本地目录名"""
    return re.sub(r"[\\/:*?\"<>|]", "_", name)


def sanitize_filename(name: str, max_len: int = 150) -> str:
    """邮件 Subject → 合法文件名"""
    if not name:
        return "(no-subject)"
    name = re.sub(r'[\\/:*?"<>|\r\n\t]+', "_", name)
    name = re.sub(r"\s+", " ", name).strip()
    name = name.rstrip(". ")
    if not name:
        return "(no-subject)"
    if len(name) > max_len:
        name = name[:max_len].rstrip()
    return name


def decode_mime_words(s) -> str:
    if not s:
        return ""
    try:
        parts = email.header.decode_header(s)
        return "".join(
            (p.decode(enc or "utf-8", errors="replace") if isinstance(p, bytes) else p)
            for p, enc in parts
        )
    except Exception:
        return str(s)


def imap_connect(host: str, port: int, ssl: bool, user: str, password: str):
    print(f"[connect] {user} @ {host}:{port} (ssl={ssl})")
    if ssl:
        m = imaplib.IMAP4_SSL(host, port)
    else:
        m = imaplib.IMAP4(host, port)
        try:
            m.starttls()
        except Exception:
            pass
    m.login(user, password)
    return m


def list_folders(m) -> list:
    typ, data = m.list()
    if typ != "OK":
        return []
    names = []
    for row in data:
        if not row:
            continue
        line = row.decode("utf-8", errors="replace") if isinstance(row, bytes) else str(row)
        # 格式: (\HasNoChildren) "." "INBOX.Sent"
        m2 = re.match(r'\((.*?)\)\s+"(.*?)"\s+"?([^"]+)"?$', line)
        if m2:
            names.append(m2.group(3))
    return names


def fetch_uid_list(m, folder: str) -> list:
    typ, _ = m.select(f'"{folder}"', readonly=True)
    if typ != "OK":
        print(f"  [warn] 无法进入文件夹 {folder}")
        return []
    typ, data = m.uid("SEARCH", None, "ALL")
    if typ != "OK" or not data or not data[0]:
        return []
    return data[0].split()


def download_folder(m, folder: str, out_root: Path, batch: int = 100):
    print(f"\n[folder] {folder}")
    uids = fetch_uid_list(m, folder)
    total = len(uids)
    print(f"  共 {total} 封")
    if total == 0:
        return

    folder_dir = out_root / sanitize(folder)
    folder_dir.mkdir(parents=True, exist_ok=True)
    index_path = folder_dir / "_index.csv"
    index_exists = index_path.exists()

    existing = set()
    for p in folder_dir.glob("*.eml"):
        m2 = re.match(r"^(\d+)__", p.name)
        if m2:
            existing.add(m2.group(1))
    print(f"  已存在 {len(existing)} 封 · 跳过")

    todo = [u for u in uids if u.decode() not in existing]
    print(f"  待下载 {len(todo)} 封")
    if not todo:
        return

    with index_path.open("a", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        if not index_exists:
            writer.writerow(["uid", "date", "from", "subject", "size_bytes", "filename"])

        start_ts = time.time()
        done = 0
        for i in range(0, len(todo), batch):
            chunk = todo[i: i + batch]
            uid_set = b",".join(chunk)
            typ, data = m.uid("FETCH", uid_set, "(RFC822)")
            if typ != "OK":
                print(f"  [warn] FETCH 失败 batch {i}")
                continue

            for item in data:
                if not isinstance(item, tuple) or len(item) < 2:
                    continue
                meta_bytes, raw = item[0], item[1]
                meta = meta_bytes.decode("utf-8", errors="replace") if isinstance(meta_bytes, bytes) else str(meta_bytes)
                m_uid = re.search(r"UID (\d+)", meta)
                uid = m_uid.group(1) if m_uid else f"unknown{done}"

                try:
                    msg: Message = email.message_from_bytes(raw)
                except Exception:
                    msg = None

                subject = decode_mime_words(msg["Subject"]) if msg else ""
                sender = decode_mime_words(msg["From"]) if msg else ""
                mdate = msg["Date"] if msg else ""

                safe_subj = sanitize_filename(subject)
                fname = f"{uid}__{safe_subj}.eml"
                (folder_dir / fname).write_bytes(raw if isinstance(raw, (bytes, bytearray)) else str(raw).encode())
                writer.writerow([uid, mdate, sender, subject, len(raw), fname])
                done += 1

            elapsed = time.time() - start_ts
            rate = done / elapsed if elapsed > 0 else 0
            eta = (len(todo) - done) / rate if rate > 0 else 0
            print(f"  [{done}/{len(todo)}] rate={rate:.1f}/s  eta={eta / 60:.1f}min")
            f.flush()

    print(f"  ✓ 完成 {folder} → {folder_dir}")


def resolve_connection(args, env, providers):
    """决定 host/port/ssl/user/password · 优先级 CLI > env > provider 预设"""
    # provider 名字确定 host/port
    prov_name = args.provider or env.get("MAIL_PROVIDER")
    host = args.host or env.get("MAIL_HOST")
    port = args.port or int(env.get("MAIL_PORT", 0) or 0)
    ssl = None

    if prov_name and prov_name in providers:
        p = providers[prov_name]
        host = host or p["host"]
        port = port or p.get("port", 993)
        ssl = p.get("ssl", True)
        print(f"[provider] {prov_name} · {p.get('note', '')}")

    if not host:
        sys.exit("[FATAL] 请指定 --provider 或 --host")
    if not port:
        port = 993
    if ssl is None:
        ssl = (port == 993)

    user = args.user or env.get("MAIL_USER")
    password = args.password or env.get("MAIL_PASSWORD")
    if not user:
        sys.exit("[FATAL] 请提供 --user 或 .env 里 MAIL_USER")
    if not password:
        sys.exit("[FATAL] 请提供 --password 或 .env 里 MAIL_PASSWORD")

    return host, port, ssl, user, password


def main():
    ap = argparse.ArgumentParser(
        description="IMAP 邮箱批量归档工具 · 通用版"
    )
    ap.add_argument("--provider", help="邮箱服务预设(gmail/qq/163/outlook/...)见 providers.json")
    ap.add_argument("--host", help="自定义 IMAP 服务器")
    ap.add_argument("--port", type=int, help="端口(默认 993)")
    ap.add_argument("--user", help="邮箱地址")
    ap.add_argument("--password", help="密码/授权码/应用专用密码")
    ap.add_argument("--folder", default="INBOX", help="文件夹(默认 INBOX)")
    ap.add_argument("--all", action="store_true", help="下载所有文件夹")
    ap.add_argument("--list", action="store_true", help="只列文件夹")
    ap.add_argument("--out", help="自定义输出目录")
    ap.add_argument("--resume", action="store_true", help="断点续传当天目录")
    ap.add_argument("--batch", type=int, default=100, help="每批 FETCH 数量")
    ap.add_argument("--env", default=str(DEFAULT_ENV), help=".env 文件路径")
    ap.add_argument("--providers", default=str(DEFAULT_PROVIDERS), help="providers.json 路径")
    args = ap.parse_args()

    env = load_env(Path(args.env))
    providers = load_providers(Path(args.providers))

    host, port, ssl, user, password = resolve_connection(args, env, providers)

    if args.out:
        out_root = Path(args.out).resolve()
    else:
        base = today_folder()
        root = DEFAULT_OUT_ROOT
        if args.resume:
            out_root = latest_out_dir(root, base) or (root / base)
        else:
            out_root = next_out_dir(root, base)
    out_root.mkdir(parents=True, exist_ok=True)
    print(f"[out] {out_root}")

    m = imap_connect(host, port, ssl, user, password)
    try:
        if args.list:
            for name in list_folders(m):
                print(f"  {name}")
            return

        folders = list_folders(m) if args.all else [args.folder]
        for folder in folders:
            download_folder(m, folder, out_root, batch=args.batch)
    finally:
        try:
            m.logout()
        except Exception:
            pass


if __name__ == "__main__":
    main()
