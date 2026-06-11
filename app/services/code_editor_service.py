import os
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from app.config.settings import settings
from app.utils.logger import plan_logger

class CodeEditorService:
    def __init__(self):
        plan_logger.info("Initializing CodeEditorService")
        self.api_key = settings.VOLC_API_KEY
        self.base_url = "https://ark.cn-beijing.volces.com/api/coding/v3"
        self.model = "ark-code-latest"
        self.project_path = Path("/Users/maogee/Documents/trae_projects/maoge_agent")
        plan_logger.info(f"CodeEditorService initialized, project path: {self.project_path}")

    def _get_file_content(self, file_path: str) -> Optional[str]:
        """读取文件内容"""
        try:
            path = Path(file_path)
            if not path.is_absolute():
                path = self.project_path / path
            
            if not path.exists():
                return None
            
            return path.read_text(encoding='utf-8')
        except Exception as e:
            plan_logger.error(f"Failed to read file {file_path}: {str(e)}")
            return None

    def _write_file_content(self, file_path: str, content: str) -> bool:
        """写入文件内容"""
        try:
            path = Path(file_path)
            if not path.is_absolute():
                path = self.project_path / path
            
            # 确保目录存在
            path.parent.mkdir(parents=True, exist_ok=True)
            
            path.write_text(content, encoding='utf-8')
            plan_logger.info(f"File written successfully: {path}")
            return True
        except Exception as e:
            plan_logger.error(f"Failed to write file {file_path}: {str(e)}")
            return False

    def _list_project_files(self) -> List[str]:
        """列出项目中的Python文件"""
        try:
            files = []
            for py_file in self.project_path.rglob("*.py"):
                # 排除虚拟环境
                if "venv" not in str(py_file) and "__pycache__" not in str(py_file):
                    files.append(str(py_file.relative_to(self.project_path)))
            return files
        except Exception as e:
            plan_logger.error(f"Failed to list project files: {str(e)}")
            return []

    async def analyze_and_modify(self, requirement: str) -> str:
        """分析需求并修改代码"""
        plan_logger.info(f"Analyzing code modification requirement: {requirement[:100]}")

        if not self.api_key:
            return "请配置火山引擎API Key"

        try:
            # 1. 获取项目文件列表
            project_files = self._list_project_files()
            if not project_files:
                return "未找到项目中的Python文件"

            # 2. 读取关键文件内容（简化版，读取主要文件）
            file_contents = {}
            for file_path in project_files[:10]:  # 限制文件数量
                content = self._get_file_content(file_path)
                if content:
                    file_contents[file_path] = content

            # 3. 构建prompt
            files_info = "\n\n".join([
                f"=== {path} ===\n{content[:1000]}"  # 限制每个文件内容长度
                for path, content in file_contents.items()
            ])

            system_prompt = """你是一个专业的代码修改助手。请根据用户的需求，分析项目代码并给出修改方案。
要求：
1. 分析现有代码结构
2. 给出具体的修改建议
3. 提供完整的修改后代码
4. 说明修改了哪些文件
5. 使用中文回答"""

            user_prompt = f"""项目文件列表：
{chr(10).join(project_files)}

部分文件内容：
{files_info}

用户需求：{requirement}

请分析并给出修改方案。如果需要修改文件，请明确说明：
1. 修改哪个文件
2. 修改内容是什么
3. 完整的修改后代码"""

            # 4. 调用API生成修改方案
            import httpx
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 4096,
                "temperature": 0.3
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data
                )

            if response.status_code == 200:
                result = response.json()
                if result.get("choices") and len(result["choices"]) > 0:
                    modification_plan = result["choices"][0]["message"]["content"]
                    
                    # 5. 解析修改方案并执行（简化版：只提取代码块）
                    return self._parse_and_execute_modification(modification_plan)
                else:
                    return "生成修改方案失败"
            else:
                return f"请求失败: {response.status_code}"

        except Exception as e:
            plan_logger.error(f"Code modification failed: {str(e)}", exc_info=True)
            return f"代码修改失败: {str(e)}"

    def _parse_and_execute_modification(self, plan: str) -> str:
        """解析修改方案并执行"""
        try:
            # 提取文件路径和代码块
            # 格式：=== 文件路径 === 或 ```python 代码 ```
            
            result_parts = []
            result_parts.append("📋 代码修改方案")
            result_parts.append("=" * 40)
            result_parts.append("")
            
            # 检查是否包含代码块
            code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', plan, re.DOTALL)
            
            if code_blocks:
                result_parts.append("📝 生成的代码块：")
                for i, block in enumerate(code_blocks, 1):
                    result_parts.append(f"\n代码块 {i}:")
                    result_parts.append(block[:500] + "..." if len(block) > 500 else block)
            
            result_parts.append("")
            result_parts.append("⚠️ 安全提示：")
            result_parts.append("1. 请仔细审查生成的代码")
            result_parts.append("2. 建议先备份原文件")
            result_parts.append("3. 确认无误后再手动应用修改")
            result_parts.append("")
            result_parts.append("💡 如需自动应用修改，请使用 /apply 命令")
            
            return "\n".join(result_parts)
            
        except Exception as e:
            plan_logger.error(f"Failed to parse modification plan: {str(e)}")
            return f"解析修改方案失败: {str(e)}\n\n原始方案:\n{plan[:1000]}"

    async def apply_modification(self, file_path: str, new_content: str) -> str:
        """应用代码修改"""
        try:
            # 安全检查
            path = Path(file_path)
            if not path.is_absolute():
                path = self.project_path / path
            
            # 确保在项目目录内
            try:
                path.relative_to(self.project_path)
            except ValueError:
                return "❌ 错误：只能修改项目目录内的文件"
            
            # 备份原文件
            if path.exists():
                backup_path = path.with_suffix(path.suffix + ".backup")
                backup_path.write_text(path.read_text(encoding='utf-8'), encoding='utf-8')
                plan_logger.info(f"Backup created: {backup_path}")
            
            # 写入新内容
            if self._write_file_content(str(path), new_content):
                return f"✅ 文件修改成功: {path}\n💾 备份文件: {path}.backup"
            else:
                return f"❌ 文件修改失败: {path}"
                
        except Exception as e:
            plan_logger.error(f"Failed to apply modification: {str(e)}")
            return f"应用修改失败: {str(e)}"
