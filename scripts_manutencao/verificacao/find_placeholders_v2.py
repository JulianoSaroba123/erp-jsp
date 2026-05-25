import zipfile
import re
import os
from lxml import etree

file_path = r'E:\Modelos de Documentos_Solar\Documento-JSPELE-0002 - Propsta Modelo 02-Usual_01.docx'

if not os.path.exists(file_path):
    print(f'Erro: O arquivo {file_path} nao existe.')
else:
    print(f'Arquivo encontrado: {file_path}')
    placeholders = set()
    
    # Regex to extract text from placeholders in raw XML, 
    # but more importantly, we should try a cleaner text extraction approach
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
                        xml_content = f.read()
                        tree = etree.fromstring(xml_content)
                        # Extract all text segments
                        texts = tree.xpath('//w:t/text()', namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})
                        full_text = "".join(texts)
                        
                        # Find placeholders in the concatenated text
                        found = combined_pattern.findall(full_text)
                        for item in found:
                            # Clean up common XML residue if any
                            clean = item.strip()
                            placeholders.add(clean)
        
        sorted_placeholders = sorted(list(placeholders))
        print('Placeholders encontrados (Limpos):')
        for p in sorted_placeholders:
            print(p)
        print(f'\nTotal de placeholders únicos: {len(sorted_placeholders)}')
    except Exception as e:
        print(f'Erro ao processar o arquivo: {e}')
