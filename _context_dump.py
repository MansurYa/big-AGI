import os

OUTPUT_FILE = "_context_dump.txt"

# Базовые папки, которые игнорируем везде
IGNORE_DIRS = {'.git', 'node_modules', '.venv', '__pycache__', '.idea', '.vscode'}

# Точные названия файлов, которые нужно пропустить
IGNORE_FILES = {
    'CLAUDE.md', 
    'ТЕХНИЧЕСКОЕ ЗАДАНИЕ ДЛЯ АВТОНОМНОЙ РАЗРАБОТКИ.md'
}

def is_dir_allowed(rel_dir_path, dir_name):
    """Проверяет, разрешено ли заходить в папку на основе ее относительного пути."""
    if dir_name in IGNORE_DIRS or dir_name.startswith('.'):
        return False
        
    # Разбиваем путь на части для проверки корневых папок
    # replace('\\', '/') гарантирует, что это будет работать и на Windows
    parts = rel_dir_path.replace('\\', '/').split('/')
    
    # Игнорируем корневую папку 'docs', но пропускаем 'context-management/docs'
    if parts[0] == 'docs':
        return False
        
    # Игнорируем корневую папку 'references'
    if parts[0] == 'references':
        return False
        
    return True

def generate_tree(dir_path, base_dir=".", prefix=""):
    """Рекурсивно строит дерево, применяя те же правила фильтрации."""
    tree_str = ""
    try:
        entries = sorted(os.listdir(dir_path))
    except PermissionError:
        return ""

    valid_entries = []
    for e in entries:
        full_path = os.path.join(dir_path, e)
        rel_path = os.path.relpath(full_path, base_dir).replace('\\', '/')
        
        if os.path.isdir(full_path):
            if is_dir_allowed(rel_path, e):
                valid_entries.append((e, full_path, True))
        else:
            if e.endswith('.md') and e not in IGNORE_FILES:
                valid_entries.append((e, full_path, False))
                
    for i, (entry, full_path, is_dir) in enumerate(valid_entries):
        is_last = (i == len(valid_entries) - 1)
        connector = "└── " if is_last else "├── "
        tree_str += f"{prefix}{connector}{entry}\n"
        
        if is_dir:
            extension = "    " if is_last else "│   "
            tree_str += generate_tree(full_path, base_dir, prefix + extension)
            
    return tree_str

def main():
    base_dir = "."
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as out_f:
        out_f.write("<context_dump>\n\n")
        
        # 1. Структура директорий
        out_f.write("<directory_structure>\n")
        out_f.write(".\n")
        out_f.write(generate_tree(base_dir, base_dir))
        out_f.write("</directory_structure>\n\n")
        
        # 2. Содержимое файлов
        out_f.write("<files>\n")
        
        for root, dirs, files in os.walk(base_dir):
            # Фильтруем папки на лету для os.walk
            valid_dirs = []
            for d in dirs:
                full_dir_path = os.path.join(root, d)
                rel_dir_path = os.path.relpath(full_dir_path, base_dir).replace('\\', '/')
                if is_dir_allowed(rel_dir_path, d):
                    valid_dirs.append(d)
            dirs[:] = valid_dirs  # Перезаписываем список, чтобы os.walk не лез в мусор
            
            for file in files:
                if not file.endswith('.md') or file in IGNORE_FILES:
                    continue
                    
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, base_dir).replace('\\', '/')
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as in_f:
                        content = in_f.read()
                        
                    out_f.write(f'<file name="{rel_path}">\n')
                    out_f.write(content)
                    if not content.endswith('\n') and content:
                        out_f.write('\n')
                    out_f.write(f'</file>\n\n')
                    
                except Exception as e:
                    print(f"⚠️ Ошибка чтения {rel_path}: {e}")
                    
        out_f.write("</files>\n\n")
        out_f.write("</context_dump>\n")
                    
    print(f"✅ Успех! Собраны все нужные .md файлы. Результат в {OUTPUT_FILE}")

if __name__ == "__main__":
    main()