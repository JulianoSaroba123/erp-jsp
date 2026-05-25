import zipfile
import re
import os

file_path = r'E:\Modelos de Documentos_Solar\Documento-JSPELE-0002 - Propsta Modelo 02-Usual_01.docx'

if not os.path.exists(file_path):
    print(f'Erro: O arquivo {file_path} nao existe.')
else:
    print(f'Arquivo encontrado: {file_path}')
    placeholders = set()
    # Regex patterns for the requested formats
    patterns = [
        r'\{\{[^{}]+\}\}',
        r'\[[^\[\]]+\]',
        r'\{[^{}]+\}',
        r'<<[^<>]+>>',
        r'\$\{[^{}]+\}',
        r'%[^% \n\t\r]+%'
    ]
    combined_pattern = re.compile('|'.join(patterns))
    
    try:
        with zipfile.ZipFile(file_path, 'r') as z:
            for name in z.namelist():
                if name.startswith('word/') and name.endswith('.xml'):
                    with z.open(name) as f:
                        content = f.read().decode('utf-8', errors='ignore')
                        # Searching in raw XML might miss split tags, 
                        # but follows the "Read all XML" instruction.
                        found = combined_pattern.findall(content)
                        placeholders.update(found)
        
        sorted_placeholders = sorted(list(placeholders))
        print('Placeholders encontrados:')
        for p in sorted_placeholders:
            print(p)
        print(f'\nTotal de placeholders únicos: {len(sorted_placeholders)}')
    except Exception as e:
        print(f'Erro ao processar o arquivo: {e}')
