# КРИТИЧЕСКИЙ БАГ #3 - Python кэш

**Дата:** 2026-03-16 15:30 UTC
**Статус:** ✅ ИСПРАВЛЕНО

---

## 🔴 ПРОБЛЕМА

После исправлений #1 и #2 система всё ещё использовала старый код:

**Логи показывали:**
```
[Agent1] Context too large (199764 tokens), using sliding window
[Agent1] Reduced to 76 lines (from 101)
```

**Но в коде было:**
```python
print(f"[Agent1] Context too large ({context_tokens} tokens), using fallback")
```

**Причина:** Python использовал кэшированные `.pyc` файлы из `__pycache__` директорий.

---

## ✅ ИСПРАВЛЕНИЕ

### 1. Очистка кэша
```bash
find src -name "__pycache__" -type d -exec rm -rf {} +
find src -name "*.pyc" -delete
```

### 2. Создан скрипт автоматической очистки
**Файл:** `RESTART_PROXY.sh`

**Использование:**
```bash
cd /Users/mansurzainullin/MyCode/big-AGI/context-management
./RESTART_PROXY.sh
```

Скрипт автоматически:
1. Очищает весь Python кэш
2. Устанавливает переменные окружения
3. Запускает прокси сервер

---

## 📝 ВАЖНО

**Всегда используй `RESTART_PROXY.sh` для перезапуска прокси!**

Если запускаешь вручную, сначала очисти кэш:
```bash
find src -name "__pycache__" -type d -exec rm -rf {} +
find src -name "*.pyc" -delete
PYTHONPATH=. python src/proxy/server.py
```

---

## 🧪 ПРОВЕРКА

После перезапуска логи должны показывать:
```
[Agent1] Context too large (199764 tokens), using fallback
[Orchestrator] Limiting to 3 blocks
[Proxy] Category 'Dialogue' - skipping (cooldown, last compressed Xs ago)
```

Если видишь "using sliding window" - кэш не очищен!

---

## 🎯 ИТОГ

Все три бага исправлены:
1. ✅ Большие контексты (fallback)
2. ✅ Повторное сжатие (cooldown)
3. ✅ Таймауты (600s)
4. ✅ Python кэш (автоочистка)

**Система готова к тестированию с чистым кэшем.**
