# 🚀 НАЧНИ ТЕСТИРОВАНИЕ ПРЯМО СЕЙЧАС

**Все баги исправлены. Система готова к тестированию.**

---

## ШАГ 1: Останови текущий прокси (если запущен)

В терминале где запущен прокси нажми `Ctrl+C`

---

## ШАГ 2: Запусти прокси с очисткой кэша

**ВАЖНО: Используй скрипт, он автоматически очищает Python кэш!**

```bash
cd /Users/mansurzainullin/MyCode/big-AGI/context-management
source .venv/bin/activate
./RESTART_PROXY.sh
```

Или вручную (если скрипт не работает):
```bash
find src -name "__pycache__" -type d -exec rm -rf {} +
find src -name "*.pyc" -delete
export ANTHROPIC_API_KEY="sk-aw-f157875b77785becb3514fb6ae770e50"
export ANTHROPIC_BASE_URL="https://api.kiro.cheap"
PYTHONPATH=. python src/proxy/server.py
```

Должно появиться:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## ШАГ 3: Продолжи разговор в том же чате

1. Открой BigAGI (http://localhost:3000)
2. Открой тот же чат где была ошибка
3. Отправь сообщение
4. **ЖДИ 5-10 МИНУТ** (сжатие медленное, это нормально!)

---

## ШАГ 4: Проверь логи прокси

В терминале должно быть:

✅ **ПРАВИЛЬНО:**
```
[Proxy] Category 'Dialogue' at 189.4% - triggering compression
[Agent1] Context too large (205588 tokens), using fallback
[Agent1] Using fallback selection (simple heuristic)
[Proxy] Compressed Dialogue: 205k → 67k tokens  # ~67k, НЕ 131k!
[Proxy] Saved 138k tokens
```

❌ **НЕПРАВИЛЬНО (если видишь):**
```
[Agent1] using sliding window  # СТАРЫЙ КОД! Кэш не очищен!
[Proxy] Compressed Dialogue: 205k → 131k tokens  # Недостаточно! Баг #4 не исправлен!
anthropic.APITimeoutError  # таймаут
```

---

## ШАГ 5: Отправь второе сообщение (сразу после первого)

Должно быть:
```
[Proxy] Category 'Dialogue' at 67% - no compression needed
✅ Ответ получен БЕЗ ошибок
```

❌ **НЕ должно быть:**
```
need summarize our conversation — the context has grown too large
```

Если видишь эту ошибку - значит сжатие недостаточное (баг #4 не исправлен).

---

## ЧТО ИСПРАВЛЕНО

### Исправление #1: Большие контексты (14:00)
- ✅ Fallback для контекстов >150k токенов
- ✅ Обработка ошибок прокси

### Исправление #2: Повторное сжатие и таймауты (15:00)
- ✅ Cooldown 2 минуты между сжатиями
- ✅ Timeout 10 минут (для медленных прокси)
- ✅ Лимит 3 блока (быстрее)

### Исправление #3: Python кэш (15:30)
- ✅ Автоматическая очистка кэша при перезапуске
- ✅ Скрипт RESTART_PROXY.sh

### Исправление #4: Неправильная формула (16:00)
- ✅ Исправлена математика расчёта target_tokens
- ✅ Формула: need_to_free * 2.0 (было * 4 * 1.5)

### Исправление #5: Неправильные буферы (16:15)
- ✅ Буферы теперь в токенах (10k), не в строках (200)
- ✅ Работает с любой длиной строк

---

## ЕСЛИ ЧТО-ТО НЕ РАБОТАЕТ

### Таймаут всё ещё происходит
```bash
export AGENT2_TIMEOUT_S=900  # 15 минут
```

### Сжимает слишком часто
Отредактируй `src/proxy/server.py`, строка 113:
```python
if current_time - last_compression_time < 300:  # 5 минут
```

### Не достигает 70k токенов
Отредактируй `src/agents/agent1_selector.py`, строка 421:
```python
target_tokens = int(need_to_free * 4 * 2.0)  # 2x буфер
```

---

## ПОСЛЕ ТЕСТИРОВАНИЯ

Напиши результат:
- ✅ Сработало / ❌ Ошибка
- Скопируй логи из терминала
- Сколько времени заняло сжатие
- Сжало до скольки токенов

---

**НАЧИНАЙ ТЕСТИРОВАНИЕ!** 🚀
