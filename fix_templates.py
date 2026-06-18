import os

fixed_count = 0
for root, _, files in os.walk('.'):
    if '.venv' in root: continue
    for f in files:
        if f.endswith('.html'):
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    lines = file.readlines()
            except UnicodeDecodeError:
                continue

            extends_idx = -1
            for i, line in enumerate(lines[:5]):
                if '{% extends' in line:
                    extends_idx = i
                    break
            
            # If extends tag exists and isn't on the first line
            # or isn't preceded only by whitespace/comments (just enforcing line 0 for safety)
            if extends_idx > 0:
                ext_line = lines.pop(extends_idx)
                # Keep any existing spacing before the `{% load` by just inserting extends line before it.
                lines.insert(0, ext_line)
                with open(path, 'w', encoding='utf-8') as file:
                    file.writelines(lines)
                fixed_count += 1
                print(f"Fixed extends order in {path}")

print(f"Total templates fixed: {fixed_count}")
