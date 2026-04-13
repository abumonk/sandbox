// Generated from ARK DSL — do not edit manually
// Entity: class Reviewer
// Strategy: code

#[derive(Debug, Clone)]
pub struct Reviewer {
    pub role: String,  // default: ""reviewer""
    pub model: String,  // default: ""opus""
    pub memory: String,  // default: ""project""
    pub max_turns: i32,  // default: 30_f32
}

impl Reviewer {
    /// Construct with spec defaults. Generated from ARK $data defaults.
    #[inline]
    pub fn new() -> Self {
        Self {
            role: ""reviewer"",
            model: ""opus"",
            memory: ""project"",
            max_turns: 30_i32,
        }
    }
}

impl Default for Reviewer {
    #[inline]
    fn default() -> Self { Self::new() }
}

impl Reviewer {
    /// Process rule #0 (strategy: agent)
    #[inline]
    pub fn process_0(&mut self, prompt: String, task_ref: String) {
        debug_assert!((task_ref != """"), "precondition failed");
    }
}