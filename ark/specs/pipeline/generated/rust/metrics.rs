// Generated from ARK DSL — do not edit manually
// Entity: class Metrics
// Strategy: code

#[derive(Debug, Clone)]
pub struct Metrics {
    pub total_tokens: i32,  // default: 0_f32
    pub total_cost: f32,  // default: 0.0_f32
    pub total_runs: i32,  // default: 0_f32
    pub failures: i32,  // default: 0_f32
}

impl Metrics {
    /// Construct with spec defaults. Generated from ARK $data defaults.
    #[inline]
    pub fn new() -> Self {
        Self {
            total_tokens: 0_i32,
            total_cost: 0.0_f32,
            total_runs: 0_i32,
            failures: 0_i32,
        }
    }
}

impl Default for Metrics {
    #[inline]
    fn default() -> Self { Self::new() }
}

impl Metrics {
    /// Check all invariants. Generated from ARK spec.
    #[inline]
    pub fn check_invariants(&self, run_tokens: i32, run_cost: f32, run_ok: bool) -> bool {
        let inv_0 = (self.total_tokens >= 0_f32);
        let inv_1 = (self.total_cost >= 0.0_f32);
        let inv_2 = (self.failures <= self.total_runs);
        inv_0 && inv_1 && inv_2
    }
}

impl Metrics {
    /// Process rule #0 (strategy: code)
    #[inline]
    pub fn process_0(&mut self, run_tokens: i32, run_cost: f32, run_ok: bool) {
        debug_assert!((run_tokens >= 0_f32), "precondition failed");
        debug_assert!((run_cost >= 0_f32), "precondition failed");
        self.total_tokens = (self.total_tokens + run_tokens);
        self.total_cost = (self.total_cost + run_cost);
        self.total_runs = (self.total_runs + 1_f32);
        debug_assert!((self.total_tokens >= 0_f32), "postcondition failed");
        debug_assert!((self.total_runs >= 0_f32), "postcondition failed");
    }
}