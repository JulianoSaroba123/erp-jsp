import zipfile
import re
import os
import xml.etree.ElementTree as ET

file_path = r'E:\Modelos de Documentos_Solar\Documento-JSPELE-0002 - Propsta Modelo 02-Usual_01.docx'

if not os.path.exists(file_path):
    print(f'Erro: O arquivo {file_path} nao existe.')
else:
    print(f'Arquivo encontrado: {file_path}')
    placeholders = set()
    patterns = [
        r'\{\{[^{}]+\}\}',
        r'\[[^\[\]]+\]',
        r'\{[^{}]+\}',
        r'<<[^<>]+>>',
        r'\$\{[^{}]+\}',
        r'%[^% \n\t\r]+%'
    ]
    combined_pattern = re.compile('|'.join(patterns))
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    
    try:
        with zipfile.ZipFile(file_path, 'r') as z:
            for name in z.namelist():
                if name.startswith('word/') and name.endswith('.xml'):
                    with z.open(name) as f:
                        tree = ET.parse(f)
                        root = tree.getroot()
                        # Extract text and join
                        texts = [node.text for node in root.findall('.//w:t', ns) if node.text]
                        full_text = "".join(texts)
                        found = combined_pattern.findall(full_text)
                        for item in found:
                            placeholders.add(item.strip())
        
        sorted_placeholders = sorted(list(placeholders))
        print('Placeholders encontrados:')
        for p in sorted_placeholders:
            print(p)
        print(f'\nTotal de placeholders únicos: {len(sorted_placeholders)}')
    except Exception as e:
        print(f'Erro ao processar o arquivo: {e}')
