# 07-5 Isaac Sim环境部署

> **前置课程**：07-4 ROS2仿真-传感器与执行器仿真
> **后续课程**：07-6 MuJoCo仿真

**作者**：霍海杰 | **联系方式**：howe12@126.com

---

> **前置说明**：NVIDIA Isaac Sim是基于NVIDIA Omniverse平台的高保真机器人仿真工具，支持PhysX物理引擎、实时光追渲染和ROS2/ROS1集成。本节将详细介绍Isaac Sim的安装部署、ROS2集成方法以及机器人仿真示例，帮助你快速掌握这款强大的机器人仿真平台。

---

## 1. Isaac Sim概述

Isaac Sim是NVIDIA推出的机器人仿真平台，构建于Omniverse平台之上，提供了业界领先的高保真物理仿真和渲染能力。它广泛用于工业机器人、移动机器人、人形机器人等各类机器人的仿真开发和测试。

### 1.1 核心特性

Isaac Sim具有以下核心特性，使其成为机器人仿真领域的首选工具：

**高保真物理仿真**：基于NVIDIA PhysX 5物理引擎，提供精确的刚体动力学、软体仿真、碰撞检测和关节约束。支持多体动力学模拟，能够准确模拟真实机器人的运动行为。

**实时光追渲染**：借助NVIDIA RTX光线追踪技术，实现照片级的视觉质量。实时光照、阴影、反射和全局光照效果，使得仿真场景与真实环境高度一致，便于进行视觉算法的开发和测试。

**ROS2/ROS1原生集成**：内置ROS2 Bridge和ROS Bridge，支持无缝的ROS生态集成。可以直接使用ROS2话题、服务和动作与仿真中的机器人进行交互，现有ROS代码无需修改即可迁移到Isaac Sim中运行。

**USD场景描述**：使用Universal Scene Description（USD）作为场景描述格式，支持场景的导入导出、版本控制和协作编辑。USD的层级结构使得复杂场景的组织和管理变得简单。

**Isaac机器人引擎**：提供预训练的机器人模型和算法，包括Isaac Manipulator（机械臂）、Isaac Mobile（移动机器人）、Isaac Perceptor（感知）等，加速机器人应用的开发。

### 1.2 应用场景

Isaac Sim广泛应用于以下场景：

| 应用场景 | 说明 |
|----------|------|
| 算法开发与验证 | 在仿真环境中开发和测试运动规划、导航、感知等算法 |
| 数字孪生 | 创建真实机器人的数字孪生，进行虚实对比和优化 |
| 训练数据生成 | 生成大规模合成数据，用于训练深度学习模型 |
| 硬件在环测试 | 在部署到真实硬件前进行完整的系统集成测试 |
| 场景重建与仿真 | 将真实环境扫描重建为仿真场景 |

### 1.3 系统架构

Isaac Sim的系统架构分为以下几个层次：

```
┌─────────────────────────────────────────┐
│         Isaac Sim UI (Omniverse)        │  ← 图形界面层
├─────────────────────────────────────────┤
│           USD Scene Graph               │  ← 场景描述层
├─────────────────────────────────────────┤
│  Isaac Core | PhysX | RTX Renderer      │  ← 核心引擎层
├─────────────────────────────────────────┤
│     ROS2 Bridge | ROS Bridge            │  ← 通信接口层
├─────────────────────────────────────────┤
│         Omniverse Kit SDK               │  ← 开发接口层
└─────────────────────────────────────────┘
```

这种分层架构使得用户可以通过Python脚本、USD API或Omniverse扩展来定制和扩展Isaac Sim的功能。

---

## 2. 安装部署

Isaac Sim可以通过多种方式安装，包括NVIDIA NGC容器、Docker镜像和本地安装。本节详细介绍各种安装方法及其适用场景。

### 2.1 系统要求

在安装Isaac Sim之前，请确保系统满足以下要求：

**最低配置**：

| 组件 | 要求 |
|------|------|
| 操作系统 | Ubuntu 20.04/22.04, Windows 10/11 |
| GPU | NVIDIA RTX 20系列或更高 |
| 显存 | 8GB+ |
| 内存 | 16GB+ |
| 存储 | 50GB+ SSD |

**推荐配置**：

| 组件 | 要求 |
|------|------|
| 操作系统 | Ubuntu 22.04 |
| GPU | NVIDIA RTX 30/40系列 |
| 显存 | 16GB+ |
| 内存 | 32GB+ |
| 存储 | 100GB+ NVMe SSD |

Isaac Sim需要NVIDIA驱动和CUDA toolkit。请确保已安装最新NVIDIA驱动（535+）和CUDA 12.x。

### 2.2 使用NVIDIA NGC容器（推荐）

使用NGC容器是最简便的安装方式，NVIDIA已预配置好所有依赖：

```bash
# 安装NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# 拉取Isaac Sim容器
docker pull nvcr.io/nvidia/isaac-sim:latest

# 运行容器（带GPU和显示支持）
docker run --name isaac-sim -it \
    --gpus all \
    --runtime=nvidia \
    -e DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
    --network host \
    nvcr.io/nvidia/isaac-sim:latest

# 或者使用Docker Compose（推荐）
# 创建 docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  isaac-sim:
    image: nvcr.io/nvidia/isaac-sim:latest
    container_name: isaac-sim
    runtime: nvidia
    environment:
      - DISPLAY=${DISPLAY}
      - NVIDIA_VISIBLE_DEVICES=all
      - NVIDIA_DRIVER_CAPABILITIES=all
    volumes:
      - ./isaac_workspace:/workspace
      - /tmp/.X11-unix:/tmp/.X11-unix:rw
    network_mode: host
    shm_size: 16g
    stdin_open: true
    tty: true
EOF

# 启动容器
docker-compose up -d
docker-compose exec isaac-sim bash
```

### 2.3 本地安装（Ubuntu）

如果需要在本地直接运行Isaac Sim，可以下载并安装Omniverse启动器和Isaac Sim应用：

```bash
# 1. 创建安装目录
mkdir -p ~/isaac-sim
cd ~/isaac-sim

# 2. 下载Isaac Sim（需要NVIDIA开发者账号）
# 访问 https://developer.nvidia.com/isaac-sim 下载
# 或者使用pip安装（Python only版本）
pip install isaacsim

# 3. 安装系统依赖
sudo apt-get update
sudo apt-get install -y \
    python3-pip \
    python3-dev \
    python3-venv \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libopenexr23 \
    libicu70

# 4. 验证NVIDIA驱动和CUDA
nvidia-smi
nvcc --version

# 5. 使用Python运行Isaac Sim
python -c "import isaacsim; print('Isaac Sim installed successfully')"

# 6. 启动Isaac Sim（需要图形界面）
# 方法1：使用Omniverse Launcher
# 下载地址：https://www.nvidia.com/en-us/omniverse/download/

# 方法2：使用headless模式（无GUI）
./isaac-sim-python.sh scripts/minimal_example.py

# 方法3：通过Python脚本运行
python3 << 'EOF'
import omni
import omni.isaac.core
from omni.isaac.core import SimulationContext

# 初始化仿真
sim = SimulationContext()
sim.set_camera_view([1, 1, 1], [0, 0, 0])
print("Isaac Sim initialized successfully")
EOF
```

### 2.4 Windows安装

在Windows系统上安装Isaac Sim：

```powershell
# 方法1：使用Omniverse Launcher（推荐）
# 1. 下载并安装 Omniverse Launcher
# https://www.nvidia.com/en-us/omniverse/download/

# 2. 在Launcher中搜索Isaac Sim并安装

# 方法2：使用pip（Python only）
pip install isaacsim

# 验证安装
python -c "import omni; print('Omniverse installed')"
python -c "import isaacsim; print('Isaac Sim installed')"
```

### 2.5 环境变量配置

无论采用哪种安装方式，都需要配置适当的环境变量：

```bash
# 添加到 ~/.bashrc
cat >> ~/.bashrc << 'EOF'

# Isaac Sim配置
export ISAACSIM_PATH=/path/to/isaac-sim
export ISAACSIM_NUCLEUS_PATH=/IsaacSim
export OMNI_USER=/path/to/omni/user
export CARB_APP_NAME=isaac-sim
export LD_LIBRARY_PATH=$ISAACSIM_PATH/kit/libs:$LD_LIBRARY_PATH
export PYTHONPATH=$ISAACSIM_PATH/kit/python/lib:$PYTHONPATH

# ROS2集成（如果使用ROS2 Bridge）
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

# 允许Docker访问显示器
xhost +local:docker
EOF

# 使配置生效
source ~/.bashrc
```

---

## 3. ROS2集成

Isaac Sim提供了原生的ROS2支持，通过Isaac Sim ROS2 Bridge扩展可以无缝对接ROS2生态。本节详细介绍ROS2与Isaac Sim的集成配置和使用方法。

### 3.1 ROS2 Bridge架构

Isaac Sim的ROS2 Bridge基于`ros2_bridge`实现，支持话题、服务和动作的双向通信：

```
┌─────────────────┐         ┌─────────────────┐
│   Isaac Sim     │         │    ROS2         │
│   (Python)      │         │    Workspace    │
├─────────────────┤         ├─────────────────┤
│ Isaac ROS2      │  ────▶  │ rclpy节点       │
│ Bridge Extension│         │ (订阅者/发布者) │
└─────────────────┘         └─────────────────┘
        │                           │
        │  OmniGraph USD            │
        ▼                           ▼
┌─────────────────┐         ┌─────────────────┐
│  USD Stage     │         │  物理仿真       │
│  (场景图)       │         │  (PhysX)        │
└─────────────────┘         └─────────────────┘
```

### 3.2 安装ROS2 Bridge

```bash
# 1. 创建ROS2工作空间
mkdir -p ~/ros2_isaac_ws/src
cd ~/ros2_isaac_ws

# 2. 克隆Isaac ROS2 Bridge
# 注意：选择与Isaac Sim版本匹配的分支
git clone https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_common.git src/isaac_ros_common
git clone https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_graph_utils.git src/isaac_ros_graph_utils
git clone https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_nvblox.git src/isaac_ros_nvblox
git clone https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_terrain_generation.git src/isaac_ros_terrain_generation

# 3. 安装依赖
rosdep install --from-paths src --ignore-src -r -y

# 4. 编译
source /opt/ros/humble/setup.bash
colcon build --symlink-install

# 5. 激活工作空间
source install/setup.bash
```

### 3.3 Isaac Sim中启用ROS2

在Isaac Sim中启用ROS2 Bridge有两种方式：通过UI配置或通过Python脚本。

**方式1：通过UI配置**

1. 打开Isaac Sim
2. Window → Extensions → Isaac Sim ROS2 Bridge
3. 启用ROS2 Bridge扩展
4. 配置ROS2域ID（Domain ID）

**方式2：通过Python脚本启用**

```python
# scripts/enable_ros2_bridge.py
import omni
from omni.isaac.core import SimulationContext
import omni.kit.commands

# 加载ROS2 Bridge扩展
omni.kit.commands.execute("LoadExtension", 
                          module_name="omni.isaac.ros2_bridge")

# 配置ROS2参数
omni.kit.commands.execute("IsaacSimROS2Config",
                          enable_ros2=True,
                          domain_id=0,  # ROS2域ID
                          use_sim_time=True)

# 初始化仿真上下文
sim = SimulationContext()
sim.play()
print("ROS2 Bridge enabled successfully")
```

### 3.4 话题通信示例

以下示例展示如何在Isaac Sim中发布和订阅ROS2话题：

```python
# scripts/ros2_publisher.py
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan, Image, JointState
from geometry_msgs.msg import Twist
import numpy as np

class IsaacSimROS2Publisher(Node):
    """Isaac Sim中的ROS2发布者节点"""
    
    def __init__(self):
        super().__init__('isaac_sim_publisher')
        
        # 创建发布者
        self.laser_pub = self.create_publisher(LaserScan, '/scan', 10)
        self.joint_pub = self.create_publisher(JointState, '/joint_states', 10)
        
        # 定时器
        self.timer = self.create_timer(0.1, self.publish_sensor_data)
        
        self.get_logger().info('Isaac Sim ROS2 Publisher started')
        
    def publish_sensor_data(self):
        # 发布激光雷达数据
        scan_msg = LaserScan()
        scan_msg.header.stamp = self.get_clock().now().to_msg()
        scan_msg.header.frame_id = 'lidar_link'
        scan_msg.angle_min = -np.pi
        scan_msg.angle_max = np.pi
        scan_msg.angle_increment = np.pi / 180
        scan_msg.range_min = 0.1
        scan_msg.range_max = 10.0
        scan_msg.ranges = np.random.uniform(0.5, 5.0, 360).tolist()
        scan_msg.intensities = [1.0] * 360
        
        self.laser_pub.publish(scan_msg)
        
        # 发布关节状态
        joint_msg = JointState()
        joint_msg.header.stamp = self.get_clock().now().to_msg()
        joint_msg.name = ['joint1', 'joint2', 'joint3', 'joint4']
        joint_msg.position = [0.0, 0.5, -0.3, 0.0]
        joint_msg.velocity = [0.0] * 4
        joint_msg.effort = [0.0] * 4
        
        self.joint_pub.publish(joint_msg)


class IsaacSimROS2Subscriber(Node):
    """Isaac Sim中的ROS2订阅者节点"""
    
    def __init__(self):
        super().__init__('isaac_sim_subscriber')
        
        # 创建订阅者
        self.cmd_sub = self.create_subscription(
            Twist, '/cmd_vel', self.cmd_callback, 10)
        
        self.get_logger().info('Isaac Sim ROS2 Subscriber started')
        
    def cmd_callback(self, msg):
        self.get_logger().info(
            f'Received cmd_vel: linear={msg.linear.x}, angular={msg.angular.z}'
        )
        # 这里可以将速度命令应用到机器人


def main(args=None):
    rclpy.init(args=args)
    
    # 创建发布者和订阅者节点
    pub_node = IsaacSimROS2Publisher()
    sub_node = IsaacSimROS2Subscriber()
    
    # 保持节点运行
    executor = rclpy.executors.MultiThreadedExecutor()
    executor.add_node(pub_node)
    executor.add_node(sub_node)
    
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        pub_node.destroy_node()
        sub_node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### 3.5 使用Omnigraph实现ROS2通信

Omnigraph是Isaac Sim的可视化编程工具，可以通过节点图的方式配置ROS2通信：

```python
# 1. 在Isaac Sim中打开Omnigraph编辑器
# Window → Graph Editor → Omnigraph

# 2. 创建新的Omnigraph

# 3. 添加ROS2节点
# 以下Python脚本创建包含ROS2功能的Omnigraph
import omni.graph.core as og
from omni.isaac.core_nodes import *

# 创建新的Omnigraph
graph = og.Graph()
graph.name = "ROS2_Graph"

# 添加ROS2发布节点
ros2_publisher = og.create_node(
    "Ros2Publish",
    graph,
    {
        "topic_name": "/robot_pose",
        "message_type": "geometry_msgs/Pose"
    }
)

# 添加ROS2订阅节点
ros2_subscriber = og.create_node(
    "Ros2Subscribe",
    graph,
    {
        "topic_name": "/cmd_vel",
        "message_type": "geometry_msgs/Twist"
    }
)

# 连接输入输出
# ... (连接其他节点)
print("Omnigraph with ROS2 nodes created successfully")
```

---

## 4. 机器人仿真示例

本节将通过具体示例展示如何使用Isaac Sim进行机器人仿真，包括移动机器人和机械臂的仿真场景。

### 4.1 创建仿真场景

首先创建一个包含地面、机器人和环境的仿真场景：

```python
# scripts/create_scene.py
import omni
from omni.isaac.core import SimulationContext
from pxr import Usd, UsdGeom, Gf, Sdf, UsdLux
import carb

class IsaacSimScene:
    """Isaac Sim仿真场景创建"""
    
    def __init__(self):
        self.stage = omni.usd.get_context().get_stage()
        self.scene = SimulationContext()
        
    def create_ground(self):
        """创建地面"""
        # 使用USD API创建地面平面
        ground_path = "/World/Ground"
        ground = UsdGeom.Xform.Define(self.stage, ground_path)
        UsdGeom.Mesh.Define(
            self.stage, 
            f"{ground_path}/Plane",
            UsdGeom.Tokens.plane
        ).AddTranslateOp().Set(Gf.Vec3d(0, 0, 0))
        UsdGeom.Mesh.Apply(self.stage.GetPrimAtPath(f"{ground_path}/Plane"))
        
        # 设置地面物理属性
        prim = self.stage.GetPrimAtPath(f"{ground_path}/Plane")
        prim.GetAttribute("xformOp:translate").Set(Gf.Vec3d(0, 0, 0))
        
        print(f"Created ground plane at {ground_path}")
        
    def create_light(self):
        """创建光照"""
        light_path = "/World/Light/DistantLight"
        light = UsdLux.DistantLight.Define(self.stage, light_path)
        light.CreateIntensityAttr(1000)
        light.CreateAngleAttr(0.5)
        
    def create_walls(self):
        """创建墙壁（障碍物）"""
        wall_positions = [
            (3, 0, 1.5, 0.1, 3, 3),    # 右墙
            (-3, 0, 1.5, 0.1, 3, 3),   # 左墙
            (0, 0, 1.5, 6, 3, 0.1),   # 前墙
            (0, 0, -1.5, 6, 3, 0.1),  # 后墙
        ]
        
        for i, (x, y, z, sx, sy, sz) in enumerate(wall_positions):
            wall_path = f"/World/Walls/Wall_{i}"
            wall = UsdGeom.Cube.Define(self.stage, wall_path)
            wall.AddTranslateOp().Set(Gf.Vec3d(x, y, z))
            wall.AddScaleOp().Set(Gf.Vec3f(sx/2, sy/2, sz/2))
            
        print(f"Created {len(wall_positions)} walls")
        
    def setup_physics(self):
        """配置物理引擎"""
        # 启用物理仿真
        self.scene.enable_physics()
        
        # 设置重力
        self.scene.get_physics_context().set_gravity_vector(
            carb.math.gf_vec3(0.0, 0.0, -9.81)
        )
        
        print("Physics enabled")


# 运行场景创建
scene = IsaacSimScene()
scene.create_ground()
scene.create_light()
scene.create_walls()
scene.setup_physics()
print("Scene created successfully")
```

### 4.2 移动机器人仿真

以下示例创建一个差分驱动的移动机器人并进行仿真：

```python
# scripts/mobile_robot.py
import omni
from omni.isaac.core import SimulationContext
from pxr import Usd, UsdGeom, Gf, Sdf, PhysxSchema
import numpy as np
import math

class MobileRobot:
    """移动机器人仿真类"""
    
    def __init__(self, usd_path=None):
        self.stage = omni.usd.get_context().get_stage()
        self.robot_path = "/World/Robot"
        self.sim_context = SimulationContext()
        
        if usd_path:
            self.load_robot_usd(usd_path)
        else:
            self.create_robot()
            
    def create_robot(self):
        """创建差分驱动机器人模型"""
        # 创建机器人基座
        base_path = f"{self.robot_path}/Base"
        base = UsdGeom.Cube.Define(self.stage, base_path)
        base.AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.1))
        base.AddScaleOp().Set(Gf.Vec3f(0.3, 0.2, 0.05))
        
        # 设置基座物理属性
        prim = self.stage.GetPrimAtPath(base_path)
        PhysxSchema.PhysxRigidBodyAPI.Apply(prim)
        mass_api = PhysxSchema.PhysxMassAPI.Apply(prim)
        mass_api.CreateMassAttr(10.0)  # 10kg
        
        # 创建左轮
        self.create_wheel(f"{self.robot_path}/LeftWheel", -0.15, 0.0, 0.1)
        
        # 创建右轮
        self.create_wheel(f"{self.robot_path}/RightWheel", 0.15, 0.0, 0.1)
        
        # 创建支撑轮
        self.create_caster(f"{self.robot_path}/Caster", 0.0, -0.15, 0.05)
        
        print("Mobile robot created successfully")
        
    def create_wheel(self, path, x, y, z):
        """创建轮子"""
        wheel = UsdGeom.Cylinder.Define(self.stage, path)
        wheel.AddTranslateOp().Set(Gf.Vec3d(x, y, z))
        wheel.AddRotateXOp().Set(90)
        wheel.AddScaleOp().Set(Gf.Vec3f(0.05, 0.08, 0.05))  # 半径0.05, 宽0.08
        
        # 轮子物理属性
        prim = self.stage.GetPrimAtPath(path)
        PhysxSchema.PhysxRigidBodyAPI.Apply(prim)
        
    def create_caster(self, path, x, y, z):
        """创建支撑轮"""
        caster = UsdGeom.Sphere.Define(self.stage, path)
        caster.AddTranslateOp().Set(Gf.Vec3d(x, y, z))
        caster.AddScaleOp().Set(Gf.Vec3f(0.02, 0.02, 0.02))
        
    def load_robot_usd(self, usd_path):
        """加载已有的机器人USD模型"""
        omni.usd.get_context().open_stage(usd_path)
        print(f"Loaded robot from {usd_path}")
        
    def set_velocity(self, linear_vel, angular_vel):
        """设置机器人速度（差分驱动）"""
        # 差分驱动运动学
        # v = (v_left + v_right) / 2
        # ω = (v_right - v_left) / wheel_base
        
        wheel_radius = 0.05
        wheel_base = 0.3
        
        # 计算左右轮速度
        v_left = (linear_vel - angular_vel * wheel_base / 2) / wheel_radius
        v_right = (linear_vel + angular_vel * wheel_base / 2) / wheel_radius
        
        # 应用到机器人
        # 这里需要通过ROS2或直接API控制
        print(f"Setting velocities: left={v_left:.2f}, right={v_right:.2f} rad/s")
        
    def get_pose(self):
        """获取机器人位姿"""
        # 获取基座位姿
        base_path = f"{self.robot_path}/Base"
        prim = self.stage.GetPrimAtPath(base_path)
        
        if prim:
            xform = UsdGeom.Xformable(prim)
            world_transform = xform.ComputeLocalToWorldTransform(Usd.TimeCode.Default())
            position = world_transform.ExtractTranslation()
            rotation = world_transform.ExtractRotation()
            
            return {
                'position': [position[0], position[1], position[2]],
                'rotation': [rotation.GetQuat().GetX(),
                           rotation.GetQuat().GetY(),
                           rotation.GetQuat().GetZ(),
                           rotation.GetQuat().GetW()]
            }
        return None


# 使用示例
robot = MobileRobot()

# 仿真循环
sim = SimulationContext()
sim.play()

for i in range(1000):
    sim.step()
    
    # 每秒更新一次机器人控制
    if i % 60 == 0:
        pose = robot.get_pose()
        if pose:
            print(f"Robot pose: {pose['position']}")
            
        # 设置前进速度
        robot.set_velocity(0.2, 0.0)  # 0.2m/s前进
        
print("Mobile robot simulation completed")
```

### 4.3 机械臂仿真

以下示例展示如何仿真一个机械臂：

```python
# scripts/manipulator.py
import omni
from omni.isaac.core import SimulationContext
from pxr import Usd, UsdGeom, Gf, Sdf, PhysxSchema, UsdPhysics
import numpy as np

class RoboticArm:
    """机械臂仿真类"""
    
    def __init__(self):
        self.stage = omni.usd.get_context().get_stage()
        self.joint_names = []
        self.joint_controllers = {}
        
    def create_arm(self):
        """创建机械臂"""
        # 创建底座
        base_path = "/World/Manipulator/Base"
        base = UsdGeom.Cylinder.Define(self.stage, base_path)
        base.AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.1))
        base.AddScaleOp().Set(Gf.Vec3f(0.1, 0.1, 0.1))
        
        # 创建关节和连杆
        self.create_joint_and_link("Joint1", 0, 0, 0.25, "z")
        self.create_joint_and_link("Joint2", 0, 0, 0.3, "y")
        self.create_joint_and_link("Joint3", 0, 0, 0.3, "y")
        self.create_joint_and_link("Joint4", 0, 0, 0.2, "x")
        
        # 创建末端执行器
        self.create_end_effector()
        
        print("Robotic arm created successfully")
        
    def create_joint_and_link(self, joint_name, x, y, length, axis):
        """创建关节和连杆"""
        link_path = f"/World/Manipulator/{joint_name}_Link"
        joint_path = f"/World/Manipulator/{joint_name}"
        
        # 创建连杆（圆柱体）
        link = UsdGeom.Cylinder.Define(self.stage, link_path)
        
        # 根据关节轴设置连杆方向
        if axis == "x":
            link.AddRotateYOp().Set(90)
            link.AddTranslateOp().Set(Gf.Vec3d(x, y + length/2, length/2))
        elif axis == "y":
            link.AddRotateXOp().Set(90)
            link.AddTranslateOp().Set(Gf.Vec3d(x, y + length/2, length/2))
        else:  # z轴
            link.AddTranslateOp().Set(Gf.Vec3d(x, y, length/2))
            
        link.AddScaleOp().Set(Gf.Vec3f(0.03, length, 0.03))
        
        # 设置连杆物理
        link_prim = self.stage.GetPrimAtPath(link_path)
        PhysxSchema.PhysxRigidBodyAPI.Apply(link_prim)
        
        # 创建关节
        joint = UsdPhysics.RevoluteJoint.Define(self.stage, joint_path)
        
        # 设置关节属性
        joint.CreateBody0Rel().SetTargets([Sdf.Path(f"/World/Manipulator/Base")])
        joint.CreateBody1Rel().SetTargets([Sdf.Path(link_path)])
        
        # 关节限制
        joint.CreateLowerLimitAttr(-3.14)
        joint.CreateUpperLimitAttr(3.14)
        joint.CreateMaxVelocityAttr(2.0)
        
        self.joint_names.append(joint_name)
        
    def create_end_effector(self):
        """创建末端执行器"""
        ee_path = "/World/Manipulator/EndEffector"
        ee = UsdGeom.Sphere.Define(self.stage, ee_path)
        ee.AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.25))
        ee.AddScaleOp().Set(Gf.Vec3f(0.03, 0.03, 0.03))
        
    def set_joint_positions(self, positions):
        """设置关节目标位置"""
        # 使用JointController控制关节
        for i, (joint_name, pos) in enumerate(zip(self.joint_names, positions)):
            joint_path = f"/World/Manipulator/{joint_name}"
            # 设置目标位置（通过物理引擎）
            print(f"Setting {joint_name} to position {pos} rad")
            
    def move_to_pose(self, target_position):
        """移动到目标位置（简化版）"""
        # 这里可以集成MoveIt!进行运动规划
        # 简化实现：直接设置关节位置
        current_pos = [0.0, 0.0, 0.0, 0.0]  # 简化
        target_pos = [0.0, -0.5, 0.5, 0.0]    # 示例目标
        
        # 简单的插值
        steps = 100
        for i in range(steps):
            interpolated = [
                current + (target - current) * i / steps
                for current, target in zip(current_pos, target_pos)
            ]
            self.set_joint_positions(interpolated)
            
            # 仿真一步
            sim = SimulationContext()
            sim.step()
            
        print(f"Move to position {target_position} completed")


# 使用示例
arm = RoboticArm()
arm.create_arm()

# 运行仿真
sim = SimulationContext()
sim.play()

# 移动机械臂到目标位置
arm.move_to_pose([0.0, -0.5, 0.5, 0.0])

print("Manipulator simulation completed")
```

### 4.4 传感器仿真

Isaac Sim支持各类传感器的仿真，包括相机、激光雷达、IMU等：

```python
# scripts/sensors.py
import omni
from omni.isaac.core import SimulationContext
import numpy as np

class IsaacSimSensors:
    """Isaac Sim传感器仿真"""
    
    def __init__(self):
        self.stage = omni.usd.get_context().get_stage()
        
    def create_camera(self, path, resolution=(640, 480), hfov=60):
        """创建相机传感器"""
        from omni.isaac.core.sensors import Camera
        
        camera = Camera(
            prim_path=path,
            resolution=resolution,
            horizontal_fov=hfov
        )
        
        # 启用渲染
        camera.initialize()
        
        print(f"Camera created at {path}")
        return camera
        
    def create_lidar(self, path, num_channels=32, horizontal_fov=360):
        """创建激光雷达传感器"""
        from omni.isaac.core.sensors import Lidar
        
        lidar = Lidar(
            prim_path=path,
            num_channels=num_channels,
            horizontal_fov=horizontal_fov
        )
        
        # 配置激光雷达参数
        lidar.set_range_parameters(
            min_range=0.5,
            max_range=100.0,
            yaw_resolution=0.2
        )
        
        lidar.initialize()
        
        print(f"Lidar created at {path}")
        return lidar
        
    def create_imu(self, path):
        """创建IMU传感器"""
        from omni.isaac.core.sensors import Imu
        
        imu = Imu(prim_path=path)
        imu.initialize()
        
        print(f"IMU created at {path}")
        return imu
        
    def get_camera_data(self, camera):
        """获取相机数据"""
        # 获取渲染图像
        rgba_data = camera.get_rgba()
        depth_data = camera.get_depth()
        
        return {
            'rgba': rgba_data,
            'depth': depth_data
        }
        
    def get_lidar_data(self, lidar):
        """获取激光雷达数据"""
        # 获取点云数据
        point_cloud = lidar.get_point_cloud()
        ranges = lidar.get_ranges()
        
        return {
            'point_cloud': point_cloud,
            'ranges': ranges
        }
        
    def get_imu_data(self, imu):
        """获取IMU数据"""
        angular_velocity = imu.get_angular_velocity()
        linear_acceleration = imu.get_linear_acceleration()
        orientation = imu.get_orientation()
        
        return {
            'angular_velocity': angular_velocity,
            'linear_acceleration': linear_acceleration,
            'orientation': orientation
        }


# 使用示例
sensors = IsaacSimSensors()

# 创建传感器
camera = sensors.create_camera("/World/Sensors/Camera")
lidar = sensors.create_lidar("/World/Sensors/Lidar")
imu = sensors.create_imu("/World/Sensors/IMU")

# 仿真循环
sim = SimulationContext()
sim.play()

for i in range(100):
    sim.step()
    
    # 获取传感器数据
    if i % 10 == 0:
        camera_data = sensors.get_camera_data(camera)
        lidar_data = sensors.get_lidar_data(lidar)
        imu_data = sensors.get_imu_data(imu)
        
        print(f"Step {i}:")
        print(f"  Lidar ranges: {len(lidar_data['ranges'])} points")
        print(f"  IMU accel: {imu_data['linear_acceleration']}")

print("Sensor simulation completed")
```

---

## 5. 练习题

### 选择题

1. Isaac Sim基于什么平台构建？
   - A) Unity
   - B) Unreal Engine
   - C) NVIDIA Omniverse
   - D) WebGL
   
   **答案：C**。Isaac Sim基于NVIDIA Omniverse平台构建，提供了高保真物理仿真和实时光追渲染能力。

2. Isaac Sim使用什么物理引擎？
   - A) Bullet Physics
   - B) ODE
   - C) NVIDIA PhysX
   - D) MuJoCo
   
   **答案：C**。Isaac Sim使用NVIDIA PhysX物理引擎，提供精确的刚体动力学和多体仿真。

3. Isaac Sim中的ROS2 Bridge主要实现什么功能？
   - A) 将USD转换为ROS消息
   - B) 实现Isaac Sim与ROS2之间的话题/服务/动作通信
   - C) 将ROS2代码转换为Python
   - D) 同步ROS2和Isaac Sim的时间
   
   **答案：B**。ROS2 Bridge实现了Isaac Sim与ROS2之间的双向通信，支持话题发布/订阅、服务调用和动作交互。

4. 以下哪种不是Isaac Sim支持的文件格式？
   - A) USD
   - B) URDF
   - C) STL
   - D) FBX
   
   **答案：B**。Isaac Sim主要使用USD格式，支持导入STL、OBJ、FBX等网格文件，但URDF主要用于ROS系统。

### 实践题

5. 创建一个简单的Isaac Sim仿真场景，包含地面和一个立方体障碍物，并启用物理仿真。
   
   **参考答案**：
   
   ```python
   import omni
   from omni.isaac.core import SimulationContext
   from pxr import Usd, UsdGeom, Gf, PhysxSchema
   import carb

   class SimpleScene:
       def __init__(self):
           self.stage = omni.usd.get_context().get_stage()
           self.scene = SimulationContext()
           
       def create_ground(self):
           """创建地面"""
           ground_path = "/World/Ground"
           ground = UsdGeom.Mesh.Get(self.stage, ground_path)
           if not ground:
               ground = UsdGeom.Mesh.Define(self.stage, ground_path)
               # 设置地面为平面
               ground.CreatePointsAttr([(-50, 0, -50), (50, 0, -50), (50, 0, 50),
               (-50, 0, 50)])
               ground.CreateFaceVertexCountsAttr([4])
               
           # 设置地面为静态刚体
           prim = self.stage.GetPrimAtPath(ground_path)
           PhysxSchema.PhysxRigidBodyAPI.Apply(prim)
           PhysxSchema.PhysxStaticRigidBodyAPI.Apply(prim)
           print("Ground created")
           
       def create_obstacle(self):
           """创建立方体障碍物"""
           obstacle_path = "/World/Obstacle"
           cube = UsdGeom.Cube.Define(self.stage, obstacle_path)
           cube.AddTranslateOp().Set(Gf.Vec3d(2, 0, 0.5))
           cube.AddScaleOp().Set(Gf.Vec3f(0.5, 0.5, 0.5))
           
           # 设置为动态刚体
           prim = self.stage.GetPrimAtPath(obstacle_path)
           PhysxSchema.PhysxRigidBodyAPI.Apply(prim)
           mass_api = PhysxSchema.PhysxMassAPI.Apply(prim)
           mass_api.CreateMassAttr(1.0)  # 1kg
           print("Obstacle created")
           
       def setup_physics(self):
           """启用物理仿真"""
           self.scene.enable_physics()
           self.scene.get_physics_context().set_gravity_vector(
               carb.math.gf_vec3(0.0, 0.0, -9.81)
           )
           print("Physics enabled")

   # 运行示例
   scene = SimpleScene()
   scene.create_ground()
   scene.create_obstacle()
   scene.setup_physics()
   
   # 运行仿真
   sim = SimulationContext()
   sim.play()
   
   for i in range(100):
       sim.step()
       if i % 10 == 0:
           print(f"Step {i}")
   
   print("Simple scene simulation completed!")
   ```

---

## 本章小结

本章我们全面学习了Isaac Sim机器人仿真平台。概述部分，我们了解了Isaac Sim基于NVIDIA Omniverse平台构建，具有高保真物理仿真、实时光追渲染、ROS2/ROS1原生集成等核心特性。安装部署部分，我们详细介绍了使用NGC容器、本地安装等多种安装方法，并配置了必要的环境变量。ROS2集成部分，我们学习了ROS2 Bridge的架构，并通过Python脚本实现了话题通信。机器人仿真示例部分，我们通过创建仿真场景、移动机器人、机械臂和传感器等示例，展示了Isaac Sim的完整仿真流程。

Isaac Sim作为NVIDIA推出的高端机器人仿真平台，特别适合需要高保真物理仿真和视觉效果的研发项目。通过ROS2集成，可以与现有ROS生态系统无缝对接，实现算法从仿真到真实机器人的平滑迁移。

---

## 参考资料

### 官方文档

1. Isaac Sim Documentation: <https://docs.omniverse.nvidia.com/isaac-sim/>
2. Isaac Sim ROS2 Bridge: <https://docs.omniverse.nvidia.com/isaac-sim/robotics_ros2.html>
3. Isaac ROS Packages: <https://developer.nvidia.com/isaac-ros>

### 学习资源

4. Isaac Sim GitHub: <https://github.com/NVIDIA-ISAAC-ROS/isaac_sim>
5. Omniverse Platform: <https://www.nvidia.com/en-us/omniverse/>
6. Isaac Sim Tutorials: <https://www.nvidia.com/en-us/omniverse/learn/>

---

## 下节预告

下一节我们将学习**07-6 MuJoCo仿真**，了解MuJoCo物理引擎的特点和使用方法，掌握另一种重要的机器人仿真工具。

---

*本章学习完成！Isaac Sim是高端机器人仿真平台，建议在有GPU条件的情况下进行实践，体验其高保真的物理仿真和渲染效果。*
