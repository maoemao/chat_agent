import json
import time
import requests
from typing import Optional, Dict, Any
from app.config.settings import settings
from app.utils.logger import plan_logger

class CodeingPlanService:
    def __init__(self):
        plan_logger.info("Initializing CodeingPlanService")
        self.api_key = settings.VOLC_API_KEY
        self.access_key = settings.VOLC_ACCESS_KEY
        self.secret_key = settings.VOLC_SECRET_KEY
        self.base_url = "https://ark.cn-beijing.volces.com/api/coding/v3"
        self.model = "ark-code-latest"
        plan_logger.info(f"CodeingPlanService initialized with API Key: {self.api_key is not None}, AK/SK: {(self.access_key and self.secret_key) is not None}")

    def _generate_signature(self, params: Dict[str, Any]) -> str:
        sorted_params = sorted(params.items())
        sign_string = "&".join([f"{k}={v}" for k, v in sorted_params])
        sign_string += f"&secret={self.secret_key}"
        import hashlib
        return hashlib.md5(sign_string.encode()).hexdigest()

    async def generate_plan(self, requirement: str) -> Optional[str]:
        plan_logger.info(f"Generating code plan for requirement: {requirement[:100]}")

        if not self.api_key and (not self.access_key or not self.secret_key):
            plan_logger.warning("No Volcengine credentials configured")
            return "请配置火山引擎API Key或Access Key/Secret Key"

        try:
            if self.api_key:
                plan_logger.debug("Using API Key authentication")
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }

                system_prompt = """你是一个专业的代码规划助手。请根据用户的需求，生成详细的代码实现方案。
要求：
1. 分析需求并给出实现思路
2. 提供具体的代码结构和关键代码片段
3. 使用Markdown格式输出
4. 代码要完整、可运行
5. 添加必要的注释说明"""

                data = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"请帮我规划以下功能的代码实现：\n\n{requirement}"}
                    ],
                    "max_tokens": 4096,
                    "temperature": 0.3
                }
            else:
                plan_logger.debug("Using AK/SK authentication")
                headers = {"Content-Type": "application/json"}
                data = {
                    "access_key": self.access_key,
                    "timestamp": str(int(time.time())),
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "你是一个专业的代码规划助手。请根据用户的需求，生成详细的代码实现方案。"},
                        {"role": "user", "content": f"请帮我规划以下功能的代码实现：\n\n{requirement}"}
                    ],
                    "max_tokens": 4096,
                    "temperature": 0.3
                }

            plan_logger.debug(f"Sending request to {self.base_url}/chat/completions")
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )

            plan_logger.debug(f"Response status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                if result.get("choices") and len(result["choices"]) > 0:
                    plan_content = result["choices"][0]["message"]["content"]
                    plan_logger.info("Code plan generated successfully")
                    return plan_content
                else:
                    error_msg = result.get("error", {}).get("message", "生成失败")
                    plan_logger.error(f"Code plan generation failed: {error_msg}")
                    return f"生成失败: {error_msg}"
            else:
                error_msg = f"请求失败: {response.status_code}"
                if response.text:
                    try:
                        error_detail = response.json().get("error", {}).get("message", "")
                        if error_detail:
                            error_msg += f" ({error_detail})"
                    except:
                        error_msg += f" - {response.text[:100]}"
                plan_logger.error(f"HTTP request failed: {error_msg}")
                return error_msg
        except requests.exceptions.RequestException as e:
            error_msg = f"网络错误: {str(e)}"
            plan_logger.error(f"Network error during plan generation: {str(e)}", exc_info=True)
            return error_msg
        except json.JSONDecodeError as e:
            plan_logger.error("Failed to parse JSON response", exc_info=True)
            return "解析响应失败"

    async def execute_plan(self, plan_id: str) -> Optional[str]:
        plan_logger.info(f"Executing plan with ID: {plan_id}")

        if not self.api_key and (not self.access_key or not self.secret_key):
            plan_logger.warning("No Volcengine credentials configured")
            return "请配置火山引擎API Key或Access Key/Secret Key"

        try:
            if self.api_key:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                data = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "你是一个代码执行助手。请根据提供的计划ID执行相应的代码任务。"},
                        {"role": "user", "content": f"请执行计划: {plan_id}"}
                    ],
                    "max_tokens": 4096,
                    "temperature": 0.3
                }
            else:
                headers = {"Content-Type": "application/json"}
                data = {
                    "access_key": self.access_key,
                    "timestamp": str(int(time.time())),
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "你是一个代码执行助手。请根据提供的计划ID执行相应的代码任务。"},
                        {"role": "user", "content": f"请执行计划: {plan_id}"}
                    ],
                    "max_tokens": 4096,
                    "temperature": 0.3
                }

            plan_logger.debug(f"Sending request to {self.base_url}/chat/completions")
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )

            plan_logger.debug(f"Response status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                if result.get("choices") and len(result["choices"]) > 0:
                    execute_result = result["choices"][0]["message"]["content"]
                    plan_logger.info(f"Plan {plan_id} executed successfully")
                    return execute_result
                else:
                    error_msg = result.get("error", {}).get("message", "执行失败")
                    plan_logger.error(f"Plan execution failed: {error_msg}")
                    return f"执行失败: {error_msg}"
            else:
                error_msg = f"请求失败: {response.status_code}"
                plan_logger.error(f"HTTP request failed: {response.status_code}")
                return error_msg
        except requests.exceptions.RequestException as e:
            plan_logger.error(f"Network error during plan execution: {str(e)}", exc_info=True)
            return f"网络错误: {str(e)}"
