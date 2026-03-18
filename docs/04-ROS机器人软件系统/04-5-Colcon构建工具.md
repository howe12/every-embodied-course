# 04-5 Colcon构建工具 Colcon构建工具深度应用

**作者**：霍海杰 | **联系方式**：howe12@126.com

---

> **前置说明**：在上一节中，我们了解了ROS2工作空间的基本结构，并完成了第一个功能包的编译。本节将深入学习ROS2的构建工具——colcon。colcon是ROS2生态中的核心构建工具，相比ROS1的catkin_make，它提供了更强大的功能和更灵活的配置选项。

---

## 1. Colcon核心命令

### 1.1 colcon build——编译（最常用）

colcon build是ROS2最常用的编译命令，它会编译src目录下的所有功能包。

```bash
# 编译整个工作空间
colcon build

# 编译时显示详细输出
colcon build --event-handlers console_direct+

# 只编译指定包（加快编译速度）
colcon build --packages-select my_package
```

### 1.2 环境配置（每次打开新终端必须执行）

```bash
# 进入工作空间
cd ~/ros2_ws

# 加载环境（必须！否则找不到包）
source install/setup.bash

# 建议添加到.bashrc（只执行一次）
echo "source ~/ros2_ws/install/setup.bash" >> ~/.bashrc
```

> **⚠️ 重要**：每次打开新终端或重新编译后，都需要执行source命令加载环境。

### 1.3 colcon test——测试

```bash
# 运行所有测试
colcon test

# 查看测试结果
colcon test-result
```

### 1.4 清理编译产物

```bash
# 清理整个工作空间（解决编译问题时常用）
colcon clean
```

---

## 2. 开发常用技巧

### 2.1 符号链接安装（开发时强烈推荐）

--symlink-install使用符号链接而不是复制文件的方式来安装编译产物。

```bash
# 使用符号链接安装（推荐开发时使用）
colcon build --symlink-install
```

> **⭐ 优点**：
> - 修改源代码后**不需要重新编译**，直接运行的就是最新代码
> - 节省磁盘空间
> - 开发调试效率大幅提升

![符号链接安装示意](./images/symlink_install.jpg)
*图注：符号链接安装 vs 传统安装*

> **⚠️ 注意**：某些包（如消息生成）可能不支持符号链接安装，此时需要用回普通安装方式。

---

## 3. Python包 vs C++包对比

> **⭐ 本节重点**：理解两种包的区别是ROS2开发的基础

ROS2支持Python和C++两种语言编写节点，它们的区别如下：

| 特性 | Python包 | C++包 |
|------|----------|-------|
| **构建类型** | ament_python | ament_cmake |
| **编译速度** | 快（解释型） | 稍慢（编译型） |
| **运行性能** | 稍慢 | 快 |
| **适用场景** | 快速原型、工具脚本 | 性能敏感场景 |

### 3.1 Python包示例

```
my_python_pkg/
├── my_python_pkg/
│   ├── __init__.py
│   └── my_node.py
├── package.xml
├── setup.py
└── setup.cfg
```

```python
# my_node.py
import rclpy
from rclpy.node import Node

class MyNode(Node):
    def __init__(self):
        super().__init__('my_node')
        self.get_logger().info('Python节点启动')

def main(args=None):
    rclpy.init(args=args)
    node = MyNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

### 3.2 C++包示例

```
my_cpp_pkg/
├── src/
│   └── my_node.cpp
├── include/
├── CMakeLists.txt
└── package.xml
```

```cpp
// my_node.cpp
#include <rclcpp/rclcpp.hpp>

class MyNode : public rclcpp::Node
{
public:
    MyNode() : Node("my_node")
    {
        RCLCPP_INFO(this->get_logger(), "C++节点启动");
    }
};

int main(int argc, char * argv[])
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<MyNode>());
    rclcpp::shutdown();
    return 0;
}
```

### 3.3 编译命令

```bash
# 编译Python包
colcon build --packages-select my_python_pkg

# 编译C++包
colcon build --packages-select my_cpp_pkg

# 两者可以同时编译
colcon build
```

---

## 4. 依赖管理

### 4.1 rosdep自动安装依赖

rosdep可以自动安装功能包所需的系统依赖：

```bash
# 安装工作空间所有包的依赖（首次编译前必须执行）
cd ~/ros2_ws
rosdep install --from-paths src --ignore-src -r -y
```

### 4.2 手动安装依赖

```bash
# 安装ROS2核心依赖
sudo apt install ros-humble-rclcpp ros-humble-std-msgs
```

---

## 5. 进阶技巧（了解即可）

### 5.1 并行编译

```bash
# 使用4个并行任务编译
colcon build --parallel-workers 4
```

### 5.2 编译类型选择

```bash
# Debug模式（包含调试信息，便于调试）
colcon build --cmake-args -DCMAKE_BUILD_TYPE=Debug

# Release模式（优化后运行更快）
colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release
```

---

## 本章小结

本章我们学习了colcon构建工具的核心用法。

**必须掌握的重点**：
- `colcon build` - 基本编译命令
- `source install/setup.bash` - 环境配置（每次新终端必执行）
- `--symlink-install` - 符号链接安装，开发时强烈推荐

**了解即可的内容**：
- 并行编译
- Debug/Release模式选择

---

## 思考与练习

1. ⭐ **动手练一练**：使用`--symlink-install`选项编译一个包，修改代码后验证不需要重新编译。
2. ⭐ **动手练一练**：创建一个Python包和一个C++包，分别编译运行。
3. 想一想：什么时候应该用Debug模式？什么时候用Release模式？

---

## 参考资料

1. Colcon Documentation: <https://colcon.readthedocs.io/>
2. ROS2 Build Tools: <https://docs.ros.org/en/rolling/Tutorials/Colcon-Tutorial.html>

---

*下一节我们将学习"2.3 开发工具链与调试技巧"，掌握VSCode配置和日志系统的使用。*
