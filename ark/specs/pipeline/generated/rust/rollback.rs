// Generated from ARK DSL — do not edit manually
// Entity: class Rollback
// Strategy: code

#[derive(Debug, Clone)]
pub struct Rollback {
    pub task_id: String,  // default: """"
    pub reason: String,  // default: """"
}

impl Rollback {
    /// Construct with spec defaults. Generated from ARK $data defaults.
    #[inline]
    pub fn new() -> Self {
        Self {
            task_id: """",
            reason: """",
        }
    }
}

impl Default for Rollback {
    #[inline]
    fn default() -> Self { Self::new() }
}

impl Rollback {
    /// Process rule #0 (strategy: verified)
    #[inline]
    pub fn process_0(&mut self, trigger: bool, from_stage: String, to_stage: String) {
        debug_assert!((trigger == true), "precondition failed");
        debug_assert!((self.task_id != """"), "precondition failed");
        debug_assert!((from_stage == ""completed""), "precondition failed");
        debug_assert!((to_stage == ""fixing""), "precondition failed");
        debug_assert!((self.reason != """"), "precondition failed");
    }
}