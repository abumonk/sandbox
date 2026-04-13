//! Runtime loader — read a parsed `ArkFile`, build an ordered list of
//! island slots, and drive them through the `WindowApp` lifecycle.
//!
//! This task is the first place in the codebase where the *spec* meets
//! the *execution*: parser → registry → runtime. It's intentionally
//! thin — each tick bumps a counter per island, leaving actual
//! `#process` body execution to downstream work (the codegen-emitted
//! Rust structs and the hecs integration are both here and available,
//! but body interpretation is out of scope for MVP).

use std::collections::HashMap;

use ark_dsl::{ArkFile, Item};

use crate::ecs::EcsWorld;
use crate::window::{WindowApp, WindowConfig};

/// One runtime slot — a single island that the tick loop visits.
#[derive(Debug, Clone, PartialEq)]
pub struct IslandSlot {
    pub name: String,
    pub priority: i64,
    /// How many times this slot has been ticked since the runtime
    /// started. Bumped every `on_frame` invocation.
    pub tick_count: u64,
}

/// The runtime state assembled from a parsed spec.
pub struct Runtime {
    pub slots: Vec<IslandSlot>,
    pub frame: u64,
    pub ecs: EcsWorld,
}

const DEFAULT_PRIORITY: i64 = 999;

impl Runtime {
    /// Build a Runtime from a parsed spec.
    ///
    /// Priorities come from any top-level `registry { register X { priority: N } }`
    /// block. Islands not mentioned in any registry fall back to
    /// `DEFAULT_PRIORITY` (sorted last). Registry entries that name a
    /// non-island item are ignored — islands are the tick-loop primitive.
    pub fn from_ark_file(file: &ArkFile) -> Self {
        let mut priorities: HashMap<String, i64> = HashMap::new();

        for item in &file.items {
            if let Item::Registry(reg) = item {
                for entry in &reg.entries {
                    if let Some(pri) = meta_int(&entry.meta, "priority") {
                        priorities.insert(entry.name.clone(), pri);
                    }
                }
            }
        }

        let mut slots: Vec<IslandSlot> = Vec::new();
        for item in &file.items {
            if let Item::Island(isl) = item {
                let priority = priorities
                    .get(&isl.name)
                    .copied()
                    .unwrap_or(DEFAULT_PRIORITY);
                slots.push(IslandSlot {
                    name: isl.name.clone(),
                    priority,
                    tick_count: 0,
                });
            }
        }

        slots.sort_by(|a, b| a.priority.cmp(&b.priority).then(a.name.cmp(&b.name)));

        Runtime {
            slots,
            frame: 0,
            ecs: EcsWorld::new(),
        }
    }

    /// Advance every island slot by one step.
    ///
    /// For MVP this just increments per-slot counters in priority order.
    /// Real `#process` body execution is a follow-up — by then the
    /// codegen-emitted structs will be wired into `self.ecs` and each
    /// slot will call into its emitted `process_all` routine.
    pub fn tick(&mut self, _dt_secs: f32) {
        for slot in &mut self.slots {
            slot.tick_count += 1;
        }
        self.frame += 1;
    }

    pub fn is_empty(&self) -> bool {
        self.slots.is_empty()
    }

    pub fn slot(&self, name: &str) -> Option<&IslandSlot> {
        self.slots.iter().find(|s| s.name == name)
    }
}

impl WindowApp for Runtime {
    fn on_init(&mut self, _config: &WindowConfig) -> anyhow::Result<()> {
        Ok(())
    }

    fn on_frame(&mut self, _frame: u64, dt_secs: f32) -> anyhow::Result<()> {
        self.tick(dt_secs);
        Ok(())
    }

    fn on_close(&mut self) -> anyhow::Result<()> {
        Ok(())
    }
}

/// Pull an i64 out of a `registry { register X { key: N } }` meta entry.
fn meta_int(meta: &[ark_dsl::MetaPair], key: &str) -> Option<i64> {
    for pair in meta {
        if pair.key == key {
            if let ark_dsl::Expr::Number(n) = &pair.value {
                if n.is_finite() {
                    return Some(*n as i64);
                }
            }
        }
    }
    None
}

// ============================================================
// Tests
// ============================================================

#[cfg(test)]
mod tests {
    use super::*;
    use crate::window::{run_frames, WindowConfig};
    use ark_dsl::parse_ark_file;

    #[test]
    fn empty_file_yields_empty_runtime() {
        let file = parse_ark_file("").unwrap();
        let rt = Runtime::from_ark_file(&file);
        assert!(rt.is_empty());
        assert_eq!(rt.frame, 0);
    }

    #[test]
    fn islands_sorted_by_registry_priority() {
        let src = r#"
            island Alpha {
                strategy: code
            }
            island Beta {
                strategy: code
            }
            island Gamma {
                strategy: code
            }
            registry Sys {
                register Alpha { phase: runtime, priority: 30 }
                register Beta  { phase: runtime, priority: 10 }
                register Gamma { phase: runtime, priority: 20 }
            }
        "#;
        let file = parse_ark_file(src).unwrap();
        let rt = Runtime::from_ark_file(&file);
        let names: Vec<&str> = rt.slots.iter().map(|s| s.name.as_str()).collect();
        assert_eq!(names, vec!["Beta", "Gamma", "Alpha"]);
        assert_eq!(rt.slots[0].priority, 10);
        assert_eq!(rt.slots[1].priority, 20);
        assert_eq!(rt.slots[2].priority, 30);
    }

    #[test]
    fn unregistered_island_falls_back_to_default_priority() {
        let src = r#"
            island Alpha {
                strategy: code
            }
            island Orphan {
                strategy: code
            }
            registry Sys {
                register Alpha { phase: runtime, priority: 1 }
            }
        "#;
        let file = parse_ark_file(src).unwrap();
        let rt = Runtime::from_ark_file(&file);
        assert_eq!(rt.slots[0].name, "Alpha");
        assert_eq!(rt.slots[0].priority, 1);
        // Orphan lands at the end with DEFAULT_PRIORITY.
        assert_eq!(rt.slots[1].name, "Orphan");
        assert_eq!(rt.slots[1].priority, DEFAULT_PRIORITY);
    }

    #[test]
    fn tick_advances_frame_and_per_slot_counters() {
        let src = r#"
            island Alpha {
                strategy: code
            }
            island Beta {
                strategy: code
            }
            registry Sys {
                register Alpha { phase: runtime, priority: 1 }
                register Beta  { phase: runtime, priority: 2 }
            }
        "#;
        let file = parse_ark_file(src).unwrap();
        let mut rt = Runtime::from_ark_file(&file);
        rt.tick(0.016);
        rt.tick(0.016);
        rt.tick(0.016);
        assert_eq!(rt.frame, 3);
        assert_eq!(rt.slot("Alpha").unwrap().tick_count, 3);
        assert_eq!(rt.slot("Beta").unwrap().tick_count, 3);
    }

    #[test]
    fn run_frames_drives_runtime_via_window_app_trait() {
        let src = r#"
            island Alpha {
                strategy: code
            }
            registry Sys {
                register Alpha { phase: runtime, priority: 1 }
            }
        "#;
        let file = parse_ark_file(src).unwrap();
        let mut rt = Runtime::from_ark_file(&file);
        run_frames(&mut rt, &WindowConfig::default(), 5, 1.0 / 60.0)
            .expect("runtime implements WindowApp so run_frames drives it");
        assert_eq!(rt.frame, 5);
        assert_eq!(rt.slot("Alpha").unwrap().tick_count, 5);
    }
}
