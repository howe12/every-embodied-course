# 11-3 MoveIt2运动规划与控制编程

> **前置课程**：05-5 MoveIt2框架基础与配置
> **后续课程**：05-7 机械臂视觉集成与协同控制

**作者**：霍海杰 | **联系方式**：howe12@126.com

---

> **前置说明**：本节是MoveIt2的实战编程篇，将在05-5的基础上深入讲解如何通过Python和C++编程接口实现机械臂的运动规划、控制与交互。我们将从基础的规划请求开始，逐步深入到复杂场景下的轨迹执行、碰撞检测优化、自定义规划器集成等高级主题，帮助你掌握MoveIt2编程的核心技能。

---

## 1. Python编程接口（MoveIt2 Servo）

MoveIt2提供了丰富的Python API，本节重点介绍MoveIt2 Servo（用于实时控制）和运动规划编程接口。

### 1.1 环境准备

首先确保已安装MoveIt2和相关依赖：

```bash
# Ubuntu 22.04 + ROS2 Humble
sudo apt install ros-humble-moveit ros-humble-panda-moveit-config
pip install moveit-py
```

对于模拟实验，我们将使用Panda机械臂（franka_description + panda_moveit_config）：

```bash
# 安装Panda模拟环境
sudo apt install ros-humble-franka-description ros-humble-panda-moveit-config
```

### 1.2 基础运动规划

使用MoveIt2 Python API实现基本的点对点运动规划：

```python
# panda_planning.py - Panda机械臂基础运动规划
import rclpy
from rclpy.node import Node
from moveit.planning import MoveItPy
from moveit.core.robot_state import RobotState
import math

class PandaPlanner(Node):
    def __init__(self):
        super().__init__('panda_planner')
        
        # 初始化MoveIt2
        self.panda = MoveItPy(node_name="panda")
        self.panda_arm = self.panda.get_planning_component("panda_arm")
        self.robot_model = self.panda.get_robot_model()
        
        self.get_logger().info('Panda planner initialized')

    def plan_to_joint_state(self, target_joints):
        """规划到指定关节角度"""
        # 获取当前机器人状态
        robot_state = RobotState(self.robot_model)
        
        # 设置目标关节位置
        robot_state.set_joint_group_positions("panda_arm", target_joints)
        
        # 配置规划请求
        self.panda_arm.set_start_state_to_current_state()
        self.panda_arm.set_goal_state(robot_state)
        
        # 设置规划参数
        plan = self.panda_arm.plan(
            planning_time=10.0,
            num_planning_attempts=10
        )
        
        return plan

    def plan_to_pose(self, target_pose, frame_id="panda_link8"):
        """规划到指定末端位姿"""
        robot_state = RobotState(self.robot_model)
        robot_state.set_to_default_values()
        
        # 设置目标位姿
        from geometry_msgs.msg import Pose
        pose_goal = Pose()
        pose_goal.position.x = target_pose[0]
        pose_goal.position.y = target_pose[1]
        pose_goal.position.z = target_pose[2]
        pose_goal.orientation.x = target_pose[3]
        pose_goal.orientation.y = target_pose[4]
        pose_goal.orientation.z = target_pose[5]
        pose_goal.orientation.w = target_pose[6]
        
        self.panda_arm.set_start_state_to_current_state()
        self.panda_arm.set_goal_state(pose=pose_goal, pose_link=frame_id)
        
        plan = self.panda_arm.plan(
            planning_time=10.0,
            num_planning_attempts=10
        )
        
        return plan

    def execute_plan(self, plan):
        """执行规划好的轨迹"""
        if plan:
            self.panda.execute(
                plan.trajectory,
                controllers=['panda_arm_controller']
            )
            self.get_logger().info('Plan executed successfully')
        else:
            self.get_logger().error('No valid plan to execute')

def main(args=None):
    rclpy.init(args=args)
    planner = PandaPlanner()
    
    # 示例：规划到特定关节位置
    # Panda机械臂7个关节的目标位置
    home_joints = [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785]
    
    planner.get_logger().info('Planning to home position...')
    plan = planner.plan_to_joint_state(home_joints)
    
    if plan:
        planner.get_logger().info(f'Plan found! Trajectory: {len(plan.trajectory.joint_trajectory.points)} points')
        planner.execute_plan(plan)
    else:
        planner.get_logger().error('Planning failed')
    
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

### 1.3 MoveIt2 Servo实时控制

MoveIt2 Servo是用于实时控制的核心组件，支持通过发送Twist（速度）或Pose（位置）命令来实时控制机械臂：

```python
# panda_servo.py - Panda机械臂实时控制
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, PoseStamped
from moveit.servo import Servo
import math

class PandaServo(Node):
    def __init__(self):
        super().__init__('panda_servo')
        
        # 初始化Servo
        self.servo = Servo(self, 'panda')
        
        # 创建订阅者
        self.twist_sub = self.create_subscription(
            Twist, '/servo_node/delta_twist_cmds', self.twist_callback, 1
        )
        
        # 创建发布者（末端位姿目标）
        self.pose_pub = self.create_publisher(
            PoseStamped, '/servo_node/pose_goal_cmds', 1
        )
        
        self.is_servoing = False
        
        # 启动Servo
        self.start_servo()
        
        self.get_logger().info('Panda Servo initialized')

    def start_servo(self):
        """启动Servo服务"""
        self.servo.start()
        self.is_servoing = True
        self.get_logger().info('Servo started')

    def stop_servo(self):
        """停止Servo"""
        self.servo.stop()
        self.is_servoing = False
        self.get_logger().info('Servo stopped')

    def twist_callback(self, twist):
        """处理Twist命令（笛卡尔空间速度控制）"""
        if not self.is_servoing:
            return
        
        # Twist命令包含linear和angular分量
        # linear: x, y, z方向的线速度
        # angular: x, y, z方向的角速度
        
        self.get_logger().debug(
            f'Twist received: linear=({twist.linear.x}, {twist.linear.y}, {twist.linear.z}), '
            f'angular=({twist.angular.x}, {twist.angular.y}, {twist.angular.z})'
        )

    def send_pose_goal(self, x, y, z, ox=0, oy=0, oz=0, ow=1):
        """发送末端位姿目标"""
        pose = PoseStamped()
        pose.header.frame_id = 'panda_link0'
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = z
        pose.pose.orientation.x = ox
        pose.pose.orientation.y = oy
        pose.pose.orientation.z = oz
        pose.pose.orientation.w = ow
        
        self.pose_pub.publish(pose)

def main(args=None):
    rclpy.init(args=args)
    servo_node = PandaServo()
    
    try:
        rclpy.spin(servo_node)
    except KeyboardInterrupt:
        pass
    finally:
        servo_node.stop_servo()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
```

### 1.4 订阅Joystick控制

通过游戏手柄实现机械臂的实时控制：

```python
# joystick_control.py - 手柄控制Panda机械臂
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from geometry_msgs.msg import Twist

class JoystickController(Node):
    def __init__(self):
        super().__init__('joystick_controller')
        
        # 订阅手柄输入
        self.joy_sub = self.create_subscription(
            Joy, '/joy', self.joy_callback, 10
        )
        
        # 发布Twist命令
        self.twist_pub = self.create_publisher(
            Twist, '/servo_node/delta_twist_cmds', 10
        )
        
        # 控制参数
        self.linear_scale = 0.1  # 线速度缩放
        self.angular_scale = 0.5  # 角速度缩放
        
        self.get_logger().info('Joystick controller started')

    def joy_callback(self, joy):
        """处理手柄输入"""
        twist = Twist()
        
        # 左摇杆：机械臂基座XYZ移动
        # axes[0]: 左摇杆X (左右)
        # axes[1]: 左摇杆Y (前后)
        twist.linear.x = joy.axes[0] * self.linear_scale
        twist.linear.y = joy.axes[1] * self.linear_scale
        
        # 右摇杆：机械臂上下和旋转
        # axes[3]: 右摇杆Y (上下)
        # axes[2]: 右摇杆X (旋转)
        twist.linear.z = -joy.axes[3] * self.linear_scale
        twist.angular.z = -joy.axes[2] * self.angular_scale
        
        self.twist_pub.publish(twist)

def main(args=None):
    rclpy.init(args=args)
    controller = JoystickController()
    rclpy.spin(controller)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

---

## 2. C++编程接口

C++ API提供更高的性能和实时性，适用于对延迟敏感的应用场景。

### 2.1 基础运动规划（C++）

```cpp
// panda_planner.cpp - C++运动规划示例
#include <rclcpp/rclcpp.hpp>
#include <moveit/move_group_interface/move_group_interface.h>
#include <geometry_msgs/msg/pose.hpp>
#include <vector>

class PandaPlanner : public rclcpp::Node
{
public:
    PandaPlanner() : Node("panda_planner")
    {
        // 初始化MoveGroup接口
        move_group_ = std::make_shared<moveit::planning_interface::MoveGroupInterface>(
            std::shared_ptr<rclcpp::Node>(this), "panda_arm"
        );
        
        // 获取规划组信息
        planning_group_name_ = move_group_->getName();
        end_effector_link_ = move_group_->getEndEffectorLink();
        
        RCLCPP_INFO(this->get_logger(), "Panda planner initialized");
    }

    bool plan_to_joint_state(const std::vector<double>& joint_positions)
    {
        // 设置目标关节位置
        move_group_->setJointValueTarget(joint_positions);
        
        // 创建规划
        moveit::planning_interface::MoveGroupInterface::Plan plan;
        
        bool success = static_cast<bool>(
            move_group_->plan(plan)
        );
        
        if (success) {
            RCLCPP_INFO(this->get_logger(), "Planning successful!");
            
            // 执行轨迹
            move_group_->execute(plan);
        } else {
            RCLCPP_ERROR(this->get_logger(), "Planning failed!");
        }
        
        return success;
    }

    bool plan_to_pose(const geometry_msgs::msg::Pose& target_pose)
    {
        // 设置目标位姿
        move_group_->setPoseTarget(target_pose);
        
        // 创建规划
        moveit::planning_interface::MoveGroupInterface::Plan plan;
        
        bool success = static_cast<bool>(
            move_group_->plan(plan)
        );
        
        if (success) {
            RCLCPP_INFO(this->get_logger(), "Pose planning successful!");
        } else {
            RCLCPP_ERROR(this->get_logger(), "Pose planning failed!");
        }
        
        return success;
    }

    void set_max_velocity_scaling(double scale)
    {
        move_group_->setMaxVelocityScalingFactor(scale);
    }

    void set_max_acceleration_scaling(double scale)
    {
        move_group_->setMaxAccelerationScalingFactor(scale);
    }

private:
    std::shared_ptr<moveit::planning_interface::MoveGroupInterface> move_group_;
    std::string planning_group_name_;
    std::string end_effector_link_;
};

int main(int argc, char** argv)
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<PandaPlanner>();
    
    // 设置速度和加速度限制
    node->set_max_velocity_scaling(0.5);
    node->set_max_acceleration_scaling(0.5);
    
    // 示例：规划到特定关节位置
    std::vector<double> home_joint = {0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785};
    node->plan_to_joint_state(home_joint);
    
    // 示例：规划到特定位姿
    geometry_msgs::msg::Pose target_pose;
    target_pose.position.x = 0.4;
    target_pose.position.y = 0.0;
    target_pose.position.z = 0.5;
    target_pose.orientation.x = 0.0;
    target_pose.orientation.y = 0.0;
    target_pose.orientation.z = 0.0;
    target_pose.orientation.w = 1.0;
    
    node->plan_to_pose(target_pose);
    
    rclcpp::shutdown();
    return 0;
}
```

### 2.2 CMakeLists.txt配置

```cmake
cmake_minimum_required(VERSION 3.8)
project(panda_planner)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(moveit_ros_planning_interface REQUIRED)
find_package(geometry_msgs REQUIRED)

# 添加可执行文件
add_executable(panda_planner src/panda_planner.cpp)

# 设置依赖
ament_target_dependencies(panda_planner
  rclcpp
  moveit_ros_planning_interface
  geometry_msgs
)

# 安装目标
install(TARGETS panda_planner
  DESTINATION lib/${PROJECT_NAME})

ament_package()
```

### 2.3 规划场景管理

C++中创建和管理规划场景：

```cpp
// planning_scene_manager.cpp - 规划场景管理
#include <rclcpp/rclcpp.hpp>
#include <moveit/planning_scene_interface/planning_scene_interface.h>
#include <moveit/move_group_interface/move_group_interface.h>
#include <geometric_shapes/shapes.h>

class PlanningSceneManager : public rclcpp::Node
{
public:
    PlanningSceneManager() : Node("planning_scene_manager")
    {
        // 创建规划场景接口
        planning_scene_interface_ = std::make_shared<
            moveit::planning_interface::PlanningSceneInterface
        >();
        
        move_group_ = std::make_shared<moveit::planning_interface::MoveGroupInterface>(
            std::shared_ptr<rclcpp::Node>(this), "panda_arm"
        );
        
        RCLCPP_INFO(this->get_logger(), "Planning scene manager initialized");
    }

    void add_box_obstacle(double x, double y, double z, 
                          double size_x, double size_y, double size_z,
                          const std::string& name)
    {
        // 创建障碍物
        moveit_msgs::msg::CollisionObject collision_object;
        collision_object.header.frame_id = move_group_->getPlanningFrame();
        collision_object.header.stamp = this->now();
        collision_object.id = name;
        collision_object.operation = collision_object.ADD;
        
        // 设置形状
        shape_msgs::msg::SolidPrimitive box;
        box.type = box.BOX;
        box.dimensions = {size_x, size_y, size_z};
        
        geometry_msgs::msg::Pose box_pose;
        box_pose.position.x = x;
        box_pose.position.y = y;
        box_pose.position.z = z;
        box_pose.orientation.w = 1.0;
        
        collision_object.primitives.push_back(box);
        collision_object.primitive_poses.push_back(box_pose);
        
        // 添加到规划场景
        std::vector<moveit_msgs::msg::CollisionObject> objects = {collision_object};
        planning_scene_interface_->applyCollisionObjects(objects);
        
        RCLCPP_INFO(this->get_logger(), "Added box obstacle: %s", name.c_str());
    }

    void add_attached_object(const std::string& object_name,
                             const std::string& link_name)
    {
        // 创建附加物体
        moveit_msgs::msg::AttachedCollisionObject attached_object;
        attached_object.object.header.frame_id = link_name;
        attached_object.object.header.stamp = this->now();
        attached_object.object.id = object_name;
        attached_object.link_name = link_name;
        
        // 设置物体形状（圆柱体）
        shape_msgs::msg::SolidPrimitive cylinder;
        cylinder.type = cylinder.CYLINDER;
        cylinder.dimensions = {0.02, 0.1};  // 半径, 高度
        
        geometry_msgs::msg::Pose cylinder_pose;
        cylinder_pose.position.x = 0.0;
        cylinder_pose.position.y = 0.0;
        cylinder_pose.position.z = 0.05;
        cylinder_pose.orientation.w = 1.0;
        
        attached_object.object.primitives.push_back(cylinder);
        attached_object.object.primitive_poses.push_back(cylinder_pose);
        
        // 应用
        planning_scene_interface_->applyAttachedCollisionObject(attached_object);
        
        RCLCPP_INFO(this->get_logger(), "Attached object: %s", object_name.c_str());
    }

    void remove_obstacle(const std::string& name)
    {
        std::vector<std::string> object_ids = {name};
        planning_scene_interface_->removeCollisionObjects(object_ids);
        
        RCLCPP_INFO(this->get_logger(), "Removed obstacle: %s", name.c_str());
    }

private:
    std::shared_ptr<moveit::planning_interface::PlanningSceneInterface> planning_scene_interface_;
    std::shared_ptr<moveit::planning_interface::MoveGroupInterface> move_group_;
};

int main(int argc, char** argv)
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<PlanningSceneManager>();
    
    // 添加障碍物
    node->add_box_obstacle(0.5, 0.0, 0.25, 0.1, 0.5, 0.5, "table");
    node->add_box_obstacle(0.3, 0.3, 0.4, 0.1, 0.1, 0.1, "obstacle1");
    
    // 附加物体到末端
    node->add_attached_object("gripper_object", "panda_link8");
    
    rclcpp::shutdown();
    return 0;
}
```

---

## 3. 运动规划实战

本节通过三个实战项目，综合运用MoveIt2的运动规划能力。

### 3.1 项目一：机械臂抓取放置

实现一个完整的抓取-放置流程：

```python
# pick_and_place.py - 抓取放置任务
import rclpy
from rclpy.node import Node
from moveit.planning import MoveItPy
from moveit.core.robot_state import RobotState
from geometry_msgs.msg import Pose
import time

class PickAndPlace(Node):
    def __init__(self):
        super().__init__('pick_and_place')
        
        # 初始化MoveIt2
        self.panda = MoveItPy(node_name="panda")
        self.panda_arm = self.panda.get_planning_component("panda_arm")
        self.panda_hand = self.panda.get_planning_component("panda_hand")
        self.robot_model = self.panda.get_robot_model()
        
        # 抓取参数
        self.grasp_pose = [0.3, 0.0, 0.15, 0.0, 1.0, 0.0, 0.0]  # 抓取位姿
        self.pre_grasp_pose = [0.4, 0.0, 0.2, 0.0, 1.0, 0.0, 0.0]  # 预抓取
        self.lift_pose = [0.3, 0.0, 0.3, 0.0, 1.0, 0.0, 0.0]  # 提升
        self.place_pose = [-0.3, 0.0, 0.15, 0.0, 1.0, 0.0, 0.0]  # 放置
        
        self.get_logger().info('Pick and place node initialized')

    def open_gripper(self):
        """打开夹爪"""
        robot_state = RobotState(self.robot_model)
        robot_state.set_joint_group_positions("panda_hand", [0.04, 0.04])
        
        self.panda_hand.set_start_state_to_current_state()
        self.panda_hand.set_goal_state(robot_state)
        
        plan = self.panda_hand.plan(planning_time=5.0)
        
        if plan:
            self.panda.execute(plan.trajectory)
            self.get_logger().info('Gripper opened')

    def close_gripper(self):
        """关闭夹爪"""
        robot_state = RobotState(self.robot_model)
        robot_state.set_joint_group_positions("panda_hand", [0.0, 0.0])
        
        self.panda_hand.set_start_state_to_current_state()
        self.panda_hand.set_goal_state(robot_state)
        
        plan = self.panda_hand.plan(planning_time=5.0)
        
        if plan:
            self.panda.execute(plan.trajectory)
            self.get_logger().info('Gripper closed')

    def move_to_pose(self, pose):
        """移动到指定位姿"""
        pose_goal = Pose()
        pose_goal.position.x = pose[0]
        pose_goal.position.y = pose[1]
        pose_goal.position.z = pose[2]
        pose_goal.orientation.x = pose[3]
        pose_goal.orientation.y = pose[4]
        pose_goal.orientation.z = pose[5]
        pose_goal.orientation.w = pose[6]
        
        self.panda_arm.set_start_state_to_current_state()
        self.panda_arm.set_goal_state(pose=pose_goal, pose_link="panda_link8")
        
        plan = self.panda_arm.plan(planning_time=10.0, num_planning_attempts=5)
        
        if plan:
            self.panda.execute(plan.trajectory)
            self.get_logger().info(f'Moved to pose: {pose[:3]}')
            return True
        else:
            self.get_logger().error(f'Failed to move to pose: {pose[:3]}')
            return False

    def move_to_joints(self, joints):
        """移动到指定关节位置"""
        robot_state = RobotState(self.robot_model)
        robot_state.set_joint_group_positions("panda_arm", joints)
        
        self.panda_arm.set_start_state_to_current_state()
        self.panda_arm.set_goal_state(robot_state)
        
        plan = self.panda_arm.plan(planning_time=10.0)
        
        if plan:
            self.panda.execute(plan.trajectory)
            self.get_logger().info(f'Moved to joints: {joints}')

    def execute_pick_and_place(self):
        """执行完整的抓取-放置流程"""
        
        # 步骤1：移动到预抓取位置
        self.get_logger().info('Step 1: Moving to pre-grasp pose')
        if not self.move_to_pose(self.pre_grasp_pose):
            return False
        time.sleep(0.5)
        
        # 步骤2：移动到抓取位置
        self.get_logger().info('Step 2: Moving to grasp pose')
        if not self.move_to_pose(self.grasp_pose):
            return False
        time.sleep(0.5)
        
        # 步骤3：关闭夹爪
        self.get_logger().info('Step 3: Closing gripper')
        self.close_gripper()
        time.sleep(0.5)
        
        # 步骤4：提升
        self.get_logger().info('Step 4: Lifting')
        if not self.move_to_pose(self.lift_pose):
            return False
        time.sleep(0.5)
        
        # 步骤5：移动到放置位置上方
        place_above = self.place_pose[:]
        place_above[2] += 0.15
        self.get_logger().info('Step 5: Moving above place pose')
        if not self.move_to_pose(place_above):
            return False
        time.sleep(0.5)
        
        # 步骤6：移动到放置位置
        self.get_logger().info('Step 6: Moving to place pose')
        if not self.move_to_pose(self.place_pose):
            return False
        time.sleep(0.5)
        
        # 步骤7：打开夹爪
        self.get_logger().info('Step 7: Opening gripper')
        self.open_gripper()
        
        # 步骤8：返回安全位置
        home = [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785]
        self.move_to_joints(home)
        
        self.get_logger().info('Pick and place completed!')
        return True

def main(args=None):
    rclpy.init(args=args)
    task = PickAndPlace()
    
    # 打开夹爪初始状态
    task.open_gripper()
    
    # 执行抓取放置任务
    task.execute_pick_and_place()
    
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

### 3.2 项目二：轨迹平滑与优化

使用MoveIt2的轨迹处理功能优化运动轨迹：

```python
# trajectory_optimization.py - 轨迹优化
import rclpy
from rclpy.node import Node
from moveit.planning import MoveItPy

class TrajectoryOptimizer(Node):
    def __init__(self):
        super().__init__('trajectory_optimizer')
        
        self.panda = MoveItPy(node_name="panda")
        self.panda_arm = self.panda.get_planning_component("panda_arm")
        self.robot_model = self.panda.get_robot_model()
        
    def plan_with_time_parameterization(self):
        """带时间参数化的规划"""
        
        # 设置规划参数
        self.panda_arm.set_start_state_to_current_state()
        
        # 设置目标（示例：设置关节目标）
        # ...
        
        plan = self.panda_arm.plan(planning_time=10.0)
        
        if plan:
            # 获取原始轨迹
            trajectory = plan.trajectory
            
            # 获取机器人模型
            robot_model = self.panda.get_robot_model()
            
            # 时间参数化（使用MoveIt2内置方法）
            # 注意：实际参数化需要根据轨迹点数量和时间约束计算
            
            self.get_logger().info(f'Planned trajectory with {len(trajectory.joint_trajectory.points)} points')
            
            return trajectory
        
        return None

def main(args=None):
    rclpy.init(args=args)
    optimizer = TrajectoryOptimizer()
    
    # 执行优化规划
    optimized_trajectory = optimizer.plan_with_time_parameterization()
    
    if optimized_trajectory:
        # 执行优化后的轨迹
        optimizer.panda.execute(optimized_trajectory)
    
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

### 3.3 项目三：碰撞检测与规避

实现基于实时碰撞检测的安全运动：

```python
# collision_avoidance.py - 碰撞检测与规避
import rclpy
from rclpy.node import Node
from moveit.planning import MoveItPy
from moveit.core.robot_state import RobotState

class CollisionAvoider(Node):
    def __init__(self):
        super().__init__('collision_avoider')
        
        self.panda = MoveItPy(node_name="panda")
        self.panda_arm = self.panda.get_planning_component("panda_arm")
        self.robot_model = self.panda.get_robot_model()
        
        self.get_logger().info('Collision avoider initialized')

    def check_collision(self, joint_positions):
        """检查指定关节位置是否有碰撞"""
        
        # 创建机器人状态
        robot_state = RobotState(self.robot_model)
        robot_state.set_joint_group_positions("panda_arm", joint_positions)
        
        # 检查碰撞
        collision_result = robot_state.check_collision()
        
        return collision_result.collision

    def plan_with_collision_check(self, target_joints):
        """带碰撞检查的规划"""
        
        # 创建目标状态
        robot_state = RobotState(self.robot_model)
        robot_state.set_joint_group_positions("panda_arm", target_joints)
        
        self.panda_arm.set_start_state_to_current_state()
        self.panda_arm.set_goal_state(robot_state)
        
        # 规划（MoveIt2默认启用碰撞检测）
        plan = self.panda_arm.plan(
            planning_time=5.0,
            num_planning_attempts=3
        )
        
        return plan

    def reactive_collision_avoidance(self):
        """反应式碰撞规避"""
        
        # 使用更鲁棒的规划器（RRT-Connect）
        self.panda_arm.set_planning_pipeline("ompl")
        self.panda_arm.set_planner_id("RRTConnectkConfigDefault")
        
        plan = self.panda_arm.plan(planning_time=10.0)
        
        return plan

def main(args=None):
    rclpy.init(args=args)
    avoider = CollisionAvoider()
    
    # 检查特定位置是否有碰撞
    test_joints = [0.5, -0.5, 0.0, -2.0, 0.0, 1.5, 0.0]
    
    has_collision = avoider.check_collision(test_joints)
    
    if has_collision:
        avoider.get_logger().warn('Target position has collision!')
        
        # 尝试使用鲁棒规划器
        avoider.get_logger().info('Trying RRT-Connect planner...')
        plan = avoider.reactive_collision_avoidance()
        
        if plan:
            avoider.get_logger().info('Alternative plan found!')
            avoider.panda.execute(plan.trajectory)
    else:
        avoider.get_logger().info('Target position is collision-free')
        
        # 执行规划
        plan = avoider.plan_with_collision_check(test_joints)
        if plan:
            avoider.panda.execute(plan.trajectory)
    
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

---

## 4. 自定义规划器集成

MoveIt2支持集成自定义规划算法。

### 4.1 OMPL规划器配置

MoveIt2默认使用OMPL作为规划库，可以配置不同的规划器：

```yaml
# moveit_planning.yaml
planning_plugin: ompl_interface/OMPLPlanner

request_adapters: >-
  default_planning_request_adapters/FixWorkspaceBounds
  default_planning_request_adapters/FixStartStateBounds
  default_planning_request_adapters/FixStartStateCollision
  default_planning_request_adapters/AddTimeOptimalParameterization
  default_planning_request_adapters/ValidateWorkspaceBounds

# OMPL规划器配置
ompl:
  planning_pipelines:
    panda_arm:
      planner_configs:
        - SBLkConfigDefault
        - ESTkConfigDefault
        - RRTkConfigDefault
        - RRTConnectkConfigDefault
        - PRMkConfigDefault
        - PRMstarkConfigDefault
        - AnytimePathShortening

      default_planner_config: RRTConnectkConfigDefault
```

### 4.2 常用规划器选择

| 规划器 | 特点 | 适用场景 |
|--------|------|----------|
| RRTConnect | 快速探索，快速收敛 | 通用场景 |
| PRM | 概率路线图 | 多查询环境 |
| SBL | 单-query双向 | 高维空间 |
| BIT* | 基于优化的搜索 | 复杂约束 |
| AnytimePathShortening | 多次规划取最优 | 追求最优轨迹 |

### 4.3 使用CHOMP（基于优化的规划）

CHOMP是梯度优化规划器，适合平滑轨迹：

```python
# chomp_planning.py - 使用CHOMP规划器
import rclpy
from moveit.planning import MoveItPy

def plan_with_chomp():
    rclpy.init()
    panda = MoveItPy(node_name="panda")
    panda_arm = panda.get_planning_component("panda_arm")
    
    # 设置使用CHOMP规划器
    panda_arm.set_planning_pipeline("chomp")
    
    # 设置目标（省略...）
    # panda_arm.set_goal_state(...)
    
    # 规划
    plan = panda_arm.plan(planning_time=10.0)
    
    if plan:
        panda.execute(plan.trajectory)
    
    rclpy.shutdown()

if __name__ == '__main__':
    plan_with_chomp()
```

---

## 5. 控制器集成

MoveIt2通过Controller Interface与底层硬件通信。

### 5.1 MoveIt2控制器配置

```yaml
# moveit_controllers.yaml
controller_names:
  - panda_arm_controller
  - panda_hand_controller

panda_arm_controller:
  type: follow_trajectory_controller/FollowTrajectoryController
  joints:
    - panda_joint1
    - panda_joint2
    - panda_joint3
    - panda_joint4
    - panda_joint5
    - panda_joint6
    - panda_joint7
  command_interfaces:
    - position
  state_interfaces:
    - position
    - velocity

panda_hand_controller:
  type: follow_trajectory_controller/FollowTrajectoryController
  joints:
    - panda_finger_joint1
    - panda_finger_joint2
  command_interfaces:
    - position
```

### 5.2 执行器配置

```python
# controller_manager.py - 控制器管理
import rclpy
from rclpy.node import Node
from controller_manager_msgs.srv import ListControllers, SwitchController

class ControllerManager(Node):
    def __init__(self):
        super().__init__('controller_manager')
        
        # 创建服务客户端
        self.list_controllers_client = self.create_client(
            ListControllers, '/controller_manager/list_controllers'
        )
        self.switch_controller_client = self.create_client(
            SwitchController, '/controller_manager/switch_controller'
        )
        
    def list_controllers(self):
        """列出所有控制器"""
        request = ListControllers.Request()
        future = self.list_controllers_client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        
        return future.result().controller

    def activate_controller(self, controller_name):
        """激活指定控制器"""
        request = SwitchController.Request()
        request.activate_controllers = [controller_name]
        request.strictness = 2  # STRICT
        
        future = self.switch_controller_client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        
        return future.result().ok

def main(args=None):
    rclpy.init(args=args)
    cm = ControllerManager()
    
    # 列出控制器
    controllers = cm.list_controllers()
    for c in controllers:
        print(f"{c.name}: {c.state}")
    
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

---

## 6. 真实机械臂控制

将模拟环境中的代码迁移到真实机械臂。

### 6.1 真实硬件接口

```python
# real_robot_control.py - 真实机械臂控制
import rclpy
from moveit.planning import MoveItPy

class RealRobotController:
    """真实机械臂控制器"""
    
    def __init__(self, robot_name="panda"):
        rclpy.init()
        
        # 连接真实机械臂
        self.panda = MoveItPy(node_name=f"{robot_name}_moveit")
        
        # 获取规划组件
        self.arm = self.panda.get_planning_component(f"{robot_name}_arm")
        
        print(f"Connected to {robot_name}")
    
    def execute_safe(self, plan):
        """安全执行轨迹"""
        # 在执行前再次检查
        # 注意：真实环境中应该有额外的安全检查
        
        self.panda.execute(
            plan.trajectory,
            controllers=[f'{robot_name}_arm_controller']
        )
    
    def stop(self):
        """紧急停止"""
        self.panda.stop()

# 使用示例
if __name__ == '__main__':
    controller = RealRobotController("panda")
    
    # 规划并执行
    # ... (规划代码)
    
    # 安全执行
    # controller.execute_safe(plan)
    
    rclpy.shutdown()
```

### 6.2 安全注意事项

1. **硬件急停**：始终确保急停按钮可用
2. **速度限制**：初始阶段设置较低的速度限制
3. **碰撞检测**：启用碰撞检测功能
4. **工作空间限制**：配置工作空间边界
5. **关节限位**：确保关节角度在安全范围内

```python
# safety_settings.py - 安全设置
class SafetySettings:
    """安全设置配置"""
    
    # 速度缩放
    MAX_VELOCITY_SCALE = 0.3  # 初始30%速度
    
    # 加速度缩放
    MAX_ACCELERATION_SCALE = 0.3
    
    # 工作空间边界
    WORKSPACE_BOUNDS = {
        'x_min': 0.2, 'x_max': 0.6,
        'y_min': -0.4, 'y_max': 0.4,
        'z_min': 0.1, 'z_max': 0.6
    }
    
    # 关节限位
    JOINT_LIMITS = {
        'panda_joint1': [-2.8973, 2.8973],
        'panda_joint2': [-1.7628, 1.7628],
        'panda_joint3': [-2.8973, 2.8973],
        'panda_joint4': [-0.0698, 3.7525],
        'panda_joint5': [-2.8973, 2.8973],
        'panda_joint6': [-0.0175, 3.7525],
        'panda_joint7': [-2.8973, 2.8973]
    }
```

---

## 练习题

### 选择题

1. MoveIt2 Python API中，用于创建运动规划器的类是什么？
   - A) `MoveGroupInterface`
   - B) `MoveItPy`
   - C) `RobotModel`
   - D) `PlanningScene`
   
   **答案：B**。`MoveItPy`是MoveIt2 Python的核心类，用于加载机器人模型和进行运动规划。

2. MoveIt2 Servo用于什么场景？
   - A) 离线轨迹规划
   - B) 实时速度/位置控制
   - C) 碰撞检测
   - D) 路径优化
   
   **答案：B**。MoveIt2 Servo是用于实时控制的组件，支持通过Twist命令进行速度控制或Pose命令进行位置控制。

3. 哪个规划器适合追求最优轨迹？
   - A) RRTConnect
   - B) RRT
   - C) AnytimePathShortening
   - D) EST
   
   **答案：C**。AnytimePathShortening通过多次规划并取最优解，适合追求高质量轨迹的场景。

### 实践题

4. 修改抓取放置示例，添加一个中间路径点，使轨迹更加平滑。
   
   **提示**：在抓取位置和提升位置之间添加一个中间点（对角线方向），使用位姿列表进行规划。

5. 配置MoveIt2使用不同的规划器（OMPL中的EST和PRM），比较它们的规划时间。
   
   **提示**：使用`planning_component.set_planner_id()`切换规划器。

---

## 本章小结

本章我们深入学习了MoveIt2的运动规划与控制编程。Python编程接口部分，我们掌握了基础运动规划、Servo实时控制、手柄控制等方法。C++编程接口部分，我们学习了高效的C++实现方式以及规划场景管理。实战项目部分，我们通过抓取放置、轨迹优化、碰撞规避三个项目综合运用了所学知识。最后，我们学习了自定义规划器集成、控制器配置以及真实机械臂控制的方法。

MoveIt2是ROS2生态中功能最强大的运动规划框架，熟练掌握其编程接口将帮助你完成各种复杂的机器人操作任务。

---

## 参考资料

### 官方文档

1. MoveIt2 Documentation: <https://moveit.picknik.ai/main/doc/tutorials/getting_started/getting_started.html>
2. MoveIt2 Python API: <https://docs.ros.org/en/humble/p/moveit_ros/planning_interface/doc.html>
3. MoveIt2 Servo: <https://moveit.picknik.ai/main/doc/examples/realtime_servo/realtime_servo.html>

### 规划器相关

4. OMPL Planners: <https://ompl.kavrakilab.org/planners.html>
5. CHOMP: <https://doi.org/10.1109/ICRA.2011.5980379>

### 机械臂相关

6. Franka Emika Panda: <https://frankaemika.github.io/>
7. MoveIt2 Servo Configuration: <https://moveit.picknik.ai/main/doc/examples/realtime_servo/realtime_servo.html#servo-configuration>

---

## 下节预告

下一节我们将学习**05-7 机械臂视觉集成与协同控制**，了解如何将视觉感知与机械臂控制相结合，实现基于视觉的目标识别、抓取策略等功能。

---

*本章学习完成！MoveIt2是机械臂控制的核心框架，建议大家多加练习，熟练掌握运动规划的编程方法。*