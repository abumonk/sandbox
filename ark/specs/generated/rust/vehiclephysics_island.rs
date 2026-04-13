// ============================================================
// Island: VehiclePhysics
// Strategy: tensor
// ============================================================

use crate::vehicle::{Vehicle, VehicleBatch};

pub struct VehiclePhysicsIsland {
    pub count: i32,
    pub vehicle_batch: VehicleBatch,
}

impl VehiclePhysicsIsland {
    pub fn update(&mut self, tick: f32) {
        // Tensor batch processing.
        // NOTE: batch signatures are derived from each entity's
        // @in port. Adapt the arguments below to the island's inputs.
        self.vehicle_batch.process_all(Default::default(), Default::default());
    }
}