import json
import time
import ssl
import requests
from typing import Optional, Dict, Any
from app.config.settings import settings
from app.utils.logger import plan_logger

class AIChatService:
    def __init__(self):
        plan_logger.info("Initializing AIChatService")
        self.api_key = settings.VOLC_API_KEY
        self.access_key = settings.VOLC_ACCESS_KEY
        self.secret_key = settings.VOLC_SECRET_KEY
        self.base_url = "https://ark.cn-beijing.volces.com/api/coding/v3"
        self.session = self._create_session()
        self.use_mock = settings.USE_MOCK_AI or (not self.api_key and not (self.access_key and self.secret_key)) or self._check_network_access()
        plan_logger.info(f"AIChatService initialized with API Key: {self.api_key is not None}, AK/SK: {(self.access_key and self.secret_key) is not None}, Use Mock: {self.use_mock}")

    def _check_network_access(self) -> bool:
        try:
            import socket
            socket.setdefaulttimeout(3)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("ark.cn-beijing.volces.com", 443))
            return False
        except Exception as e:
            plan_logger.warning(f"Cannot connect to ark.cn-beijing.volces.com, will use mock mode: {str(e)}")
            return True

    def _create_session(self) -> requests.Session:
        session = requests.Session()

        adapter = requests.adapters.HTTPAdapter(
            max_retries=2,
            pool_connections=10,
            pool_maxsize=10
        )
        session.mount("https://", adapter)

        session.trust_env = False

        return session

    def _generate_signature(self, params: Dict[str, Any]) -> str:
        sorted_params = sorted(params.items())
        sign_string = "&".join([f"{k}={v}" for k, v in sorted_params])
        sign_string += f"&secret={self.secret_key}"
        import hashlib
        return hashlib.md5(sign_string.encode()).hexdigest()

    def _get_mock_response(self, message: str) -> str:
        mock_responses = {
            "hello": "你好！我是你的智能助手，很高兴为你服务！",
            "hi": "嗨！有什么我可以帮助你的吗？",
            "start": "欢迎使用聊天机器人！\n\n可用命令：\n/help - 显示帮助\n/rag [问题] - RAG问答\n/plan [需求] - 生成代码规划\n/mcp - 显示可用MCP工具",
            "help": "可用命令：\n/start - 开始使用\n/help - 显示此帮助\n/rag [问题] - 基于文档进行问答\n/plan [需求] - 生成代码规划\n/mcp - 显示可用MCP工具",
        }

        message_lower = message.lower().strip()
        for key, response in mock_responses.items():
            if key in message_lower:
                return response

        return f"感谢你的消息！你说的是：\"{message}\"\n\n（当前处于模拟模式，实际AI服务需要配置火山引擎API密钥）"

    async def chat(self, message: str) -> Optional[str]:
        plan_logger.info(f"Generating AI response for message: {message[:100]}")

        if self.use_mock:
            plan_logger.info("Using mock AI response")
            return self._get_mock_response(message)

        try:
            if self.api_key:
                plan_logger.debug("Using API Key authentication")
                headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
                data = {
                    "model": "ark-code-latest",
                    "messages": [
                        {"role": "system", "content": "你是一个聪明的助手，请用自然、友好的语言回答用户的问题。"},
                        {"role": "user", "content": message}
                    ],
                    "max_tokens": 2048
                }
            else:
                plan_logger.debug("Using AK/SK authentication")
                headers = {"Content-Type": "application/json"}
                data = {
                    "access_key": self.access_key,
                    "timestamp": str(int(time.time())),
                    "model": "ark-code-latest",
                    "messages": [
                        {"role": "system", "content": "你是一个聪明的助手，请用自然、友好的语言回答用户的问题。"},
                        {"role": "user", "content": message}
                    ],
                    "max_tokens": 2048
                }

            plan_logger.debug(f"Sending request to {self.base_url}/chat/completions")
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )

            plan_logger.debug(f"Response status: {response.status_code}")
            plan_logger.debug(f"Response headers: {dict(response.headers) if response.headers else 'None'}")

            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get("choices"):
                        content = result["choices"][0]["message"]["content"]
                        plan_logger.info("AI response generated successfully")
                        return content
                    else:
                        error_msg = result.get("error", {}).get("message", "生成失败")
                        plan_logger.error(f"AI response generation failed: {error_msg}")
                        return error_msg
                except json.JSONDecodeError:
                    plan_logger.error(f"Failed to parse JSON, response text: {response.text[:200]}")
                    return f"响应解析失败: {response.text[:100]}"
            else:
                try:
                    error_detail = response.json().get("error", {}).get("message", "") if response.text else ""
                except:
                    error_detail = response.text[:100] if response.text else ""
                error_msg = f"请求失败: {response.status_code}"
                if error_detail:
                    error_msg += f" ({error_detail})"
                plan_logger.error(f"HTTP request failed: {response.status_code}, detail: {error_detail}")
                return error_msg
        except requests.exceptions.SSLError as e:
            error_msg = f"TLS连接错误，请检查网络环境"
            plan_logger.error(f"TLS/SSL error during AI chat: {str(e)}", exc_info=True)
            return error_msg
        except requests.exceptions.RequestException as e:
            error_msg = f"网络错误，请检查网络连接"
            plan_logger.error(f"Network error during AI chat: {str(e)}", exc_info=True)
            return error_msg
        except Exception as e:
            error_msg = f"服务错误: {str(e)[:50]}"
            plan_logger.error(f"Unexpected error during AI chat: {str(e)}", exc_info=True)
            return error_msg
