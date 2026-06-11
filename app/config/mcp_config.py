from typing import List, Optional
from pydantic import BaseModel

class MCPTool(BaseModel):
    name: str
    enabled: bool = True
    description: Optional[str] = None

class MCPServer(BaseModel):
    name: str
    url: str
    enabled: bool = True
    tools: List[MCPTool] = []

class MCPConfig(BaseModel):
    servers: List[MCPServer] = []
    
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