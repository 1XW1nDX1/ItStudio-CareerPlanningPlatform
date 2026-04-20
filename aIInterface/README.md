# AI Interface Service

这是一个FastAPI服务，用于适配后端的AI聊天功能，支持调用外部AI API或本地大模型。

## 功能特性

- 完全适配后端的WebSocket接口 (`/ws/v1/ai-chat`)
- 支持两种对话模式：
  - `has_file=true`: 简历分析助手（使用Agent01.md）
  - `has_file=false`: 职业咨询助手（使用Agent02.md）
- 支持流式输出，实时返回AI回复
- 自动维护用户画像，持续学习用户信息
- 支持本地大模型（Ollama）和外部API（如SiliconFlow、OpenAI等）

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置环境变量

创建 `.env` 文件或设置环境变量：

```bash
# 模型类型：external（外部API）或 local（本地模型）
MODEL_TYPE=external

# 外部API配置（使用external时）
EXTERNAL_API_KEY=your-api-key-here
EXTERNAL_BASE_URL=https://api.siliconflow.cn/v1
EXTERNAL_MODEL=deepseek-ai/DeepSeek-V3

# 本地模型配置（使用local时）
LOCAL_BASE_URL=http://localhost:11434/v1
LOCAL_MODEL=qwen2

# 服务端口
PORT=8002
```

## 启动服务

```bash
cd aIInterface/src
python fastapi_server.py
```

服务将在 `http://localhost:8002` 启动

## API端点

### HTTP端点

- `GET /health` - 健康检查
- `GET /api/v1/ai-chat/new-chat` - 创建新会话，返回UUID
- `GET /api/profile/{user_id}` - 获取用户画像
- `POST /api/profile/{user_id}` - 更新用户画像
- `GET /api/sessions` - 列出活跃会话

### WebSocket端点

`ws://localhost:8001/ws/v1/ai-chat?uuid={uuid}&has_file={true/false}&user_id={user_id}`

参数说明：
- `uuid`: 会话唯一标识（必需）
- `has_file`: 是否上传简历（true=Agent01，false=Agent02）
- `user_id`: 用户ID（可选，用于画像管理）

## 与后端集成

此服务完全兼容后端的接口格式，集成步骤：

1. **后端生成UUID**：后端的 `GET /api/v1/ai-chat/new-chat` 返回UUID
2. **前端连接WebSocket**：使用UUID连接到此服务
3. **参数传递**：
   - 用户上传简历：`has_file=true`
   - 直接聊天：`has_file=false`
   - 传递用户ID：`user_id=xxx`（用于画像管理）

### 示例：Python客户端

```python
import asyncio
import websockets

async def chat_with_ai():
    # 连接WebSocket（简历分析模式）
    uri = "ws://localhost:8001/ws/v1/ai-chat?uuid=test123&has_file=true&user_id=user001"
    
    async with websockets.connect(uri) as websocket:
        # 接收欢迎消息
        welcome = await websocket.recv()
        print(f"AI: {welcome}")
        
        # 发送消息
        await websocket.send("我是一名Python开发者，有3年工作经验")
        
        # 接收流式回复
        while True:
            try:
                chunk = await websocket.recv()
                print(chunk, end='', flush=True)
            except:
                break

asyncio.run(chat_with_ai())
```

## 用户画像功能

服务会自动分析对话内容，提取并保存用户信息到 `profiles/{user_id}_profile.json`：

```json
{
  "education": "本科",
  "major": "计算机科学",
  "skills": ["Python", "Java", "React"],
  "career_goals": "成为全栈工程师",
  "last_updated": "2026-04-20T10:30:00"
}
```

## 支持的AI模型

### 本地模型（Ollama）

```bash
# 安装Ollama
# 下载模型
ollama pull qwen2

# 设置环境变量
export MODEL_TYPE=local
export LOCAL_MODEL=qwen2
```

### 外部API

支持任何OpenAI兼容的API：
- SiliconFlow
- OpenAI
- DeepSeek
- 其他兼容服务

## 目录结构

```
aIInterface/
├── src/
│   ├── fastapi_server.py    # 主服务
│   └── ai_chat_adapter.py   # 客户端适配器
├── prompt/
│   ├── Agent01.md           # 简历分析prompt
│   └── Agent02.md           # 职业咨询prompt
├── profiles/                # 用户画像存储
├── requirements.txt
└── README.md
```
