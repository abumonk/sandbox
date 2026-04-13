// Generated from ARK DSL — do not edit manually
// Entity: class CascadeTracker
// Strategy: code

#[derive(Debug, Clone)]
pub struct CascadeTracker {
    pub changed_nodes_json: String,  // default: ""[]""
    pub affected_nodes_json: String,  // default: ""[]""
    pub severity_max: i32,  // default: 0_f32
}

impl CascadeTracker {
    /// Construct with spec defaults. Generated from ARK $data defaults.
    #[inline]
    pub fn new() -> Self {
        Self {
            changed_nodes_json: ""[]"",
            affected_nodes_json: ""[]"",
            severity_max: 0_i32,
        }
    }
}

impl Default for CascadeTracker {
    #[inline]
    fn default() -> Self { Self::new() }
}

impl CascadeTracker {
    /// Check all invariants. Generated from ARK spec.
    #[inline]
    pub fn check_invariants(&self, modified_files: String) -> bool {
        let inv_0 = (self.severity_max >= 0_i32);
        let inv_1 = (self.severity_max <= 10_i32);
        inv_0 && inv_1
    }
}

impl CascadeTracker {
    /// Process rule #0 (strategy: code)
    #[inline]
    pub fn process_0(&mut self, modified_files: String) {
        debug_assert!((modified_files != """"), "precondition failed");
    }
}