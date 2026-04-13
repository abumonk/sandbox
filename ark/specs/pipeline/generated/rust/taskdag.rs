// Generated from ARK DSL — do not edit manually
// Entity: class TaskDAG
// Strategy: code

#[derive(Debug, Clone)]
pub struct TaskDAG {
    pub edges_json: String,  // default: ""[]""
    pub cycle_free: bool,  // default: true
}

impl TaskDAG {
    /// Construct with spec defaults. Generated from ARK $data defaults.
    #[inline]
    pub fn new() -> Self {
        Self {
            edges_json: ""[]"",
            cycle_free: true,
        }
    }
}

impl Default for TaskDAG {
    #[inline]
    fn default() -> Self { Self::new() }
}

impl TaskDAG {
    /// Check all invariants. Generated from ARK spec.
    #[inline]
    pub fn check_invariants(&self, tasks: String) -> bool {
        let inv_0 = (self.cycle_free == true);
        inv_0
    }
}

impl TaskDAG {
    /// Process rule #0 (strategy: code)
    #[inline]
    pub fn process_0(&mut self, tasks: String) {
        debug_assert!((tasks != """"), "precondition failed");
        debug_assert!((self.cycle_free == true), "postcondition failed");
    }
}