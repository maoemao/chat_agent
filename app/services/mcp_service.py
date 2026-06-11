import json
import asyncio
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import aiohttp
import subprocess
import httpx
from app.config.settings import settings
from app.config.mcp_config import MCPConfig, MCPServer, MCPTool

class DuckDuckGoSearcher:
    BASE_URL = "https://html.duckduckgo.com/html"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    def __init__(self, safe_search: str = "MODERATE", default_region: str = ""):
        self.safe_search = safe_search
        self.default_region = default_region

    async def search(self, query: str, max_results: int = 10, region: str = "") -> str:
        try:
            effective_region = region if region else self.default_region
            
            data = {
                "q": query,
                "b": "",
                "kl": effective_region,
                "kp": "1" if self.safe_search == "STRICT" else "-1" if self.safe_search == "MODERATE" else "-2",
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.BASE_URL, data=data, headers=self.HEADERS, timeout=30.0
                )
                response.raise_for_status()

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, "html.parser")
            
            results = []
            for result in soup.select(".result")[:max_results]:
                title_elem = result.select_one(".result__title")
                if not title_elem:
                    continue
                
                link_elem = title_elem.find("a")
                if not link_elem:
                    continue
                
                title = link_elem.get_text(strip=True)
                link = link_elem.get("href", "")
                
                if "y.js" in link:
                    continue
                
                if link.startswith("//duckduckgo.com/l/?uddg="):
                    import urllib.parse
                    link = urllib.parse.unquote(link.split("uddg=")[1].split("&")[0])
                
                snippet_elem = result.select_one(".result__snippet")
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                
                results.append({
                    "title": title,
                    "link": link,
                    "snippet": snippet
                })
            
            if not results:
                return "未找到搜索结果"
            
            formatted = "🔍 搜索结果:\n\n"
            for i, item in enumerate(results, 1):
                formatted += f"{i}. [{item['title']}]({item['link']})\n{item['snippet']}\n\n"
            
            return formatted
            
        except Exception as e:
            return f"搜索失败: {str(e)}"

class MCPManager:
    def __init__(self):
        self.config = self._load_config()
        self.servers: Dict[str, MCPServer] = {server.name: server for server in self.config.servers}
        self.searcher = None
        self._init_searcher()
    
    def _init_searcher(self):
        for server in self.config.servers:
            if server.name == "ddg-search":
                safe_search = server.env.get("DDG_SAFE_SEARCH", "MODERATE")
                region = server.env.get("DDG_REGION", "")
                self.searcher = DuckDuckGoSearcher(safe_search=safe_search, default_region=region)
                break
    
    def _load_config(self) -> MCPConfig:
        config_path = Path(settings.MCP_CONFIG_PATH)
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'mcpServers' in data:
                        return MCPConfig.from_langchain_format(data)
                    return MCPConfig(**data)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return MCPConfig()
    
    async def start_server(self, server: MCPServer) -> bool:
        if not server.command:
            return False
        
        env = os.environ.copy()
        env.update(server.env)
        try:
            process = await asyncio.create_subprocess_exec(
                server.command,
                *server.args,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            server.process = process
            await asyncio.sleep(2)
            return process.returncode is None
        except Exception as e:
            return False
    
    async def stop_server(self, server_name: str) -> bool:
        server = self.servers.get(server_name)
        if server and server.process:
            server.process.terminate()
            try:
                await server.process.wait()
            except Exception:
                pass
            server.process = None
            return True
        return False
    
    async def start_all_servers(self):
        for server in self.config.servers:
            if server.enabled and server.command:
                await self.start_server(server)
    
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
    
    async def call_mcp_tool(self, server_name: str, tool_name: str, **kwargs) -> Optional[str]:
        if tool_name == "search" and self.searcher:
            query = kwargs.get('query', '')
            max_results = kwargs.get('max_results', 10)
            region = kwargs.get('region', '')
            return await self.searcher.search(query, max_results, region)
        return None
    
    async def list_server_tools(self, server_name: str) -> Optional[List[Dict[str, Any]]]:
        return [
            {"name": "search", "description": "使用 DuckDuckGo 进行网络搜索"}
        ]