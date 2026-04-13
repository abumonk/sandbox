// Generated from ARK DSL — do not edit manually
// Entity: class Wrapup
// Strategy: code

#[derive(Debug, Clone)]
pub struct Wrapup {
    pub date: String,  // default: """"
    pub session_dir: String,  // default: ""docs/sessions/""
}

impl Wrapup {
    /// Construct with spec defaults. Generated from ARK $data defaults.
    #[inline]
    pub fn new() -> Self {
        Self {
            date: """",
            session_dir: ""docs/sessions/"",
        }
    }
}

impl Default for Wrapup {
    #[inline]
    fn default() -> Self { Self::new() }
}

impl Wrapup {
    /// Process rule #0 (strategy: code)
    #[inline]
    pub fn process_0(&mut self, trigger: bool) {
        debug_assert!((trigger == true), "precondition failed");
        debug_assert!((trigger == true), "postcondition failed");
    }
}