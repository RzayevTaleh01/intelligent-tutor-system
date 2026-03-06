from typing import Dict, Type
from src.core.plugin.interfaces import LearningPlugin

class PluginRegistry:
    _plugins: Dict[str, LearningPlugin] = {}

    @classmethod
    def register(cls, name: str, plugin: LearningPlugin):
        cls._plugins[name] = plugin

    @classmethod
    def get(cls, name: str) -> LearningPlugin:
        return cls._plugins.get(name)

    @classmethod
    def list_plugins(cls):
        return list(cls._plugins.keys())
