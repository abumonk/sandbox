// Generated from ARK DSL — do not edit manually
// Entity: class Adventure
// Strategy: code

#[derive(Debug, Clone)]
pub struct Adventure {
    pub id: String,  // default: ""ADV-000""
    pub title: String,  // default: """"
    pub state: AdventureState,  // default: concept
    pub task_count: i32,  // default: 0_f32
    pub tasks_done: i32,  // default: 0_f32
    pub tasks_blocked: i32,  // default: 0_f32
    pub tokens_used: i32,  // default: 0_f32
    pub cost_used: f32,  // default: 0.0_f32
    pub designs_count: i32,  // default: 0_f32
    pub plans_count: i32,  // default: 0_f32
    pub target_conditions_cnt: i32,  // default: 0_f32
}

impl Adventure {
    /// Construct with spec defaults. Generated from ARK $data defaults.
    #[inline]
    pub fn new() -> Self {
        Self {
            id: ""ADV-000"",
            title: """",
            state: concept,
            task_count: 0_i32,
            tasks_done: 0_i32,
            tasks_blocked: 0_i32,
            tokens_used: 0_i32,
            cost_used: 0.0_f32,
            designs_count: 0_i32,
            plans_count: 0_i32,
            target_conditions_cnt: 0_i32,
        }
    }
}

impl Default for Adventure {
    #[inline]
    fn default() -> Self { Self::new() }
}

impl Adventure {
    /// Check all invariants. Generated from ARK spec.
    #[inline]
    pub fn check_invariants(&self, concept: String, approval: bool, child_status: TeamTaskStatus) -> bool {
        let inv_0 = (self.tasks_done >= 0_f32);
        let inv_1 = (self.tasks_done <= self.task_count);
        let inv_2 = (self.tasks_blocked >= 0_f32);
        let inv_3 = (self.tasks_blocked <= self.task_count);
        inv_0 && inv_1 && inv_2 && inv_3
    }
}

impl Adventure {
    /// Process rule #0 (strategy: code)
    #[inline]
    pub fn process_0(&mut self, concept: String, approval: bool, child_status: TeamTaskStatus) {
        debug_assert!((self.task_count >= self.tasks_done), "precondition failed");
        debug_assert!(((self.tasks_done + self.tasks_blocked) <= self.task_count), "precondition failed");
        debug_assert!(((self.tasks_done + self.tasks_blocked) <= self.task_count), "postcondition failed");
    }
}