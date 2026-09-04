with open("repo_files/bot.py", "r", encoding="utf-8") as f:
    code = f.read()

bad_str = '''async def cancel_outside_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "در حال حاضر هیچ فرآیند رزرو یا درخواستی فعال نیست که لغو شود.
"
        "برای شروع، /start را ارسال کنید."
    )'''

good_str = '''async def cancel_outside_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "در حال حاضر هیچ فرآیند رزرو یا درخواستی فعال نیست که لغو شود.\\n"
        "برای شروع، /start را ارسال کنید."
    )'''

if bad_str in code:
    code = code.replace(bad_str, good_str)
    with open("repo_files/bot.py", "w", encoding="utf-8") as f:
        f.write(code)
    print("Replaced successfully")
else:
    # regex fix
    import re
    code = re.sub(
        r'async def cancel_outside_conversation.*?برای شروع، /start را ارسال کنید\."\s*\)',
        good_str,
        code,
        flags=re.DOTALL
    )
    with open("repo_files/bot.py", "w", encoding="utf-8") as f:
        f.write(code)
    print("Regex replaced")
