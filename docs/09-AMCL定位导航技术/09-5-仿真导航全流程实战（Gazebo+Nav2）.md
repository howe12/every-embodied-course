# 09-5 仿真导航全流程实战（Gazebo+Nav2）

> **前置课程**：09-4 ROS2导航栈架构与核心模块
> **后续课程**：待补充

**作者**：霍海杰 | **联系方式**：howe12@126.com

---

> **前置说明**：本节将带领大家在Gazebo仿真环境中，从零开始搭建完整的Nav2导航系统。我们将涵盖地图配置、定位配置、导航参数设置以及目标点导航的完整流程。通过本节的学习，你将掌握在仿真环境中部署导航系统的完整技能，为后续在真实机器人上的部署打下坚实基础。

---

## 1. 概述：仿真导航完整流程

在正式进入实战之前，我们先整体了解一下Gazebo+Nav2导航的完整流程。导航系统的部署通常包括以下几个关键步骤：

1. **环境准备**：启动Gazebo仿真世界，加载机器人模型
2. **地图构建**：使用SLAM技术生成环境地图（或使用现成地图）
3. **地图配置**：将地图加载到Nav2系统中
4. **定位配置**：配置AMCL定位参数，确保机器人能准确估计自身位置
5. **导航配置**：配置路径规划、避障等导航参数
6. **目标点导航**：发送目标点，让机器人自主导航

```
┌─────────────────────────────────────────────────────────────────┐
│                      Gazebo + Nav2 导航流程                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│  │  Gazebo  │───▶│  Cartographer│───▶│   AMCL   │───▶│  Nav2    │ │
│  │  仿真环境│    │  /GMapping │    │  定位    │    │  导航    │ │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘ │
│       │               │               │               │        │
│       ▼               ▼               ▼               ▼        │
│  机器人模型        地图构建        位置估计        路径规划     │
│  传感器仿真       .pgm/.yaml      粒子滤波        自主导航     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

本节我们将使用TurtleBot3作为演示机器人，它是在ROS2学习中最常用的实验平台。如果你使用的是其他机器人，核心流程是类似的，只需要根据具体机器人型号调整相应的配置文件。

---

## 2. 环境准备

### 2.1 安装TurtleBot3相关包

首先确保你已经安装了TurtleBot3的相关功能包。如果尚未安装，执行以下命令：

```bash
# 安装TurtleBot3仿真功能包
sudo apt update
sudo apt install ros-humble-turtlebot3-simulations ros-humble-turtlebot3-navigation2

# 或者从源码安装
cd ~/ros2_ws/src
git clone -b humble https://github.com/ROBOTIS-GIT/turtlebot3_simulations.git
git clone -b humble https://github.com/ROBOTIS-GIT/turtlebot3_navigation2.git
cd ~/ros2_ws
colcon build --packages-select turtlebot3_navigation2
source install/setup.bash
```

### 2.2 启动Gazebo仿真世界

TurtleBot3提供了多个预定义的仿真世界，我们使用经典的`waffle.world`作为演示：

```bash
# 设置TurtleBot3模型
export TURTLEBOT3_MODEL=waffle

# 启动Gazebo仿真世界（带机器人的室内环境）
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
```

或者使用更简单的环境进行测试：

```bash
# 启动空旷世界
ros2 launch turtlebot3_gazebo empty_world.launch.py world_name:=tb3_world
```

启动成功后，你将看到Gazebo界面，其中包含一个TurtleBot3机器人。

### 2.3 验证传感器数据

在另一个终端中，验证机器人传感器正常工作：

```bash
# 查看所有可用话题
ros2 topic list

# 查看激光雷达数据
ros2 topic echo /scan

# 查看TF变换树
ros2 run rqt_tf_tree rqt_tf_tree
```

确保以下话题正常发布：
- `/scan`：激光雷达数据
- `/odom`：里程计数据
- `/imu`：IMU数据
- `/tf`：坐标变换

---

## 3. 地图构建

在导航之前，我们需要先构建环境地图。本节我们将介绍两种方式：使用SLAM实时构建地图，以及使用现成的地图文件。

### 3.1 使用Cartographer实时建图

Cartographer是ROS2中最流行的SLAM方案之一，适合实时建图场景：

```bash
# 启动Cartographer建图
ros2 launch turtlebot3_navigation2 navigation.launch.py use_sim_time:=True map:=/home/nx_ros/map.yaml
```

### 3.2 手动控制机器人建图

使用键盘遥控机器人在环境中移动，完成地图绘制：

```bash
# 启动键盘控制
ros2 run turtlebot3_teleop teleop_keyboard
```

操作按键说明：
- `w`/`W`：前进
- `s`/`S`：后退
- `a`/`A`：左转
- `d`/`D`：右转
- `空格`：停止

### 3.3 保存地图

地图构建完成后，将其保存到文件：

```bash
# 创建地图保存目录
mkdir -p ~/maps

# 保存地图
ros2 run nav2_map_server map_saver_cli -f ~/maps/my_map
```

这将生成两个文件：
- `my_map.pgm`：地图的栅格图像
- `my_map.yaml`：地图的元数据配置

```yaml
# my_map.yaml 示例
image: /home/nx_ros/maps/my_map.pgm
resolution: 0.05
origin: [-10.0, -10.0, 0.0]
negate: 0
occupied_thresh: 0.65
free_thresh: 0.196
```

地图参数说明：

| 参数 | 说明 | 典型值 |
|------|------|--------|
| `image` | 地图图像文件路径 | `*.pgm` |
| `resolution` | 地图分辨率（米/像素） | 0.05 |
| `origin` | 地图原点坐标 | `[-X, -Y, 0.0]` |
| `occupied_thresh` | 占据阈值 | 0.65 |
| `free_thresh` | 空闲阈值 | 0.196 |

---

## 4. 地图配置

地图配置是Nav2启动的第一步。我们需要将地图加载到map_server中，并配置相关参数。

### 4.1 创建导航启动文件

创建一个完整的导航启动文件：

```python
# turtlebot3_nav2.launch.py
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    map_file = LaunchConfiguration('map')
    use_sim_time = LaunchConfiguration('use_sim_time')
    
    return LaunchDescription([
        DeclareLaunchArgument(
            'map',
            default_value='/home/nx_ros/maps/my_map.yaml',
            description='地图文件路径'
        ),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='True',
            description='使用仿真时间'
        ),
        
        # Map Server - 加载地图
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            parameters=[{
                'yaml_filename': map_file,
                'use_sim_time': use_sim_time,
            }],
            output='screen',
        ),
        
        # Lifecycle Manager - 管理节点生命周期
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager',
            parameters=[{
                'use_sim_time': use_sim_time,
                'autostart': True,
                'node_names': ['map_server'],
            }],
        ),
    ])
```

### 4.2 启动地图服务器

```bash
# 启动导航（包含地图服务）
ros2 launch turtlebot3_navigation2 navigation.launch.py map:=/home/nx_ros/maps/my_map.yaml
```

---

## 5. 定位配置

定位是导航的基础，Nav2使用AMCL（Adaptive Monte Carlo Localization）实现机器人的位置估计。

### 5.1 AMCL节点配置

```yaml
# amcl_config.yaml
amcl:
  ros__parameters:
    use_sim_time: True
    
    # 激光雷达配置
    laser_model_type: "likelihood_field"
    laser_min_range: 0.12
    laser_max_range: 3.5
    laser_max_beams: 30
    
    # 里程计模型配置
    odom_model_type: "diff-corrected"
    odom_alpha1: 0.2
    odom_alpha2: 0.2
    odom_alpha3: 0.2
    odom_alpha4: 0.2
    odom_frame_id: "odom"
    base_frame_id: "base_link"
    
    # 定位参数
    initial_pose_x: 0.0
    initial_pose_y: 0.0
    initial_pose_a: 0.0
    
    # 粒子滤波器参数
    max_particles: 5000
    min_particles: 500
    transform_tolerance: 1.0
    
    # 地图配置
    global_frame_id: "map"
```

关键参数说明：

| 参数 | 说明 | 调优建议 |
|------|------|----------|
| `laser_model_type` | 激光模型类型 | `likelihood_field`适合室内环境 |
| `odom_model_type` | 里程计模型 | `diff-corrected`适合差分驱动机器人 |
| `odom_alpha*` | 里程计噪声参数 | 根据机器人实际运动调整 |
| `max_particles` | 最大粒子数 | 精度要求高时增大 |

### 5.2 设置初始位姿

机器人启动时需要设置初始位姿，否则AMCL无法准确知道机器人在地图中的位置。

**方法一：通过Rviz2设置**

1. 在rviz2中点击"2D Pose Estimate"按钮
2. 在地图上点击机器人位置
3. 拖动鼠标设置机器人朝向

**方法二：通过代码设置**

```python
# set_initial_pose.py
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseWithCovarianceStamped
import math

class InitialPoseSetter(Node):
    def __init__(self):
        super().__init__('initial_pose_setter')
        self.publisher = self.create_publisher(
            PoseWithCovarianceStamped, 
            '/initialpose', 
            10
        )
        
    def set_pose(self, x, y, theta):
        msg = PoseWithCovarianceStamped()
        msg.header.frame_id = 'map'
        msg.header.stamp = self.get_clock().now().to_msg()
        
        msg.pose.pose.position.x = x
        msg.pose.pose.position.y = y
        msg.pose.pose.position.z = 0.0
        
        # 设置四元数朝向
        msg.pose.pose.orientation.z = math.sin(theta / 2)
        msg.pose.pose.orientation.w = math.cos(theta / 2)
        
        self.publisher.publish(msg)
        self.get_logger().info(f'Initial pose set to: x={x}, y={y}, theta={theta}')

def main(args=None):
    rclpy.init(args=args)
    setter = InitialPoseSetter()
    setter.set_pose(0.0, 0.0, 0.0)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

---

## 6. 导航配置

导航配置是Nav2最核心的部分，涉及到路径规划、避障、行为树等多个组件。

### 6.1 导航参数配置

```yaml
# nav2_params.yaml
bt_navigator:
  ros__parameters:
    use_sim_time: True
    global_frame: "map"
    robot_base_frame: "base_link"
    odom_topic: "/odom"
    
    # 插件配置
    planner_plugins: ["GridBased"]
    controller_plugins: ["FollowPath"]

controller_server:
  ros__parameters:
    use_sim_time: True
    controller_frequency: 20.0
    
    # 机器人参数
    max_x_velocity: 0.26
    max_y_velocity: 0.26
    max_theta_velocity: 1.96
    
    # 目标容差
    goal_checker_plugins: ["general_goal_checker"]
    general_goal_checker:
      plugin: "nav2_controller/plugins/GeneralGoalChecker"
      xy_goal_tolerance: 0.25
      yaw_goal_tolerance: 0.25

planner_server:
  ros__parameters:
    use_sim_time: True
    planner_plugins: ["GridBased"]
    
    GridBased:
      plugin: "nav2_smac_planner/SmacPlanner2D"
      allow_unknown: True
      max_iterations: 1000000
      max_planning_time: 5.0
```

### 6.2 核心参数详解

**控制器参数**：

| 参数 | 说明 | 典型值 |
|------|------|--------|
| `desired_linear_vel` | 期望线速度 | 0.3 m/s |
| `desired_angular_vel` | 期望角速度 | 0.3 rad/s |
| `max_linear_accel` | 最大线加速度 | 2.5 m/s² |
| `xy_goal_tolerance` | XY位置容差 | 0.25 m |
| `yaw_goal_tolerance` | 角度容差 | 0.25 rad |

### 6.3 启动导航堆栈

```bash
# 启动完整导航堆栈
ros2 launch turtlebot3_navigation2 navigation.launch.py \
    map:=/home/nx_ros/maps/my_map.yaml \
    use_sim_time:=True
```

导航启动包含以下节点：

| 节点名称 | 功能 |
|----------|------|
| `map_server` | 地图服务 |
| `amcl` | 定位 |
| `bt_navigator` | 行为树导航 |
| `controller_server` | 轨迹跟踪 |
| `planner_server` | 路径规划 |
| `behavior_server` | 恢复行为 |

---

## 7. 目标点导航

### 7.1 使用Rviz2发送目标点

最简单的方式是通过Rviz2可视化界面：

1. 点击"Navigation2 Goal"按钮
2. 在地图上点击目标位置
3. 拖动箭头设置目标朝向
4. 点击"Publish Goal"发送目标

### 7.2 通过代码发送目标点

```python
# navigate_to_point.py
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
import math

class NavigationClient(Node):
    def __init__(self):
        super().__init__('navigation_client')
        self.action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        
    def send_goal(self, x, y, theta=0.0):
        goal_msg = NavigateToPose.Goal()
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.get_clock().now().to_msg()
        
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = 0.0
        pose.pose.orientation.z = math.sin(theta / 2)
        pose.pose.orientation.w = math.cos(theta / 2)
        
        goal_msg.pose = pose
        
        self.action_client.wait_for_server()
        self._send_goal_future = self.action_client.send_goal_async(
            goal_msg,
            feedback_callback=self.feedback_callback
        )
        self._send_goal_future.add_done_callback(self.goal_response_callback)
        
    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Goal rejected')
            return
        self.get_logger().info('Goal accepted')
        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)
        
    def get_result_callback(self, future):
        result = future.result().result
        self.get_logger().info(f'Result: {result.result}')
        rclpy.shutdown()
        
    def feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        self.get_logger().info(
            f'Distance remaining: {feedback.distance_remaining:.2f}m'
        )

def main(args=None):
    rclpy.init(args=args)
    nav_client = NavigationClient()
    nav_client.send_goal(2.0, 1.0, 0.0)
    rclpy.spin(nav_client)

if __name__ == '__main__':
    main()
```

### 7.3 多点巡检脚本

```python
# patrol_navigation.py
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
import math

class PatrolNavigation(Node):
    def __init__(self):
        super().__init__('patrol_navigation')
        self.action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.current_goal_index = 0
        self.is_navigating = False
        
        self.patrol_points = [
            {'x': 0.5, 'y': 0.0, 'theta': 0.0},
            {'x': 0.5, 'y': 1.0, 'theta': -math.pi/2},
            {'x': -0.5, 'y': 1.0, 'theta': math.pi},
            {'x': -0.5, 'y': 0.0, 'theta': math.pi/2},
        ]
        
    def start_patrol(self):
        self.is_navigating = True
        self.navigate_to_next_point()
        
    def navigate_to_next_point(self):
        if not self.is_navigating:
            return
            
        if self.current_goal_index >= len(self.patrol_points):
            self.get_logger().info('Patrol completed!')
            self.is_navigating = False
            return
            
        point = self.patrol_points[self.current_goal_index]
        self.get_logger().info(
            f'Navigating to point {self.current_goal_index + 1}/'
            f'{len(self.patrol_points)}: ({point["x"]}, {point["y"]})'
        )
        self.send_goal(point['x'], point['y'], point['theta'])
        
    def send_goal(self, x, y, theta):
        goal_msg = NavigateToPose.Goal()
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.get_clock().now().to_msg()
        
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = 0.0
        pose.pose.orientation.z = math.sin(theta / 2)
        pose.pose.orientation.w = math.cos(theta / 2)
        
        goal_msg.pose = pose
        
        self.action_client.wait_for_server()
        self._send_goal_future = self.action_client.send_goal_async(
            goal_msg,
            feedback_callback=self.feedback_callback
        )
        self._send_goal_future.add_done_callback(self.goal_response_callback)
        
    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Goal rejected, retrying...')
            self.navigate_to_next_point()
            return
        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)
        
    def get_result_callback(self, future):
        result = future.result().result
        if result.result == 1:  # SUCCEEDED
            self.get_logger().info(f'Point {self.current_goal_index + 1} reached!')
            self.current_goal_index += 1
            self.create_timer(1.0, self.navigate_to_next_point)
        else:
            self.get_logger().error(f'Navigation failed: {result.result}')
            self.navigate_to_next_point()

def main(args=None):
    rclpy.init(args=args)
    patrol_nav = PatrolNavigation()
    patrol_nav.start_patrol()
    rclpy.spin(patrol_nav)
    patrol_nav.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

---

## 8. 完整启动流程演示

```bash
# 终端1：启动Gazebo仿真环境
export TURTLEBOT3_MODEL=waffle
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py

# 终端2：启动导航系统
ros2 launch turtlebot3_navigation2 navigation.launch.py \
    map:=/home/nx_ros/maps/my_map.yaml \
    use_sim_time:=True

# 终端3：启动rviz2可视化
ros2 run rviz2 rviz2 -d $(find turtlebot3_navigation2 -name navigation2.rviz)
```

---

## 9. 常见问题与解决

### 9.1 机器人无法定位

**症状**：机器人在地图上漂移，无法准确确定自身位置

**解决方案**：
1. 检查激光雷达数据是否正常
2. 确保初始位姿设置正确
3. 调整AMCL参数（增加粒子数）
4. 检查TF变换是否正确

```bash
# 检查TF变换
ros2 run rqt_tf_tree rqt_tf_tree
```

### 9.2 机器人导航路径不平滑

**解决方案**：
1. 调整控制器参数
2. 启用轨迹平滑器
3. 降低最大速度

### 9.3 机器人无法通过狭窄通道

**解决方案**：
1. 调整代价地图膨胀半径
2. 增加规划迭代次数

---

## 练习题

### 选择题

1. 在Nav2导航中，哪个节点负责机器人的定位？
   - A) planner_server
   - B) controller_server
   - C) amcl
   - D) bt_navigator
   
   **答案：C**。AMCL（Adaptive Monte Carlo Localization）负责机器人在地图中的定位。

2. TurtleBot3的激光雷达话题名称是什么？
   - A) /laser
   - B) /scan
   - C) /lidar
   - D) /pointcloud
   
   **答案：B**。TurtleBot3的标准激光雷达话题是`/scan`。

3. 导航参数中，`xy_goal_tolerance`表示什么？
   - A) 路径规划的容差
   - B) 目标点XY位置的容差
   - C) 激光雷达的容差
   - D) 速度的容差
   
   **答案：B**。`xy_goal_tolerance`是机器人到达目标点时XY位置的容差。

4. 以下哪个不是Nav2的恢复行为？
   - A) rotate_recovery
   - B) wait_recovery
   - C) back_up_recovery
   - D) spiral_recovery
   
   **答案：D**。Nav2标准恢复行为包括rotate_recovery和wait_recovery。

### 实践题

5. 使用代码实现一个简单的多点导航程序，让机器人在3个点之间循环移动。
   
   **参考答案**：
   
   ```python
   import rclpy
   from rclpy.node import Node
   from geometry_msgs.msg import PoseStamped
   from nav2_msgs.action import NavigateToPose
   from rclpy.action import ActionClient
   import math
   
   class MultiPointNavigator(Node):
       def __init__(self):
           super().__init__('multi_point_navigator')
           self.action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
           self.target_index = 0
           
           # 三个目标点
           self.targets = [
               {'x': 1.0, 'y': 0.0, 'theta': 0.0},
               {'x': 1.0, 'y': 1.0, 'theta': -math.pi/2},
               {'x': 0.0, 'y': 1.0, 'theta': math.pi},
           ]
   
       def navigate_to_target(self):
           target = self.targets[self.target_index]
           self.get_logger().info(f'前往目标点 {self.target_index + 1}/3')
           
           goal_msg = NavigateToPose.Goal()
           pose = PoseStamped()
           pose.header.frame_id = 'map'
           pose.header.stamp = self.get_clock().now().to_msg()
           pose.pose.position.x = target['x']
           pose.pose.position.y = target['y']
           pose.pose.position.z = 0.0
           pose.pose.orientation.z = math.sin(target['theta']/2)
           pose.pose.orientation.w = math.cos(target['theta']/2)
           goal_msg.pose = pose
           
           self.action_client.wait_for_server()
           future = self.action_client.send_goal_async(goal_msg)
           future.add_done_callback(self.goal_done_callback)
   
       def goal_done_callback(self, future):
           result = future.result().get_result_async().result().result
           if result == 1:  # 成功到达
               self.get_logger().info(f'目标点 {self.target_index + 1} 到达!')
               self.target_index = (self.target_index + 1) % 3
               # 等待1秒后前往下一个点
               self.create_timer(1.0, self.navigate_to_target)

def main(args=None):
    rclpy.init(args=args)
    navigator = MultiPointNavigator()
    navigator.navigate_to_target()
    rclpy.spin(navigator)
    navigator.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
   ```

---

## 本章小结

本章我们全面学习了Gazebo+Nav2仿真导航的完整流程。从环境准备开始，我们安装了TurtleBot3相关功能包并启动了Gazebo仿真世界。接着学习了地图构建的两种方式：使用Cartographer实时建图和使用现成地图。然后详细介绍了地图配置、AMCL定位配置以及导航参数设置。最后通过代码演示了如何发送导航目标点，实现了机器人的自主导航。

通过本节的学习，你应该能够：
- 在Gazebo中启动TurtleBot3仿真环境
- 使用SLAM构建环境地图
- 配置Nav2导航系统的各个组件
- 通过代码实现目标点导航

---

## 参考资料

### 官方文档

1. Nav2 Documentation: <https://navigation.ros.org/>
2. TurtleBot3 Documentation: <https://emanual.robotis.com/docs/en/platform/turtlebot3/overview/>
3. Gazebo Tutorial: <https://gazebosim.org/docs>

### 相关资源

4. AMCL Parameters: <https://navigation.ros.org/configuration/packages/configuring-amcl.html>
5. Nav2 Controller: <https://navigation.ros.org/configuration/packages/configuring-controller-server.html>

---

## 下节预告

待补充...

---

*本章学习完成！建议大家多多动手实践，在仿真环境中熟练掌握导航系统的部署流程。*
