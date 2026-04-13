// Generated from ARK DSL — do not edit manually
// Entity: class Scheduler
// Strategy: code

#[derive(Debug, Clone)]
pub struct Scheduler {
    pub cron_rules: String,  // default: ""[]""
}

impl Scheduler {
    /// Construct with spec defaults. Generated from ARK $data defaults.
    #[inline]
    pub fn new() -> Self {
        Self {
            cron_rules: ""[]"",
        }
    }
}

impl Default for Scheduler {
    #[inline]
    fn default() -> Self { Self::new() }
}

impl Scheduler {
    /// Process rule #0 (strategy: code)
    #[inline]
    pub fn process_0(&mut self, now: u64) {
        debug_assert!((now >= 0_f32), "precondition failed");
    }
}