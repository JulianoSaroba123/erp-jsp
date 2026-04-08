import os, re

patterns = [
    r'href.*colab.*nome',
    r'url_for.*colab.*nome',
    r'/colaborador.*nome',
    r'action.*colab.*nome',
    r'colaborador[/\+].*colab',
]

for root, dirs, files in os.walk('app'):
    for f in files:
        if f.endswith('.html') or f.endswith('.py'):
            path = os.path.join(root, f)
            try:
                with open(path, encoding='utf-8', errors='ignore') as fh:
                    for i, line in enumerate(fh, 1):
                        for p in patterns:
                            if re.search(p, line, re.IGNORECASE):
                                print(f'{path}:{i}: {line.rstrip()}')
                                break
            except Exception as e:
                pass
