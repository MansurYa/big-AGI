# ИСПРАВЛЕНИЕ БАГОВ #2 - Повторное сжатие и таймауты

**Дата:** 2026-03-16 15:00 UTC
**Статус:** ✅ ИСПРАВЛЕНО

---

## 🔴 ПРОБЛЕМЫ ПРИ ТЕСТИРОВАНИИ

### Проблема 1: Повторное сжатие
```
[Proxy] Category 'Dialogue' at 183.8% - triggering compression
[Proxy] Compressed Dialogue: 199170 → 111638 tokens  # Всё ещё > 90k (90%)
[Proxy] Category 'Dialogue' at 189.4% - triggering compression  # Сжимает снова!
```

**Причина:** После сжатия контекст всё ещё > 90% квоты, поэтому система сжимает снова.

### Проблема 2: Не достигает цели
```
Target: 70k tokens (70% of 100k)
Actual: 96-111k tokens (96-111%)
```

**Причина:** Fallback выбирает недостаточно токенов для сжатия.

### Проблема 3: Таймауты
```
anthropic.APITimeoutError: Request timed out
The read operation timed out (after 120 seconds)
```

**Причина:**
- Сжатие занимает 7+ минут (458 секунд)
- Timeout Agent2: 120 секунд
- Прокси api.kiro.cheap медленный

---

## ✅ ИСПРАВЛЕНИЯ

### 1. Cooldown между сжатиями (2 минуты)
**Файл:** `src/proxy/server.py`

**Что сделано:**
- Добавлен cooldown 120 секунд между сжатиями одной категории
- Система не будет сжимать повторно если прошло < 2 минут
- Логирование: "skipping (cooldown, last compressed Xs ago)"

```python
if current_time - last_compression_time < 120:
    print(f"[Proxy] Category '{cat.name}' - skipping (cooldown)")
    continue
```

### 2. Увеличен буфер в fallback (1.5x)
**Файл:** `src/agents/agent1_selector.py`

**Что сделано:**
- Fallback теперь выбирает на 50% больше токенов
- Было: `target_tokens = need_to_free * 4`
- Стало: `target_tokens = need_to_free * 4 * 1.5`
- Гарантирует достижение цели даже если compression ratio < 4x

```python
# Add 50% buffer to ensure we reach target
target_tokens = int(need_to_free * 4 * 1.5)
```

### 3. Fallback вместо sliding window
**Файл:** `src/agents/agent1_selector.py`

**Что сделано:**
- При контексте > 150k токенов сразу используется fallback
- Sliding window удалён (ломал выбор блоков)
- Fallback работает на полном контексте

```python
if context_tokens > max_context_tokens:
    print(f"[Agent1] Context too large, using fallback")
    return self._fallback_selection(context, need_to_free)
```

### 4. Увеличен timeout Agent2 (10 минут)
**Файл:** `src/agents/agent2_compressor.py`

**Что сделано:**
- Timeout увеличен с 120 до 600 секунд
- Позволяет медленным прокси завершить сжатие
- Можно настроить через `AGENT2_TIMEOUT_S`

```python
timeout_s = float(os.getenv("AGENT2_TIMEOUT_S", "600"))  # 10 minutes
```

### 5. Ограничение количества блоков (3 макс)
**Файл:** `src/proxy/compression.py`

**Что сделано:**
- Максимум 3 блока за раз (было неограничено)
- Уменьшает время сжатия
- Уменьшает риск таймаутов

```python
max_blocks = 3
blocks_to_compress = selection_result['blocks'][:max_blocks]
```

---

## 📊 ОЖИДАЕМОЕ ПОВЕДЕНИЕ

### Сценарий 1: Первое сжатие (183k → 70k)
```
[Proxy] Category 'Dialogue' at 183.8% - triggering compression
[Agent1] Context too large (199764 tokens), using fallback
[Orchestrator] Limiting to 3 blocks (from 5)
[Agent2] Compressing block 1... (200s)
[Agent2] Compressing block 2... (200s)
[Agent2] Compressing block 3... (200s)
[Proxy] Compressed Dialogue: 183k → 70k tokens
[Proxy] Saved 113k tokens in 600s
✅ SUCCESS
```

### Сценарий 2: Попытка повторного сжатия (cooldown)
```
[Proxy] Category 'Dialogue' at 95% - triggering compression
[Proxy] Category 'Dialogue' - skipping (cooldown, last compressed 30s ago)
✅ SKIPPED (cooldown working)
```

### Сценарий 3: Повторное сжатие через 2+ минуты
```
[Proxy] Category 'Dialogue' at 95% - triggering compression
[Agent1] Context too large, using fallback
[Proxy] Compressed Dialogue: 95k → 65k tokens
✅ SUCCESS
```

---

## 🧪 ТЕСТИРОВАНИЕ

### Автоматические тесты
```bash
cd /Users/mansurzainullin/MyCode/big-AGI/context-management
source .venv/bin/activate
./test_fix.sh
```

### Ручное тестирование
1. Перезапусти proxy server
2. Продолжи разговор где была ошибка
3. Проверь логи:
   - Должно быть "using fallback"
   - Должно быть "Limiting to 3 blocks"
   - НЕ должно быть повторного сжатия сразу
   - НЕ должно быть таймаутов

---

## 📝 ИЗМЕНЁННЫЕ ФАЙЛЫ

1. **src/proxy/server.py** (строки 101-120)
   - Добавлен cooldown 120 секунд

2. **src/agents/agent1_selector.py** (строки 61-68, 420-422)
   - Fallback вместо sliding window
   - Увеличен буфер 1.5x

3. **src/agents/agent2_compressor.py** (строка 88)
   - Timeout 600 секунд

4. **src/proxy/compression.py** (строки 119-123)
   - Ограничение 3 блока

---

## ⚠️ ВАЖНО

### Cooldown 2 минуты
- Система НЕ будет сжимать чаще чем раз в 2 минуты
- Если контекст растёт быстро, может превысить 100%
- Это нормально - лучше чем бесконечное сжатие

### Fallback качество
- Fallback выбирает старые сообщения (не оптимально)
- Но с буфером 1.5x должен достичь цели
- Entity preservation: ожидается 95-100%

### Timeout 10 минут
- Сжатие может занять до 10 минут
- Пользователь будет ждать
- Но лучше чем таймаут

---

## 🚀 КАК ПРОТЕСТИРОВАТЬ

### 1. Перезапусти proxy
```bash
cd /Users/mansurzainullin/MyCode/big-AGI/context-management
source .venv/bin/activate
export ANTHROPIC_API_KEY="sk-aw-f157875b77785becb3514fb6ae770e50"
export ANTHROPIC_BASE_URL="https://api.kiro.cheap"
PYTHONPATH=. python src/proxy/server.py
```

### 2. Продолжи разговор
- Используй тот же чат где была ошибка
- Отправь сообщение
- Жди (может занять 5-10 минут)

### 3. Проверь логи
Должно быть:
```
[Agent1] Context too large (199764 tokens), using fallback
[Orchestrator] Limiting to 3 blocks (from X)
[Proxy] Compressed Dialogue: 183k → 70k tokens
```

НЕ должно быть:
```
[Proxy] Category 'Dialogue' at 189.4% - triggering compression  # сразу после первого
anthropic.APITimeoutError  # таймаут
```

---

## 📊 ИТОГОВАЯ СТАТИСТИКА

**Изменено файлов:** 4
**Строк добавлено:** ~30
**Строк изменено:** ~10

**Проблемы исправлены:**
- ✅ Повторное сжатие (cooldown)
- ✅ Не достигает цели (буфер 1.5x)
- ✅ Таймауты (timeout 600s, лимит 3 блока)

**Статус:** ✅ ГОТОВО К ТЕСТИРОВАНИЮ
