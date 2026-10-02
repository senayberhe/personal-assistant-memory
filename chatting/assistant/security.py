from enum import Enum


class RiskLevel(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class SecurityPolicy:
    def requires_confirmation(self, risk_level: RiskLevel) -> bool:
        return risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL}

    def is_allowed(
            self,
            risk_level: RiskLevel
    ) -> bool:
        if risk_level == RiskLevel.CRITICAL:
            return False
        return True
