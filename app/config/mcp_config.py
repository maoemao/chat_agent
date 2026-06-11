from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class MCPTool(BaseModel):
    name: str
    enabled: bool = True
    description: Optional[str] = None

class MCPServer(BaseModel):
    name: str
    url: str = ""
    enabled: bool = True
    tools: List[MCPTool] = []
    command: Optional[str] = None
    args: List[str] = []
    env: Dict[str, str] = {}
    process: Optional[Any] = None
    mode: str = "http"

class MCPConfig(BaseModel):
    servers: List[MCPServer] = []
    
    @classmethod
    def from_langchain_format(cls, data: Dict[str, Any]) -> 'MCPConfig':
        servers = []
        mcp_servers = data.get('mcpServers', {})
        for name, server_config in mcp_servers.items():
            server = MCPServer(
                name=name,
                enabled=server_config.get('enabled', True),
                command=server_config.get('command'),
                args=server_config.get('args', []),
                env=server_config.get('env', {}),
                mode=server_config.get('mode', 'http'),
                tools=[]
            )
            servers.append(server)
        return cls(servers=servers)
    
    def get_enabled_tools(self) -> List[MCPTool]:
        tools = []
        for server in self.servers:
            if server.enabled:
                tools.extend([tool for tool in server.tools if tool.enabled])
        return tools
    
    def get_server_by_name(self, name: str) -> Optional[MCPServer]:
        for server in self.servers:
            if server.name == name:
                return server
        return None