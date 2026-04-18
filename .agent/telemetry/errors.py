"""Shared exception hierarchy for the telemetry capture subsystem."""


class CaptureError(Exception):
    """Base for all telemetry capture failures."""


class PayloadError(CaptureError):
    """Raised when a capture payload is malformed or incomplete."""


class SchemaError(CaptureError):
    """Raised when an event payload fails schema validation."""


class CostModelError(CaptureError):
    """Raised when the cost model cannot be loaded or is misconfigured."""


class UnknownModelError(CostModelError):
    """Raised when a model ID cannot be resolved to a known rate entry."""


class WriteError(CaptureError):
    """Raised when writing a telemetry record to disk fails."""


class AggregationError(CaptureError):
    """Raised when aggregating metrics across tasks fails."""


class TaskActualsError(CaptureError):
    """Raised when reading or writing task actuals fields fails."""
