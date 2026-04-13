// Generated from ARK DSL — do not edit manually
// Entity: class Deploy
// Strategy: code

#[derive(Debug, Clone)]
pub struct Deploy {
    pub mode: GitMode,  // default: current_branch
    pub commit_style: CommitStyle,  // default: conventional
    pub base_branch: String,  // default: ""main""
    pub repos_json: String,  // default: ""[]""
}

impl Deploy {
    /// Construct with spec defaults. Generated from ARK $data defaults.
    #[inline]
    pub fn new() -> Self {
        Self {
            mode: current_branch,
            commit_style: conventional,
            base_branch: ""main"",
            repos_json: ""[]"",
        }
    }
}

impl Default for Deploy {
    #[inline]
    fn default() -> Self { Self::new() }
}

impl Deploy {
    /// Process rule #0 (strategy: code)
    #[inline]
    pub fn process_0(&mut self, task_id: String, stage_from: String, stage_to: String, review_result: ReviewResult) {
    }
    /// Process rule #1 (strategy: code)
    #[inline]
    pub fn process_1(&mut self, task_id: String, stage_from: String, stage_to: String, review_result: ReviewResult) {
    }
    /// Process rule #2 (strategy: verified)
    #[inline]
    pub fn process_2(&mut self, task_id: String, stage_from: String, stage_to: String, review_result: ReviewResult) {
        debug_assert!((review_result == self.passed), "precondition failed");
        debug_assert!((review_result == self.passed), "postcondition failed");
    }
}