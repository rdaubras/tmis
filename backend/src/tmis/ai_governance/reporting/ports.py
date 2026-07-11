from collections.abc import Callable
from typing import TypeAlias

from tmis.ai_governance.reporting.schemas import GovernanceReport

ReportBuilder: TypeAlias = Callable[..., GovernanceReport]
