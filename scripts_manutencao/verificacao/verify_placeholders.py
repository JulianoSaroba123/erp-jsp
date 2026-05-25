import zipfile
import os
import re
from collections import Counter

input_path = r'E:\Modelos de Documentos_Solar\Documento-JSPELE-0002 - Propsta Modelo 02-Usual_01_PLACEHOLDERS_NORMALIZADOS.docx'

if not os.path.exists(input_path):
    print(f"Erro: Arquivo nao encontrado: {input_path}")
    exit(1)

patterns = {
    '[VAR]': re.compile(r'\[[^\[\]]+\]'),
    '{{VAR}}': re.compile(r'\{\{[^{}]+\}\}'),
    '{VAR}': re.compile(r'(?<!\{)\{[^{}]+\}(?!\})'), # Avoid matching {{VAR}} parts
    '<<VAR>>': re.compile(r'(?:<<|&lt;&lt;)[^<>&]+(?:>>|&gt;&gt;)'),
    '': re.compile(r'\$\{[^{}]+\}'),
    '%VAR%': re.compile(r'%[^% \n\t\r]+%')
}

counts = Counter()
found_placeholders = {k: [] for k in patterns.keys()}

try:
    with zipfile.ZipFile(input_path, 'r') as zin:
        for item in zin.infolist():
            if item.filename.startswith('word/') and item.filename.endswith('.xml'):
                content = zin.read(item.filename).decode('utf-8', errors='ignore')
                for label, pattern in patterns.items():
                    matches = pattern.findall(content)
                    counts[label] += len(matches)
                    found_placeholders[label].extend(matches)

    print("--- Resumo de Placeholders ---")
    for label, count in counts.items():
        print(f"{label}: {count}")
    
    others_found = False
    for label, count in counts.items():
        if label != '[VAR]' and count > 0:
            others_found = True
            break
    
    if others_found:
        print("\nAVISO: Ainda foram encontrados placeholders fora do formato [VAR].")
    else:
        print("\nSUCESSO: Apenas placeholders no formato [VAR] foram encontrados (ou nenhum placeholder restou).")

except Exception as e:
    print(f"Erro ao processar o arquivo: {e}")
