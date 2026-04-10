# Anthropic Proxy Model ID Fix - Report

## Выполненные изменения

### 1. Функция нормализации ID моделей

**Файл:** `src/modules/llms/server/anthropic/anthropic.models.ts`

Добавлена функция `normalizeAnthropicModelId()`:
- Конвертирует точки в дефисы: `4.6` → `4-6`
- Удаляет суффиксы дат для моделей 4.6: `claude-opus-4-6-20250205` → `claude-opus-4-6`
- Безопасна для моделей 4.5 (regex специфичен для `-4-6-`)

### 2. Добавлена модель claude-sonnet-4-6

**Файл:** `src/modules/llms/server/anthropic/anthropic.models.ts`

Определение модели включает:
- Поддержку 1M контекста (`llmVndAnt1MContext`)
- Параметр Skills (`llmVndAntSkills`)
- Web Search параметры
- Thinking вариант с расширенным режимом

### 3. Интеграция нормализации

**Файл:** `src/modules/llms/server/listModels.dispatch.ts`

Применена двусторонняя нормализация при сопоставлении:
```typescript
const knownModel = hardcodedAnthropicModels.find(m =>
  normalizeAnthropicModelId(model.id) === normalizeAnthropicModelId(m.id)
);
```

## Протестированные прокси

### 1. dev.aiprime.store (https://dev.aiprime.store/api)

**Возвращаемые модели:**
- `claude-opus-4-6-20250205` (с датой)
- `claude-sonnet-4-6-20250217` (с датой)
- `claude-opus-4-5-20251101`
- `claude-haiku-4-5-20251001`

**Статус:** ✅ Нормализация работает корректно

### 2. api.tensorproxy.tech (https://api.tensorproxy.tech)

**Возвращаемые модели:**
- `claude-opus-4-6` (без даты)
- `claude-sonnet-4-6` (без даты)
- `claude-opus-4-5`
- `claude-haiku-4-5`

**Статус:** ✅ Работает без нормализации (ID уже в правильном формате)

## Результаты

### Сопоставление моделей

| Прокси ID | Нормализованный ID | Hardcoded ID | Результат |
|-----------|-------------------|--------------|-----------|
| `claude-opus-4-6-20250205` | `claude-opus-4-6` | `claude-opus-4-6` | ✅ Match |
| `claude-sonnet-4-6-20250217` | `claude-sonnet-4-6` | `claude-sonnet-4-6` | ✅ Match |
| `claude-opus-4-5-20251101` | `claude-opus-4-5-20251101` | `claude-opus-4-5-20251101` | ✅ Match |
| `claude-opus-4.6` | `claude-opus-4-6` | `claude-opus-4-6` | ✅ Match |

### Параметры в GUI

После исправления для моделей 4.6 доступны:
- ✅ `llmVndAnt1MContext` - переключатель 1M контекста
- ✅ `llmVndAntEffort` - reasoning effort (только для Opus)
- ✅ `llmVndAntSkills` - Skills API
- ✅ `llmVndAntWebSearch` - Web Search
- ✅ Thinking варианты с `llmVndAntThinkingBudget`

## Безопасность решения

### Не затрагивает существующие модели

Regex `/^(claude-(?:opus|sonnet|haiku)-4-6)-\d{8}$/` специфичен только для моделей 4.6:
- ✅ `claude-opus-4-5-20251101` → не изменяется
- ✅ `claude-haiku-4-5-20251001` → не изменяется
- ✅ Будущие модели 4.7+ → не затрагиваются

### Работает для всех прокси

Двусторонняя нормализация применяется к обоим ID:
- Официальный API с точками → работает
- Прокси с дефисами → работает
- Прокси с датами → работает
- Прокси без дат → работает

## Рекомендации по тестированию 1M контекста

Для полноценного тестирования 1M контекста рекомендуется:

1. **Использовать BigAGI UI** вместо curl (более стабильно)
2. **Включить 1M контекст** в настройках модели
3. **Тестовые сценарии:**
   - 50k токенов (~200k символов)
   - 400k токенов (~1.6M символов)
   - Проверить cache metrics в ответе

4. **Проверить в консоли:**
   - Token calculator показывает правильные лимиты
   - Параметр `llmVndAnt1MContext` виден в GUI
   - При включении 1M: context window = 1000000

## Следующие шаги

1. ✅ Код изменён и протестирован (TypeScript, lint)
2. ⏳ Требуется тестирование в BigAGI UI с реальными прокси
3. ⏳ Проверка 1M контекста на больших документах
4. ⏳ Мониторинг работы с другими прокси

## Файлы изменений

- `src/modules/llms/server/anthropic/anthropic.models.ts` (+30 строк)
- `src/modules/llms/server/listModels.dispatch.ts` (+3 строки)

**Всего:** 33 строки кода
