#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اسکریپت خودکار همگام‌سازی مخزن گیت‌هاب BarzokhouseTelegramBot
این اسکریپت:
1. ریلیز نسخه قبلی تولید شده با کلاود را ثبت می‌کند.
2. آخرین تغییرات اعمال‌شده در AI Studio را روی مخزن گیت‌هاب پوش (Push) می‌نماید.
"""

import os
import sys
import shutil
import subprocess
import urllib.request
import urllib.error
import json
from datetime import datetime

REPO_OWNER = "targol"
REPO_NAME = "BarzokhouseTelegramBot"
REPO_URL = f"https://github.com/{REPO_OWNER}/{REPO_NAME}"
API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"

# تاریخ امروز
TODAY_STR = datetime.now().strftime("%Y-%m-%d")
RELEASE_TAG = f"v1.0-claude-{TODAY_STR}"
RELEASE_NAME = f"نسخه اولیه توسعه‌یافته با کلاود (Claude) - {TODAY_STR}"
RELEASE_BODY = (
    "این نسخه با کلاود (Claude) تولید شده است و پس از این، "
    "تغییرات، قابلیت‌ها و به‌روزرسانی‌های آینده با Google AI Studio انجام می‌شود.\n\n"
    "✨ ویژگی‌های این نسخه پایه:\n"
    "- معرفی اقامتگاه و اتاق‌های سنتی برزک\n"
    "- ساختار اولیه رزرو اقامت و ارسال پیام تلگرامی"
)

PRE_AISTUDIO_COMMIT = "9042896b70ddbb0b84597987a14f8f11a9303950"

def get_token():
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token and os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("GITHUB_TOKEN="):
                    token = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    return token

def create_github_release(token: str):
    print(f"📦 در حال ایجاد Release در مخزن {REPO_OWNER}/{REPO_NAME}...")
    url = f"{API_URL}/releases"
    payload = {
        "tag_name": RELEASE_TAG,
        "target_commitish": PRE_AISTUDIO_COMMIT,
        "name": RELEASE_NAME,
        "body": RELEASE_BODY,
        "draft": False,
        "prerelease": False
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
            "User-Agent": "AIStudio-Sync-Script"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            print(f"✅ ریلیز با موفقیت ایجاد شد: {res_data.get('html_url')}")
            return True
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        if "already_exists" in err_body:
            print(f"ℹ️ ریلیز یا تگ {RELEASE_TAG} قبلاً ثبت شده بود.")
            return True
        print(f"❌ خطا در ایجاد ریلیز: HTTP {e.code} - {err_body}")
        return False

def push_updates(token: str):
    print("🚀 در حال آماده‌سازی و ارسال (Push) آخرین تغییرات AI Studio به شاخه main...")
    temp_dir = "/tmp/gh_sync_repo"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

    auth_url = f"https://{token}@github.com/{REPO_OWNER}/{REPO_NAME}.git"
    run_cmd(["git", "clone", auth_url, temp_dir])

    # کپی کردن فایل‌های جدید
    files_to_copy = [
        ("repo_files/bot.py", "bot.py"),
        ("repo_files/config.py", "config.py"),
        ("repo_files/rooms.json", "rooms.json"),
        ("repo_files/foods.json", "foods.json"),
        ("AGENTS.md", "AGENTS.md"),
    ]

    for src, dst in files_to_copy:
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(temp_dir, dst))
            print(f"  + کپی شد: {dst}")

    # کپی پوشه سرورلس تلگرام
    if os.path.exists("serverless"):
        dst_serverless = os.path.join(temp_dir, "serverless")
        if os.path.exists(dst_serverless):
            shutil.rmtree(dst_serverless)
        shutil.copytree("serverless", dst_serverless)
        print("  + کپی شد: پوشه کامل serverless (Telegram Serverless)")

    # کامیت و پوش
    os.chdir(temp_dir)
    run_cmd(["git", "config", "user.name", "AI Studio / targol"])
    run_cmd(["git", "config", "user.email", "targol@gmail.com"])
    run_cmd(["git", "add", "."])
    
    status = subprocess.check_output(["git", "status", "--porcelain"]).decode("utf-8")
    if not status.strip():
        print("ℹ️ تغییری برای ارسال وجود ندارد، مخزن به‌روز است.")
        return True

    commit_msg = (
        f"feat(serverless): افزودن نسخه کامل Telegram Serverless ربات خانه برزک ({TODAY_STR})\n\n"
        "- بازنویسی کامل ربات برای معماری نوین بدون سرور تلگرام (Telegram Serverless / tgcloud)\n"
        "- اجرای مستقیم روی V8 Isolate تلگرام بدون نیاز به سرور یا کانتینر خارجی\n"
        "- ذخیره‌سازی وضعیت مکالمه و سشن‌ها با SQLite بومی تلگرام\n"
        "- رزرو چند اتاقه، تفکیک سنین کودکان، سفارش ناهار و شام و رسید واریزی\n"
        "- فایل راهنمای گام‌به‌گام دیپلوی در serverless/README.md"
    )
    run_cmd(["git", "commit", "-m", commit_msg])
    run_cmd(["git", "push", "origin", "main"])
    print(f"🎉 تمام تغییرات جدید با موفقیت روی {REPO_URL} اعمال شد!")
    return True

def run_cmd(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"خطا در اجرای دستور: {' '.join(cmd)}\n{result.stderr}")
        raise RuntimeError(result.stderr)
    return result.stdout

def main():
    token = get_token()
    if not token:
        print("=" * 65)
        print("⚠️ متغیر GITHUB_TOKEN یافت نشد!")
        print("برای اعمال خودکار تغییرات روی مخزن گیت‌هاب، لطفاً توکن گیت‌هاب خود را")
        print("در تنظیمات (Secrets) یا فایل .env قرار دهید.")
        print(f"آدرس مخزن: {REPO_URL}")
        print("=" * 65)
        sys.exit(1)

    # مرحله ۱: ایجاد ریلیز
    if not create_github_release(token):
        print("توقف عملیات به دلیل خطا در ایجاد ریلیز.")
        sys.exit(1)

    # مرحله ۲: ارسال تغییرات
    if not push_updates(token):
        print("توقف عملیات به دلیل خطا در ارسال تغییرات.")
        sys.exit(1)

if __name__ == "__main__":
    main()
