// Generated from ARK DSL — do not edit manually
// Entity: abstraction Agent
// Strategy: code

#[derive(Debug, Clone)]
pub struct Agent {
    pub role: String,  // default: ""generic""
    pub model: String,  // default: ""sonnet""
    pub memory: String,  // default: ""none""
    pub max_turns: i32,  // default: 30_f32
}

impl Agent {
    /// Construct with spec defaults. Generated from ARK $data defaults.
    #[inline]
    pub fn new() -> Self {
        Self {
            role: ""generic"",
            model: ""sonnet"",
            memory: ""none"",
            max_turns: 30_i32,
        }
    }
}

impl Default for Agent {
    #[inline]
    fn default() -> Self { Self::new() }
}

impl Agent {
    /// Check all invariants. Generated from ARK spec.
    #[inline]
    pub fn check_invariants(&self, prompt: String, task_ref: String) -> bool {
        let inv_0 = (self.max_turns >= 1_i32);
        let inv_1 = (self.max_turns <= 100_i32);
        inv_0 && inv_1
    }
}

impl Agent {
    /// Process rule #0 (strategy: agent)
    #[inline]
    pub fn process_0(&mut self, prompt: String, task_ref: String) {
        debug_assert!((self.max_turns > 0_i32), "precondition failed");
    }
}