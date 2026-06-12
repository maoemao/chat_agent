# MCP 功能调用（/mcp）

## 一、概述

MCP（Model Context Protocol）是 LangChain 定义的工具调用协议，本项目支持 DuckDuckGo 搜索和文件系统操作。

## 二、架构设计

```
┌──────────────────────┐
│      Agent Core      │
└──────────┬─────────┘
           │ 调用工具
           ▼
┌──────────────────────┐
│     MCP Manager      │
│  ┌────────────────┐  │
│  │ 模式判断逻辑   │  │
│  └────────┬───────┘  │
└───────────┼──────────┘
            │
    ┌───────┴───────┐
    ▼               ▼
┌─────────┐   ┌─────────┐
│ HTTP    │   │ MCP     │
│ 模式    │   │ 模式    │
└────┬────┘   └────┬────┘
     │             │
     ▼             ▼
┌─────────┐   ┌─────────────┐
│ DuckDuckGo│ │ MCP Server  │
│ HTTP API │   │ (ddg-mcp)  │
└─────────┘   └─────────────┘
```

## 三、双模式支持

### 3.1 模式对比

| 模式 | 说明 | 优点 | 缺点 |
|------|------|------|------|
| **HTTP** | 直接调用 DuckDuckGo API | 无需启动额外服务器 | 功能有限 |
| **MCP** | 通过官方 MCP 服务器调用 | 功能完整 | 需要启动服务器 |

### 3.2 模式切换机制

```python
# app/services/mcp_service.py
async def call_mcp_tool(self, server_name: str, tool_name: str, **kwargs) -> Optional[str]:
    server = self.servers.get(server_name)
    if not server:
        return None
    
    if tool_name == "search":
        # 根据配置的模式选择执行方式
        mode = server.mode.lower()
        
        if mode == "http":
            # HTTP 模式：直接调用 DuckDuckGo API
            return await self._call_search_http(**kwargs)
        elif mode == "mcp":
            # MCP 模式：通过 MCP 服务器调用
            return await self._call_search_mcp(server, **kwargs)
        else:
            return f"未知模式: {mode}，请使用 'http' 或 'mcp'"
```

## 四、HTTP 模式实现

### 4.1 核心代码

```python
# app/services/mcp_service.py
async def _call_search_http(self, query: str) -> str:
    """直接调用 DuckDuckGo 搜索 API"""
    url = "https://api.duckduckgo.com/"
    params = {
        "q": query,
        "format": "json",
        "t": "maoge_agent",
        "region": "cn-zh"  # 中文地区
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
    
    if response.status_code == 200:
        results = response.json()
        # 解析搜索结果
        return self._format_search_results(results)
    else:
        return f"❌ 搜索失败：{response.status_code}"
```

### 4.2 结果格式化

```python
def _format_search_results(self, results: dict) -> str:
    """格式化搜索结果为 Markdown"""
    output = []
    
    # 获取相关搜索结果
    if "RelatedTopics" in results:
        for topic in results["RelatedTopics"][:5]:
            if "Text" in topic and "FirstURL" in topic:
                output.append(f"- [{topic['Text']}]({topic['FirstURL']})")
    
    # 获取回答摘要
    if "AbstractText" in results and results["AbstractText"]:
        output.insert(0, f"📌 {results['AbstractText']}")
    
    # 获取来源
    if "AbstractSource" in results and results["AbstractSource"]:
        output.append(f"\n来源：{results['AbstractSource']}")
    
    if not output:
        return "未找到相关结果"
    
    return "\n".join(output)
```

## 五、MCP 模式实现

### 5.1 MCP 服务器启动

```bash
# 安装 MCP 服务器
pip install duckduckgo-mcp-server

# 启动服务器
duckduckgo-mcp-server --transport streamable-http --host 0.0.0.0 --port 8787
```

### 5.2 MCP 客户端调用

```python
# app/services/mcp_service.py
async def _call_search_mcp(self, server, query: str) -> str:
    """通过 MCP 服务器调用搜索"""
    from langchain_mcp import MCPClient
    
    async with MCPClient(server.url) as client:
        result = await client.call_tool(
            tool_name="search",
            arguments={"query": query}
        )
    
    return result.content
```

## 六、配置文件

### 6.1 MCP 配置

```json
// config/mcp_config.json
{
  "mcpServers": {
    "ddg-search": {
      "command": "duckduckgo-mcp-server",
      "args": ["--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8787"],
      "env": {
        "DDG_REGION": "cn-zh"
      },
      "mode": "http"  // 或 "mcp"
    },
    "filesystem": {
      "command": "mcp-server-filesystem",
      "args": ["/path/to/project"],
      "env": {}
    }
  }
}
```

### 6.2 配置说明

| 字段 | 说明 |
|------|------|
| **command** | MCP 服务器命令 |
| **args** | 启动参数 |
| **env** | 环境变量 |
| **mode** | 运行模式（http/mcp） |

## 七、文件系统 MCP

### 7.1 功能说明

文件系统 MCP 提供项目文件浏览功能：

- ✅ 列出目录文件
- ✅ 读取文件内容
- ✅ 搜索文件
- ✅ 获取文件统计信息

### 7.2 启动命令

```bash
# 安装文件系统 MCP
pip install @modelcontextprotocol/server-filesystem

# 启动服务器
mcp-server-filesystem /path/to/project
```

## 八、使用示例

### 8.1 基础用法

```
# 显示可用工具
/mcp

# DuckDuckGo 搜索
/mcp search AI最新动态
/mcp search Python教程
/mcp search 2024年世界杯
```

### 8.2 命令格式

```
/mcp <工具名> <参数>
```

## 九、代码位置

| 文件 | 说明 |
|------|------|
| `app/services/mcp_service.py` | MCP 服务实现 |
| `app/core/agent.py` | /mcp 命令处理 |
| `config/mcp_config.json` | MCP 配置文件 |
