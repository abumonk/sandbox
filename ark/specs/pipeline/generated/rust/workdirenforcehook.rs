// Generated from ARK DSL — do not edit manually
// Entity: class WorkdirEnforceHook
// Strategy: code

#[derive(Debug, Clone)]
pub struct WorkdirEnforceHook {
    pub event: HookEvent,  // default: PreToolUse
    pub mode: HookMode,  // default: enforce
}

impl WorkdirEnforceHook {
    /// Construct with spec defaults. Generated from ARK $data defaults.
    #[inline]
    pub fn new() -> Self {
        Self {
            event: PreToolUse,
            mode: enforce,
        }
    }
}

impl Default for WorkdirEnforceHook {
    #[inline]
    fn default() -> Self { Self::new() }
}

impl WorkdirEnforceHook {
    /// Process rule #0 (strategy: code)
    #[inline]
    pub fn process_0(&mut self, context: String) {
        debug_assert!(true, "precondition failed");
        debug_assert!(true, "postcondition failed");
    }
}