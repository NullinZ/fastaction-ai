from __future__ import annotations


class FastActionError(Exception):
    """Base FastAction error."""


class RegistryNotFoundError(FastActionError):
    """A registry item was not found."""


class ProviderError(FastActionError):
    """A provider call failed."""


class PlanningError(FastActionError):
    """Planning failed before an instruction could be created."""
