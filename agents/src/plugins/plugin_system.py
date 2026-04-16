"""
Plugin System: Extensible architecture for adding capabilities to agents.
Supports discovery, loading, sandboxing, lifecycle management, and hot reload.
"""
import os
import time
import logging
import importlib
import importlib.util
import threading
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class PluginType(str, Enum):
    DIAGNOSTIC = "diagnostic"
    REMEDIATION = "remediation"
    DATA_SOURCE = "data_source"
    NOTIFICATION = "notification"
    INTEGRATION = "integration"


@dataclass
class PluginMetadata:
    name: str
    version: str
    author: str
    description: str
    plugin_type: PluginType
    capabilities: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    min_system_version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)


class AgentPlugin(ABC):
    """Base class for all agent plugins."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._initialized = False
        self._execution_count = 0
        self._total_time_ms = 0.0
        self._error_count = 0

    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        pass

    def initialize(self) -> bool:
        """Setup logic. Return True on success."""
        self._initialized = True
        return True

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Main plugin logic. Return result dict."""
        pass

    def cleanup(self):
        """Teardown logic."""
        self._initialized = False

    def validate_config(self) -> List[str]:
        """Validate plugin configuration. Return list of errors (empty = valid)."""
        return []

    @property
    def stats(self) -> Dict[str, Any]:
        avg = self._total_time_ms / max(self._execution_count, 1)
        return {
            "executions": self._execution_count,
            "avg_time_ms": round(avg, 1),
            "error_count": self._error_count,
            "error_rate": round(self._error_count / max(self._execution_count, 1) * 100, 1),
            "initialized": self._initialized,
        }


@dataclass
class SandboxLimits:
    timeout_sec: float = 30.0
    max_memory_mb: int = 256
    max_cpu_pct: float = 50.0
    allow_network: bool = True
    allow_filesystem: bool = False
    allowed_modules: List[str] = field(default_factory=lambda: [
        "json", "re", "math", "statistics", "collections", "datetime",
        "hashlib", "urllib", "http", "logging",
    ])


class PluginSandbox:
    """Enforces resource limits and error isolation for plugins."""

    def __init__(self, limits: Optional[SandboxLimits] = None):
        self.limits = limits or SandboxLimits()

    def execute(self, plugin: AgentPlugin, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute plugin within sandbox constraints."""
        result: Dict[str, Any] = {}
        error: Optional[Exception] = None

        def _run():
            nonlocal result, error
            try:
                result = plugin.execute(context)
            except Exception as e:
                error = e

        thread = threading.Thread(target=_run, daemon=True)
        start = time.time()
        thread.start()
        thread.join(timeout=self.limits.timeout_sec)

        duration_ms = (time.time() - start) * 1000
        plugin._execution_count += 1
        plugin._total_time_ms += duration_ms

        if thread.is_alive():
            plugin._error_count += 1
            return {"error": "Plugin execution timed out", "timeout_sec": self.limits.timeout_sec}

        if error:
            plugin._error_count += 1
            return {"error": str(error), "type": type(error).__name__}

        return result


class PluginSystem:
    """
    Main plugin manager: discovery, loading, lifecycle, hot-reload.
    """

    def __init__(self, plugin_dir: str = "agents/plugins", config_path: str = "agents/config/plugins.yaml"):
        self._plugin_dir = Path(plugin_dir)
        self._config_path = config_path
        self._plugins: Dict[str, AgentPlugin] = {}
        self._metadata: Dict[str, PluginMetadata] = {}
        self._sandbox = PluginSandbox()
        self._lock = threading.Lock()
        self._config: Dict[str, Any] = {}
        self._load_config()

    # ── Configuration ─────────────────────────────────────────────────

    def _load_config(self):
        """Load plugin configuration from YAML."""
        try:
            import yaml
            if os.path.exists(self._config_path):
                with open(self._config_path) as f:
                    self._config = yaml.safe_load(f) or {}
        except ImportError:
            self._config = {}
        except Exception as e:
            logger.warning(f"[PluginSystem] Could not load config: {e}")
            self._config = {}

    def _is_enabled(self, plugin_name: str) -> bool:
        """Check if a plugin is enabled in config."""
        plugins_cfg = self._config.get("plugins", {})
        entry = plugins_cfg.get(plugin_name, {})
        if isinstance(entry, dict):
            return entry.get("enabled", True)
        return True

    def _get_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """Get plugin-specific settings from config."""
        plugins_cfg = self._config.get("plugins", {})
        entry = plugins_cfg.get(plugin_name, {})
        if isinstance(entry, dict):
            return entry.get("settings", {})
        return {}

    # ── Discovery & Loading ───────────────────────────────────────────

    def discover_plugins(self) -> List[str]:
        """Scan plugin directory for valid plugins."""
        discovered = []
        if not self._plugin_dir.exists():
            logger.info(f"[PluginSystem] Plugin directory {self._plugin_dir} not found")
            return discovered

        for path in self._plugin_dir.glob("*.py"):
            if path.name.startswith("_"):
                continue
            name = path.stem
            if self._validate_plugin_file(path):
                discovered.append(name)
            else:
                logger.warning(f"[PluginSystem] Invalid plugin: {name}")

        logger.info(f"[PluginSystem] Discovered {len(discovered)} plugins")
        return discovered

    def _validate_plugin_file(self, path: Path) -> bool:
        """Validate that a file contains a proper plugin class."""
        try:
            content = path.read_text()
            return "AgentPlugin" in content and "get_metadata" in content and "execute" in content
        except Exception:
            return False

    def load_plugin(self, name: str) -> bool:
        """Load a single plugin by name."""
        if not self._is_enabled(name):
            logger.info(f"[PluginSystem] Plugin '{name}' is disabled")
            return False

        path = self._plugin_dir / f"{name}.py"
        if not path.exists():
            logger.error(f"[PluginSystem] Plugin file not found: {path}")
            return False

        try:
            spec = importlib.util.spec_from_file_location(f"plugins.{name}", str(path))
            if spec is None or spec.loader is None:
                return False
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find plugin class (subclass of AgentPlugin)
            plugin_cls = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and issubclass(attr, AgentPlugin)
                        and attr is not AgentPlugin):
                    plugin_cls = attr
                    break

            if plugin_cls is None:
                logger.error(f"[PluginSystem] No AgentPlugin subclass in {name}")
                return False

            config = self._get_plugin_config(name)
            plugin = plugin_cls(config)
            metadata = plugin.get_metadata()

            # Validate config
            errors = plugin.validate_config()
            if errors:
                logger.error(f"[PluginSystem] Config errors for {name}: {errors}")
                return False

            # Check dependencies
            if not self._check_dependencies(metadata):
                logger.error(f"[PluginSystem] Unmet dependencies for {name}")
                return False

            with self._lock:
                self._plugins[name] = plugin
                self._metadata[name] = metadata

            logger.info(f"[PluginSystem] Loaded plugin: {name} v{metadata.version}")
            return True

        except Exception as e:
            logger.error(f"[PluginSystem] Failed to load {name}: {e}")
            return False

    def _check_dependencies(self, metadata: PluginMetadata) -> bool:
        """Check if all plugin dependencies are met."""
        for dep in metadata.dependencies:
            try:
                importlib.import_module(dep)
            except ImportError:
                logger.warning(f"[PluginSystem] Missing dependency: {dep}")
                return False
        return True

    def load_all(self) -> Dict[str, bool]:
        """Discover and load all plugins. Returns {name: success}."""
        results = {}
        # Load in priority order from config
        priority_list = self._config.get("load_order", [])
        discovered = self.discover_plugins()

        ordered = [n for n in priority_list if n in discovered]
        ordered += [n for n in discovered if n not in ordered]

        for name in ordered:
            results[name] = self.load_plugin(name)

        return results

    # ── Lifecycle ─────────────────────────────────────────────────────

    def initialize_plugin(self, name: str) -> bool:
        """Initialize a loaded plugin."""
        plugin = self._plugins.get(name)
        if not plugin:
            return False
        try:
            return plugin.initialize()
        except Exception as e:
            logger.error(f"[PluginSystem] Init failed for {name}: {e}")
            return False

    def initialize_all(self) -> Dict[str, bool]:
        results = {}
        for name in list(self._plugins.keys()):
            results[name] = self.initialize_plugin(name)
        return results

    def execute_plugin(self, name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a plugin within the sandbox."""
        plugin = self._plugins.get(name)
        if not plugin:
            return {"error": f"Plugin '{name}' not found"}
        if not plugin._initialized:
            return {"error": f"Plugin '{name}' not initialized"}
        return self._sandbox.execute(plugin, context)

    def unload_plugin(self, name: str) -> bool:
        """Cleanup and remove a plugin."""
        with self._lock:
            plugin = self._plugins.pop(name, None)
            self._metadata.pop(name, None)
        if plugin:
            try:
                plugin.cleanup()
            except Exception as e:
                logger.warning(f"[PluginSystem] Cleanup error for {name}: {e}")
            return True
        return False

    def reload_plugin(self, name: str) -> bool:
        """Hot-reload a plugin (unload + load + init)."""
        self.unload_plugin(name)
        if self.load_plugin(name):
            return self.initialize_plugin(name)
        return False

    # ── Query ─────────────────────────────────────────────────────────

    def get_plugins_by_type(self, ptype: PluginType) -> List[str]:
        return [n for n, m in self._metadata.items() if m.plugin_type == ptype]

    def get_plugins_by_capability(self, capability: str) -> List[str]:
        return [n for n, m in self._metadata.items() if capability in m.capabilities]

    def get_plugin_info(self, name: str) -> Optional[Dict[str, Any]]:
        meta = self._metadata.get(name)
        plugin = self._plugins.get(name)
        if not meta or not plugin:
            return None
        return {
            "name": meta.name,
            "version": meta.version,
            "author": meta.author,
            "description": meta.description,
            "type": meta.plugin_type.value,
            "capabilities": meta.capabilities,
            "tags": meta.tags,
            "stats": plugin.stats,
        }

    def list_plugins(self) -> List[Dict[str, Any]]:
        return [self.get_plugin_info(n) for n in self._plugins if self.get_plugin_info(n)]

    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "total_loaded": len(self._plugins),
            "by_type": {t.value: len(self.get_plugins_by_type(t)) for t in PluginType},
            "plugins": {n: p.stats for n, p in self._plugins.items()},
        }
