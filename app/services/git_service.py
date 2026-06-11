import subprocess
import re
from typing import Optional, Dict, Any, List
from pathlib import Path
from app.config.settings import settings
from app.utils.logger import git_logger

class GitService:
    """Git 操作服务类"""

    def __init__(self, repo_path: str = None):
        git_logger.info("Initializing GitService")
        self.repo_path = Path(repo_path) if repo_path else Path("/Users/maogee/Documents/trae_projects/maoge_agent")
        self.github_token = settings.GITHUB_TOKEN
        git_logger.info(f"GitService initialized, repo path: {self.repo_path}")

        # 检查是否配置了 GitHub Token
        if not self.github_token:
            git_logger.warning("GitHub token not configured")

    def _run_git_command(self, *args) -> Dict[str, Any]:
        """执行 Git 命令"""
        try:
            result = subprocess.run(
                ["git"] + list(args),
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            git_logger.error("Git command timeout")
            return {
                "success": False,
                "stdout": "",
                "stderr": "Git command timeout",
                "returncode": -1
            }
        except Exception as e:
            git_logger.error(f"Git command failed: {str(e)}")
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }

    def get_status(self) -> str:
        """获取 Git 状态"""
        git_logger.info("Getting git status")
        result = self._run_git_command("status")

        if not result["success"]:
            return f"❌ 获取状态失败：{result['stderr']}"

        output = result["stdout"]

        # 检查是否有未提交的更改
        if "nothing to commit" in output.lower():
            return "✅ 工作区干净，没有未提交的更改"
        elif "changes not staged" in output.lower() or "Changes not staged" in output:
            # 提取修改的文件列表
            modified_files = self._extract_modified_files(output)
            if modified_files:
                return f"📝 有 {len(modified_files)} 个文件被修改：\n\n" + "\n".join([f"- {f}" for f in modified_files[:10]])
            return "📝 有未提交的更改"
        elif "Untracked files" in output:
            # 提取未跟踪的文件
            untracked = self._extract_untracked_files(output)
            if untracked:
                return f"🆕 有 {len(untracked)} 个未跟踪的文件：\n\n" + "\n".join([f"- {f}" for f in untracked[:10]])
            return "🆕 有未跟踪的文件"
        else:
            return f"✅ Git 状态：\n\n{output[:500]}"

    def _extract_modified_files(self, status_output: str) -> List[str]:
        """从状态输出中提取修改的文件"""
        files = []
        # 匹配 modified: 或 changed: 开头的行
        pattern = r'(?:modified|changed):\s+(.+)'
        for line in status_output.split('\n'):
            match = re.search(pattern, line)
            if match:
                files.append(match.group(1).strip())
        return files

    def _extract_untracked_files(self, status_output: str) -> List[str]:
        """从状态输出中提取未跟踪的文件"""
        files = []
        in_untracked_section = False
        for line in status_output.split('\n'):
            if "Untracked files" in line:
                in_untracked_section = True
                continue
            if in_untracked_section:
                if line.strip() and not line.startswith(" "):
                    break
                if line.strip():
                    files.append(line.strip())
        return files

    def get_diff(self) -> str:
        """获取未暂存的更改"""
        git_logger.info("Getting git diff")
        result = self._run_git_command("diff")

        if not result["success"]:
            return f"❌ 获取差异失败：{result['stderr']}"

        output = result["stdout"]
        if not output:
            return "✅ 没有未暂存的更改"

        # 限制输出长度
        if len(output) > 2000:
            return f"📄 差异统计：\n\n{self._summarize_diff(output)}"
        else:
            return f"📄 未暂存的更改：\n\n```diff\n{output[:2000]}\n```"

    def _summarize_diff(self, diff: str) -> str:
        """总结差异内容"""
        stats = []
        file_pattern = r'diff --git a/(.+) b/(.+)'

        for match in re.finditer(file_pattern, diff):
            stats.append(f"- {match.group(2)}")

        return f"共修改了 {len(stats)} 个文件：\n\n" + "\n".join(stats[:10])

    def stage_all(self) -> str:
        """暂存所有更改"""
        git_logger.info("Staging all changes")
        result = self._run_git_command("add", "-A")

        if not result["success"]:
            return f"❌ 暂存失败：{result['stderr']}"

        return "✅ 已暂存所有更改"

    def commit(self, message: str) -> str:
        """提交更改"""
        if not message:
            return "❌ 请提供提交信息"

        git_logger.info(f"Committing with message: {message[:50]}")

        # 处理多行提交信息
        if '\n' in message:
            result = self._run_git_command("commit", "-m", message)
        else:
            result = self._run_git_command("commit", "-m", message)

        if not result["success"]:
            error_msg = result["stderr"]
            if "nothing to commit" in error_msg.lower():
                return "✅ 没有需要提交的内容"
            return f"❌ 提交失败：{error_msg}"

        return f"✅ 提交成功！\n\n{result['stdout'][:500]}"

    def push(self) -> str:
        """推送到远程仓库"""
        git_logger.info("Pushing to remote")

        # 检查是否有 GitHub Token
        if not self.github_token:
            git_logger.warning("GitHub token not configured, checking remote URL")

            # 检查远程仓库 URL
            remote_result = self._run_git_command("remote", "-v")
            if remote_result["success"]:
                for line in remote_result["stdout"].split('\n'):
                    if 'origin' in line and '(push)' in line:
                        remote_url = line.split()[1] if len(line.split()) > 1 else ""

                        # 如果是 SSH 协议但没有配置 token，尝试转换为 HTTPS
                        if remote_url.startswith('git@github.com:'):
                            # 提取仓库路径
                            repo_path = remote_url.replace('git@github.com:', '')
                            # 转换为 HTTPS URL
                            https_url = f"https://github.com/{repo_path}"
                            git_logger.info(f"Converting remote URL to HTTPS: {https_url}")

                            # 更新远程 URL
                            update_result = self._run_git_command("remote", "set-url", "origin", https_url)
                            if not update_result["success"]:
                                return f"❌ 无法切换到 HTTPS 协议：{update_result['stderr']}\n\n💡 请手动配置 GitHub Token：\n在 .env 文件中添加：\nGITHUB_TOKEN=your_github_token_here"
                            else:
                                git_logger.info("Remote URL updated to HTTPS")
                                break
            else:
                return f"❌ 获取远程仓库信息失败：{remote_result['stderr']}"

        # 执行推送
        result = self._run_git_command("push", "origin", "main")

        if not result["success"]:
            error_msg = result["stderr"]

            # 常见错误处理
            if "Authentication failed" in error_msg or "could not read Username" in error_msg:
                return "❌ GitHub 认证失败\n\n💡 请在 .env 文件中配置你的 GitHub Token：\n```\nGITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx\n```\n\n获取 Token 方法：\n1. 访问 https://github.com/settings/tokens\n2. 生成新的 Personal Access Token\n3. 勾选 repo 权限\n4. 将 Token 复制到 .env 文件"
            elif "rejected" in error_msg.lower():
                return f"❌ 推送被拒绝，可能有冲突：\n\n{error_msg}\n\n💡 建议先拉取远程更新：\n```bash\ngit pull --rebase origin main\n```"
            elif "Connection closed" in error_msg:
                return "❌ 连接被关闭，可能是 SSH 连接问题\n\n💡 建议切换到 HTTPS 协议，或检查网络连接"
            else:
                return f"❌ 推送失败：{error_msg}"

        return f"✅ 推送成功！\n\n{result['stdout'][:500]}"

    def get_log(self, limit: int = 5) -> str:
        """获取最近的提交日志"""
        git_logger.info(f"Getting git log, limit: {limit}")
        result = self._run_git_command("log", f"--oneline", f"-{limit}")

        if not result["success"]:
            return f"❌ 获取日志失败：{result['stderr']}"

        output = result["stdout"]
        if not output:
            return "📜 暂无提交记录"

        return f"📜 最近 {limit} 条提交记录：\n\n{output}"

    def get_branch(self) -> str:
        """获取当前分支信息"""
        git_logger.info("Getting current branch")

        # 获取当前分支
        branch_result = self._run_git_command("branch", "--show-current")
        if not branch_result["success"]:
            return f"❌ 获取分支失败：{branch_result['stderr']}"

        current_branch = branch_result["stdout"] or "unknown"

        # 获取远程跟踪分支
        tracking_result = self._run_git_command("rev-parse", "--abbrev-ref", "@{upstream}")
        tracking_branch = tracking_result["stdout"] if tracking_result["success"] else None

        # 获取领先/落后于远程的提交数
        ahead_behind = ""
        if tracking_branch:
            ahead_result = self._run_git_command("rev-list", "--left-right", "--count",
                                                  f"{current_branch}...{tracking_branch}")
            if ahead_result["success"]:
                ahead, behind = ahead_result["stdout"].split()
                if int(ahead) > 0 or int(behind) > 0:
                    ahead_behind = f"\n本地领先远程 {ahead} 个提交，落后 {behind} 个提交"

        return f"🌿 当前分支：{current_branch}\n{tracking_branch and f'远程跟踪：{tracking_branch}' or '无远程跟踪分支'}{ahead_behind}"
