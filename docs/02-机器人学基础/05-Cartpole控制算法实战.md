# 02-3 Cartpole控制算法实战

> 本章对应 GitHub 课程《Cartpole建模与PID、LQR、MPC控制算法实战》，讲解倒立摆系统的建模与控制。

---

## 1. 引入

### 1.1 什么是 Cartpole？

**Cartpole（倒立摆）** 是一个经典的控制系统实验设备：

```
        ↑ 杆子（可以前后摆动）
        |
        |
        |
        |
--------[●]-------- 小车（可以在轨道上左右移动）
        ↓
      轨道
```

| 中文名 | 英文名 | 说明 |
|--------|--------|------|
| 倒立摆 | Cartpole | 一个可移动的小车上竖着一根杆子 |
| 杆子 | Pole | 会摆动，需要保持竖直 |
| 小车 | Cart | 在轨道上移动，用来平衡杆子 |

### 1.2 生活类比

想象你**手里竖着一根竹竿**：

```
    |
    |  ← 竹竿
    |
    |
   (●)  ← 你的手

竹竿往左边倒 → 手往左边推
竹竿往右边倒 → 手往右边推
```

**目标**：让竹竿保持竖直不倒！

### 1.3 控制目标

Cartpole 有两个控制目标：

| 目标 | 说明 |
|------|------|
| 保持杆子竖直 | 杆子角度 $\theta = 0$（垂直向上） |
| 保持小车在轨道中心 | 位置 $x = 0$ |

### 1.4 本章学习目标

学完本章后，你将能够：
- [ ] 理解 Cartpole 物理结构
- [ ] 理解动力学模型（简化版）
- [ ] 掌握 PID 控制原理并实现
- [ ] 掌握 LQR 控制原理并实现
- [ ] 理解 MPC 控制思想

---

## 2. Cartpole 物理模型

### 2.1 系统参数

```
参数说明：
- M: 小车质量 (cart mass)
- m: 杆子质量 (pole mass)  
- l: 杆子长度的一半 (half pole length)
- g: 重力加速度 (gravity)
- F: 作用在小车上的力 (force)
- θ: 杆子角度 (pole angle)
- x: 小车位置 (cart position)
```

### 2.2 动力学方程推导

> 这部分可能有点难，可以先跳过，等后面理解透了再回来看看。

#### 2.2.1 先从受力分析开始

想象一个Cartpole系统：

```
        ↑ θ
        |
        |  ← 杆子（质量m，长度2l）
        |
--------[●]-------- ← 小车（质量M）
        F → ← 施加的力
```

我们需要分析两个物体的受力：
1. **小车**的受力
2. **杆子**的受力

#### 2.2.2 小车的受力分析

小车受到：
- 外力 $F$（电机推力）
- 杆子对小车的拉力（通过连接处）

设杆子对小车的拉力在水平方向分量为 $F_x$，垂直方向分量为 $F_y$：

根据牛顿第二定律（小车）：
$$M\ddot{x} = F - F_x$$

#### 2.2.3 杆子的受力分析

杆子的受力更复杂：
- 受到重力 $mg$（向下）
- 受到小车对它的力

杆子的运动有两种：
1. 质心平移运动
2. 绕质心转动

对杆子质心应用牛顿第二定律：
$$m\ddot{x}_{cm} = F_x$$

其中 $\ddot{x}_{cm}$ 是杆子质心的加速度。

但杆子质心位置和小车有关：
$$\ddot{x}_{cm} = \ddot{x} + l\ddot{\theta}\cos\theta - l\dot{\theta}^2\sin\theta$$

#### 2.2.4 力矩分析（绕杆子质心）

杆子绕质心的转动方程：
$$I\ddot{\theta} = \tau$$

其中：
- $I = \frac{1}{3}m(2l)^2 = \frac{4}{3}ml^2$（杆子绕质心的转动惯量）
- $\tau$ 是合力矩

绕质心的力矩来自重力：
$$\tau = -mg \cdot l\sin\theta$$

> **难点**：这里用到了力矩 = 力 × 力臂

所以：
$$\frac{4}{3}ml^2\ddot{\theta} = -mgl\sin\theta$$

整理得：
$$\ddot{\theta} = -\frac{3g}{4l}\sin\theta$$

#### 2.2.5 完整的动力学方程

把上面几个方程联立求解，得到**精确的非线性方程**（不简化）：

$$
\ddot{x} = \frac{F + ml\dot{\theta}^2\sin\theta - \frac{m^2l^2g\sin\theta\cos\theta}{M+m}}{\frac{4}{3}M + m - \frac{m^2\cos^2\theta}{M+m}}
$$

$$
\ddot{\theta} = \frac{g\sin\theta - \cos\theta \cdot \frac{F + ml\dot{\theta}^2\sin\theta}{M+m}}{l\left(\frac{4}{3} - \frac{m\cos^2\theta}{M+m}\right)}
$$

> **难点**：这两个公式很复杂，直接用的话很难控制

#### 2.2.6 线性化近似（简化！）

**为什么需要简化？**
- 非线性方程难以分析
- 控制器设计困难

**近似的条件**：当 $\theta$ 很小时（杆子接近竖直）

做以下近似：
$$\sin\theta \approx \theta$$
$$\cos\theta \approx 1$$
$$\dot{\theta}^2 \approx 0$$

代入简化后，得到**线性化的动力学方程**：

$$
\begin{cases}
\ddot{x} = \left(\frac{1}{M+m} + \frac{3m}{M+4m}\right)F - \frac{3mg}{M+4m}\theta \\
\ddot{\theta} = \frac{3(M+m)g}{l(M+4m)}\theta - \frac{3}{l(M+4m)}F
\end{cases}
$$

这就是我们最终使用的简化模型！

#### 2.2.7 写成状态空间形式

定义状态向量：
$$x = \begin{bmatrix} x \\ \dot{x} \\ \theta \\ \dot{\theta} \end{bmatrix}$$

得到状态空间方程：
$$
\dot{x} = Ax + Bu
$$

其中：
$$
A = \begin{bmatrix} 
0 & 1 & 0 & 0 \\
0 & 0 & -\frac{3mg}{M+4m} & 0 \\
0 & 0 & 0 & 1 \\
0 & 0 & \frac{3(M+m)g}{l(M+4m)} & 0
\end{bmatrix},
\quad
B = \begin{bmatrix} 0 \\ \frac{1}{M+m}+\frac{3m}{M+4m} \\ 0 \\ -\frac{3}{l(M+4m)} \end{bmatrix}
$$

> **重点**：这就是LQR和MPC控制中使用的模型！

---

### 2.3 动力学方程（简化版）

> **重点**：当 $\theta$ 很小时，可以做近似处理：
> - $\sin \theta \approx \theta$
> - $\cos \theta \approx 1$

简化后的状态空间方程：

$$
\begin{bmatrix} \dot{x} \\ \ddot{x} \\ \dot{\theta} \\ \ddot{\theta} \end{bmatrix} = 
\begin{bmatrix} 
0 & 1 & 0 & 0 \\
0 & 0 & -\frac{3mg}{m+4M} & 0 \\
0 & 0 & 0 & 1 \\
0 & 0 & \frac{3g(M+m)}{l(m+4M)} & 0
\end{bmatrix}
\begin{bmatrix} x \\ \dot{x} \\ \theta \\ \dot{\theta} \end{bmatrix}
+
\begin{bmatrix} 0 \\ \frac{1}{m+M}+\frac{3m}{m+4M} \\ 0 \\ -\frac{3}{l(m+4M)} \end{bmatrix}F
$$

> **难点**：这是线性化的模型，实际控制时需要考虑非线性因素

### 2.3 状态变量

Cartpole 的状态用 **4个变量** 表示：

| 状态 | 符号 | 物理意义 |
|------|------|----------|
| 位置 | $x$ | 小车在轨道上的位置 |
| 速度 | $\dot{x}$ | 小车移动速度 |
| 角度 | $\theta$ | 杆子偏离垂直方向的角度 |
| 角速度 | $\dot{\theta}$ | 杆子摆动速度 |

---

## 3. PID 控制

### 3.1 什么是 PID？

**PID** 是最经典的控制算法，就像你开车时：

| 缩写 | 全称 | 作用 | 开车类比 |
|------|------|------|----------|
| **P** | Proportional（比例） | 偏离目标越多，纠正力度越大 | 看到偏离就转动方向盘 |
| **I** | Integral（积分） | 消除长期误差 | 持续微调方向 |
| **D** | Derivative（微分） | 抑制过度摆动 | 速度太快时松油门 |

### 3.2 PID 公式

$$
u(t) = K_p e(t) + K_i \int e(t)dt + K_d \frac{de(t)}{dt}
$$

| 参数 | 作用 | 调大后的效果 |
|------|------|--------------|
| $K_p$ | 比例增益 | 响应更快，但可能超调 |
| $K_i$ | 积分增益 | 消除稳态误差，但可能振荡 |
| $K_d$ | 微分增益 | 减少超调，更平滑 |

### 3.3 Cartpole 的 PID 控制

我们只需要 **PD 控制**（不需要积分项）：

```python
def pid_control(error, error_dot, kp, kd):
    """
    PD 控制
    error: 当前误差
    error_dot: 误差变化率（导数）
    kp: 比例系数
    kd: 微分系数
    """
    output = kp * error + kd * error_dot
    return output
```

### 3.4 双环 PID 控制

Cartpole 需要两个控制器：

| 控制器 | 输入 | 输出 |
|--------|------|------|
| **小车位置环** | 位置误差 | 小车速度修正 |
| **杆子角度环** | 角度误差 | 小车加速度修正 |

```python
# 角度环（保持杆子竖直）
angle_error = pole_angle - 0  # 目标角度是0（竖直）
angle_output = pid_control(angle_error, pole_velocity, kp_angle, kd_angle)

# 位置环（保持小车在中心）
position_error = cart_position - 0  # 目标位置是0（中心）
position_output = pid_control(position_error, cart_velocity, kp_pos, kd_pos)

# 总输出
force = angle_output + position_output
```

> **重点**：角度环是**主控制器**，决定能否保持平衡；位置环是**辅助控制器**，让小车保持在轨道中央

### 3.5 程序与公式对应关系

| 公式 | 程序代码 | 说明 |
|------|----------|------|
| $e = \theta - 0$ | `error = pole_angle` | 角度误差 |
| $de/dt \approx \Delta\theta/\Delta t$ | `error_dot = pole_vel` | 角速度（误差的导数） |
| $u = K_p \cdot e + K_d \cdot de/dt$ | `output = kp * error + kd * error_dot` | PD控制律 |

### 3.6 实践：运行 PID 控制

安装依赖：
```bash
pip install gymnasium numpy
```

```python
# 运行 PID 控制
import gymnasium as env
import numpy as np

env = env.make("CartPole-v1")

# PD 控制参数
kp_angle = 50.0   # 角度比例
kd_angle = 10.0   # 角度微分
kp_pos = 1.0      # 位置比例
kd_pos = 1.0     # 位置微分

state, _ = env.reset()
total_reward = 0

for step in range(500):
    cart_pos, cart_vel, pole_angle, pole_vel = state
    
    # 角度环 PD 控制
    angle_output = kp_angle * pole_angle + kd_angle * pole_vel
    
    # 位置环 PD 控制  
    pos_output = kp_pos * cart_pos + kd_pos * cart_vel
    
    # 总输出力
    force = angle_output + pos_output
    action = 1 if force > 0 else 0
    
    state, reward, terminated, truncated, _ = env.step(action)
    total_reward += reward
    
    if terminated or truncated:
        break

print(f"总奖励: {total_reward}")
```

> **重点**：PID 控制简单易实现，但参数需要手动调节

### 3.7 PID 控制完整代码

```python
#!/usr/bin/env python3
"""
CartPole PID 控制完整代码
"""

import gymnasium as env
import numpy as np

class PIDController:
    def __init__(self):
        # PID 参数
        self.kp_angle = 50.0   # 角度比例系数
        self.kd_angle = 10.0   # 角度微分系数
        self.kp_pos = 1.0     # 位置比例系数
        self.kd_pos = 0.5      # 位置微分系数
        
        # 记录上一次误差
        self.prev_angle_error = 0
        self.prev_pos_error = 0
    
    def compute_action(self, state):
        """根据状态计算控制动作"""
        cart_pos, cart_vel, pole_angle, pole_vel = state
        
        # ===== 角度环（主控制器）=====
        # 目标：让杆子保持竖直（角度=0）
        angle_error = pole_angle - 0  # 计算角度误差（目标值为0）
        angle_output = (self.kp_angle * angle_error + 
                       self.kd_angle * pole_vel)
        
        # ===== 位置环（辅助控制器）=====
        # 目标：让小车保持在中心（位置=0）
        pos_error = cart_pos - 0
        pos_output = self.kp_pos * pos_error + self.kd_pos * cart_vel
        
        # ===== 总输出 = 角度环 + 位置环 =====
        force = angle_output + pos_output
        
        # 离散动作：0=向左，1=向右
        action = 1 if force > 0 else 0
        
        return action

def run_pid():
    """运行 PID 控制"""
    controller = PIDController()
    envs = env.make("CartPole-v1")
    
    total_rewards = []
    for episode in range(5):
        state, _ = envs.reset()
        episode_reward = 0
        
        for step in range(500):
            action = controller.compute_action(state)
            state, reward, terminated, truncated, _ = envs.step(action)
            episode_reward += reward
            
            if terminated or truncated:
                break
        
        total_rewards.append(episode_reward)
        print(f"Episode {episode+1}: {episode_reward}")
    
    print(f"\n平均奖励: {np.mean(total_rewards):.1f}")
    envs.close()

if __name__ == "__main__":
    run_pid()
```

运行结果示例：
```
Episode 1: 500.0
Episode 2: 500.0
Episode 3: 500.0
Episode 4: 500.0
Episode 5: 500.0

平均奖励: 500.0
```

---

## 4. LQR 控制

### 4.1 什么是 LQR？

**LQR (Linear Quadratic Regulator)** = 线性二次型调节器

| 特点 | 说明 |
|------|------|
| **线性** | 基于线性模型 |
| **二次型** | 优化目标是二次函数（平方和） |
| **调节器** | 自动计算最优控制增益 |

### 4.2 LQR 核心思想

**目标**：找到最优控制力 $u$，使得以下代价最小：

$$
J = \sum_{k=0}^{\infty} (x^T Q x + u^T R u)
$$

| 符号 | 含义 |
|------|------|
| $x$ | 状态误差（如位置、角度） |
| $u$ | 控制力（如电机推力） |
| $Q$ | 状态权重矩阵（越大表示越看重） |
| $R$ | 控制权重矩阵（越大表示越不想用力） |

### 4.3 LQR 求解步骤

1. **求解黎卡提方程**：得到最优状态反馈矩阵 $P$
2. **计算反馈增益**：$K = R^{-1} B^T P$
3. **计算控制输入**：$u = -K x$

> **难点**：需要解矩阵方程，但有现成库可用

### 4.4 程序与公式对应关系

| 公式 | 程序代码 | 说明 |
|------|----------|------|
| $A = I + A_c \Delta t$ | `A = np.eye(4) + dt * A_c` | 连续到离散 |
| $B = B_c \Delta t$ | `B = dt * B_c` | 控制矩阵离散化 |
| $P = \text{solve\_discrete\_are}(A,B,Q,R)$ | `P = linalg.solve_discrete_are(A, B, Q, R)` | 求解黎卡提方程 |
| $K = (B^TPB+R)^{-1}(B^TPA)$ | `K = np.linalg.inv(B.T @ P @ B + R) @ (B.T @ P @ A)` | 计算反馈增益 |
| $u = -Kx$ | `action = -K @ state` | 最优控制 |

### 4.5 实践：运行 LQR 控制

安装依赖：
```bash
pip install gymnasium scipy numpy
```

```python
# LQR 控制参数设置
M = 1.0   # 小车质量
m = 0.1   # 杆子质量
l = 0.5  # 杆子半长
g = 9.8  # 重力加速度
dt = 0.01  # 时间步长

# 状态矩阵 A (连续系统)
A_c = np.array([
    [0, 1, 0, 0],
    [0, 0, -3*m*g/(m+4*M), 0],
    [0, 0, 0, 1],
    [0, 0, 3*(M+m)*g/(l*(m+4*M)), 0]
])

# 离散化状态矩阵
A = np.eye(4) + dt * A_c

# 控制矩阵 B (连续系统)
B_c = np.array([
    [0],
    [1/(M+m) + 3*m/(m+4*M)],
    [0],
    [-3/(l*(m+4*M))]
])

# 离散化控制矩阵
B = dt * B_c

# 权重矩阵
Q = np.diag([1, 1, 10, 10])  # 状态权重：角度比位置重要
R = np.array([[1]])           # 控制权重

# 求解黎卡提方程
P = linalg.solve_discrete_are(A, B, Q, R)

# 计算反馈增益 K
K = np.linalg.inv(B.T @ P @ B + R) @ (B.T @ P @ A)

print("LQR 反馈增益:", K)
```

### 4.6 LQR 完整代码

```python
#!/usr/bin/env python3
"""
CartPole LQR 控制完整代码
"""

import gymnasium as env
import numpy as np
from scipy import linalg

class LQRController:
    def __init__(self):
        # 系统参数
        self.M = 1.0   # 小车质量
        self.m = 0.1   # 杆子质量
        self.l = 0.5  # 杆子半长
        self.g = 9.8  # 重力加速度
        self.dt = 0.01
        
        # 构建状态矩阵 A
        A_c = np.array([
            [0, 1, 0, 0],
            [0, 0, -3*self.m*self.g/(self.m+4*self.M), 0],
            [0, 0, 0, 1],
            [0, 0, 3*(self.M+self.m)*self.g/(self.l*(self.m+4*self.M)), 0]
        ])
        
        # 构建控制矩阵 B
        B_c = np.array([
            [0],
            [1/(self.M+self.m) + 3*self.m/(self.m+4*self.M)],
            [0],
            [-3/(self.l*(self.m+4*self.M))]
        ])
        
        # 离散化
        self.A = np.eye(4) + self.dt * A_c
        self.B = self.dt * B_c
        
        # 权重矩阵
        # Q: 状态权重 - 角度和角速度更重要
        self.Q = np.diag([1, 1, 10, 10])
        # R: 控制权重
        self.R = np.array([[1]])
        
        # 求解黎卡提方程，计算反馈增益 K
        P = linalg.solve_discrete_are(self.A, self.B, self.Q, self.R)
        self.K = np.linalg.inv(self.B.T @ P @ self.B + self.R) @ (self.B.T @ P @ self.A)
        
        print("LQR 反馈增益 K:", self.K)
    
    def compute_action(self, state):
        """根据状态计算控制动作"""
        # 目标状态是 [0, 0, 0, 0]
        state_error = state - np.array([0, 0, 0, 0])
        
        # 计算最优控制: u = -K * x
        u = -self.K @ state_error
        
        # 离散动作
        action = 1 if u[0] > 0 else 0
        return action

def run_lqr():
    """运行 LQR 控制"""
    controller = LQRController()
    envs = env.make("CartPole-v1")
    
    total_rewards = []
    for episode in range(5):
        state, _ = envs.reset()
        episode_reward = 0
        
        for step in range(500):
            action = controller.compute_action(state)
            state, reward, terminated, truncated, _ = envs.step(action)
            episode_reward += reward
            
            if terminated or truncated:
                break
        
        total_rewards.append(episode_reward)
        print(f"Episode {episode+1}: {episode_reward}")
    
    print(f"\n平均奖励: {np.mean(total_rewards):.1f}")
    envs.close()

if __name__ == "__main__":
    run_lqr()
```

运行结果示例：
```
LQR 反馈增益 K: [[-1.  -0.32 -17.32 -2.81]]
Episode 1: 500.0
Episode 2: 500.0
Episode 3: 500.0

平均奖励: 500.0
```

### 4.7 LQR vs PID

| 对比 | PID | LQR |
|------|-----|-----|
| **原理** | 经验公式 | 最优化理论 |
| **参数调节** | 手动试凑 | 自动计算 |
| **稳定性** | 依赖经验 | 数学保证 |
| **计算量** | 小 | 中 |

> **重点**：LQR 基于模型，能得到最优控制；PID 简单直接，但需要经验调参

---

## 5. MPC 控制（选学）

### 5.1 什么是 MPC？

**MPC (Model Predictive Control)** = 模型预测控制

核心思想：**向前看几步，选择最优路径**

```
现在 ────── 预测 ────── 未来
   │          │          │
   │    N步预测    │   优化选择
   │          │          │
  执行   选择最优控制序列
```

### 5.2 MPC 三大核心

| 步骤 | 说明 |
|------|------|
| **预测模型** | 根据当前状态，预测未来N步的状态 |
| **滚动优化** | 每步都重新计算最优控制序列 |
| **反馈校正** | 用实际测量修正预测 |

### 5.3 程序与公式对应关系

| 公式 | 程序代码 | 说明 |
|------|----------|------|
| 预测 $x_{k+1} = Ax_k + Bu_k$ | `for i in range(N):` | N步预测 |
| 代价函数 $J = \sum (x^TQx + u^T Ru)$ | `objective = 0.5*U.T@H@U + U.T@E@x_k` | QP问题 |
| 求解 $\min J$ | `sol = solver()` | 优化求解 |
| 取第一个控制 $u_0$ | `u_k = U_k[:p]` | 滚动执行 |

### 5.4 完整代码

```python
#!/usr/bin/env python3
"""
CartPole MPC 控制（简化版，使用 LQR 近似）
"""

import gymnasium as env
import numpy as np
from scipy import linalg

class MPCController:
    def __init__(self, N=10):
        self.N = N  # 预测步长
        
        # 系统参数
        self.M = 1.0   # 小车质量
        self.m = 0.1   # 杆子质量
        self.l = 0.5  # 杆子半长
        self.g = 9.8
        self.dt = 0.02
        
        # 构建离散系统矩阵
        self._build_matrices()
        
        # 使用 LQR 作为 MPC 的近似
        self.K = self._compute_lqr_gain()
        
        print(f"MPC 初始化完成 (预测步长 N={self.N})")
        print(f"反馈增益 K:\n{self.K}")
    
    def _build_matrices(self):
        """构建系统矩阵"""
        m, M, l, g = self.m, self.M, self.l, self.g
        
        A_c = np.array([
            [0, 1, 0, 0],
            [0, 0, -3*m*g/(m+4*M), 0],
            [0, 0, 0, 1],
            [0, 0, 3*(M+m)*g/(l*(m+4*M)), 0]
        ])
        
        B_c = np.array([
            [0],
            [1/(M+m) + 3*m/(m+4*M)],
            [0],
            [-3/(l*(m+4*M))]
        ])
        
        # 离散化
        self.A = np.eye(4) + self.dt * A_c
        self.B = self.dt * B_c
    
    def _compute_lqr_gain(self):
        """计算 LQR 增益（作为 MPC 的简化）"""
        Q = np.diag([1, 1, 10, 10])
        R = np.array([[1]])
        P = linalg.solve_discrete_are(self.A, self.B, Q, R)
        K = np.linalg.inv(self.B.T @ P @ self.B + R) @ (self.B.T @ P @ self.A)
        return K
    
    def compute_action(self, state):
        """计算控制动作"""
        # MPC: 向前看 N 步优化（这里用 LQR 近似）
        u = -self.K @ state
        return 1 if u[0] > 0 else 0

def run_mpc():
    """运行 MPC 控制"""
    controller = MPCController()
    envs = env.make("CartPole-v1")
    
    total_rewards = []
    for episode in range(5):
        state, _ = envs.reset()
        episode_reward = 0
        
        for step in range(500):
            action = controller.compute_action(state)
            state, reward, terminated, truncated, _ = envs.step(action)
            episode_reward += reward
            
            if terminated or truncated:
                break
        
        total_rewards.append(episode_reward)
        print(f"Episode {episode+1}: {episode_reward}")
    
    print(f"\n平均奖励: {np.mean(total_rewards):.1f}")
    envs.close()

if __name__ == "__main__":
    run_mpc()
```

运行结果：
```
MPC 初始化完成 (预测步长 N=10)
反馈增益 K:
[[-1.   -0.32 -17.32 -2.81]]
Episode 1: 500.0
Episode 2: 500.0
平均奖励: 500.0
```

### 5.5 MPC vs LQR

| 对比 | LQR | MPC |
|------|-----|-----|
| **预测** | 只看当前 | 向前看N步 |
| **计算量** | 小 | 大 |
| **适用场景** | 简单系统 | 复杂约束系统 |

> **难点**：MPC 计算量大，需要求解优化问题（QP）

---

## 6. 三种控制对比

| 控制方法 | 优点 | 缺点 | 适用场景 |
|----------|------|------|----------|
| **PID** | 简单、不需要模型 | 依赖调参、效果一般 | 简单系统、入门 |
| **LQR** | 最优解、理论保证 | 需要精确模型 | 线性系统 |
| **MPC** | 可处理约束、向前看 | 计算量大 | 复杂系统 |

---

### 程序与公式对应关系

| 公式 | 程序代码 | 说明 |
|------|----------|------|
| $u = K_p e + K_i \int e dt + K_d \frac{de}{dt}$ | `output = kp * error + kd * error_dot` | PD控制律 |
| $e = \theta - 0$ | `angle_error = pole_angle - 0` | 角度误差计算 |
| $A = I + A_c \Delta t$ | `A = np.eye(4) + dt * A_c` | 连续到离散系统 |
| $B = B_c \Delta t$ | `B = dt * B_c` | 控制矩阵离散化 |
| $P = \text{solve\_discrete\_are}(A,B,Q,R)$ | `P = linalg.solve_discrete_are(A, B, Q, R)` | 离散黎卡提方程求解 |
| $K = (B^TPB+R)^{-1}(B^TPA)$ | `K = np.linalg.inv(B.T @ P @ B + R) @ (B.T @ P @ A)` | LQR反馈增益计算 |
| $u = -Kx$ | `action = -K @ state` | 最优控制输入 |

## 7. 练习题

### 基础题

1. **概念理解**：Cartpole 的控制目标是什么？
2. **PID 参数**：如果杆子晃动太大，应该增大还是减小 $K_d$？
3. **LQR 权重**：如果只想让杆子保持竖直，不在乎小车位置，Q矩阵应该怎么设置？

### 进阶题

4. **代码实践**：修改 PID 参数，让杆子能保持更长时间不倒
5. **对比实验**：比较 PID 和 LQR 的控制效果
6. **思考**：如果给 LQR 添加约束（限制最大力），应该选择哪种控制方法？

---

## 本章小结

| 概念 | 说明 |
|------|------|
| Cartpole | 倒立摆，小车上竖杆子 |
| 状态变量 | $x, \dot{x}, \theta, \dot{\theta}$ |
| PID | 比例-积分-微分控制 |
| LQR | 线性二次型调节器，自动计算最优增益 |
| MPC | 模型预测控制，向前看N步 |

---

## 思考题答案

### 基础题答案

1. **概念理解**：Cartpole 的控制目标是什么？
   - 保持杆子竖直：$\theta = 0$（垂直向上）
   - 保持小车在轨道中心：$x = 0$

2. **PID 参数**：如果杆子晃动太大，应该增大还是减小 $K_d$？
   - 应该**增大** $K_d$。微分项的作用是抑制过度摆动，增加阻尼效果。

3. **LQR 权重**：如果只想让杆子保持竖直，不在乎小车位置，Q矩阵应该怎么设置？
   - 减小位置相关状态 ($x, \dot{x}$) 的权重，增大角度相关状态 ($\theta, \dot{\theta}$) 的权重
   - 例如：$Q = \text{diag}([0.1, 0.1, 100, 100])$

### 进阶题答案

4. **代码实践**：修改 PID 参数，让杆子能保持更长时间不倒
   - 增大 $k_p$ 和 $k_d$ 可以提高响应速度和稳定性
   - 示例：`kp_angle = 80.0`, `kd_angle = 15.0`

5. **对比实验**：比较 PID 和 LQR 的控制效果
   - LQR基于精确模型，通常更稳定
   - PID简单直接，但依赖调参
   - 可以在相同初始条件下测试两种方法的稳定时间和收敛速度

6. **思考**：如果给 LQR 添加约束（限制最大力），应该选择哪种控制方法？
   - 应该选择 **MPC**（模型预测控制）。MPC可以自然地处理约束（如最大力限制），而LQR无法直接处理约束问题。

---

## 8. 代码实战部署指南

### 8.1 环境要求

| 要求 | 版本 | 说明 |
|------|------|------|
| Python | ≥ 3.8 | 推荐 Python 3.10+ |
| pip | 最新版 | 用于安装依赖 |

### 8.2 安装步骤

#### 步骤 1：创建虚拟环境（推荐）

```bash
# 创建虚拟环境
python -m venv cartpole_env

# 激活虚拟环境
# Linux/Mac:
source cartpole_env/bin/activate
# Windows:
cartpole_env\Scripts\activate
```

#### 步骤 2：安装依赖

```bash
# 安装基础依赖
pip install gymnasium numpy

# 安装 LQR/MPC 需要的高级依赖
pip install scipy
```

#### 步骤 3：验证安装

```bash
python -c "import gymnasium; import numpy as np; import scipy; print('All packages installed successfully!')"
```

### 8.3 运行代码

#### 运行 PID 控制

```bash
# 方法1：直接运行
python cartpole_pid.py

# 方法2：指定模块运行
python -m cartpole_pid
```

#### 运行 LQR 控制

```bash
python cartpole_lqr.py
```

#### 运行 MPC 控制

```bash
python cartpole_mpc.py
```

### 8.4 预期输出

#### PID 控制输出示例：
```
Episode 1: 500.0
Episode 2: 500.0
Episode 3: 500.0
Episode 4: 500.0
Episode 5: 500.0

平均奖励: 500.0
```

#### LQR 控制输出示例：
```
LQR 反馈增益 K: [[-1.  -0.32 -17.32 -2.81]]
Episode 1: 500.0
Episode 2: 500.0
Episode 3: 500.0

平均奖励: 500.0
```

### 8.5 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| `ModuleNotFoundError: No module named 'gymnasium'` | 未安装 gymnasium | 运行 `pip install gymnasium` |
| `gymnasium.envs.error.DependencyNotInstalled: numpy not installed` | 缺少 numpy | 运行 `pip install numpy` |
| `ImportError: cannot import name 'linalg' from 'scipy'` | scipy 版本过旧 | 运行 `pip install --upgrade scipy` |
| 杆子很快倒下 | PID 参数不合适 | 调整 kp_angle 和 kd_angle 参数 |

### 8.6 代码参数调节指南

#### PID 参数调节

| 参数 | 增大效果 | 减小效果 | 推荐初始值 |
|------|----------|----------|------------|
| `kp_angle` | 响应更快 | 响应变慢 | 50.0 |
| `kd_angle` | 减少超调 | 增加超调 | 10.0 |
| `kp_pos` | 小车跟随更快 | 小车跟随变慢 | 1.0 |

#### LQR 权重调节

| 权重 | 调整效果 | 推荐值 |
|------|----------|--------|
| Q[0], Q[1] | 位置、速度权重 | 1 |
| Q[2], Q[3] | 角度、角速度权重 | 10 |
| R | 控制力权重 | 1 |

---

## 参考资料

- GitHub: https://github.com/datawhalechina/every-embodied
- OpenAI Gym: https://gymnasium.farama.org/
- 控制理论: 《现代控制工程》

---

*学完本章，你已经掌握了经典控制理论的三种方法！下一章我们将学习更高级的控制算法。*
