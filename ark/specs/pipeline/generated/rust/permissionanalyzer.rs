// Generated from ARK DSL — do not edit manually
// Entity: class PermissionAnalyzer
// Strategy: code

#[derive(Debug, Clone)]
pub struct PermissionAnalyzer {
    pub allowed_tools_json: String,  // default: ""[]""
    pub requested_json: String,  // default: ""[]""
    pub gaps_count: i32,  // default: 0_f32
}

impl PermissionAnalyzer {
    /// Construct with spec defaults. Generated from ARK $data defaults.
    #[inline]
    pub fn new() -> Self {
        Self {
            allowed_tools_json: ""[]"",
            requested_json: ""[]"",
            gaps_count: 0_i32,
        }
    }
}

impl Default for PermissionAnalyzer {
    #[inline]
    fn default() -> Self { Self::new() }
}

impl PermissionAnalyzer {
    /// Check all invariants. Generated from ARK spec.
    #[inline]
    pub fn check_invariants(&self, task_ref: String, roles_json: String) -> bool {
        let inv_0 = (self.gaps_count >= 0_i32);
        inv_0
    }
}

impl PermissionAnalyzer {
    /// Process rule #0 (strategy: code)
    #[inline]
    pub fn process_0(&mut self, task_ref: String, roles_json: String) {
        debug_assert!((task_ref != """"), "precondition failed");
        debug_assert!((self.gaps_count >= 0_i32), "postcondition failed");
    }
}