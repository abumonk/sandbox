// Generated from ARK DSL — do not edit manually
// Entity: abstraction Movable
// Strategy: code

#[derive(Debug, Clone, Default)]
pub struct Movable {
}

impl Movable {
    /// Check all invariants. Generated from ARK spec.
    #[inline]
    pub fn check_invariants(&self, throttle: f32, dt: f32) -> bool {
        let inv_0 = (throttle >= 0_f32);
        inv_0
    }
}