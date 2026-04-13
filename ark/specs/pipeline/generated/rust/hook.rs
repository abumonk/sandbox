// Generated from ARK DSL — do not edit manually
// Entity: abstraction Hook
// Strategy: code

#[derive(Debug, Clone)]
pub struct Hook {
    pub event: HookEvent,  // default: PreToolUse
    pub mode: HookMode,  // default: advisory
}

impl Hook {
    /// Construct with spec defaults. Generated from ARK $data defaults.
    #[inline]
    pub fn new() -> Self {
        Self {
            event: PreToolUse,
            mode: advisory,
        }
    }
}

impl Default for Hook {
    #[inline]
    fn default() -> Self { Self::new() }
}

impl Hook {
    /// Check all invariants. Generated from ARK spec.
    #[inline]
    pub fn check_invariants(&self, context: String) -> bool {
        let inv_0 = (((self.mode == self.enforce) or (self.mode == self.advisory)) or (self.mode == self.always));
        inv_0
    }
}

impl Hook {
    /// Process rule #0 (strategy: code)
    #[inline]
    pub fn process_0(&mut self, context: String) {
        debug_assert!(true, "precondition failed");
    }
}