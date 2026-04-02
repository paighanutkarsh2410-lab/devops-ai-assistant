"""
Kubernetes Controller: Manages K8s resources for remediation actions.
Uses the official Kubernetes Python client.
"""
import logging
import time

logger = logging.getLogger(__name__)

try:
    from kubernetes import client, config as k8s_config
    K8S_AVAILABLE = True
except ImportError:
    K8S_AVAILABLE = False


class KubernetesController:
    """Controls Kubernetes resources for remediation."""

    def __init__(self):
        self._apps_v1 = None
        self._core_v1 = None
        self._initialized = False

    def _init_client(self):
        """Initialize K8s client (in-cluster or kubeconfig)."""
        if self._initialized:
            return
        if not K8S_AVAILABLE:
            raise RuntimeError("Kubernetes SDK not installed. pip install kubernetes")
        try:
            k8s_config.load_incluster_config()
        except Exception:
            try:
                k8s_config.load_kube_config()
            except Exception as e:
                raise RuntimeError(f"Cannot connect to Kubernetes: {e}")
        self._apps_v1 = client.AppsV1Api()
        self._core_v1 = client.CoreV1Api()
        self._initialized = True

    def restart_pod(self, pod_name: str, namespace: str = "default") -> dict:
        """Delete a pod to trigger restart (managed by deployment)."""
        try:
            self._init_client()
            self._core_v1.delete_namespaced_pod(pod_name, namespace)
            logger.info(f"[K8s] Deleted pod {pod_name} in {namespace} for restart")
            return {"success": True, "message": f"Pod {pod_name} deleted for restart"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def scale_deployment(self, deployment: str, replicas: int, namespace: str = "default") -> dict:
        """Scale a deployment to the specified number of replicas."""
        try:
            self._init_client()
            body = {"spec": {"replicas": replicas}}
            self._apps_v1.patch_namespaced_deployment_scale(deployment, namespace, body)
            logger.info(f"[K8s] Scaled {deployment} to {replicas} replicas in {namespace}")

            # Wait for rollout
            self._wait_for_deployment(deployment, namespace, timeout=120)
            return {"success": True, "message": f"Scaled {deployment} to {replicas} replicas"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def rollback_deployment(self, deployment: str, namespace: str = "default") -> dict:
        """Rollback a deployment to the previous revision."""
        try:
            self._init_client()
            # Get current deployment
            dep = self._apps_v1.read_namespaced_deployment(deployment, namespace)
            annotations = dep.spec.template.metadata.annotations or {}
            annotations["kubectl.kubernetes.io/restartedAt"] = ""

            # Trigger rollback by patching with rollback annotation
            body = {
                "spec": {
                    "rollbackTo": {"revision": 0}  # Previous revision
                }
            }
            # For modern K8s, use rollout undo equivalent
            self._apps_v1.patch_namespaced_deployment(deployment, namespace, body)
            logger.info(f"[K8s] Rolled back {deployment} in {namespace}")
            return {"success": True, "message": f"Rolled back {deployment}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_pod_logs(self, pod_name: str, namespace: str = "default", lines: int = 100) -> dict:
        """Get recent logs from a pod."""
        try:
            self._init_client()
            logs = self._core_v1.read_namespaced_pod_log(
                pod_name, namespace, tail_lines=lines
            )
            return {"success": True, "logs": logs}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_pod_status(self, pod_name: str, namespace: str = "default") -> dict:
        """Get the status of a pod."""
        try:
            self._init_client()
            pod = self._core_v1.read_namespaced_pod(pod_name, namespace)
            return {
                "success": True,
                "phase": pod.status.phase,
                "conditions": [
                    {"type": c.type, "status": c.status}
                    for c in (pod.status.conditions or [])
                ],
                "container_statuses": [
                    {"name": cs.name, "ready": cs.ready, "restart_count": cs.restart_count}
                    for cs in (pod.status.container_statuses or [])
                ],
            }
        except Exception as e:
            return {"success": False, "message": str(e)}

    def delete_pod(self, pod_name: str, namespace: str = "default") -> dict:
        """Force delete a pod."""
        try:
            self._init_client()
            self._core_v1.delete_namespaced_pod(
                pod_name, namespace,
                body=client.V1DeleteOptions(grace_period_seconds=0)
            )
            return {"success": True, "message": f"Pod {pod_name} force deleted"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def _wait_for_deployment(self, deployment: str, namespace: str, timeout: int = 120):
        """Wait for a deployment to finish rolling out."""
        start = time.time()
        while time.time() - start < timeout:
            try:
                dep = self._apps_v1.read_namespaced_deployment(deployment, namespace)
                if (dep.status.ready_replicas or 0) == (dep.spec.replicas or 0):
                    return True
            except Exception:
                pass
            time.sleep(5)
        return False

    def is_available(self) -> bool:
        """Check if Kubernetes is available."""
        try:
            self._init_client()
            self._core_v1.list_namespace(limit=1)
            return True
        except Exception:
            return False
