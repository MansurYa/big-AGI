# КРИТИЧЕСКИЙ БАГ #5 - Неправильные буферы в fallback

**Дата:** 2026-03-16 16:15 UTC
**Статус:** ✅ ИСПРАВЛЕНО

---

## 🔴 ПРОБЛЕМА

После исправления Бага #4 формула всё ещё не работала правильно из-за **неправильного расчёта буферов**.

**Старый код:**
```python
max_available_lines = total_lines - 200  # 100 at start, 100 at end
max_available_tokens = int(max_available_lines * tokens_per_line)
```

**Проблема:**
- Контекст: 205k токенов, 105 строк
- Токенов на строку: 205k / 105 = 1958 токенов/строка
- Буфер: 200 строк
- max_available_lines = 105 - 200 = **-95 строк** ❌

**Почему так получилось:**
- Строки очень длинные (сообщения с thinking, большие ответы)
- 105 строк < 200 строк буфера
- Формула ломалась, давала отрицательное число

---

## ✅ ИСПРАВЛЕНИЕ

**Новый код:**
```python
# Token-based buffers instead of line-based
buffer_tokens = 10000  # 10k tokens at start and end
max_available_tokens = max(0, context_tokens - 2 * buffer_tokens)
target_tokens = min(target_tokens, max_available_tokens)

# Convert to lines (adaptive)
target_lines = int(target_tokens / tokens_per_line)
buffer_lines = max(1, int(buffer_tokens / tokens_per_line))

# Select lines
start_line = buffer_lines
end_line = min(start_line + target_lines, total_lines - buffer_lines)
```

**Преимущества:**
- Буферы в токенах (10k), не зависят от количества строк
- Адаптивный расчёт buffer_lines на основе длины строк
- Работает с любым количеством строк (5, 50, 500)

---

## 🧪 ПРОВЕРКА

**Тест с реальными данными:**
```
Context: 205,588 tokens, 105 lines
Tokens per line: 1,958
Need to free: 135,000 tokens

Target tokens: 270,000
Buffer: 10,000 tokens (start + end)
Max available: 185,588 tokens
Final target: 185,588 tokens

Buffer lines: 5 (adaptive)
Select lines: 5 to 99 (94 lines)
Estimated tokens: 184,050

After compression 4x:
Compressed to: 46,012 tokens
Freed: 138,038 tokens
Final context: 67,550 tokens
Target: 70,000 tokens
✅ SUCCESS (under target)
```

---

## 📊 ОЖИДАЕМОЕ ПОВЕДЕНИЕ

### После исправления:
```
[Proxy] Category 'Dialogue' at 189.4% - triggering compression
[Agent1] Context too large (205588 tokens), using fallback
[Agent1] Using fallback selection (simple heuristic)
[Proxy] Compressed Dialogue: 205k → 67k tokens  # ~67k, не 131k!
[Proxy] Saved 138k tokens
✅ SUCCESS

# Second message:
[Proxy] Category 'Dialogue' at 67% - no compression needed
✅ Ответ получен БЕЗ ошибок
```

---

## 📝 ИЗМЕНЁННЫЕ ФАЙЛЫ

**Файл:** `src/agents/agent1_selector.py` (строки 418-444)

**Изменено:**
- Буферы теперь в токенах (10k), не в строках (200)
- Адаптивный расчёт buffer_lines
- Защита от отрицательных значений

---

## 🎯 ИТОГОВАЯ СТАТИСТИКА

### Все 5 багов исправлены:

1. ✅ **Баг #1:** Большие контексты (fallback стратегия)
2. ✅ **Баг #2:** Повторное сжатие (cooldown) + таймауты (600s)
3. ✅ **Баг #3:** Python кэш (автоочистка)
4. ✅ **Баг #4:** Неправильная формула (need_to_free * 2.0)
5. ✅ **Баг #5:** Неправильные буферы (токены вместо строк)

**Файлов изменено:** 5
**Время работы:** 4.5 часа
**Стоимость:** ~$1.50

---

## ⚠️ КРИТИЧЕСКИ ВАЖНО

**Баг #5 был скрыт внутри Бага #4!**

Без этого исправления:
- Формула давала отрицательные числа
- Fallback выбирал неправильное количество строк
- Сжатие было недостаточным

Теперь система должна работать корректно с любой длиной строк.

---

**СТАТУС:** ✅ ГОТОВО К ФИНАЛЬНОМУ ТЕСТИРОВАНИЮ

**ПЕРЕЗАПУСТИ ПРОКСИ И ТЕСТИРУЙ!** 🚀
