from __future__ import annotations

from fastaction.domain.enums import RiskLevel
from fastaction.schemas import APIDefinition


class PolicyChecker:
    def requires_confirmation(self, api: APIDefinition) -> bool:
        policy = api.policy
        if policy.requires_confirmation is True:
            return True
        if isinstance(policy.requires_confirmation, str):
            return policy.requires_confirmation.lower() in {"true", "always", "by_policy"}
        return policy.risk in {RiskLevel.WRITE, RiskLevel.DESTRUCTIVE, RiskLevel.EXTERNAL}
