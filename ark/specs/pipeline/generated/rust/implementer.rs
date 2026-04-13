// Generated from ARK DSL — do not edit manually
// Entity: class Implementer
// Strategy: code

#[derive(Debug, Clone)]
pub struct Implementer {
    pub role: String,  // default: ""implementer""
    pub model: String,  // default: ""sonnet""
    pub memory: String,  // default: ""project""
    pub max_turns: i32,  // default: 50_f32
}

impl Implementer {
    /// Construct with spec defaults. Generated from ARK $data defaults.
    #[inline]
    pub fn new() -> Self {
        Self {
            role: ""implementer"",
            model: ""sonnet"",
            memory: ""project"",
            max_turns: 50_i32,
        }
    }
}

impl Default for Implementer {
    #[inline]
    fn default() -> Self { Self::new() }
}

impl Implementer {
    /// Process rule #0 (strategy: agent)
    #[inline]
    pub fn process_0(&mut self, prompt: String, task_ref: String, review_ref: String) {
        debug_assert!((task_ref != """"), "precondition failed");
    }
    /// Process rule #1 (strategy: agent)
    #[inline]
    pub fn process_1(&mut self, prompt: String, task_ref: String, review_ref: String) {
        debug_assert!((review_ref != """"), "precondition failed");
    }
}