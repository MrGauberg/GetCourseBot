import os
import fnmatch
import re
from datetime import datetime

class GitignoreParser:
    def __init__(self, gitignore_path):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Загрузка правил из .gitignore...")
        self.patterns = []
        self.root_dir = os.path.dirname(os.path.abspath(gitignore_path))
        # Список директорий и файлов, которые нужно игнорировать
        self.ignore_dirs = {
            'venv', '__pycache__', '.git', 'node_modules',
            'migrations', 'staticfiles', 'static', 'media',
            'alembic/versions', 'htmlcov', '.pytest_cache',
            '.cache', '.coverage', 'coverage', 'dist', 'build',
            '.mypy_cache', '.ruff_cache', '.tox', 'pip-log.txt',
            'pip-delete-this-directory.txt', '.eggs', '*.egg-info',
            'celerybeat-schedule', '.env', '.DS_Store'
        }
        # Паттерны файлов для игнорирования
        self.ignore_patterns = {
            '*_migration.py',
            '*_migrations.py',
            '*.pyc',
            '*.pyo',
            '*.pyd',
            '*.so',
            '*.dll',
            '*.dylib',
            '*.class',
            '*.jar',
            '*.war',
            '*.ear',
            '*.zip',
            '*.tar.gz',
            '*.tgz',
            '*.rar',
            '*.7z',
            '*.db',
            '*.sqlite3',
            '*.sqlite',
            '*.log',
            '*.bak',
            '*.swp',
            '*.swo',
            '*.tmp',
            '*.temp',
            '*.cache',
            '*.pid',
            '*.seed',
            '*.pid.lock'
        }
        
        # Паттерны для исключения только в определенных директориях
        self.conditional_ignore_patterns = {
            '*.html': ['htmlcov', 'staticfiles', 'static', 'dist', 'build'],
            '*.css': ['htmlcov', 'staticfiles', 'static', 'dist', 'build'],
            '*.js': ['htmlcov', 'staticfiles', 'static', 'dist', 'build', 'node_modules'],
            '*.webmanifest': ['dist', 'build'],
            'sw.js': ['dist', 'build'],
            'registerSW.js': ['dist', 'build']
        }
        
        # Имена файлов, которые нужно исключить в dist/build
        self.dist_excluded_files = {
            'sw.js', 'registerSW.js', 'manifest.webmanifest'
        }
        self.load_gitignore(gitignore_path)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Загружено {len(self.patterns)} правил из .gitignore")
    
    def load_gitignore(self, gitignore_path):
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Преобразуем паттерны .gitignore в паттерны fnmatch
                    pattern = line
                    if pattern.startswith('/'):
                        pattern = pattern[1:]
                    if pattern.endswith('/'):
                        pattern = pattern[:-1]
                    # Нормализуем слеши для Windows
                    pattern = pattern.replace('\\', '/')
                    # Исправляем экранирование точки
                    pattern = pattern.replace('.', r'\.').replace('*', '.*')
                    if pattern.startswith('!'):
                        # Исключения (паттерны с !) обрабатываются отдельно
                        self.patterns.append(('include', pattern[1:]))
                    else:
                        self.patterns.append(('exclude', pattern))
    
    def should_ignore(self, path):
        # Получаем абсолютный путь
        abs_path = os.path.abspath(path)
        # Получаем путь относительно корневой директории
        rel_path = os.path.relpath(abs_path, self.root_dir)
        # Нормализуем путь для сравнения
        normalized_path = rel_path.replace('\\', '/')
        
        # Проверяем системные директории
        path_parts = normalized_path.split('/')
        if any(part in self.ignore_dirs for part in path_parts):
            return True
            
        # Проверяем паттерны файлов
        filename = os.path.basename(normalized_path)
        if any(fnmatch.fnmatch(filename, pattern) for pattern in self.ignore_patterns):
            return True
        
        # Проверяем условные паттерны (только в определенных директориях)
        for pattern, required_dirs in self.conditional_ignore_patterns.items():
            if fnmatch.fnmatch(filename, pattern):
                if any(part in required_dirs for part in path_parts):
                    return True
        
        # Проверяем специальные файлы в dist/build
        if filename in self.dist_excluded_files:
            if any(part in ['dist', 'build'] for part in path_parts):
                return True
        
        # Исключаем минифицированные и хешированные файлы из dist/build
        if any(part in ['dist', 'build'] for part in path_parts):
            # Исключаем файлы с хешами в имени (например, index-BtE_AaX-.js, workbox-42774e1b.js)
            if re.search(r'-[a-zA-Z0-9]{8,}\.', filename):
                return True
            # Исключаем скомпилированные asset файлы
            if filename.startswith('index-') and filename.endswith('.js'):
                return True
            if filename.startswith('workbox-') and filename.endswith('.js'):
                return True
        
        # Проверяем миграции по содержимому пути
        if 'migrations' in path_parts and not path_parts[-1] == '__init__.py':
            return True
            
        # Проверяем статические файлы, кеши, отчеты покрытия
        system_dirs = ['static', 'staticfiles', 'media', 'htmlcov', 
                      '.pytest_cache', '.cache', 'coverage', '.coverage',
                      'celerybeat-schedule', 'dist', 'build']
        if any(part in system_dirs for part in path_parts):
            return True
        
        # Проверяем файлы покрытия и отчеты
        if filename.startswith('.coverage') or filename in ['coverage.xml', 'coverage.json']:
            return True
        
        # Проверяем, что файл не внутри venv или других виртуальных окружений
        if any(part.startswith('venv') or part.startswith('.venv') or 
               part.startswith('env') for part in path_parts):
            return True
        
        # Сначала проверяем исключения (паттерны с !)
        for pattern_type, pattern in self.patterns:
            if pattern_type == 'include':
                if fnmatch.fnmatch(normalized_path, pattern):
                    return False
        
        # Затем проверяем паттерны исключения
        for pattern_type, pattern in self.patterns:
            if pattern_type == 'exclude':
                if fnmatch.fnmatch(normalized_path, pattern):
                    return True
        
        return False

def is_code_file(filename):
    code_extensions = {
        '.py', '.js', '.jsx', '.ts', '.tsx', '.css', '.scss', '.html', 
        '.json', '.yaml', '.yml', '.md', '.sh', '.sql', '.vue', '.php',
        '.go', '.java', '.kt', '.swift', '.rb', '.rs', '.cpp', '.h',
        '.c', '.hpp', '.cs', '.fs', '.fsx', '.fsi', '.fsproj'
    }
    
    # Исключаем системные и конфигурационные файлы
    excluded_files = {
        'manage.py', 'conftest.py', 'pytest.ini', 'setup.py', 
        'requirements.txt', 'requirements-dev.txt', 'pyproject.toml',
        'tox.ini', '.flake8', '.pylintrc', 'mypy.ini', '.editorconfig',
        'test_tz_compliance.py', 'README.md', 'README.rst', 'CHANGELOG.md',
        'LICENSE', 'LICENSE.txt', '.gitignore', '.dockerignore',
        'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml',
        'FRONTEND_IMPLEMENTATION.md', 'FRONTEND_STATUS.md',
        'BACKEND_IMPLEMENTATION.md', 'BACKEND_STATUS.md'
    }
    
    # Исключаем все markdown файлы (документация)
    if filename.endswith('.md'):
        return False
    
    # Исключаем lock файлы пакетных менеджеров
    if filename.endswith('-lock.json') or filename.endswith('.lock'):
        return False
    
    if filename in excluded_files:
        return False
    
    return os.path.splitext(filename)[1].lower() in code_extensions

def add_code_to_text(text_content, filepath, relative_path):
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Обработка файла: {relative_path}")
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Добавляем путь к файлу как заголовок
        text_content.append(f"\n{'='*80}")
        text_content.append(f"ФАЙЛ: {relative_path}")
        text_content.append(f"{'='*80}\n")
        
        # Добавляем содержимое файла
        text_content.append(content)
        
        # Добавляем разделитель
        text_content.append(f"\n{'='*80}\n")
        
        # Выводим размер файла
        file_size = os.path.getsize(filepath) / 1024  # размер в КБ
        print(f"[{datetime.now().strftime('%H:%M:%S')}] OK Файл обработан ({file_size:.1f} КБ)")
        
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR Ошибка при чтении файла {relative_path}: {str(e)}")
        text_content.append(f'Ошибка при чтении файла {relative_path}: {str(e)}\n')

def process_directory(text_content, root_dir, gitignore_parser):
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Начинаем обработку директории: {root_dir}")
    total_files = 0
    processed_files = 0
    skipped_files = 0
    
    # Сначала посчитаем общее количество файлов
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Модифицируем dirnames на месте, чтобы не спускаться в игнорируемые директории
        dirnames[:] = [d for d in dirnames if not gitignore_parser.should_ignore(os.path.join(dirpath, d))]
        
        if gitignore_parser.should_ignore(dirpath):
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Пропускаем директорию: {os.path.relpath(dirpath, root_dir)}")
            continue
            
        for filename in filenames:
            if is_code_file(filename):
                full_path = os.path.join(dirpath, filename)
                if not gitignore_parser.should_ignore(full_path):
                    total_files += 1
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Найдено {total_files} файлов для обработки")
    
    # Теперь обрабатываем файлы
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Модифицируем dirnames на месте, чтобы не спускаться в игнорируемые директории
        dirnames[:] = [d for d in dirnames if not gitignore_parser.should_ignore(os.path.join(dirpath, d))]
        
        if gitignore_parser.should_ignore(dirpath):
            continue
            
        relative_dir = os.path.relpath(dirpath, root_dir)
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Обработка директории: {relative_dir}")
            
        for filename in filenames:
            if not is_code_file(filename):
                continue
                
            full_path = os.path.join(dirpath, filename)
            relative_path = os.path.relpath(full_path, root_dir)
            
            if gitignore_parser.should_ignore(full_path):
                skipped_files += 1
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Пропускаем файл (по .gitignore): {relative_path}")
                continue
                
            add_code_to_text(text_content, full_path, relative_path)
            processed_files += 1
            
            # Выводим прогресс
            progress = (processed_files + skipped_files) / total_files * 100
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Прогресс: {progress:.1f}% ({processed_files + skipped_files}/{total_files})")
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Директория {root_dir} обработана:")
    print(f"  - Всего файлов: {total_files}")
    print(f"  - Обработано: {processed_files}")
    print(f"  - Пропущено: {skipped_files}")

def get_root_directories(script_dir):
    """Возвращает список директорий в корне проекта (где находится скрипт)"""
    root_dirs = []
    # Директории, которые нужно исключить
    exclude_dirs = {
        '.git', '__pycache__', 'venv', 'env', '.venv',
        'node_modules', 'dist', 'build', '.idea', '.vscode',
        'htmlcov', 'code_snapshots', 'docs'  # Исключаем папку с результатами
    }
    
    for item in os.listdir(script_dir):
        item_path = os.path.join(script_dir, item)
        # Проверяем, что это директория и не исключена
        if os.path.isdir(item_path) and item not in exclude_dirs:
            root_dirs.append(item)
    
    return sorted(root_dirs)

def main():
    start_time = datetime.now()
    print(f"[{start_time.strftime('%H:%M:%S')}] Начало сбора кода проекта")
    
    # Определяем директорию, где находится скрипт
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if not script_dir:
        script_dir = os.getcwd()
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Рабочая директория: {script_dir}")
    
    # Создаем папку для результатов
    output_dir = os.path.join(script_dir, 'code_snapshots')
    os.makedirs(output_dir, exist_ok=True)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Папка для результатов: {output_dir}")
    
    # Инициализируем парсер .gitignore
    gitignore_path = os.path.join(script_dir, '.gitignore')
    if not os.path.exists(gitignore_path):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ВНИМАНИЕ: .gitignore не найден, используются только системные правила")
        # Создаем минимальный парсер без .gitignore
        class DummyParser:
            def should_ignore(self, path):
                return False
        gitignore_parser = DummyParser()
    else:
        gitignore_parser = GitignoreParser(gitignore_path)
    
    # Находим все директории в корне
    root_directories = get_root_directories(script_dir)
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Найдено директорий для обработки: {len(root_directories)}")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Директории: {', '.join(root_directories)}")
    
    # Обрабатываем каждую директорию отдельно
    for dir_name in root_directories:
        dir_path = os.path.join(script_dir, dir_name)
        
        print(f"\n{'='*80}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Обработка директории: {dir_name}")
        print(f"{'='*80}")
        
        # Создаем список для хранения текстового содержимого
        text_content = []
        text_content.append("СБОРКА КОДА ПРОЕКТА")
        text_content.append("=" * 80)
        text_content.append(f"Директория: {dir_name}")
        text_content.append(f"Дата создания: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        text_content.append("=" * 80)
        
        # Обрабатываем директорию
        process_directory(text_content, dir_path, gitignore_parser)
        
        # Сохраняем файл для этой директории
        output_filename = f"{dir_name}_code.txt"
        output_path = os.path.join(output_dir, output_filename)
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Сохранение файла: {output_filename}")
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(text_content))
            
            file_size = os.path.getsize(output_path) / 1024  # размер в КБ
            print(f"[{datetime.now().strftime('%H:%M:%S')}] OK Файл сохранен ({file_size:.1f} КБ): {output_path}")
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR Ошибка при сохранении файла {output_path}: {str(e)}")
    
    end_time = datetime.now()
    duration = end_time - start_time
    print(f"\n{'='*80}")
    print(f"[{end_time.strftime('%H:%M:%S')}] Готово!")
    print(f"Время выполнения: {duration.total_seconds():.1f} секунд")
    print(f"Обработано директорий: {len(root_directories)}")
    print(f"Результаты сохранены в: {output_dir}")
    print(f"{'='*80}")

if __name__ == '__main__':
    main()