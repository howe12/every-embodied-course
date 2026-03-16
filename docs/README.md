<div align="center">

  # Every Embodied Course
  
  ## ROS2机器人仿真课程

  > 本课程围绕 [datawhalechina/every-embodied](https://github.com/datawhalechina/every-embodied) 开展
  > 
  > 仅需Python基础，从0构建自己的具身智能机器人；从0逐步构建VLA/OpenVLA/SmolVLA/Pi0，深入理解具身智能

  <p align="center">
    📌 课程主页 · ✨ 学习路线 · 🤖 实践项目
  </p>

  <p align="center">
      <a href="https://github.com/howe12/every-embodied-course/stargazers" target="_blank">
          <img src="https://img.shields.io/github/stars/howe12/every-embodied-course?color=0052cc&style=for-the-badge" alt="Stars"></a>
      <a href="https://github.com/howe12/every-embodied-course/network/members" target="_blank">
          <img src="https://img.shields.io/github/forks/howe12/every-embodied-course?color=0052cc&style=for-the-badge" alt="Forks"></a>
  </p>
</div>

---

## 📖 阅读指南

### 如何开始学习

1. **环境准备**
   - 安装 Ubuntu 20.04/22.04 系统
   - 安装 ROS2 (推荐 Humble 版本)
   - 配置开发环境

2. **学习顺序**
   - 建议按目录顺序学习：从01到02
   - 每个章节配有代码示例和实践项目
   - 学完即可动手实践

3. **代码获取**
   ```bash
   git clone https://github.com/howe12/every-embodied-course.git
   cd every-embodied-course/docs
   ```

### 章节速览

| 章节 | 内容 | 难度 |
| :--- | :--- | :--- |
| 01-具身智能概述 | 机器人基础、ROS发展、Linux基础 | ⭐ 入门 |
| 02-机器人基础和控制 | ROS2工作空间、Colcon、开发工具 | ⭐⭐ 进阶 |

### 配套资源

- 🐢 [turtlesim仿真](https://github.com/ros/ros_tutorials) - 入门练习
- 📚 [ROS2官方文档](https://docs.ros.org/en/humble/) - 权威参考
- 💻 [本课程GitHub](https://github.com/howe12/every-embodied-course) - 获取源码

---

## 🚀 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/howe12/every-embodied-course.git
cd every-embodied-course

# 2. 安装ROS2 (以Humble为例)
sudo apt update
sudo apt install ros-humble-desktop

# 3. 运行第一个示例
ros2 run turtlesim turtlesim_node
```

---

## 📚 课程简介

本课程是 [every-embodied](https://github.com/datawhalechina/every-embodied) 的ROS2机器人仿真子课程，系统学习ROS2机器人仿真技术，从基础入门到实践项目。

- **入门友好**：从零开始，无需ROS1基础
- **实践导向**：强调"跑起来-看结果-再理解原理"的学习路径
- **循序渐进**：从环境搭建到机器人控制，逐步深入

---

## 🗺️ 学习地图

### 01-具身智能概述
- 机器人发展历史
- 机器人系统组成
- ROS发展历程
- ROS2系统架构
- ROS2安装
- Linux操作基础

### 02-机器人基础和控制
- ROS2工作空间
- Colcon构建工具
- 开发工具链
- ROS2常用工具
- 版本控制
