import json
from pathlib import Path
from typing import Optional, Dict, Any, List
import aiohttp
from app.config.settings import settings
from app.config.mcp_config import MCPConfig, MCPServer, MCPTool

class MCPManager:
    def __init__(self):
        self.config = self._load_config()
        self.servers: Dict[str, MCPServer] = {server.name: server for server in self.config.servers}
    
    def _load_config(self) -> MCPConfig:
        config_path = Path(settings.MCP_CONFIG_PATH)
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return MCPConfig(**data)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return MCPConfig()
    
    def register_mcp_server(self, server: MCPServer):
        self.servers[server.name] = server
        if server not in self.config.servers:
            self.config.servers.append(server)
    
    def unregister_mcp_server(self, name: str):
        self.servers.pop(name, None)
        self.config.servers = [s for s in self.config.servers if s.name != name]
    
    def get_enabled_tools(self) -> List[MCPTool]:
        return self.config.get_enabled_tools()
    
    def get_server(self, name: str) -> Optional[MCPServer]:
        return self.servers.get(name)
    
    async def call_mcp_tool(self, server_name: str, tool_name: str, **kwargs) -> Optional[Dict[str, Any]]:
        server = self.servers.get(server_name)
        if not server or not server.enabled:
            return None
        
        tool = next((t for t in server.tools if t.name == tool_name and t.enabled), None)
        if not tool:
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{server.url}/tools/{tool_name}"
                async with session.post(url, json=kwargs) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except Exception as e:
            return None
    
    async def list_server_tools(self, server_name: str) -> Optional[List[Dict[str, Any]]]:
        server = self.servers.get(server_name)
        if not server or not server.enabled:
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{server.url}/tools"
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except Exception as e:
            return None