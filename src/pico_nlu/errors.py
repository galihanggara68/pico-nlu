"""Typed exception hierarchy for pico-nlu.

Every public failure mode raises one of these rather than a built-in, so callers can
catch pico-specific errors without introspecting messages. See ARCHITECTURE.md §4.3.
"""


class PicoError(Exception):
    """Base type for every pico-nlu error. Catch this to catch them all."""


class DatasetValidationError(PicoError):
    """Raised when a dataset fails schema or semantic validation.

    Carries a dotted ``field`` path so callers can pinpoint the offending entry.
    """


class ModelNotTrainedError(PicoError):
    """Raised when :meth:`Engine.parse` is called before :meth:`Engine.fit`."""


class PersistenceError(PicoError):
    """Raised on unreadable, truncated, or format-incompatible model blobs."""


class ExtraNotInstalledError(PicoError):
    """Raised when a neural component is used without the ``[neural]`` extra."""
