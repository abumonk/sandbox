// Generated from ARK DSL — do not edit manually
// Entity: class Task
// Strategy: code

#[derive(Debug, Clone)]
pub struct Task {
    pub id: String,  // default: ""TASK-000""
    pub title: String,  // default: """"
    pub tags: String,  // default: """"
    pub stage: TaskStage,  // default: planning
    pub status: TeamTaskStatus,  // default: pending
    pub assignee: String,  // default: ""planner""
    pub iterations: i32,  // default: 0_f32
    pub max_iterations: i32,  // default: 3_f32
    pub token_budget: i32,  // default: 200000_f32
    pub cost_budget: f32,  // default: 5.0_f32
    pub tokens_used: i32,  // default: 0_f32
    pub cost_used: f32,  // default: 0.0_f32
    pub depends_on: String,  // default: """"
    pub repos_json: String,  // default: ""[]""
    pub files: String,  // default: """"
    pub adventure_id: String,  // default: """"
}

impl Task {
    /// Construct with spec defaults. Generated from ARK $data defaults.
    #[inline]
    pub fn new() -> Self {
        Self {
            id: ""TASK-000"",
            title: """",
            tags: """",
            stage: planning,
            status: pending,
            assignee: ""planner"",
            iterations: 0_i32,
            max_iterations: 3_i32,
            token_budget: 200000_i32,
            cost_budget: 5.0_f32,
            tokens_used: 0_i32,
            cost_used: 0.0_f32,
            depends_on: """",
            repos_json: ""[]"",
            files: """",
            adventure_id: """",
        }
    }
}

impl Default for Task {
    #[inline]
    fn default() -> Self { Self::new() }
}

impl Task {
    /// Check all invariants. Generated from ARK spec.
    #[inline]
    pub fn check_invariants(&self, request: String, event: PipelineEvent) -> bool {
        let inv_0 = (self.iterations >= 0_f32);
        let inv_1 = (self.iterations <= self.max_iterations);
        let inv_2 = (self.tokens_used <= self.token_budget);
        let inv_3 = (self.cost_used <= self.cost_budget);
        inv_0 && inv_1 && inv_2 && inv_3
    }
}

impl Task {
    /// Process rule #0 (strategy: code)
    #[inline]
    pub fn process_0(&mut self, request: String, event: PipelineEvent) {
        debug_assert!((self.id != ""TASK-000""), "precondition failed");
        debug_assert!((self.iterations <= self.max_iterations), "precondition failed");
        debug_assert!((self.tokens_used <= self.token_budget), "precondition failed");
        debug_assert!((self.cost_used <= self.cost_budget), "precondition failed");
        self.updated_at = (self.updated_at + 1_f32);
        debug_assert!(((self.stage == self.planning) or (self.stage == self.implementing)), "postcondition failed");
        debug_assert!((self.iterations <= self.max_iterations), "postcondition failed");
    }
}