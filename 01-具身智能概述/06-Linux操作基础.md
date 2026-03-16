# 1.6 Linux系统操作基础

**作者**：霍海杰 | **联系方式**：howe12@126.com

---

> **前置说明**：ROS2运行在Linux系统上，选择Ubuntu作为开发系统是最佳选择——官方支持最好，社区资源最丰富。但Linux基础不够扎实会遇到很多障碍。本节将学习机器人开发必备的Linux技能。

---

## 1. Ubuntu系统安装（📖 参考了解即可）

> **⚠️ 安装部分仅供参考，实际操作请参考专业安装教程**

### 1.1 版本选择

| Ubuntu版本 | ROS2版本 | 推荐程度 |
|------------|----------|----------|
| Ubuntu 22.04 | Humble | ⭐⭐⭐ 推荐 |
| Ubuntu 24.04 | Iron/Jazzy | ⭐⭐ 较新 |
| Ubuntu 20.04 | Foxy | ⭐ 过时 |

> **⭐ 推荐**：Ubuntu 22.04 + ROS2 Humble，最稳定组合

### 1.2 安装要点（了解）

- 关闭BIOS中的Secure Boot
- 推荐分区：/boot(1G) + /(80G) + /home(剩余) + swap(16G)
- 安装后务必更新：`sudo apt update && sudo apt upgrade`

---

## 2. 常用命令——机器人开发必备

> **⭐ 本节重点**：以下命令是日常开发中高频使用的，必须掌握

### 2.1 文件操作命令

> **💡 使用场景**：在项目中浏览、创建、删除文件时

#### ls——查看文件列表

```bash
# 最常用：查看当前目录内容
ls

# 查看详细信息（权限、所有者、大小、日期）
ls -lh

# 显示隐藏文件
ls -la

# 按时间排序（最新的在最后）
ls -ltr
```

**💡 什么时候用？**
- 进入一个新目录，想看看有什么文件 → 用 `ls`
- 想看文件大小 → 用 `ls -lh`
- 找某个隐藏配置文件 → 用 `ls -la`

#### cd——切换目录

```bash
# 进入目录
cd ~/ros2_ws/src

# 回到 home 目录
cd ~

# 回到上级目录
cd ..

# 回到刚才的目录
cd -
```

**💡 什么时候用？**
- 进入工作空间继续开发 → `cd ~/ros2_ws`
- 想去上级目录看看 → `cd ..`

#### pwd——查看当前位置

```bash
# 显示当前完整路径
pwd
# 输出：/home/user/ros2_ws/src
```

**💡 什么时候用？**
- 不知道自己在哪了 → 立即 `pwd`
- 写绝对路径前确认位置

#### mkdir——创建目录

```bash
# 创建单个目录
mkdir my_package

# 创建多级目录（常用！）
mkdir -p src/navigation/launch
```

**💡 什么时候用？**
- 创建新功能包目录 → `mkdir -p my_pkg/src`

#### cp/mv/rm——复制/移动/删除

```bash
# 复制文件
cp source.cpp destination.cpp

# 复制目录
cp -r src/ backup_src/

# 移动/重命名
mv old_name.cpp new_name.cpp

# 删除文件
rm temp.txt

# 删除目录（危险！）
rm -rf my_package/
```

> **⚠️ 危险命令**：`rm -rf` 删除前务必确认路径！

**💡 什么时候用？**
- 备份重要代码 → `cp -r`
- 整理文件结构 → `mv`
- 清理编译产物 → `rm -rf build/`

---

### 2.2 权限管理命令

> **⭐ 重点**：理解权限是Linux开发的基础

#### chmod——修改文件权限

```bash
# 添加可执行权限（常用！）
chmod +x my_script.sh

# 赋予所有权限
chmod 777 myfile

# 移除写权限
chmod -w myfile
```

**💡 什么时候用？**
- 下载了一个脚本运行不了 → `chmod +x script.sh`
- 保护重要文件不被修改 → `chmod -w file`

#### sudo——管理员权限

```bash
# 安装软件
sudo apt install vim

# 修改系统文件
sudo vim /etc/hosts
```

> **⚠️ 谨慎使用**：sudo可以修改系统文件，密码输入前确认

**💡 什么时候用？**
- 安装软件 → `sudo apt install ...`
- 需要修改系统配置 → `sudo vim ...`
- **不要**日常开发使用sudo

---

### 2.3 进程管理命令

> **⭐ 重点**：调试ROS节点时经常用到

#### ps——查看进程

```bash
# 查看所有进程
ps aux

# 查找特定进程
ps aux | grep ros2

# 查看ROS进程（常用组合）
ps -ef | grep node_name
```

**💡 什么时候用？**
- 节点起不来 → 检查是否已有同名进程在运行
- 查看系统资源占用

#### kill——结束进程

```bash
# 结束进程（正常退出）
kill PID

# 强制结束（救命用）
kill -9 PID

# 按名称结束进程
pkill -9 ros2_node_name
```

**💡 什么时候用？**
- 节点卡死无法停止 → `kill -9 PID`
- 重启某个卡住的ROS节点

#### top/htop——查看系统资源

```bash
# 查看系统资源占用
top

# 更友好的界面（需要安装）
htop
```

**💡 什么时候用？**
- 系统变卡 → 查看哪个进程占用高
- 内存不足排查

---

### 2.4 网络命令

#### ping——测试网络连通

```bash
# 测试网络
ping www.baidu.com

# 测试ROS通信
ping robot_pc_ip
```

**💡 什么时候用？**
- 两台机器无法ROS通信 → 先ping一下
- 检查网络是否正常

#### ifconfig/ip——查看IP

```bash
# 查看IP地址
ip addr
# 或
ifconfig
```

**💡 什么时候用？**
- 多机器人通信需要知道IP地址
- 检查网络配置

---

### 2.5 文档编辑命令

> **📖 了解即可**：有图形界面可以用VSCode/Gedit

#### vim——终端编辑器（进阶）

```bash
# 编辑文件
vim file.txt

# 基本操作：
# i     - 进入编辑模式
# Esc   - 退出编辑模式
# :w    - 保存
# :q    - 退出
# :wq   - 保存并退出
# :q!   - 不保存强制退出
```

> **💡 什么时候用？**
- 远程连接服务器时（无图形界面）
- 需要快速修改配置文件

#### nano——简单编辑器（入门推荐）

```bash
# 编辑文件（比vim简单）
nano file.txt

# 基本操作：
# Ctrl+O - 保存
# Ctrl+X - 退出
```

> **💡 什么时候用？**
- 初次使用Linux → 推荐nano
- 快速修改简单文件

#### gedit——图形化编辑器

```bash
# 用图形界面编辑
gedit file.txt &
```

> **💡 什么时候用？**
- Ubuntu桌面系统 → 推荐gedit
- 初学者友好

---

## 3. 终端优化（📖 了解即可）

> 这部分内容可以后续深入学习，初学者可以跳过

### 3.1 Terminator分屏终端

多窗口同时操作，提高效率。

### 3.2 命令别名

```bash
# 临时设置（当前终端有效）
alias ll='ls -lh'

# 永久设置（不推荐修改~/.bashrc，新手容易出错）
```

### 3.3 SSH远程连接

远程控制机器人或服务器时使用。

---

## 4. 实训案例：ROS2小海龟测试

> **⭐ 本节重点**：通过实际动手操作巩固Linux命令

### 4.1 实训目标

1. 掌握基本Linux命令
2. 运行ROS2小海龟Demo
3. 使用命令控制小海龟

### 4.2 实训步骤

#### 步骤1：打开终端

```bash
# 在Ubuntu桌面打开终端：Ctrl+Alt+T
```

#### 步骤2：启动小海龟仿真器

```bash
# 方式1：临时配置ROS2环境（推荐！不修改系统）
# 每次打开新终端都要执行

cd ~/ros2_ws
source install/setup.bash

# 启动小海龟
ros2 run turtlesim turtlesim_node
```

> **⚠️ 注意**：每次新开终端都需要重新source

#### 步骤3：打开控制节点（另开终端）

```bash
# 新开一个终端（Ctrl+Alt+T）
cd ~/ros2_ws
source install/setup.bash

# 启动键盘控制
ros2 run turtlesim turtle_teleop_key
```

> **💡 按方向键控制小海龟移动！**

#### 步骤4：查看节点信息（练习命令）

```bash
# 在第三个终端练习：

# 查看运行中的节点
ros2 node list

# 查看话题列表
ros2 topic list

# 查看系统状态
ros2 doctor
```

#### 步骤5：停止节点

```bash
# 找到进程
ps aux | grep turtlesim

# 结束进程
kill -9 PID
```

### 4.3 验收标准

| 任务 | 验收要求 |
|------|----------|
| ⭐ | 能正确source环境并启动turtlesim |
| ⭐ | 能用键盘控制小海龟移动 |
| | 能用ros2命令查看节点和话题 |
| | 理解source命令的作用 |

---

## 本章小结

**必须掌握的命令（⭐）**：

| 命令 | 作用 | 使用场景 |
|------|------|----------|
| `ls` | 查看文件 | 进入目录先看看有什么 |
| `cd` | 切换目录 | 开始开发前进入工作空间 |
| `pwd` | 查看当前位置 | 不知道在哪时 |
| `mkdir -p` | 创建目录 | 创建新功能包 |
| `chmod +x` | 添加执行权限 | 运行脚本前 |
| `source` | 加载环境 | 每次新终端都要 |
| `ps aux \| grep` | 查看进程 | 节点冲突时 |
| `kill -9` | 结束进程 | 节点卡死时 |

**了解即可（📖）**：
- vim编辑器
- Terminator分屏
- SSH远程连接

---

## 思考与练习

1. ⭐ **动手练一练**：启动turtlesim，用键盘控制小海龟画一个圈
2. ⭐ **动手练一练**：练习ls/cd/pwd/mkdir等基本命令
3. 想一想：为什么每次打开新终端都要source？
4. 查一查：还有哪些ROS2 Demo可以体验？

---

## 参考资料

1. ROS2官方教程: <https://docs.ros.org/en/rolling/Tutorials/Beginner-CLI-Tools.html>
2. Ubuntu命令手册: <https://help.ubuntu.com/>
3. 鸟哥的Linux私房菜: <https://linux.vbird.org/>

---

*下一节我们将学习"2.1 ROS2工作空间结构与规范"，开始正式的ROS2开发学习！*
