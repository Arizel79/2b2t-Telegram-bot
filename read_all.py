import os


def process_current_directory():
    """Обработка файлов в текущей директории и поддиректориях"""
    for root, dirs, files in os.walk('.'):
        # Пропускаем скрытые папки
        dirs[:] = [d for d in dirs if not d.startswith('.')]

        for file in files:
            # Пропускаем файлы, начинающиеся с точки
            if file.startswith('.') or file.endswith(".log") or file == "msgs.txt":
                continue

            file_path = os.path.join(root, file)

            print(f"--------( {file_path[2:]} )---------")  # Убираем './' в начале

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for line in content.split('\n'):
                        print(f"  {line}")
            except:
                print("  ОШИБКА ЧТЕНИЯ ФАЙЛА")
            print()


if __name__ == "__main__":
    process_current_directory()
