// Generated from ARK DSL — do not edit manually
// Entity: class RoleMemory
// Strategy: code

#[derive(Debug, Clone)]
pub struct RoleMemory {
    pub role: String,  // default: ""planner""
    pub capacity: i32,  // default: 200_f32
    pub entries: i32,  // default: 0_f32
}

impl RoleMemory {
    /// Construct with spec defaults. Generated from ARK $data defaults.
    #[inline]
    pub fn new() -> Self {
        Self {
            role: ""planner"",
            capacity: 200_i32,
            entries: 0_i32,
        }
    }
}

impl Default for RoleMemory {
    #[inline]
    fn default() -> Self { Self::new() }
}

impl RoleMemory {
    /// Check all invariants. Generated from ARK spec.
    #[inline]
    pub fn check_invariants(&self, new_entry: String, prune: bool) -> bool {
        let inv_0 = (self.entries >= 0_i32);
        let inv_1 = (self.entries <= self.capacity);
        inv_0 && inv_1
    }
}

impl RoleMemory {
    /// Process rule #0 (strategy: code)
    #[inline]
    pub fn process_0(&mut self, new_entry: String, prune: bool) {
        debug_assert!((self.entries >= 0_i32), "precondition failed");
        debug_assert!((self.entries <= self.capacity), "postcondition failed");
    }
}