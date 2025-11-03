"""
Tool Discovery Service
Provides centralized tool detection and management.
"""

from dynamic_tools import detect_available_tools, get_tool_categories
import logging

logger = logging.getLogger(__name__)


class ToolService:
    """Service for managing tool discovery and information."""

    def __init__(self):
        """Initialize tool service and detect available tools."""
        self._tools = None
        self._categories = None
        self._refresh_tools()

    def _refresh_tools(self):
        """Refresh tool detection."""
        logger.info('Detecting available tools...')
        self._tools = detect_available_tools()
        self._categories = get_tool_categories(self._tools)
        logger.info(f'Detected {len(self._tools)} tools in {len(self._categories)} categories')

    @property
    def tools(self):
        """Get detected tools."""
        return self._tools

    @property
    def categories(self):
        """Get tool categories."""
        return self._categories

    def get_tool_count(self):
        """Get number of detected tools."""
        return len(self._tools)

    def get_tool_info(self, tool_name):
        """Get information about a specific tool."""
        return self._tools.get(tool_name)

    def tool_exists(self, tool_name):
        """Check if a tool exists."""
        return tool_name in self._tools


# Global tool service instance
tool_service = ToolService()
