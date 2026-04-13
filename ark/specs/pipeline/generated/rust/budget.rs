// Generated from ARK DSL — do not edit manually
// Entity: abstraction Budget
// Strategy: code

#[derive(Debug, Clone)]
pub struct Budget {
    pub scope: BudgetScope,  // default: task
    pub tokens_cap: i32,  // default: 1000000_f32
    pub cost_cap: f32,  // default: 100.0_f32
}

impl Budget {
    /// Construct with spec defaults. Generated from ARK $data defaults.
    #[inline]
    pub fn new() -> Self {
        Self {
            scope: task,
            tokens_cap: 1000000_i32,
            cost_cap: 100.0_f32,
        }
    }
}

impl Default for Budget {
    #[inline]
    fn default() -> Self { Self::new() }
}

impl Budget {
    /// Check all invariants. Generated from ARK spec.
    #[inline]
    pub fn check_invariants(&self, consumed_tokens: i32, consumed_cost: f32) -> bool {
        let inv_0 = (self.tokens_cap >= 0_f32);
        let inv_1 = (self.cost_cap >= 0_f32);
        inv_0 && inv_1
    }
}

impl Budget {
    /// Process rule #0 (strategy: code)
    #[inline]
    pub fn process_0(&mut self, consumed_tokens: i32, consumed_cost: f32) {
        debug_assert!((consumed_tokens >= 0_f32), "precondition failed");
        debug_assert!((consumed_cost >= 0_f32), "precondition failed");
    }
}