import zipfile
import os
import re

input_path = r'E:\Modelos de Documentos_Solar\Documento-JSPELE-0002 - Propsta Modelo 02-Usual_01.docx'
output_path = r'E:\Modelos de Documentos_Solar\Documento-JSPELE-0002 - Propsta Modelo 02-Usual_01_PLACEHOLDERS_NORMALIZADOS.docx'

if not os.path.exists(input_path):
    print(f"Erro: Arquivo nao encontrado: {input_path}")
    exit(1)

# Regex to match different formats and capture the name
# Order matters to catch {{VAR}} before {VAR}
patterns = [
    r'\{\{([^{}]+)\}\}',                         # 1. {{VAR}}
    r'\$\{([^{}]+)\}',                           # 2. 
    r'(?:<<|&lt;&lt;)([^<>&]+)(?:>>|&gt;&gt;)',  # 3. <<VAR>> (handled XML escapes)
    r'%([^% \n\t\r]+)%',                         # 4. %VAR%
    r'\{([^{}]+)\}'                              # 5. {VAR}
]

combined_pattern = re.compile('|'.join(patterns))

def normalize_match(match):
    for group in match.groups():
        if group is not None:
            # group is the name inside the placeholder
            return f"[{group}]"
    return match.group(0)

total_substitutions = 0

try:
    with zipfile.ZipFile(input_path, 'r') as zin:
        with zipfile.ZipFile(output_path, 'w') as zout:
            for item in zin.infolist():
                content = zin.read(item.filename)
                # Word document contents are in word/ directory (document.xml, headers, footers, etc.)
                if item.filename.startswith('word/') and item.filename.endswith('.xml'):
                    try:
                        text = content.decode('utf-8')
                        new_text, count = combined_pattern.subn(normalize_match, text)
                        total_substitutions += count
                        zout.writestr(item, new_text.encode('utf-8'))
                    except UnicodeDecodeError:
                        # Fallback for non-UTF8 if any
                        zout.writestr(item, content)
                else:
                    zout.writestr(item, content)

    print(f"Sucesso!")
    print(f"Total de substituicoes realizadas: {total_substitutions}")
    print(f"Arquivo gerado em: {output_path}")

except Exception as e:
    print(f"Erro ao processar o arquivo: {e}")
