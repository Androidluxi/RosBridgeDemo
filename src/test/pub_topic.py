#!/usr/bin/env python3
"""ROS 2 rosbridge 发布话题示例"""
import asyncio
import websockets
import json
from typing import Dict, Optional

# ROSbridge 配置
ROSBRIDGE_WS_URI = "ws://localhost:9090"  # 对应启动的端口
TOPIC_NAME = "/test_pub_topic"
MSG_TYPE = "std_msgs/String"

def build_advertise_msg() -> Dict:
    """构造 rosbridge 广告指令（遵循 rosbridge v2 协议）"""
    return {
        "op": "advertise",        # 操作类型：广告
        "topic": TOPIC_NAME,      # 话题名称
        "type": MSG_TYPE          # 消息类型
    }

def build_publish_msg(data: str) -> Dict:
    """构造 rosbridge 发布指令（遵循 rosbridge v2 协议）"""
    return {
        "op": "publish",          # 操作类型：发布
        "topic": TOPIC_NAME,      # 话题名称
        "type": MSG_TYPE,         # 消息类型（必须匹配 ROS 2 消息定义）
        "msg": {                  # 消息内容（与 std_msgs/String 结构一致）
            "data": data
        }
    }

async def publish_topic():
    """发布话题主逻辑"""
    try:
        # 连接 rosbridge WebSocket 服务
        async with websockets.connect(ROSBRIDGE_WS_URI) as websocket:
            print(f"成功连接到 rosbridge: {ROSBRIDGE_WS_URI}")
            
            # 1. 广告话题
            advertise_msg = build_advertise_msg()
            await websocket.send(json.dumps(advertise_msg))
            print(f"已广告话题: {TOPIC_NAME}")
            
            # 等待广告完成
            await asyncio.sleep(1)
            
            # 2. 发布多条测试消息
            for i in range(100):
                test_msg = build_publish_msg(f"Hello from rosbridge (ROS 2)! - Message #{i+1}")
                await websocket.send(json.dumps(test_msg))
                print(f"已发布消息到 {TOPIC_NAME}: {test_msg['msg']['data']}")
                await asyncio.sleep(1)  # 每条消息间隔0.5秒
            
            # 保持连接一段时间，确保所有消息被处理
            await asyncio.sleep(2)
            
            print("发布完成！")
            
    except Exception as e:
        print(f"发布失败: {e}")

if __name__ == "__main__":
    # 测试步骤：
    # 1. 启动 rosbridge: ros2 launch rosbridge_server rosbridge_websocket_launch.xml
    # 2. 新开终端监听话题: ros2 topic echo /test_pub_topic
    # 3. 运行本脚本
    asyncio.run(publish_topic())
