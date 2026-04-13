# ARK — Architecture Kernel

Декларативная система описания игрового движка.
Всё есть граф сущностей, связей и правил.

## Четыре примитива

```
@in{}           — что входит
#process[]{}    — что происходит  
@out[]          — что выходит
$data           — что хранится
```

Эти четыре символа описывают **всё** — от игрового объекта
до build pipeline и оркестрации агентов.

## Три уровня

```
abstraction  — контракт без реализации (скелет)
class        — конкретная реализация
instance     — живой объект
```

## Структура проекта

```
ark/
├── docs/DSL_SPEC.md         # Спецификация языка
├── specs/                    # .ark файлы — источник истины
│   ├── root.ark             # Якорная точка
│   ├── game/                # Игровые подсистемы
│   ├── infra/               # Инфраструктура (сеть, серверы)
│   └── pipeline/            # Build/asset pipeline
├── dsl/                     # Парсер и AST
│   ├── grammar/ark.pest     # PEG-грамматика
│   ├── stdlib/              # Стандартная библиотека типов
│   └── src/lib.rs           # Парсер → AST
├── codegen/                 # Генерация C++/Rust/Proto
├── verify/                  # SMT-верификация (Z3)
├── runtime/                 # wgpu + ECS runtime
├── orchestrator/            # Агентная оркестрация
└── skills/claude-code/      # Skill для Claude Code
```

## Принципы

1. **DSL — единственный источник истины.** Код генерируется, не пишется.
2. **Острова изолированы.** Общение только через типизированные порты.
3. **Стратегия явная.** Каждый остров декларирует: tensor / code / asm / gpu / verified / script.
4. **AI — последний resort.** Оркестратор предпочитает скрипты и codegen. Агент вызывается только для решений, требующих рассуждения.
5. **Один корень.** `root.ark` — якорная точка. Всё растёт от неё.

## Quick Start

```bash
# Парсинг .ark файла в JSON AST
cargo run -p ark-dsl -- parse specs/root.ark

# Генерация Rust-кода
cargo run -p ark-codegen -- specs/game/vehicle.ark --target rust

# Верификация инвариантов
cargo run -p ark-verify -- specs/game/vehicle.ark

# Анализ влияния изменений
cargo run -p ark-verify -- impact specs/game/vehicle.ark
```

## Для Claude Code

Установи skill из `skills/claude-code/` и используй для работы
с .ark файлами. Skill знает синтаксис, workflow, и паттерны.
