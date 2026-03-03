#!/usr/bin/env python3
"""ROS 2 rosbridge 订阅话题示例（订阅 自定义话题）"""

import asyncio
import json
from typing import Dict, Any

import websockets

# rosbridge 配置
ROSBRIDGE_WS_URI = "ws://localhost:9090"  # 对应启动的端口
TOPIC_NAME = "/test_customized_pub_topic"
# 使用自定义消息类型，格式为：包名/msg/消息名
MSG_TYPE = "demo_topic_interface/msg/CustomMsg"


def build_subscribe_msg() -> Dict[str, Any]:
    """构造 rosbridge 订阅指令（遵循 rosbridge v2 协议）"""
    return {
        "op": "subscribe",
        "topic": TOPIC_NAME,
        "type": MSG_TYPE,  # 指定消息类型，便于调试和检查
        # "throttle_rate": 0,     # 可选：节流频率（ms）
        # "queue_length": 0,      # 可选：队列长度
        # "fragment_size": 0,     # 可选：分片大小
    }


async def sub_topic():
    """订阅话题主逻辑"""
    try:
        async with websockets.connect(ROSBRIDGE_WS_URI) as websocket:
            print(f"成功连接到 rosbridge: {ROSBRIDGE_WS_URI}")

            # 1. 发送订阅请求
            sub_msg = build_subscribe_msg()
            await websocket.send(json.dumps(sub_msg))
            print(f"已发送订阅请求: {TOPIC_NAME} ({MSG_TYPE})")

            # 2. 持续接收 自定义话题 消息
            while True:
                raw = await websocket.recv()
                msg = json.loads(raw)

                # rosbridge 订阅消息格式通常为：
                # {
                #     "op": "publish",
                #     "topic": "/test_customized_pub_topic",
                #     "type": "demo_topic_interface/msg/CustomMsg",
                #     "msg": {
                #         "name": "Message #1",
                #         "id": 1,
                #         "value": 3.14
                #     }
                # }
                if msg.get("op") == "publish" and msg.get("topic") == TOPIC_NAME:
                    customized_msg = msg.get("msg", {})
                    print(f"收到 /test_customized_pub_topic 消息: {customized_msg}")

    except Exception as e:
        print(f"订阅失败: {e}")


if __name__ == "__main__":
    # 测试步骤：
    # 1. 启动 rosbridge:
    #    ros2 launch rosbridge_server rosbridge_websocket_launch.xml
    # 2. 确保有 /clock 话题（例如启动带 /clock 的仿真或节点）
    # 3. 运行本脚本:
    #    python3 sub_topic.py
    asyncio.run(sub_topic())

