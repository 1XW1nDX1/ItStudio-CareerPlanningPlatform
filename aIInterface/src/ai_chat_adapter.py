import asyncio
import json
import requests
import websockets
from typing import Optional, Callable


class AIChatAdapter:
    """适配器：连接后端AI聊天API和WebSocket"""

    def __init__(self, base_url: str = "http://localhost:8080", ws_url: str = "ws://localhost:8080"):
        self.base_url = base_url
        self.ws_url = ws_url
        self.token: Optional[str] = None
        self.uuid: Optional[str] = None

    def set_token(self, token: str):
        """设置认证token"""
        self.token = token

    def get_new_chat_uuid(self) -> Optional[str]:
        """获取新的聊天UUID"""
        response = requests.get(f"{self.base_url}/api/v1/ai-chat/new-chat")

        if response.status_code == 200:
            self.uuid = response.json()
            return self.uuid
        return None

    async def connect_websocket(self, on_message: Callable[[str], None], has_file: bool = False, user_id: Optional[str] = None):
        """连接WebSocket并接收AI回复"""
        if not self.uuid:
            raise ValueError("UUID未设置，请先调用get_new_chat_uuid()")

        ws_endpoint = f"{self.ws_url}/ws/v1/ai-chat?uuid={self.uuid}&has_file={str(has_file).lower()}"
        if user_id:
            ws_endpoint += f"&user_id={user_id}"

        async with websockets.connect(ws_endpoint) as websocket:
            print(f"WebSocket已连接: {ws_endpoint}")

            async for message in websocket:
                on_message(message)

    async def send_message(self, websocket, message: str):
        """通过WebSocket发送消息"""
        await websocket.send(message)

    async def chat_session(self, on_message: Callable[[str], None], has_file: bool = False, user_id: Optional[str] = None):
        """创建聊天会话"""
        if not self.uuid:
            raise ValueError("UUID未设置，请先调用get_new_chat_uuid()")

        ws_endpoint = f"{self.ws_url}/ws/v1/ai-chat?uuid={self.uuid}&has_file={str(has_file).lower()}"
        if user_id:
            ws_endpoint += f"&user_id={user_id}"

        async with websockets.connect(ws_endpoint) as websocket:
            print(f"聊天会话已建立: {ws_endpoint}")

            async def receive_messages():
                async for message in websocket:
                    on_message(message)

            receive_task = asyncio.create_task(receive_messages())

            try:
                while True:
                    user_input = await asyncio.get_event_loop().run_in_executor(
                        None, input, "你: "
                    )

                    if user_input.lower() in ['exit', 'quit', '退出']:
                        break

                    await websocket.send(user_input)

            finally:
                receive_task.cancel()


def example_usage():
    """使用示例"""
    adapter = AIChatAdapter(base_url="http://localhost:8002", ws_url="ws://localhost:8002")

    # 获取新的聊天UUID
    uuid = adapter.get_new_chat_uuid()
    print(f"获取到UUID: {uuid}")

    # 定义消息处理函数
    def handle_message(message: str):
        print(f"AI: {message}", end="", flush=True)

    # 启动聊天会话（has_file=False表示使用Agent02，user_id可选）
    asyncio.run(adapter.chat_session(handle_message, has_file=False, user_id="test_user"))


if __name__ == "__main__":
    example_usage()
