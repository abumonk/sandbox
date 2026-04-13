# CLAUDE.md — Инструкции для Claude Code по проекту ARK

## Что это

ARK (Architecture Kernel) — декларативная система описания игрового движка MMO.
Всё описывается через `.ark` спецификации. Код генерируется, не пишется.
Ты (Claude Code) — основной инструмент разработки. Работай с .ark файлами
напрямую, запускай инструменты, итерируй быстро.

## Первый запуск

```bash
# 1. Клонировать / распаковать проект
cd ~/projects/ark  # или где лежит проект

# 2. Установить Python-зависимости
pip install lark-parser z3-solver

# 3. Проверить что всё работает
python ark.py pipeline specs/test_minimal.ark

# Ожидаемый результат:
# [1/4] Parsing...     ✓ 6 items
# [2/4] Verifying...   1/2 passed, 1 failed (это нормально — тестовый баг)
# [3/4] Codegen...     ✓ 3 files
# [4/4] Graph...       ✓ HTML
```

Если `ark.py pipeline` прошёл — среда готова.

## Структура проекта

```
ark/
├── ark.py                    # ТОЧКА ВХОДА — единый CLI
├── CLAUDE.md                 # ЭТА ИНСТРУКЦИЯ
├── docs/DSL_SPEC.md          # Спецификация языка ARK (ЧИТАЙ ПЕРВЫМ)
│
├── specs/                    # .ark файлы — ЕДИНСТВЕННЫЙ ИСТОЧНИК ИСТИНЫ
│   ├── root.ark              # Якорь. Всё растёт отсюда.
│   ├── test_minimal.ark      # Минимальный тест парсера
│   └── game/
│       └── vehicle_physics.ark  # Пример: Vehicle подсистема
│
├── tools/                    # Python-инструменты (рабочие, проверенные)
│   ├── parser/
│   │   ├── ark_grammar.lark  # Грамматика (Lark EBNF)
│   │   └── ark_parser.py     # Парсер → AST → JSON
│   ├── verify/
│   │   ├── ark_verify.py     # Z3 SMT верификатор
│   │   └── ark_impact.py     # Анализ влияния изменений
│   ├── codegen/
│   │   └── ark_codegen.py    # Генерация Rust / C++ (UE5) / Protobuf
│   └── visualizer/
│       └── ark_visualizer.py # Интерактивный HTML-граф с LOD
│
├── dsl/                      # Rust-реализация (каркас, pest grammar)
│   ├── grammar/ark.pest      # PEG грамматика для Rust
│   ├── stdlib/types.ark      # Стандартные типы
│   └── src/lib.rs            # AST-определения
│
├── codegen/                  # Rust crate (каркас)
├── verify/                   # Rust crate (каркас)
├── runtime/                  # Rust crate (каркас)
├── orchestrator/             # Rust crate (каркас)
├── skills/claude-code/       # Skill-файл
│   └── SKILL.md
└── Cargo.toml                # Rust workspace
```

## Команды CLI

```bash
# Парсинг в JSON AST
python ark.py parse specs/game/vehicle_physics.ark

# Z3 верификация инвариантов
python ark.py verify specs/game/vehicle_physics.ark

# Анализ влияния: "что сломается если поменять Vehicle?"
python ark.py impact specs/test_minimal.ark Vehicle

# Генерация кода (rust | cpp | proto)
python ark.py codegen specs/game/vehicle_physics.ark --target rust
python ark.py codegen specs/game/vehicle_physics.ark --target cpp --out generated/

# Интерактивный граф
python ark.py graph specs/test_minimal.ark

# Полный pipeline: parse → verify → codegen → graph
python ark.py pipeline specs/test_minimal.ark --target rust
```

## Четыре фундаментальных примитива

Запомни — они используются ВЕЗДЕ, на каждом уровне:

```
@in{}           — входной порт (что сущность принимает)
#process[]{}    — правило обработки (что происходит)
@out[]          — выходной порт (что сущность производит)
$data           — состояние (что хранится)
```

## Три уровня сущностей

```
abstraction  — скелет, контракт без реализации
class        — конкретная реализация с $data и #process
instance     — живой объект в runtime
```

## Workflow: как работать с проектом

### Создание новой подсистемы

1. Прочитай `docs/DSL_SPEC.md` для синтаксиса
2. Создай .ark файл в `specs/game/` (или `specs/infra/` для инфраструктуры)
3. Начни с `abstraction` — определи контракт (@in/@out/invariant)
4. Реализуй как `class` — добавь $data, #process, strategy
5. Оберни в `island` — задай strategy для группы, memory, contains
6. Если связан с другим островом — создай `bridge` с `contract`
7. Добавь `verify` блок с проверками
8. Зарегистрируй в `specs/root.ark` → `registry SystemRegistry`
9. Запусти `python ark.py pipeline specs/game/new_system.ark`
10. Если verify нашёл баги — исправь .ark, повтори с шага 9

### Модификация существующей подсистемы

1. Запусти impact ДО изменений: `python ark.py impact file.ark EntityName`
2. Внеси изменения в .ark файл
3. Запусти verify: `python ark.py verify file.ark`
4. Если verify пройден — запусти codegen
5. Если verify не пройден — Z3 покажет контрпример, исправь спеку

### Выбор стратегии для #process

```
strategy: tensor      — когда: однородные данные, массовая обработка, SoA
                        пример: позиции 10000 сущностей, heightmap batch
                        codegen: Rust SoA batch structs + SIMD-ready

strategy: code        — когда: ветвистая логика, условия, мало данных
                        пример: AI поведение, квесты, UI
                        codegen: обычные Rust/C++ классы

strategy: asm_avx2    — когда: hot loop, точно знаем layout, нужен SIMD
                        пример: broadphase коллизий, terrain deform
                        codegen: Rust с #[inline] + intrinsics placeholder

strategy: gpu_compute — когда: параллелизм >1000, texture/buffer данные
                        пример: эрозия, частицы, пост-обработка
                        codegen: WGSL shader stub

strategy: verified    — когда: протокол, контракт, критичная корректность
                        пример: entity handoff, state sync
                        codegen: Rust + Z3 assertions

strategy: script      — когда: часто меняется, не критично по перфу
                        пример: скрипты квестов, конфиг, баланс
                        codegen: Lua/Wren bindings
```

## Приоритеты выполнения

Оркестратор (root.ark → Orchestrator) выбирает способ выполнения:

```
priority 100: script/codegen  — детерминированные операции без AI
priority  80: verify          — Z3 solver, тоже детерминированный
priority  50: agent           — Claude Code, когда нужно рассуждение
```

ПРАВИЛО: если задачу можно выполнить скриптом или codegen — ДЕЛАЙ ТАК.
AI (ты) используется ТОЛЬКО для:
- Проектирование новых .ark спеков
- Решения о стратегии / архитектуре
- Диагностика сложных верификационных ошибок
- Написание нового функционала для tools/

## Текущее состояние и что нужно делать

### Работает сейчас (проверено)
- [x] Парсер: .ark → JSON AST (все 6 типов items)
- [x] Z3 верификатор: $data constraints, invariant checks
- [x] Codegen: Rust (AoS + SoA batch), C++ (UE5 USTRUCT), Protobuf
- [x] Impact analyzer: зависимости, мосты, re-verification
- [x] Визуализатор: HTML граф с 3 LOD-уровнями
- [x] Unified CLI: ark.py с 6 командами
- [x] Полный pipeline: parse → verify → codegen → graph

### Бэклог (по приоритету)

#### Приоритет 1 — Парсер / Codegen глубина  ✅ ЗАКРЫТ
- [x] Parser: раздельное хранение класса и его инстансов (SeparateInstanceStorageTask — classes/instances/island_classes индексы, Python + Rust dsl)
- [x] Codegen: генерация тел #process (ProcessBodiesTask)
- [x] Codegen: SoA batch process_all() с реальными формулами (SoAProcessAllTask)
- [x] Codegen: default values в конструкторах Rust-структур (DefaultValuesTask)
- [x] Парсер: robustness — ArkParseError со snippet/caret/expected (ParserRobustnessTask)
- [x] Парсер: import resolution — stdlib/types.ark подключается (ImportResolutionTask)
- [x] Grammar: primitive/struct/enum для stdlib (StdlibKeywordsTask — добыто из import work)
- [x] Тесты: 25 pytest-тестов для всех типов .ark сущностей (UnitTestsTask)
- [x] Parser: bridge_body flatten + true/false atom order (ParserBugfixTask — вскрыто тестами)

#### Приоритет 2 — Верификация глубина  ✅ ЗАКРЫТ
- [x] Verify: трансляция ВСЕХ выражений #process в Z3 (VerifyFullExprTask — assignment-body + post-obligation check, поймал баг в Backlog spec)
- [x] Verify: проверка bridge contracts (type matching между портами) (BridgeContractTask)
- [x] Verify: temporal properties через bounded model checking (TemporalBMCTask — K=10 BMC, □ only, PASS_BOUNDED/FAIL/UNKNOWN)
- [x] `ark diff` — семантический diff двух версий .ark файла (ArkDiffTask — structural AST diff, Change-records, CLI subcommand)

#### Приоритет 3 — Оркестратор  ✅ ЗАКРЫТ
- [x] Оркестратор: чтение root.ark → реальный execution pipeline (OrchestratorRootTask — Rust, phase-grouped DAG с bridge-рёбрами)
- [x] Оркестратор: file watcher → auto re-verify → auto re-codegen (FileWatcherTask — stdlib-only polling Watcher, `ark watch`)
- [x] Оркестратор: задачи для Claude Code через .ark спеки (ClaudeTaskBridgeTask — dispatch planner `ark dispatch`)

#### Приоритет 4 — Runtime прототип
- [x] Runtime: wgpu + winit окно — скаффолдинг (WgpuWindowTask). Реальный backend отложен в WgpuBackendTask
- [ ] Runtime: реальный wgpu+winit backend (WgpuBackendTask — follow-up)
- [x] Runtime: ECS (hecs) интеграция с codegen output (HecsEcsTask — EcsWorld façade над hecs 0.10)
- [x] Runtime: загрузка island → исполнение tick loop из root.ark (IslandTickLoopTask — Runtime struct + WindowApp-driven tick)

#### Приоритет 5 — Перенос на Rust  ✅ ЗАКРЫТ
- [x] Rust-парсер: pest Pairs → ArkFile AST (PestParseRsTask)
- [x] Rust-codegen: 282 loc, 5 тестов зелёных, SoA вынесен отдельно (RustCodegenTask)
- [x] Rust-verify: ArkFile → .smt2 текст, без libz3 (SmtLibTask — пошли через SMT-LIB2, не z3-sys)
- [x] Rust-orchestrator: parse→verify→codegen DAG, 3 теста (OrchestratorRsTask — частично закрывает P3)

### Игровые подсистемы (создавать по мере готовности tooling)
- [ ] specs/game/terrain_system.ark — Terrain + deformation
- [ ] specs/game/network_layer.ark — MMO dispatcher + entity sync
- [ ] specs/game/audio_mixer.ark — Audio island
- [ ] specs/infra/asset_pipeline.ark — Asset cook pipeline
- [ ] specs/infra/build_system.ark — Build orchestration

## Типичные сессии

### "Создай новый остров для террейна"
```bash
# 1. Ты создаёшь specs/game/terrain_system.ark
# 2. Запусти verify
python ark.py verify specs/game/terrain_system.ark
# 3. Запусти codegen
python ark.py codegen specs/game/terrain_system.ark --target rust --out generated/rust/
# 4. Запусти impact чтобы увидеть связи
python ark.py impact specs/game/terrain_system.ark TerrainSystem
# 5. Обнови root.ark — добавь в registry
# 6. Запусти graph чтобы визуализировать
python ark.py graph specs/game/terrain_system.ark
```

### "Улучши codegen — добавь тела #process"
```bash
# 1. Открой tools/codegen/ark_codegen.py
# 2. Найди gen_rust_entity → _gen_rust_aos / _gen_rust_soa
# 3. В секции "Process methods" — заполни body generation
# 4. Тестируй на specs/test_minimal.ark:
python ark.py codegen specs/test_minimal.ark --target rust
# 5. Проверь что сгенерированный Rust валиден:
#    (если Rust доступен)
#    cd generated && cargo check
```

### "Добавь поддержку нового типа в DSL"
```bash
# 1. Добавь тип в dsl/stdlib/types.ark
# 2. Добавь маппинг в tools/codegen/ark_codegen.py → RUST_TYPES / CPP_TYPES / PROTO_TYPES
# 3. Тестируй: создай .ark файл использующий новый тип
# 4. Запусти pipeline
```

## Принципы при работе

1. **DSL first** — никогда не пиши игровой код напрямую. Сначала .ark, потом codegen.
2. **Verify before codegen** — всегда проверяй инварианты перед генерацией.
3. **Impact before change** — всегда проверяй влияние перед модификацией.
4. **Minimal AI** — если можешь сделать задачу через ark.py — делай. Не рассуждай, выполняй.
5. **One island at a time** — не пытайся собрать всё сразу. Один остров, одна верификация, один codegen.
6. **Root anchors everything** — root.ark всегда актуален. Обновляй registry при добавлении островов.
7. **Auto-tick** — см. ниже.

## Auto-tick (цепная работа по бэклогу)

После того как **все задачи текущего тика закрыты** (`status = "done"`, `in_flight = 0`), автоматически начни следующий тик без ожидания команды от пользователя.

**Критерий готовности тика:**
- Целевая задача помечена `done` в `specs/meta/backlog.ark`
- `Backlog.done_count` и `ArkBacklog.done_count` инкрементированы
- Регрессия прошла: `pytest tests/` зелёный, `python ark.py verify specs/meta/backlog.ark` зелёный
- Тестовый summary напечатан пользователю

**Выбор следующей задачи** (в порядке применения):
1. Минимальный `priority` (1 = срочно, 5 = отложено)
2. При равенстве приоритета — наименьший scope (предпочитай узкие, ограниченные задачи большим open-ended)
3. При равенстве scope — задачи, продолжающие цепочку разблокировки уже тронутого файла (cohesion)

**Стоп-условия (не делать auto-tick, отчитаться пользователю):**
- `done_count == total` — бэклог пуст.
- Все оставшиеся ready-задачи требуют архитектурного решения от пользователя (выбор подхода, неочевидный scope, открытые вопросы дизайна).
- Последний тик обнаружил **побочную проблему** — не начинай её фиксить без подтверждения, даже если понимаешь как.
- Регрессия упала (красные тесты или failed verify) — остановиться и чинить, не продолжать.
- Подряд прошло **≥ 5 auto-тиков** — пауза для sanity check, показать пользователю сводку и ждать команды.
- Пользователь явно сказал «стоп», «пауза», «хватит» или аналогично.

**При срабатывании стоп-условия:** одним абзацем сообщи состояние бэклога (`done/total`), что именно блокирует, и дождись команды.
