# ARK DSL Specification v0.1

## Philosophy

ARK (Architecture Kernel) — декларативный язык описания систем.
Всё есть граф сущностей, связей и правил.
Код генерируется, а не пишется.

## Четыре фундаментальные абстракции

Эти символы существуют на **каждом** уровне системы — от описания
игрового объекта до оркестрации build pipeline.

### `@in{}` — входной порт

Декларирует что сущность **принимает**. Типизированный вход.

```ark
@in{ position: Vec3, velocity: Vec3, dt: Float }
```

### `#process[]{}` — правило обработки

Декларирует **что происходит**. Содержит условия, приоритеты,
стратегию выполнения. Квадратные скобки — метаданные/модификаторы.
Фигурные — тело правила.

```ark
#process[strategy: tensor, priority: 10]{
  position' = position + velocity * dt
  invariant: position'.valid()
}
```

### `@out[]` — выходной порт

Декларирует что сущность **производит**. Квадратные скобки —
метаданные выхода (формат, гарантии).

```ark
@out[guaranteed: true]{ position': Vec3, velocity': Vec3 }
```

### `$data` — данные/состояние

Декларирует хранимое состояние. Не вход и не выход — 
внутренние данные сущности.

```ark
$data fuel: Float [0..100] = 100.0
$data wheels: Int {2, 4, 6} = 4
```

## Три уровня сущностей

### `abstraction` — скелет без деталей

```ark
abstraction Drivable {
  @in{ throttle: Float }
  #process[]{
    requires: $data fuel > 0
    // нет конкретной реализации — только контракт
  }
  @out[]{ movement: Vec3 }
  
  invariant: fuel >= 0
  temporal: □(fuel = 0 → movement = Vec3.zero)
}
```

### `class` — конкретная реализация

```ark
class Vehicle : Drivable {
  $data fuel: Float [0..100] = 100.0
  $data speed: Float [0..max_speed] = 0.0
  $data wheels: Int {2, 4, 6} = 4
  
  @in{ throttle: Float, dt: Float }
  
  #process[strategy: code, priority: 10]{
    pre:  fuel > throttle * burn_rate * dt
    speed' = clamp(speed + throttle * accel * dt, 0, max_speed)
    fuel'  = fuel - throttle * burn_rate * dt
    post: fuel' >= 0
  }
  
  @out[guaranteed: true]{ speed': Float, fuel': Float }
}
```

### `instance` — живой объект

```ark
instance player_car: Vehicle {
  fuel = 75.0
  wheels = 4
  // наследует все process и invariant от Vehicle
}
```

## Острова (Islands)

Остров — группа связанных сущностей с единой стратегией выполнения.

```ark
island VehiclePhysics {
  strategy: tensor
  memory: { pool(Vehicle, max: 10000), arena(16MB, per_frame) }
  
  contains: [Vehicle, Wheel, Suspension]
  
  @in{ world_state: WorldSnapshot }
  @out[]{ physics_results: PhysicsOutput }
  
  #process[tick]{
    // тензорная обработка всех Vehicle за один проход
    for_all Vehicle as v:
      v.process(world_state.extract(v))
  }
}
```

## Связи между островами

```ark
bridge Physics_to_Terrain {
  from: VehiclePhysics.@out.physics_results
  to:   TerrainSystem.@in.collision_data
  
  contract {
    type_match: true
    invariant: data.valid()
    temporal: latency <= 1 tick
  }
}
```

## Стратегии выполнения

```ark
#process[strategy: tensor]{}   // тензорная свёртка, массовые SoA
#process[strategy: code]{}     // обычная кодогенерация C++/Rust
#process[strategy: asm_avx2]{} // ручная SIMD-вставка
#process[strategy: gpu_compute]{} // compute shader (WGSL/HLSL)
#process[strategy: verified]{}  // SMT-верифицированный протокол
#process[strategy: script]{}    // интерпретируемый (Lua/Wren)
```

## Система условий и приоритетов

```ark
#process[
  priority: 10,          // порядок выполнения
  condition: fuel > 0,   // условие активации
  fallback: idle_process  // если условие не выполнено
]{}
```

## Метаданные для оркестрации

Те же абстракции работают для build pipeline:

```ark
island AssetPipeline {
  strategy: code
  
  class ImportJob {
    @in{ raw_file: Path, format: AssetFormat }
    #process[priority: by_dependency]{
      // импорт ассета
    }
    @out[]{ cooked_asset: Asset }
  }
  
  class BuildJob {
    @in{ sources: [SourceFile], config: BuildConfig }
    #process[
      strategy: code,
      condition: any(sources.changed),
      priority: dependency_order
    ]{
      // компиляция
    }
    @out[]{ binary: Artifact }
  }
}
```

## Верификация

```ark
verify VehiclePhysics {
  // SMT-проверки (Z3)
  check invariants_hold: 
    for_all transition in Vehicle:
      pre(transition) ∧ body(transition) → post(transition)
  
  check no_deadlock:
    for_all state in Vehicle:
      exists transition: pre(transition, state)
  
  // Темпоральные свойства (model checking)
  check respawn:
    □(player.health = 0 → ◇ player.alive)
}
```
