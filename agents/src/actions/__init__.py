from .base_action import RemediationAction
from .restart_service import RestartServiceAction
from .scale_service import ScaleServiceAction
from .rollback_deployment import RollbackDeploymentAction
from .clear_cache import ClearCacheAction
from .increase_resources import IncreaseResourcesAction
from .kill_process import KillProcessAction
from .adjust_rate_limit import AdjustRateLimitAction

ACTION_REGISTRY = {
    "restart_service": RestartServiceAction,
    "scale_service": ScaleServiceAction,
    "rollback_deployment": RollbackDeploymentAction,
    "clear_cache": ClearCacheAction,
    "increase_resources": IncreaseResourcesAction,
    "kill_process": KillProcessAction,
    "adjust_rate_limit": AdjustRateLimitAction,
}
