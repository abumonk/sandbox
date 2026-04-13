// Generated from ARK DSL — do not edit manually
// Entity: class Vehicle
// Strategy: tensor

#[derive(Debug, Clone)]
pub struct Vehicle {
    pub fuel: f32,  // default: 50.0_f32
    pub speed: f32,  // default: 0.0_f32
}

impl Vehicle {
    /// Construct with spec defaults. Generated from ARK $data defaults.
    #[inline]
    pub fn new() -> Self {
        Self {
            fuel: 50.0_f32,
            speed: 0.0_f32,
        }
    }
}

impl Default for Vehicle {
    #[inline]
    fn default() -> Self { Self::new() }
}

/// SoA layout for batch processing (tensor strategy)
#[derive(Debug, Clone)]
pub struct VehicleBatch {
    pub count: usize,
    pub fuel: Vec<f32>,
    pub speed: Vec<f32>,
}

impl VehicleBatch {
    pub fn with_capacity(cap: usize) -> Self {
        Self {
            count: 0,
            fuel: Vec::with_capacity(cap),
            speed: Vec::with_capacity(cap),
        }
    }

    /// Batch process all entities. Generated from #process[strategy: tensor].
    /// Scalar fallback; replace with SIMD/AVX2 for hot loops.
    #[inline]
    pub fn process_all(&mut self, throttle: f32, dt: f32) {
        for i in 0..self.count {
            debug_assert!((self.fuel[i] > 0_f32), "precondition failed");
            self.speed[i] = (self.speed[i] + (throttle * dt));
            self.fuel[i] = (self.fuel[i] - ((throttle * 0.1_f32) * dt));
            debug_assert!((self.fuel[i] >= 0_f32), "postcondition failed");
        }
    }
}

impl Vehicle {
    /// Check all invariants. Generated from ARK spec.
    #[inline]
    pub fn check_invariants(&self, throttle: f32, dt: f32) -> bool {
        let inv_0 = (self.fuel >= 0_f32);
        inv_0
    }
}

impl Vehicle {
    /// Process rule #0 (strategy: tensor)
    #[inline]
    pub fn process_0(&mut self, throttle: f32, dt: f32) {
        debug_assert!((self.fuel > 0_f32), "precondition failed");
        self.speed = (self.speed + (throttle * dt));
        self.fuel = (self.fuel - ((throttle * 0.1_f32) * dt));
        debug_assert!((self.fuel >= 0_f32), "postcondition failed");
    }
}