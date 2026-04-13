//! ECS glue between ARK codegen output and `hecs`.
//!
//! `hecs` is an archetype-based ECS — components are plain Rust structs
//! that you `spawn` into a `World` as tuples, and query back with
//! `world.query::<(&A, &B)>()`. The codegen already emits per-class
//! structs (e.g. `struct Vehicle { speed: f32, fuel: f32 }`), so there
//! is no wrapper layer needed per component — we just re-export the
//! pieces of `hecs` we use and provide an `EcsWorld` newtype with the
//! 4 lifecycle ops the rest of the runtime actually cares about:
//! spawn, despawn, count, iterate.
//!
//! The newtype also gives us a stable API surface that future migrations
//! (to `bevy_ecs` or a hand-rolled SoA store) can replace without
//! ripping out call sites.

pub use hecs::{Entity, World};

/// Thin façade over `hecs::World` with a small, deliberately boring API.
///
/// If you need the full hecs surface, call `.inner_mut()` and use it
/// directly — the façade exists for discoverability and to keep the
/// common path short.
#[derive(Default)]
pub struct EcsWorld {
    world: World,
}

impl EcsWorld {
    /// Create a fresh empty world.
    pub fn new() -> Self {
        Self::default()
    }

    /// Borrow the underlying `hecs::World` for direct use (queries
    /// with multiple components, change detection, etc.).
    pub fn inner(&self) -> &World {
        &self.world
    }

    pub fn inner_mut(&mut self) -> &mut World {
        &mut self.world
    }

    /// Spawn an entity with one or more components. Accepts any
    /// `hecs::DynamicBundle`, which includes tuples like `(A,)`,
    /// `(A, B)`, etc. Returns the new `Entity` handle.
    pub fn spawn<B: hecs::DynamicBundle>(&mut self, components: B) -> Entity {
        self.world.spawn(components)
    }

    /// Despawn an entity and return whether it was present.
    pub fn despawn(&mut self, e: Entity) -> bool {
        self.world.despawn(e).is_ok()
    }

    /// Count entities that carry component `C`.
    pub fn count<C: hecs::Component>(&self) -> usize {
        self.world.query::<&C>().iter().count()
    }

    /// Total entity count across all archetypes.
    pub fn len(&self) -> usize {
        self.world.iter().count()
    }

    pub fn is_empty(&self) -> bool {
        self.world.iter().next().is_none()
    }

    /// Visit every component `C` with a mutable reference. The callback
    /// is the caller's systems tick — one place in the codebase where
    /// the tick loop is hooked up.
    pub fn for_each_mut<C: hecs::Component>(&mut self, mut f: impl FnMut(&mut C)) {
        for (_entity, c) in self.world.query_mut::<&mut C>() {
            f(c);
        }
    }
}

// ============================================================
// Tests
// ============================================================

#[cfg(test)]
mod tests {
    use super::*;

    // Test-local components matching the shape of codegen-emitted structs.
    #[derive(Debug, Clone, PartialEq)]
    struct Position {
        x: f32,
        y: f32,
    }

    #[derive(Debug, Clone, PartialEq)]
    struct Velocity {
        dx: f32,
        dy: f32,
    }

    #[test]
    fn new_world_is_empty() {
        let w = EcsWorld::new();
        assert!(w.is_empty());
        assert_eq!(w.len(), 0);
        assert_eq!(w.count::<Position>(), 0);
    }

    #[test]
    fn spawn_and_count_single_component() {
        let mut w = EcsWorld::new();
        w.spawn((Position { x: 1.0, y: 2.0 },));
        w.spawn((Position { x: 3.0, y: 4.0 },));
        w.spawn((Position { x: 5.0, y: 6.0 },));
        assert_eq!(w.len(), 3);
        assert_eq!(w.count::<Position>(), 3);
        assert_eq!(w.count::<Velocity>(), 0);
    }

    #[test]
    fn spawn_multi_component_tuples() {
        let mut w = EcsWorld::new();
        w.spawn((Position { x: 1.0, y: 2.0 }, Velocity { dx: 0.1, dy: -0.1 }));
        w.spawn((Position { x: 3.0, y: 4.0 },)); // only Position
        assert_eq!(w.count::<Position>(), 2);
        assert_eq!(w.count::<Velocity>(), 1);
    }

    #[test]
    fn despawn_removes_entity() {
        let mut w = EcsWorld::new();
        let a = w.spawn((Position { x: 1.0, y: 2.0 },));
        let b = w.spawn((Position { x: 3.0, y: 4.0 },));
        assert_eq!(w.len(), 2);
        assert!(w.despawn(a));
        assert_eq!(w.len(), 1);
        // Second despawn of the same entity is a no-op (returns false).
        assert!(!w.despawn(a));
        assert!(w.despawn(b));
        assert!(w.is_empty());
    }

    #[test]
    fn for_each_mut_advances_positions_like_a_tick() {
        let mut w = EcsWorld::new();
        w.spawn((Position { x: 0.0, y: 0.0 },));
        w.spawn((Position { x: 10.0, y: 20.0 },));
        // Pretend this is a system: step each Position by (1, 1).
        w.for_each_mut(|p: &mut Position| {
            p.x += 1.0;
            p.y += 1.0;
        });
        // Collect back via direct hecs query and assert the tick landed.
        let ps: Vec<Position> = w
            .inner()
            .query::<&Position>()
            .iter()
            .map(|(_, p)| p.clone())
            .collect();
        // Positions are not ordered by hecs — check as a set.
        assert!(ps.contains(&Position { x: 1.0, y: 1.0 }));
        assert!(ps.contains(&Position { x: 11.0, y: 21.0 }));
    }
}
