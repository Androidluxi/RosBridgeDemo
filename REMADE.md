# ROS 2 Humble rosbridge_server 完整使用文档

## 一、文档说明

适配版本：ROS 2 Humble Hawksbill（Ubuntu 22.04）
核心功能：通过 WebSocket/HTTP 协议让非 ROS 2 程序（Web/Python/Java）与 ROS 2 系统通信，支持话题发布 / 订阅、服务调用、参数操作等核心功能。

## 二、环境前置要求

已完成 ROS 2 Humble 基础安装（参考ROS 2 官方安装文档）；
Ubuntu 22.04 系统，网络通畅；
已配置 ROS 2 环境变量（终端执行 source /opt/ros/humble/setup.bash，建议添加到 ~/.bashrc）。

## 三、安装 rosbridge_server

3.1 方式 1：APT 安装（推荐，适用于已配置 ROS 2 源的环境）

```shell
# 更新软件源
sudo apt update

# 安装 rosbridge_server 核心包
sudo apt install -y ros-humble-rosbridge-server

# 验证安装
ros2 pkg prefix rosbridge_server
```

## 四、启动 rosbridge_server

### 4.1 基础启动（默认配置）

```shell
# 启动 WebSocket 服务（默认端口 9090）
ros2 launch rosbridge_server rosbridge_websocket_launch.xml delay_between_messages:=0.0
```

- 启动成功日志：终端输出 `WebSocket server started on port 9090`，无红色报错。

![image-20260122085732837](/pic/REMADE/image-20260122085732837.png)

### 4.2 自定义启动（修改端口 / 跨域 / 日志等）

|    配置项    |          作用          |                           启动示例                           |
| :----------: | :--------------------: | :----------------------------------------------------------: |
|     port     |  修改 WebSocket 端口   | `ros2 launch rosbridge_server rosbridge_websocket_launch.xml port:=8080` |
| allow_origin | 允许跨域访问（Web 用） | `ros2 launch rosbridge_server rosbridge_websocket_launch.xml allow_origin:=*` |
|  log_level   |      调整日志级别      | `ros2 launch rosbridge_server rosbridge_websocket_launch.xml log_level:=debug` |

### 4.3 后台启动（避免终端关闭后服务停止）

```shell
# 方式1：nohup 后台启动（日志输出到 nohup.out）
nohup ros2 launch rosbridge_server rosbridge_websocket_launch.xml > ~/rosbridge.log 2>&1 &

# 方式2：查看后台进程
ps -ef | grep rosbridge

# 方式3：停止后台服务
kill -9 [进程ID]
```

## 使用案例（ROS 2 专属）

### 5.1 前置准备：安装客户端依赖

以 Python 客户端为例（最常用），安装 WebSocket 库：

```
pip install websockets python-dotenv   # 推荐在python虚拟环境安装 python3 -m venv .venv
```

### 5.2 案例 1：发布 ROS 2 话题

#### 功能说明

通过 Python 脚本经 WebSocket 向 ROS 2 发布 `std_msgs/String` 类型话题 `/test_pub_topic`。

```shell
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

```

#### 测试步骤

1. 启动 rosbridge：`ros2 launch rosbridge_server rosbridge_websocket_launch.xml`；
2. 新开终端监听话题：`ros2 topic echo /test_pub_topic`；
3. 运行脚本：`python3 pub_topic_demo.py`；
4. 验证结果：监听终端输出 `data: Hello from rosbridge (ROS 2)!`。

#### 注意事项

ROS中，话题必须先被"广告"（告知ROS系统这个话题的存在和类型），然后才能发布消息。

rosbridge对某些操作（如advertise、publish）可能不会发送响应，或者响应有延迟。所以我们不需要等待响应。

在话题持续发布期间：

```shell
lux@lux-HP-Robot:~$ ros2 topic list
/client_count
/connected_clients
/parameter_events
/rosout
/test_pub_topic
lux@lux-HP-Robot:~$ ros2 topic type /test_pub_topic 
std_msgs/msg/String
lux@lux-HP-Robot:~$ ros2 interface show std_msgs/msg/String
# This was originally provided as an example message.
# It is deprecated as of Foxy
# It is recommended to create your own semantically meaningful message.
# However if you would like to continue using this please use the equivalent in example_msgs.

```

### 5.3 案例 2：发布 ROS 2 自定义的话题

#### 功能说明

通过 Python 脚本经 WebSocket 向 ROS 2 发布 `demo_topic_interface/msg/CustomMsg` 类型话题 `//test_customized_pub_topic `。

```shell
lux@lux-HP-Robot:~$ ros2 interface show demo_topic_interface/msg/CustomMsg
string name
int32 id
float64 value
```

```shell
#!/usr/bin/env python3
"""ROS 2 rosbridge 发布自定义话题示例"""
import asyncio
import websockets
import json
from typing import Dict

# ROSbridge 配置
ROSBRIDGE_WS_URI = "ws://localhost:9090"  # 对应启动的端口
TOPIC_NAME = "/test_customized_pub_topic"
# 使用自定义消息类型，格式为：包名/msg/消息名
MSG_TYPE = "demo_topic_interface/msg/CustomMsg"

def build_advertise_msg() -> Dict:
    """构造 rosbridge 广告指令（遵循 rosbridge v2 协议）"""
    return {
        "op": "advertise",        # 操作类型：广告
        "topic": TOPIC_NAME,      # 话题名称
        "type": MSG_TYPE          # 自定义消息类型
    }

def build_publish_msg(name: str, id: int, value: float) -> Dict:
    """构造 rosbridge 发布指令（遵循自定义消息结构）"""
    return {
        "op": "publish",          # 操作类型：发布
        "topic": TOPIC_NAME,      # 话题名称
        "type": MSG_TYPE,         # 自定义消息类型
        "msg": {                  # 消息内容（与自定义消息结构一致）
            "name": name,
            "id": id,
            "value": value
        }
    }

async def publish_topic():
    """发布话题主逻辑"""
    try:
        # 连接 rosbridge WebSocket 服务
        async with websockets.connect(ROSBRIDGE_WS_URI) as websocket:
            print(f"成功连接到 rosbridge: {ROSBRIDGE_WS_URI}")
            
            # 1. 广告自定义话题
            advertise_msg = build_advertise_msg()
            await websocket.send(json.dumps(advertise_msg))
            print(f"已广告自定义话题: {TOPIC_NAME} (类型: {MSG_TYPE})")
            
            # 等待广告完成
            await asyncio.sleep(0.5)
            
            # 2. 发布自定义消息
            for i in range(100):
                test_msg = build_publish_msg(
                    name=f"Message #{i+1}",
                    id=i+1,
                    value=3.14 * (i+1)
                )
                await websocket.send(json.dumps(test_msg))
                print(f"已发布自定义消息到 {TOPIC_NAME}: {test_msg['msg']}")
                await asyncio.sleep(2)  # 每条消息间隔2秒
            
            # 保持连接一段时间，确保所有消息被处理
            await asyncio.sleep(2)
            
            print("发布完成！")
            
    except Exception as e:
        print(f"发布失败: {e}")

if __name__ == "__main__":
    # 测试步骤：
    # 需要先 source install/setup.bash 才能运行
    # 1. 启动 rosbridge: ros2 launch rosbridge_server rosbridge_websocket_launch.xml
    # 2. 新开终端监听话题: ros2 topic echo /test_pub_topic
    # 3. 运行本脚本
    asyncio.run(publish_topic())
```

#### 测试步骤

1. 新建终端，在一个已经 source install/setup.bash 的终端， 启动 rosbridge：`ros2 launch rosbridge_server rosbridge_websocket_launch.xml delay_between_messages:=0.0`；

2. 新开终端监听话题：`ros2 topic echo /test_customized_pub_topic`；

3. 运行脚本：`python3 pub_customized_topic.py`；

4. 验证结果：监听终端输出 

   ```
   name: 'Message #47'
   id: 47
   value: 147.58
   ---
   name: 'Message #48'
   id: 48
   value: 150.72
   ---
   ```

#### 注意事项

### 5.4 案例 3：订阅 ROS 2 话题

#### 功能说明

订阅 ROS 2 自定义话题`/test_customized_pub_topic` ，实时接收消息。

当前是先通过ros_bridge发布`test_customized_pub_topic`话题，然后在通过ros_bridge去订阅`test_customized_pub_topic`话题

```shell
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


```

#### 测试步骤

1. 新建终端，在一个已经 source install/setup.bash 的终端， 启动 rosbridge：`ros2 launch rosbridge_server rosbridge_websocket_launch.xml delay_between_messages:=0.0`；

2. 运行脚本：`python3 pub_customized_topic.py`；

3. 运行脚本：`python sub_topic.py` 

4. 验证结果：监听终端输出 

   ```shell
   (.venv) lux@lux-robot:~/code/mine/ros2_test/rosbridge_test/src/test$ python sub_topic.py 
   成功连接到 rosbridge: ws://localhost:9090
   已发送订阅请求: /test_customized_pub_topic (demo_topic_interface/msg/CustomMsg)
   收到 /test_customized_pub_topic 消息: {'name': 'Message #11', 'id': 11, 'value': 34.54}
   收到 /test_customized_pub_topic 消息: {'name': 'Message #12', 'id': 12, 'value': 37.68}
   收到 /test_customized_pub_topic 消息: {'name': 'Message #13', 'id': 13, 'value': 40.82}
   收到 /test_customized_pub_topic 消息: {'name': 'Message #14', 'id': 14, 'value': 43.96}
   收到 /test_customized_pub_topic 消息: {'name': 'Message #15', 'id': 15, 'value': 47.1}
   收到 /test_customized_pub_topic 消息: {'name': 'Message #16', 'id': 16, 'value': 50.24}
   ```

#### 注意事项

### 5.5 案例 4：发布ROS 2 服务



### 5.6 案例 5：订阅ROS 2 服务



### 5.7 案例 6：发布ROS 2 动作



### 5.8 案例 7：订阅ROS 2 动作