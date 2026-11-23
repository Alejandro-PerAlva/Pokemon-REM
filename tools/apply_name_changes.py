import os
import re

def replace_names():
    root_dir = '.'
    extensions = ('.txt', '.py', '.rb', '.json', '.md')
    exclude_dirs = {'.git', '.system_generated', 'Descartados_ConBases'}
    
    modified_files = []
    total_beltrán = 0
    total_ariadna = 0
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Prune excluded directories
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        
        for f in filenames:
            if not f.endswith(extensions):
                continue
            filepath = os.path.join(dirpath, f)
            try:
                with open(filepath, 'r', encoding='utf-8') as fp:
                    content = fp.read()
            except Exception:
                try:
                    with open(filepath, 'r', encoding='latin-1') as fp:
                        content = fp.read()
                except Exception:
                    continue
            
            orig = content
            
            # Count
            count_b = len(re.findall(r'Beltrán', content, re.IGNORECASE))
            count_n = len(re.findall(r'Ariadna', content, re.IGNORECASE))
            
            if count_b == 0 and count_n == 0:
                continue
                
            # Identifiers / uppercase:
            # CHAR_BELTRAN -> CHAR_BELTRAN
            content = content.replace('CHAR_BELTRAN', 'CHAR_BELTRAN')
            content = content.replace('CHAR_ARIADNA', 'CHAR_ARIADNA')
            
            # Exact case replacements:
            # Beltrán -> Beltrán
            content = content.replace('Beltrán', 'Beltrán')
            content = content.replace('beltrán', 'beltrán')
            content = content.replace('BELTRÁN', 'BELTRÁN')
            
            # Ariadna -> Ariadna
            content = content.replace('Ariadna', 'Ariadna')
            content = content.replace('ariadna', 'ariadna')
            content = content.replace('ARIADNA', 'ARIADNA')
            
            if content != orig:
                with open(filepath, 'w', encoding='utf-8') as fp:
                    fp.write(content)
                modified_files.append((filepath, count_b, count_n))
                total_beltrán += count_b
                total_ariadna += count_n

    print(f"Archivos modificados: {len(modified_files)}")
    print(f"Total reemplazos Beltrán -> Beltrán: {total_beltrán}")
    print(f"Total reemplazos Ariadna -> Ariadna: {total_ariadna}")
    for path, cb, cn in modified_files:
        print(f" - {path} (Beltrán: {cb}, Ariadna: {cn})")

if __name__ == '__main__':
    replace_names()
