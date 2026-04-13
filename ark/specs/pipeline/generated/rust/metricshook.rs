// Generated from ARK DSL — do not edit manually
// Entity: class MetricsHook
// Strategy: code

#[derive(Debug, Clone)]
pub struct MetricsHook {
    pub event: HookEvent,  // default: SubagentStop
    pub mode: HookMode,  // default: always
}

impl MetricsHook {
    /// Construct with spec defaults. Generated from ARK $data defaults.
    #[inline]
    pub fn new() -> Self {
        Self {
            event: SubagentStop,
            mode: always,
        }
    }
}

impl Default for MetricsHook {
    #[inline]
    fn default() -> Self { Self::new() }
}

impl MetricsHook {
    /// Process rule #0 (strategy: code)
    #[inline]
    pub fn process_0(&mut self, context: String) {
    }
}