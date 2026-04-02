"""
Docker Controller: Manages Docker containers for remediation actions.
Uses the official Docker Python SDK.
"""
import logging
import time

logger = logging.getLogger(__name__)

try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False


class DockerController:
    """Controls Docker containers for remediation."""

    def __init__(self, base_url: str = None):
        self._client = None
        self._base_url = base_url

    @property
    def client(self):
        if self._client is None:
            if not DOCKER_AVAILABLE:
                raise RuntimeError("Docker SDK not installed. pip install docker")
            try:
                if self._base_url:
                    self._client = docker.DockerClient(base_url=self._base_url)
                else:
                    self._client = docker.from_env()
                self._client.ping()
            except Exception as e:
                raise RuntimeError(f"Cannot connect to Docker: {e}")
        return self._client

    def restart_container(self, container_name: str, timeout: int = 30) -> dict:
        """Restart a container and wait for it to be healthy."""
        try:
            container = self.client.containers.get(container_name)
            logger.info(f"[Docker] Restarting {container_name}...")
            container.restart(timeout=timeout)

            # Wait for healthy
            if self._wait_healthy(container_name, timeout=60):
                return {"success": True, "message": f"Container {container_name} restarted and healthy"}
            return {"success": True, "message": f"Container {container_name} restarted (health unknown)"}
        except Exception as e:
            logger.error(f"[Docker] Restart failed: {e}")
            return {"success": False, "message": str(e)}

    def stop_container(self, container_name: str, timeout: int = 30) -> dict:
        """Stop a running container."""
        try:
            container = self.client.containers.get(container_name)
            container.stop(timeout=timeout)
            return {"success": True, "message": f"Container {container_name} stopped"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def start_container(self, container_name: str) -> dict:
        """Start a stopped container."""
        try:
            container = self.client.containers.get(container_name)
            container.start()
            self._wait_healthy(container_name, timeout=60)
            return {"success": True, "message": f"Container {container_name} started"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def scale_service(self, service_name: str, replicas: int) -> dict:
        """Scale a Docker Compose service (requires Compose labels)."""
        try:
            containers = self.client.containers.list(
                filters={"label": f"com.docker.compose.service={service_name}"}
            )
            current = len(containers)
            if replicas == current:
                return {"success": True, "message": f"Already at {replicas} replicas"}

            if replicas > current:
                # Scale up by running more containers based on existing config
                return {"success": True, "message": f"Scale up requested: {current} -> {replicas}",
                        "note": "Use docker-compose scale for full support"}
            else:
                # Scale down by stopping excess
                to_stop = current - replicas
                for container in containers[:to_stop]:
                    container.stop(timeout=10)
                return {"success": True, "message": f"Scaled down: {current} -> {replicas}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_container_logs(self, container_name: str, lines: int = 100) -> dict:
        """Get recent logs from a container."""
        try:
            container = self.client.containers.get(container_name)
            logs = container.logs(tail=lines, timestamps=True).decode('utf-8', errors='replace')
            return {"success": True, "logs": logs}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_container_stats(self, container_name: str) -> dict:
        """Get current resource stats for a container."""
        try:
            container = self.client.containers.get(container_name)
            stats = container.stats(stream=False)

            # Parse CPU usage
            cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - \
                        stats["precpu_stats"]["cpu_usage"]["total_usage"]
            system_delta = stats["cpu_stats"]["system_cpu_usage"] - \
                           stats["precpu_stats"]["system_cpu_usage"]
            cpu_pct = (cpu_delta / system_delta) * 100 if system_delta > 0 else 0

            # Parse memory usage
            mem_usage = stats["memory_stats"].get("usage", 0)
            mem_limit = stats["memory_stats"].get("limit", 1)
            mem_pct = (mem_usage / mem_limit) * 100

            return {
                "success": True,
                "cpu_percent": round(cpu_pct, 2),
                "memory_usage_mb": round(mem_usage / (1024 * 1024), 2),
                "memory_percent": round(mem_pct, 2),
                "memory_limit_mb": round(mem_limit / (1024 * 1024), 2),
            }
        except Exception as e:
            return {"success": False, "message": str(e)}

    def inspect_container(self, container_name: str) -> dict:
        """Get detailed container inspection data."""
        try:
            container = self.client.containers.get(container_name)
            info = container.attrs
            return {
                "success": True,
                "name": container.name,
                "status": container.status,
                "image": info["Config"]["Image"],
                "created": info["Created"],
                "ports": info["NetworkSettings"]["Ports"],
                "env": info["Config"].get("Env", []),
            }
        except Exception as e:
            return {"success": False, "message": str(e)}

    def _wait_healthy(self, container_name: str, timeout: int = 60) -> bool:
        """Wait for a container to become healthy."""
        start = time.time()
        while time.time() - start < timeout:
            try:
                container = self.client.containers.get(container_name)
                state = container.attrs.get("State", {})
                health = state.get("Health", {}).get("Status", "")
                if container.status == "running" and health in ("healthy", ""):
                    return True
            except Exception:
                pass
            time.sleep(2)
        return False

    def is_available(self) -> bool:
        """Check if Docker is available."""
        try:
            self.client.ping()
            return True
        except Exception:
            return False
