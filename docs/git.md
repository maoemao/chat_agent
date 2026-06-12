# Git 操作服务（/git）

## 一、概述

Git 操作服务允许用户通过 Telegram 命令执行 Git 操作，支持代码提交、推送等功能。

## 二、核心原理

```
Telegram命令 → 解析命令 → subprocess执行Git命令 → 返回结果
```

## 三、支持的命令

| 命令 | 功能 | 实现方式 |
|------|------|----------|
| `/git status` | 查看工作区状态 | `git status` |
| `/git diff` | 查看未暂存的更改 | `git diff` |
| `/git log [数量]` | 查看提交记录 | `git log --oneline` |
| `/git branch` | 查看分支信息 | `git branch --show-current` |
| `/git add` | 暂存所有更改 | `git add -A` |
| `/git commit [信息]` | 提交更改 | `git commit -m` |
| `/git push` | 推送到远程 | `git push origin main` |
| `/git commitpush [信息]` | 一键提交并推送 | 组合操作 |

## 四、核心实现

### 4.1 Git 命令执行器

```python
# app/services/git_service.py
def _run_git_command(self, *args) -> Dict[str, Any]:
    """执行 Git 命令并返回结果"""
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
        return {
            "success": False,
            "stdout": "",
            "stderr": "Git command timeout",
            "returncode": -1
        }
```

### 4.2 命令处理流程

```python
# app/core/agent.py
async def _handle_git(self, command: Command, message: Message) -> str:
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
/git commitpush [message] - 提交并推送"""

    subcommand = command.args[0].lower()
    subargs = command.args[1:]

    if subcommand == "status":
        return self.git_service.get_status()
    
    elif subcommand == "commitpush":
        # 一键提交并推送
        if not subargs:
            return "❌ 请提供提交信息"
        
        commit_message = " ".join(subargs)
        
        # 先提交
        commit_result = self.git_service.commit(commit_message)
        if not commit_result.startswith("✅"):
            return commit_result
        
        # 再推送
        push_result = self.git_service.push()
        return f"{commit_result}\n\n{push_result}"
```

## 五、状态检测

### 5.1 状态解析

```python
def get_status(self) -> str:
    """获取 Git 状态"""
    result = self._run_git_command("status")

    if not result["success"]:
        return f"❌ 获取状态失败：{result['stderr']}"

    output = result["stdout"]

    # 检查是否有未提交的更改
    if "nothing to commit" in output.lower():
        return "✅ 工作区干净，没有未提交的更改"
    elif "changes not staged" in output.lower():
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
```

## 六、GitHub 认证处理

### 6.1 协议自动切换

```python
def push(self) -> str:
    """推送到远程仓库"""
    # 检查远程 URL 是否为 SSH 协议
    remote_result = self._run_git_command("remote", "-v")
    for line in remote_result["stdout"].split('\n'):
        if 'origin' in line and '(push)' in line:
            remote_url = line.split()[1]
            
            # 如果是 SSH 协议，自动切换为 HTTPS
            if remote_url.startswith('git@github.com:'):
                repo_path = remote_url.replace('git@github.com:', '')
                https_url = f"https://github.com/{repo_path}"
                self._run_git_command("remote", "set-url", "origin", https_url)
    
    # 执行推送
    result = self._run_git_command("push", "origin", "main")
    
    # 处理认证失败
    if "Authentication failed" in result["stderr"]:
        return """❌ GitHub 认证失败

💡 请在 .env 文件中配置你的 GitHub Token：
```
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
```

获取 Token 方法：
1. 访问 https://github.com/settings/tokens
2. 生成新的 Personal Access Token
3. 勾选 repo 权限
4. 将 Token 复制到 .env 文件"""
    
    return result["stdout"]
```

### 6.2 认证方式对比

| 方式 | 优点 | 缺点 |
|------|------|------|
| **SSH** | 无需每次输入密码 | 需要配置 SSH Key |
| **HTTPS + Token** | 配置简单 | 需要 Token |

## 七、使用示例

### 7.1 基本流程

```
# 查看状态
/git status

# 提交更改
/git commit 修复了登录bug

# 推送到远程
/git push
```

### 7.2 一键操作

```
# 一键提交并推送（最常用）
/git commitpush 添加了新功能

# 查看提交历史
/git log 5
```

## 八、配置说明

### 8.1 环境变量

```env
# GitHub 配置
GITHUB_TOKEN=your_github_token_here
```

### 8.2 获取 GitHub Token

1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token"
3. 输入描述信息
4. 勾选 `repo` 权限
5. 点击 "Generate token"
6. 复制 Token 到 .env 文件

## 九、代码位置

| 文件 | 说明 |
|------|------|
| `app/services/git_service.py` | Git 服务实现 |
| `app/core/agent.py` | /git 命令处理 |
| `.env` | GitHub Token 配置 |
