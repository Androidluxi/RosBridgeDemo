#!/usr/bin/env python3
"""ROS 2 rosbridge 订阅（调用）自定义服务示例

通过 rosbridge 调用自定义服务 demo_topic_interface/srv/CustomServer：
Request:
    float32 target_x
    float32 target_y
--- 
Response:
    float32 result      # target_x + target_y
"""

import asyncio
import json
from typing import Dict, Any

import websockets

# rosbridge 配置
ROSBRIDGE_WS_URI = "ws://localhost:9090"

# 注意：这里的 SERVICE_NAME 必须和你在 ROS2 里实际启动的服务名保持一致
# 比如你在 C++/Python 里写的服务服务器节点提供的是 "/custom_server"
SERVICE_NAME = "/custom_server"

# 自定义服务类型，格式为：包名/srv/服务名
SERVICE_TYPE = "demo_topic_interface/srv/CustomServer"

# 本次调用的 id，用于和 service_response 对应
CALL_ID = "call_custom_server_1"


def build_call_service_msg(target_x: float, target_y: float) -> Dict[str, Any]:
    """构造 rosbridge 调用自定义服务指令"""
    return {
        "op": "call_service",
        "service": SERVICE_NAME,
        "type": SERVICE_TYPE,
        "args": {
            "target_x": target_x,
            "target_y": target_y,
        },
        "id": CALL_ID,
    }


async def call_custom_service():
    """调用自定义服务主逻辑"""
    try:
        async with websockets.connect(ROSBRIDGE_WS_URI) as websocket:
            print(f"成功连接到 rosbridge: {ROSBRIDGE_WS_URI}")

            # 1. 构造并发送服务调用请求
            req = build_call_service_msg(1.23, 4.56)
            await websocket.send(json.dumps(req))
            print(
                f"已发送服务调用: {SERVICE_NAME}, type={SERVICE_TYPE}, args={req['args']}"
            )

            # 2. 循环等待 rosbridge 返回 service_response
            while True:
                raw = await websocket.recv()
                msg = json.loads(raw)

                # 只关心 service_response 且 id 匹配的消息
                if msg.get("op") == "service_response" and msg.get("id") == CALL_ID:
                    if msg.get("result", False):
                        values = msg.get("values", {})
                        print(f"服务调用成功, 响应: {values}")
                    else:
                        print(f"服务调用失败, 响应: {msg}")
                    break

    except Exception as e:
        print(f"调用自定义服务出错: {e}")


if __name__ == "__main__":
    # 测试步骤：
    # 1. 启动 rosbridge:
    #    ros2 launch rosbridge_server rosbridge_websocket_launch.xml delay_between_messages:=0.0
    # 2. 在 ROS2 里启动自定义服务服务器节点，且服务名为 /custom_server，
    #    服务类型为 demo_topic_interface/srv/CustomServer
    # 3. 运行本脚本：
    #    cd src/test
    #    python3 sub_service.py
    asyncio.run(call_custom_service())

