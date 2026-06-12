# 代码修改助手（/code）

## 一、概述

代码修改助手允许用户通过自然语言描述需求，系统自动分析项目代码结构并生成代码修改方案。

## 二、核心原理

```
用户需求 → 扫描项目文件 → 读取关键文件 → 调用火山API → 生成修改方案 → 返回结果
```

## 三、处理流程

### 3.1 流程详解

```
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  用户输入需求    │───→│   扫描项目文件   │───→│   读取文件内容   │
└──────────────────┘    └──────────────────┘    └────────┬─────────┘
                                                          │
                                                          ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   生成代码方案   │←───│   调用火山API    │←───│   构建提示词     │
└────────┬─────────┘    └──────────────────┘    └──────────────────┘
         │
         ▼
┌──────────────────┐    ┌──────────────────┐
│   返回修改建议   │───→│   一键应用修改   │
└──────────────────┘    └──────────────────┘
```

### 3.2 关键代码

```python
# app/services/code_editor_service.py
async def analyze_and_modify(self, requirement: str) -> str:
    # 1. 获取项目文件列表（排除虚拟环境、测试文件等）
    project_files = self._list_project_files()
    
    # 2. 读取关键文件内容（最多10个文件，每个文件最多1000字符）
    file_contents = {}
    for file_path in project_files[:10]:
        content = self._get_file_content(file_path)
        if content:
            file_contents[file_path] = content[:1000]
    
    # 3. 构建提示词
    files_info = "\n\n".join([
        f"=== {path} ===\n{content}"
        for path, content in file_contents.items()
    ])
    
    # 4. 调用火山引擎代码规划 API
    data = {
        "model": "ark-code-latest",
        "messages": [
            {
                "role": "system", 
                "content": "你是一个专业的代码修改助手，请根据用户需求分析现有代码并生成修改方案。"
            },
            {
                "role": "user", 
                "content": f"项目文件：\n{files_info}\n\n需求：{requirement}"
            }
        ],
        "max_tokens": 4096,
        "temperature": 0.3  # 较低温度，更确定性的输出
    }
    
    # 5. 发送请求
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=data
        )
    
    # 6. 解析并返回结果
    result = response.json()
    return result["choices"][0]["message"]["content"]
```

## 四、项目文件扫描

### 4.1 扫描策略

```python
def _list_project_files(self):
    """列出项目中的 Python 文件，排除不需要的目录"""
    exclude_dirs = {
        "venv", ".venv", "__pycache__", ".git",
        "tests", "test", "dist", "build"
    }
    
    files = []
    for path in self.project_path.rglob("*.py"):
        # 检查是否在排除目录中
        if any(exclude in str(path.parent) for exclude in exclude_dirs):
            continue
        
        # 检查文件大小（排除过大的文件）
        if path.stat().st_size > 500 * 1024:  # 500KB
            continue
        
        files.append(path)
    
    return sorted(files)
```

### 4.2 文件过滤规则

| 规则 | 说明 |
|------|------|
| **排除目录** | venv, .git, __pycache__, tests 等 |
| **文件类型** | 仅 Python 文件 (.py) |
| **文件大小** | 最大 500KB |
| **数量限制** | 最多 10 个文件 |

## 五、安全机制

### 5.1 路径安全检查

```python
async def apply_modification(self, file_path: str, new_content: str) -> str:
    # 1. 安全检查：确保路径在项目目录内
    path = Path(file_path)
    if not path.is_absolute():
        path = self.project_path / path
    
    # 2. 防止路径遍历攻击
    try:
        path.relative_to(self.project_path)
    except ValueError:
        return "❌ 错误：只能修改项目目录内的文件"
    
    # 3. 自动备份原文件
    if path.exists():
        backup_path = path.with_suffix(path.suffix + ".backup")
        backup_path.write_text(path.read_text(encoding='utf-8'), encoding='utf-8')
    
    # 4. 写入新内容
    path.write_text(new_content, encoding='utf-8')
    return f"✅ 文件修改成功"
```

### 5.2 安全特性

| 特性 | 说明 |
|------|------|
| **路径限制** | 仅允许修改项目目录内的文件 |
| **自动备份** | 修改前自动创建 .backup 文件 |
| **权限检查** | 检查文件写入权限 |
| **大小限制** | 防止写入过大文件 |

## 六、火山引擎 API 调用

### 6.1 API 配置

```python
class CodeingPlanService:
    def __init__(self):
        self.api_key = settings.VOLC_API_KEY
        self.base_url = "https://ark.cn-beijing.volces.com/api/text/v1"
```

### 6.2 请求参数

| 参数 | 值 | 说明 |
|------|-----|------|
| model | ark-code-latest | 使用最新代码模型 |
| max_tokens | 4096 | 最大输出 token 数 |
| temperature | 0.3 | 较低温度，更确定的输出 |
| top_p | 0.9 | nucleus sampling |

## 七、使用示例

### 7.1 基本用法

```
/code 添加用户登录功能
/code 修改数据库连接配置
/code 为RAG服务添加缓存机制
```

### 7.2 高级用法

```
/code 优化代码性能
/code 添加错误处理
/code 重构代码结构
```

## 八、输出格式

### 8.1 代码块格式

系统返回的修改方案包含多个代码块：

```
📋 代码修改方案
========================================

代码块 1:
app/services/rag_service.py
[代码内容]

代码块 2:
app/core/agent.py
[代码内容]

安全提示：
1. 请仔细审查生成的代码
2. 建议先备份原文件
3. 确认无误后再手动应用修改

如需自动应用修改，请使用 /apply 命令
```

## 九、配置说明

### 9.1 环境变量

```env
# 火山引擎配置
VOLC_API_KEY=your_api_key_here
```

### 9.2 获取 API Key

1. 登录火山引擎控制台
2. 进入 ARK 平台
3. 创建 API Key
4. 复制到 .env 文件

## 十、代码位置

| 文件 | 说明 |
|------|------|
| `app/services/code_editor_service.py` | 代码编辑服务实现 |
| `app/services/codeing_plan_service.py` | 代码规划服务（火山 API 调用） |
| `app/core/agent.py` | /code 命令处理 |
