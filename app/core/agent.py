from typing import Optional, Dict, Any
from app.core.types import Message, MessageType, Command
from app.services.rag_service import RAGService
from app.services.codeing_plan_service import CodeingPlanService
from app.services.code_editor_service import CodeEditorService
from app.services.ai_chat_service import AIChatService
from app.services.mcp_service import MCPManager
from app.services.git_service import GitService
from app.core.message_router import MessageRouter
from app.utils.logger import agent_logger

class AgentCore:
    def __init__(self):
        agent_logger.info("Initializing AgentCore")
        self.rag_service = RAGService()
        self.codeing_plan_service = CodeingPlanService()
        self.code_editor_service = CodeEditorService()
        self.ai_chat_service = AIChatService()
        self.mcp_manager = MCPManager()
        self.git_service = GitService()
        self.message_router = MessageRouter()
        self._register_handlers()
        agent_logger.info("AgentCore initialized successfully")
    
    def _register_handlers(self):
        agent_logger.debug("Registering message handlers")
        self.message_router.register_handler(MessageType.COMMAND, self.handle_command)
        self.message_router.register_handler(MessageType.TEXT, self.handle_text)
    
    async def handle_command(self, message: Message) -> Optional[str]:
        agent_logger.info(f"Handling command message from {message.sender_name} (id: {message.sender}): {message.content[:100]}")
        command = self._parse_command(message.content)
        agent_logger.debug(f"Parsed command: name={command.name}, args={command.args}")
        
        command_handlers = {
            'start': self._handle_start,
            'help': self._handle_help,
            'rag': self._handle_rag,
            'plan': self._handle_plan,
            'code': self._handle_code,
            'mcp': self._handle_mcp,
            'git': self._handle_git,
        }
        
        handler = command_handlers.get(command.name)
        if handler:
            try:
                result = await handler(command, message)
                agent_logger.info(f"Command '{command.name}' executed successfully, response: {result[:100] if result else 'None'}")
                return result
            except Exception as e:
                agent_logger.error(f"Error executing command '{command.name}': {str(e)}", exc_info=True)
                return "执行命令时发生错误"
        agent_logger.warning(f"Unknown command: {command.name}")
        return "未知命令，请使用 /help 查看可用命令"
    
    async def handle_text(self, message: Message) -> Optional[str]:
        agent_logger.info(f"Handling text message from {message.sender_name} (id: {message.sender}): {message.content[:100]}")
        try:
            ai_response = await self.ai_chat_service.chat(message.content)
            if ai_response:
                agent_logger.info(f"AI response generated: {ai_response[:100]}")
                return ai_response
            agent_logger.debug("No AI response found")
            return "我不太明白你的意思，请尝试使用命令或重新表述问题。"
        except Exception as e:
            agent_logger.error(f"Error handling text message: {str(e)}", exc_info=True)
            return "处理消息时发生错误"
    
    async def _handle_start(self, command: Command, message: Message) -> str:
        agent_logger.debug(f"Handling /start command from {message.sender}")
        return f"""欢迎使用聊天机器人！

可用命令：
/help - 显示帮助
/rag [问题] - RAG问答（基于文档）
/plan [需求] - 生成代码规划
/code [需求] - 分析并修改代码
/git [操作] - Git操作（status/diff/push等）
/mcp - 显示可用MCP工具"""
    
    async def _handle_help(self, command: Command, message: Message) -> str:
        agent_logger.debug(f"Handling /help command from {message.sender}")
        return """可用命令：
/start - 开始使用
/help - 显示此帮助
/rag [问题] - 基于文档进行问答
/plan [需求] - 生成代码规划
/code [需求] - 分析并修改项目代码
/git [操作] - Git操作（status/diff/push等）
/mcp - 显示可用MCP工具"""
    
    async def _handle_rag(self, command: Command, message: Message) -> str:
        if not command.args:
            agent_logger.warning(f"/rag command called without args from {message.sender}")
            return "请提供问题，例如：/rag 如何使用这个系统？"
        question = " ".join(command.args)
        agent_logger.debug(f"Handling /rag command with question: {question[:100]}")
        response = await self.rag_service.query(question)
        return response or "未能找到相关答案"
    
    async def _handle_plan(self, command: Command, message: Message) -> str:
        if not command.args:
            agent_logger.warning(f"/plan command called without args from {message.sender}")
            return "请提供需求描述，例如：/plan 创建一个登录页面"
        requirement = " ".join(command.args)
        agent_logger.debug(f"Handling /plan command with requirement: {requirement[:100]}")
        plan = await self.codeing_plan_service.generate_plan(requirement)
        return plan or "未能生成代码规划"
    
    async def _handle_code(self, command: Command, message: Message) -> str:
        if not command.args:
            agent_logger.warning(f"/code command called without args from {message.sender}")
            return """📝 代码修改助手

用法：
/code [需求描述] - 分析并生成代码修改方案

示例：
/code 添加用户登录功能
/code 修改数据库连接配置
/code 为RAG服务添加缓存机制

功能说明：
1. 分析项目现有代码结构
2. 根据需求生成修改方案
3. 提供完整的修改后代码
4. 安全提示：自动备份原文件"""
        requirement = " ".join(command.args)
        agent_logger.debug(f"Handling /code command with requirement: {requirement[:100]}")
        result = await self.code_editor_service.analyze_and_modify(requirement)
        return result or "未能生成代码修改方案"
    
    async def _handle_mcp(self, command: Command, message: Message) -> str:
        agent_logger.debug(f"Handling /mcp command from {message.sender}")
        if not command.args:
            agent_logger.debug("No args provided, showing tool list")
            tools = self.mcp_manager.get_enabled_tools()
            if not tools:
                agent_logger.debug("No MCP tools available")
                return """🔧 MCP工具

用法：
/mcp - 显示可用工具
/mcp <工具名> <参数> - 调用指定工具

示例：
/mcp search AI最新动态

可用工具：
暂无可用的MCP工具"""
            tool_list = "\n".join([f"- {tool.name}: {tool.description or '无描述'}" for tool in tools])
            return f"""🔧 MCP工具

用法：
/mcp - 显示可用工具
/mcp <工具名> <参数> - 调用指定工具

示例：
/mcp search AI最新动态

可用工具：
{tool_list}"""
        
        tool_name = command.args[0]
        tool_args = command.args[1:]
        
        if tool_name == "search":
            if not tool_args:
                return "请提供搜索关键词，例如：/mcp search AI最新动态"
            query = " ".join(tool_args)
            agent_logger.debug(f"Calling MCP search tool with query: {query}")
            try:
                result = await self.mcp_manager.call_mcp_tool("ddg-search", "search", query=query)
                if result:
                    return self._format_search_result(result)
                return "搜索失败，请稍后重试"
            except Exception as e:
                agent_logger.error(f"Error calling MCP tool: {str(e)}")
                return f"调用MCP工具时发生错误: {str(e)}"
        
        return f"未知工具: {tool_name}"

    async def _handle_git(self, command: Command, message: Message) -> str:
        """处理 Git 命令"""
        agent_logger.debug(f"Handling /git command from {message.sender}, args: {command.args}")

        # 无参数时显示帮助
        if not command.args:
            return """📦 Git 操作助手

用法：
/git status - 查看工作区状态
/git diff - 查看未暂存的更改
/git log - 查看最近的提交记录
/git branch - 查看当前分支信息
/git add - 暂存所有更改
/git commit [message] - 提交更改
/git push - 推送到远程仓库
/git commitpush [message] - 提交并推送

示例：
/git status
/git commit 修复了登录bug
/git commitpush 添加了新功能"""

        subcommand = command.args[0].lower()
        subargs = command.args[1:]

        try:
            if subcommand == "status":
                return self.git_service.get_status()

            elif subcommand == "diff":
                return self.git_service.get_diff()

            elif subcommand == "log":
                limit = int(subargs[0]) if subargs and subargs[0].isdigit() else 5
                return self.git_service.get_log(limit)

            elif subcommand == "branch":
                return self.git_service.get_branch()

            elif subcommand == "add":
                return self.git_service.stage_all()

            elif subcommand == "commit":
                if not subargs:
                    return "❌ 请提供提交信息\n\n示例：/git commit 修复了登录bug"
                commit_message = " ".join(subargs)
                return self.git_service.commit(commit_message)

            elif subcommand == "push":
                return self.git_service.push()

            elif subcommand == "commitpush":
                """一键提交并推送"""
                if not subargs:
                    return "❌ 请提供提交信息\n\n示例：/git commitpush 修复了登录bug"

                commit_message = " ".join(subargs)

                # 先提交
                commit_result = self.git_service.commit(commit_message)
                if not commit_result.startswith("✅"):
                    return commit_result

                # 如果提交成功，再推送
                push_result = self.git_service.push()
                return f"{commit_result}\n\n{push_result}"

            else:
                return f"❌ 未知Git命令：{subcommand}\n\n使用 /git 查看帮助信息"

        except Exception as e:
            agent_logger.error(f"Error handling git command: {str(e)}", exc_info=True)
            return f"❌ Git操作失败：{str(e)}"
    
    def _format_search_result(self, result: Dict[str, Any]) -> str:
        if not result:
            return "未找到搜索结果"
        if isinstance(result, dict) and 'results' in result:
            results = result['results']
            if not results:
                return "未找到搜索结果"
            formatted = "🔍 搜索结果:\n\n"
            for i, item in enumerate(results[:5], 1):
                title = item.get('title', '')
                url = item.get('url', '')
                snippet = item.get('snippet', '')
                formatted += f"{i}. [{title}]({url})\n{snippet}\n\n"
            return formatted
        return str(result)
    
    def _parse_command(self, content: str) -> Command:
        parts = content.split()
        name = parts[0][1:] if parts else ""
        args = parts[1:] if len(parts) > 1 else []
        return Command(name=name, args=args, raw=content)
    
    def register_adapter(self, adapter):
        agent_logger.info(f"Registering adapter: {adapter.get_name()}")
        self.message_router.register_adapter(adapter)