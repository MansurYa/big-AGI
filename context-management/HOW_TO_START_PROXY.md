# 🚀 Как запускать прокси

## Два варианта запуска:

### 1. Обычный запуск (быстрый)
Используй когда просто перезапускаешь прокси, код не менялся:

```bash
./START_PROXY.sh
```

### 2. Запуск с очисткой кэша (после изменений кода)
Используй когда:
- Исправлял баги
- Обновлял код
- Python может использовать старые .pyc файлы

```bash
./RESTART_PROXY.sh
```

---

## Когда использовать какой скрипт?

### START_PROXY.sh (обычный)
✅ Прокси упал, нужно перезапустить
✅ Перезагрузил компьютер
✅ Закрыл терминал случайно
✅ Код не менялся

### RESTART_PROXY.sh (с очисткой)
✅ Исправил баг в коде
✅ Обновил файлы .py
✅ Git pull с новыми изменениями
✅ Не уверен - лучше с очисткой

---

## Ручной запуск (если скрипты не работают)

### Обычный:
```bash
cd /Users/mansurzainullin/MyCode/big-AGI/context-management
source .venv/bin/activate
export ANTHROPIC_API_KEY="sk-aw-f157875b77785becb3514fb6ae770e50"
export ANTHROPIC_BASE_URL="https://api.kiro.cheap"
PYTHONPATH=. python src/proxy/server.py
```

### С очисткой кэша:
```bash
cd /Users/mansurzainullin/MyCode/big-AGI/context-management
source .venv/bin/activate
find src -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
find src -name "*.pyc" -delete 2>/dev/null
export ANTHROPIC_API_KEY="sk-aw-f157875b77785becb3514fb6ae770e50"
export ANTHROPIC_BASE_URL="https://api.kiro.cheap"
PYTHONPATH=. python src/proxy/server.py
```

---

## Проверка что прокси запустился

Должно появиться:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

## Остановка прокси

В терминале где запущен прокси нажми `Ctrl+C`

---

**Рекомендация:** Для повседневного использования используй `./START_PROXY.sh` (быстрее).
