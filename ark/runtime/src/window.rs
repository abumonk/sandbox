//! Window app scaffolding for the ARK runtime.
//!
//! This module defines the *shape* of a runtime window app — config,
//! lifecycle callbacks, runner signature — but does NOT yet pull in
//! `winit` or `wgpu`. Those heavy deps are deferred to a focused
//! follow-up task (`WgpuBackendTask`) so the workspace build stays
//! fast and `HecsEcsTask` / `IslandTickLoopTask` can build against
//! stable interfaces in the meantime.
//!
//! Today `run_stub` is a no-op that returns immediately; a follow-up
//! will replace it with a real event loop and a wgpu surface while
//! keeping the `WindowConfig` + `WindowApp` API stable.

use std::fmt;

/// Platform-agnostic knobs for a runtime window.
///
/// Defaults are sized for a standard 1080p dev monitor with sane
/// vsync and a non-resizable window (so tests have a deterministic
/// surface rect when we eventually plug in the real backend).
#[derive(Debug, Clone, PartialEq)]
pub struct WindowConfig {
    pub title: String,
    pub width: u32,
    pub height: u32,
    pub vsync: bool,
    pub resizable: bool,
}

impl Default for WindowConfig {
    fn default() -> Self {
        Self {
            title: "ARK Runtime".to_string(),
            width: 1280,
            height: 720,
            vsync: true,
            resizable: false,
        }
    }
}

impl WindowConfig {
    /// Builder: set the window title.
    pub fn with_title(mut self, title: impl Into<String>) -> Self {
        self.title = title.into();
        self
    }

    /// Builder: set width & height in pixels.
    pub fn with_size(mut self, width: u32, height: u32) -> Self {
        self.width = width;
        self.height = height;
        self
    }

    /// Aspect ratio (width / height) for anything that needs it up front.
    pub fn aspect_ratio(&self) -> f32 {
        if self.height == 0 {
            return 1.0;
        }
        self.width as f32 / self.height as f32
    }
}

/// Lifecycle hooks a runtime app must implement.
///
/// The runner will call `on_init` once before the event loop, `on_frame`
/// each tick with a monotonically increasing frame index and a
/// per-frame delta-time in seconds, and `on_close` once when the
/// window is asked to close. Any hook may return `Err` to short-circuit
/// the runner.
pub trait WindowApp {
    fn on_init(&mut self, config: &WindowConfig) -> anyhow::Result<()> {
        let _ = config;
        Ok(())
    }

    fn on_frame(&mut self, frame: u64, dt_secs: f32) -> anyhow::Result<()> {
        let _ = (frame, dt_secs);
        Ok(())
    }

    fn on_close(&mut self) -> anyhow::Result<()> {
        Ok(())
    }
}

/// Stub runner — returns immediately without opening a real window.
///
/// Invokes `on_init` and `on_close` exactly once so app-authored setup
/// and teardown code still gets exercised under tests. The real runner
/// will land in `WgpuBackendTask` and replace this function's body
/// while keeping the signature identical.
pub fn run_stub<A: WindowApp>(
    app: &mut A,
    config: &WindowConfig,
) -> anyhow::Result<()> {
    app.on_init(config)?;
    // In the stub we don't simulate frames — the follow-up will drive
    // them off the winit event loop. Tests that need frame callbacks
    // should use `run_frames` below.
    app.on_close()?;
    Ok(())
}

/// Deterministic runner that drives `n_frames` of `on_frame` at a
/// fixed `dt`. Useful for unit tests of tick-loop logic (ECS systems,
/// island transitions) without needing a real window.
pub fn run_frames<A: WindowApp>(
    app: &mut A,
    config: &WindowConfig,
    n_frames: u64,
    dt_secs: f32,
) -> anyhow::Result<()> {
    app.on_init(config)?;
    for frame in 0..n_frames {
        app.on_frame(frame, dt_secs)?;
    }
    app.on_close()?;
    Ok(())
}

impl fmt::Display for WindowConfig {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "WindowConfig({}, {}x{}, vsync={}, resizable={})",
            self.title, self.width, self.height, self.vsync, self.resizable
        )
    }
}

// ============================================================
// Tests
// ============================================================

#[cfg(test)]
mod tests {
    use super::*;
    use std::cell::Cell;

    /// Test app that records every lifecycle call for assertion.
    #[derive(Default)]
    struct RecordingApp {
        inits: Cell<u32>,
        frames: Cell<u64>,
        closes: Cell<u32>,
    }

    impl WindowApp for RecordingApp {
        fn on_init(&mut self, _config: &WindowConfig) -> anyhow::Result<()> {
            self.inits.set(self.inits.get() + 1);
            Ok(())
        }

        fn on_frame(&mut self, _frame: u64, _dt: f32) -> anyhow::Result<()> {
            self.frames.set(self.frames.get() + 1);
            Ok(())
        }

        fn on_close(&mut self) -> anyhow::Result<()> {
            self.closes.set(self.closes.get() + 1);
            Ok(())
        }
    }

    #[test]
    fn default_window_config_is_720p_vsync() {
        let cfg = WindowConfig::default();
        assert_eq!(cfg.width, 1280);
        assert_eq!(cfg.height, 720);
        assert!(cfg.vsync);
        assert!(!cfg.resizable);
        assert_eq!(cfg.title, "ARK Runtime");
    }

    #[test]
    fn config_builder_overrides_fields() {
        let cfg = WindowConfig::default()
            .with_title("Terrain Tool")
            .with_size(800, 600);
        assert_eq!(cfg.title, "Terrain Tool");
        assert_eq!(cfg.width, 800);
        assert_eq!(cfg.height, 600);
        // Aspect ratio must be computed from the overridden size.
        assert!((cfg.aspect_ratio() - 4.0 / 3.0).abs() < 1e-6);
    }

    #[test]
    fn run_stub_invokes_init_and_close_exactly_once() {
        let mut app = RecordingApp::default();
        run_stub(&mut app, &WindowConfig::default()).expect("stub runs clean");
        assert_eq!(app.inits.get(), 1);
        assert_eq!(app.closes.get(), 1);
        // No frames in the stub runner.
        assert_eq!(app.frames.get(), 0);
    }

    #[test]
    fn run_frames_drives_exact_number_of_ticks() {
        let mut app = RecordingApp::default();
        run_frames(&mut app, &WindowConfig::default(), 5, 1.0 / 60.0)
            .expect("frame runner is infallible for RecordingApp");
        assert_eq!(app.inits.get(), 1);
        assert_eq!(app.frames.get(), 5);
        assert_eq!(app.closes.get(), 1);
    }

    #[test]
    fn aspect_ratio_zero_height_falls_back_to_one() {
        let cfg = WindowConfig {
            width: 800,
            height: 0,
            ..Default::default()
        };
        assert_eq!(cfg.aspect_ratio(), 1.0);
    }
}
