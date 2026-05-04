# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Tool Registry.

Singleton registry for managing system tools (formerly tools).
"""

from typing import List, Optional, Any
from .base import Tool


class ToolRegistry:
    """Singleton registry for managing system tools.
    
    This class implements the singleton pattern to provide a centralized
    registry for all system tools. Tools can be registered, unregistered,
    and retrieved by name. The registry also manages tool lifecycle
    (initialization and shutdown).
    
    Attributes:
        _instance: Singleton instance of ToolRegistry.
        _tools: Dictionary mapping tool names to Tool instances.
        _initialized: Boolean flag indicating if the registry has been initialized.
        _container: Dependency injection container for tool initialization.
    """
    
    _instance: Optional['ToolRegistry'] = None
    _tools: dict[str, Tool]
    _initialized: bool
    _container: Any

    def __new__(cls) -> 'ToolRegistry':
        """Create or return the singleton ToolRegistry instance.
        
        Returns:
            The singleton ToolRegistry instance.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools = {}
            cls._instance._initialized = False
        return cls._instance

    def register(self, tool: Tool) -> None:
        """Register a tool with the registry.
        
        Registers a new tool with the registry. If the tool implements
        accessibility features (AccessibleTool), it logs an ISO compliance
        message. The tool is also initialized if the registry has a container.
        
        Args:
            tool: The Tool instance to register.
            
        Raises:
            ValueError: If a tool with the same name is already registered.
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool {tool.name} already registered")

        # Check for accessibility compliance before registering
        from nodupe.core.api.codes import ActionCode
        import logging
        logger = logging.getLogger(__name__)

        # Check if the tool implements accessibility features
        from nodupe.core.tool_system.base import AccessibleTool
        if isinstance(tool, AccessibleTool):
            logger.info(f"[{ActionCode.ACC_ISO_CMP}] Registering ISO accessibility compliant tool: {tool.name}")
        else:
            logger.info(f"[{ActionCode.ACC_FEATURE_DISABLED}] Registering tool without accessibility features: {tool.name}")

        self._tools[tool.name] = tool
        if hasattr(self, '_container') and self._container:
            tool.initialize(self._container)

    def unregister(self, name: str) -> None:
        """Unregister a tool from the registry.
        
        Removes a tool from the registry and calls its shutdown method
        to clean up any resources.
        
        Args:
            name: The name of the tool to unregister.
            
        Raises:
            KeyError: If no tool with the given name is registered.
        """
        if name not in self._tools:
            raise KeyError(f"Tool {name} not found")

        tool = self._tools[name]
        tool.shutdown()
        del self._tools[name]

    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name.
        
        Retrieves a registered tool by its name.
        
        Args:
            name: The name of the tool to retrieve.
            
        Returns:
            The Tool instance if found, None otherwise.
        """
        return self._tools.get(name)

    def get_tools(self) -> List[Tool]:
        """Get all registered tools.
        
        Returns a list of all currently registered tools.
        
        Returns:
            A list of all Tool instances in the registry.
        """
        return list(self._tools.values())

    def clear(self) -> None:
        """Clear all registered tools.
        
        Removes all tools from the registry without calling their
        shutdown methods. Use shutdown() instead if proper cleanup
        is required.
        """
        self._tools.clear()

    def shutdown(self) -> None:
        """Shutdown all tools and clear the registry.
        
        Calls the shutdown method on all registered tools to properly
        clean up resources. After shutdown, clears all tools and
        resets the container and initialization state.
        """
        for tool in self._tools.values():
            try:
                tool.shutdown()
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Error shutting down tool {tool.name}: {e}")

        self._tools.clear()
        self._container = None
        self._initialized = False

    def initialize(self, container: Any) -> None:
        """Initialize the registry with a dependency container.
        
        Sets the dependency injection container that will be used to
        initialize tools when they are registered. This should be called
        before registering any tools.
        
        Args:
            container: The dependency injection container to use for tool initialization.
        """
        self._container = container
        self._initialized = True

    @property
    def container(self):
        """Get the service container.
        
        Returns the dependency injection container if it has been set,
        or None if the registry has not been initialized.
        
        Returns:
            The dependency container or None if not initialized.
        """
        return getattr(self, '_container', None)

    @classmethod
    def _reset_instance(cls):
        """Reset the singleton instance.
        
        This method is primarily intended for testing purposes. It clears
        the singleton instance, allowing a new one to be created. This
        should be used with caution in production code.
        """
        cls._instance = None


# Alias for compatibility
PluginRegistry = ToolRegistry
"""Alias for ToolRegistry for backwards compatibility.

This alias allows existing code that references PluginRegistry to
continue working with the renamed ToolRegistry class.
"""

__all__ = ['ToolRegistry', 'PluginRegistry']
