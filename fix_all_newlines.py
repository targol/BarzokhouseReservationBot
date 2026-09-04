import re

with open("repo_files/bot.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    # Check if a string literal starts on this line without closing quote
    # Count unescaped quotes
    stripped = line.strip()
    if (stripped.startswith('"') or stripped.startswith('f"')) and not stripped.endswith('"') and not stripped.endswith('",') and not stripped.endswith('")'):
        if i + 1 < len(lines) and lines[i+1].strip() == '"':
            # Joined by broken newline
            merged = line.rstrip('\r\n') + '\\n"' + lines[i+2] if i + 2 < len(lines) else line
            new_lines.append(line.rstrip('\r\n') + '\\n"\n')
            i += 2
            continue
    new_lines.append(line)
    i += 1

print("Total lines:", len(lines))
