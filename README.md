# 古代明堂建筑采光仿真与日照优化系统

## 项目简介

本系统是为汉长安明堂遗址数字化复原研究而开发的全栈应用，集成了采光仿真、日照优化、传感器数据采集和MQTT告警推送功能。

**研究背景**：汉长安明堂建于西汉元始四年（公元4年），是古代帝王宣明政教、举行大典的重要场所。本系统通过计算机仿真技术，复原研究古代明堂建筑的采光性能，为建筑史研究提供量化数据支持。

**系统架构**：
- **后端**：Python FastAPI + InfluxDB 2.x + MQTT
- **前端**：React 18 + TypeScript + Three.js + Canvas
- **核心算法**：光线追踪 + Perez天空模型 + 粒子群优化算法

---

## 目录结构

```
AI_solo_coder_task_A_135/
├── backend/                          # 后端服务
│   ├── app/
│   │   ├── api/                      # API路由
│   │   │   ├── sensor.py             # 传感器接口
│   │   │   ├── simulation.py         # 仿真接口
│   │   │   ├── optimization.py       # 优化接口
│   │   │   ├── alert.py              # 告警接口
│   │   │   └── router.py             # 总路由
│   │   ├── core/                     # 核心模块
│   │   │   ├── config.py             # 配置管理
│   │   │   └── database.py           # InfluxDB管理
│   │   ├── models/                   # 数据模型
│   │   │   └── schemas.py            # Pydantic模型
│   │   ├── services/                 # 业务服务
│   │   │   ├── alert_service.py      # MQTT告警服务
│   │   │   ├── sensor_service.py     # 传感器数据服务
│   │   │   ├── simulation_service.py # 仿真任务服务
│   │   │   └── optimization_service.py # 优化任务服务
│   │   └── main.py                   # FastAPI主入口
│   ├── simulation/                   # 采光仿真引擎
│   │   ├── sky_model.py              # 天空模型（Perez/CIE）
│   │   ├── ray_tracer.py             # 光线追踪核心
│   │   └── lighting_calc.py          # 照度计算器
│   ├── optimization/                 # 日照优化引擎
│   │   └── pso_optimizer.py          # 粒子群优化算法
│   ├── scripts/                      # 工具脚本
│   │   ├── init_influxdb.py          # InfluxDB初始化脚本
│   │   └── sensor_simulator.py       # 传感器模拟器
│   ├── requirements.txt              # Python依赖
│   ├── .env.example                  # 环境变量示例
│   └── docker-compose.yml            # Docker编排
├── frontend/                         # 前端应用
│   ├── src/
│   │   ├── components/               # React组件
│   │   │   ├── Mingtang3DModel.tsx   # Three.js三维模型
│   │   │   ├── LightCloudMap.tsx     # Canvas伪彩色云图
│   │   │   ├── ControlPanel.tsx      # 控制面板
│   │   │   ├── SensorPanel.tsx       # 传感器数据面板
│   │   │   └── AlertNotification.tsx # 告警通知
│   │   ├── api/                      # API服务
│   │   ├── store/                    # 状态管理（Zustand）
│   │   ├── types/                    # TypeScript类型
│   │   ├── utils/                    # 工具函数
│   │   ├── App.tsx                   # 主应用组件
│   │   └── main.tsx                  # 应用入口
│   ├── tailwind.config.js            # TailwindCSS配置
│   ├── tsconfig.json                 # TypeScript配置
│   ├── vite.config.ts                # Vite配置
│   └── package.json                  # Node依赖
└── README.md                         # 本文件
```

---

## 核心功能

### 1. 采光仿真模型

基于光线追踪算法和Perez天空模型，精确计算室内各时段的照度分布：

- **天空模型**：支持Perez真实天空、CIE晴天、CIE阴天三种模型
- **光线追踪**：支持直接光照、漫反射、多阶反射计算
- **空间离散**：三维网格划分，输出照度分布矩阵
- **时间序列**：支持逐小时仿真，输出全日照变化曲线

### 2. 日照优化引擎

采用粒子群优化算法（PSO）优化窗户参数，提升室内采光均匀度：

- **优化变量**：窗户位置(x, z)、尺寸(width, height)、透光率
- **适应度函数**：采光均匀度 + 平均照度加权组合
- **约束条件**：窗户不重叠、不超出墙面、建筑结构限制
- **输出结果**：最优窗户方案、收敛曲线、优化前后对比

### 3. 传感器数据采集

模拟传感器每小时上报明堂室内6个监测点的实时数据：

- **监测位置**：主殿中心、东室、西室、南室、北室、中心祭台
- **采集参数**：室内照度、太阳高度角、太阳方位角、窗户透光率
- **数据存储**：InfluxDB时序数据库，支持历史追溯
- **采集模式**：实时连续模式、历史数据回填模式

### 4. 告警系统

冬季日照不足时自动触发预警，通过MQTT推送通知：

- **触发条件**：冬季（11月-次年2月）日照时长 < 3小时/天
- **推送方式**：MQTT消息（主题：`mingtang/alerts`）
- **告警等级**：轻度不足（2-3h）、中度不足（1-2h）、严重不足（<1h）
- **历史记录**：告警记录持久化存储，支持追溯

---

## 技术栈

### 后端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.11 | 开发语言 |
| FastAPI | 0.104.x | Web框架 |
| Uvicorn | 0.24.x | ASGI服务器 |
| Pydantic | 2.x | 数据验证 |
| InfluxDB | 2.7 | 时序数据库 |
| Flux | - | 查询语言 |
| Eclipse Mosquitto | 2.0 | MQTT代理 |
| paho-mqtt | 1.6.x | MQTT客户端 |
| NumPy | 1.26.x | 科学计算 |
| SciPy | 1.11.x | 数值计算 |
| PySolar | 0.10 | 太阳位置计算 |

### 前端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 18.2 | UI框架 |
| TypeScript | 5.3 | 类型系统 |
| Vite | 5.0 | 构建工具 |
| Three.js | 0.160 | 三维渲染 |
| @react-three/fiber | 8.15 | Three.js React绑定 |
| @react-three/drei | 9.92 | Three.js工具库 |
| @react-three/postprocessing | 2.15 | 后期处理 |
| ECharts | 5.4 | 数据可视化 |
| TailwindCSS | 3.4 | CSS框架 |
| Zustand | 4.4 | 状态管理 |
| Axios | 1.6 | HTTP客户端 |
| MQTT.js | 5.3 | MQTT客户端 |

---

## 快速开始

### 方法一：Docker Compose 一键启动（推荐）

```bash
# 1. 克隆项目
cd AI_solo_coder_task_A_135

# 2. 配置环境变量
cp backend/.env.example backend/.env

# 3. 启动所有服务
docker-compose up -d

# 4. 初始化InfluxDB
docker-compose exec backend python scripts/init_influxdb.py

# 5. 启动传感器模拟器（可选，填入历史数据）
docker-compose exec backend python scripts/sensor_simulator.py --backfill
```

### 方法二：手动部署

#### 1. 启动基础设施

```bash
# 启动InfluxDB
docker run -d --name influxdb \
  -p 8086:8086 \
  -v influxdb-data:/var/lib/influxdb2 \
  influxdb:2.7-alpine

# 启动Mosquitto MQTT
docker run -d --name mosquitto \
  -p 1883:1883 -p 9001:9001 \
  eclipse-mosquitto:2.0
```

#### 2. 初始化数据库

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置InfluxDB连接参数

# 初始化数据库
python scripts/init_influxdb.py
```

#### 3. 启动后端服务

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 4. 启动传感器模拟器

```bash
cd backend
# 持续模式：每小时上报一次
python scripts/sensor_simulator.py

# 回填模式：填入过去7天的历史数据
python scripts/sensor_simulator.py --backfill --days 7
```

#### 5. 启动前端服务

```bash
cd frontend

# 安装依赖
npm install

# 开发模式
npm run dev

# 生产构建
npm run build
```

---

## API接口文档

启动后端服务后，访问以下地址查看完整API文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 主要API端点

#### 传感器数据接口

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/sensor/data` | 上报传感器数据 |
| GET | `/api/sensor/data` | 查询历史数据 |
| GET | `/api/sensor/latest` | 获取最新数据 |
| GET | `/api/sensor/statistics` | 获取统计数据 |
| GET | `/api/sensor/sunshine-hours` | 查询日照时长 |

#### 采光仿真接口

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/simulation/run` | 运行仿真任务 |
| GET | `/api/simulation/status/{task_id}` | 查询任务状态 |
| GET | `/api/simulation/tasks` | 获取任务列表 |
| POST | `/api/simulation/cancel/{task_id}` | 取消任务 |
| GET | `/api/simulation/result/{task_id}` | 获取仿真结果 |

#### 日照优化接口

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/optimization/run` | 运行优化任务 |
| GET | `/api/optimization/status/{task_id}` | 查询任务状态 |
| GET | `/api/optimization/result/{task_id}` | 获取优化结果 |
| POST | `/api/optimization/compare` | 对比优化前后 |

#### 告警管理接口

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/alert/check` | 检查日照告警 |
| GET | `/api/alert/history` | 查询告警历史 |
| POST | `/api/alert/test` | 发送测试告警 |

---

## 前端功能说明

### 3D视图

- **建筑模型**：精细还原汉长安明堂建筑结构，包括主殿、四室、围墙、重檐屋顶
- **太阳运动**：实时太阳位置计算，动态光照效果
- **交互控制**：鼠标左键旋转、右键平移、滚轮缩放
- **显示模式**：实体模式/线框模式切换
- **传感器标注**：6个监测点实时显示当前照度值

### 采光云图

- **伪彩色显示**：Jet色彩映射，直观展示照度分布
- **切面显示**：y=1.5m水平面切面（人眼高度）
- **实时数据**：显示最大/最小/平均照度、均匀度指标
- **时间序列**：支持不同时段切换查看
- **透明度调节**：云图透明度可调节

### 控制面板

#### 采光仿真
- 日期和时间范围选择
- 天空模型选择（Perez/CIE晴天/CIE阴天）
- 网格分辨率调节
- 大气浑浊度参数
- 实时进度显示

#### 日照优化
- 窗户数量设置（1-8个）
- 粒子群参数（种群大小、迭代次数）
- 目标均匀度设置
- 收敛过程可视化
- 最优方案自动应用

#### 告警管理
- 手动检查日照时长
- 发送测试告警
- 告警规则说明

#### 显示设置
- 云图显示开关
- 云图透明度调节
- 自动旋转视角
- 线框模式切换

---

## 核心算法说明

### 1. Perez天空模型

Perez模型是目前最精确的晴天天空亮度分布模型，考虑了太阳位置、大气浑浊度等参数：

```
L(θ, γ) = Lz * [1 + a * exp(b / cosθ)] * [1 + c * exp(d * γ) + e * cos²γ]
```

其中：
- θ：天顶角
- γ：与太阳的角距离
- Lz：天顶亮度
- a, b, c, d, e：Perez系数（根据浑浊度插值）

### 2. 光线追踪算法

系统实现了简化但高效的光线追踪：

1. **光线生成**：从每个采样点向上半球生成多束采样光线
2. **相交测试**：与场景中的几何体进行求交测试
3. **照度计算**：
   - 直接光照：太阳直射 + 天空光
   - 间接光照：墙面反射（Lambertian模型）
4. **蒙特卡洛积分**：对采样结果进行统计平均

### 3. 粒子群优化算法（PSO）

标准PSO算法的速度和位置更新公式：

```
v_i(t+1) = w * v_i(t) + c1 * r1 * (pbest_i - x_i(t)) + c2 * r2 * (gbest - x_i(t))
x_i(t+1) = x_i(t) + v_i(t+1)
```

其中：
- w：惯性权重（线性递减 0.9 → 0.4）
- c1, c2：学习因子（均为2.0）
- r1, r2：[0,1]随机数
- pbest：个体历史最优
- gbest：全局历史最优

**适应度函数设计**：
```
fitness = α * uniformity + β * (avg_illuminance / target_illuminance)
```
- uniformity：采光均匀度（min/avg）
- α, β：权重系数（默认 α=0.7, β=0.3）

---

## 伪彩色云图例程

```
照度(lux) → 颜色
────────────────────────────
> 10000    深红 #800000   极强
 5000-10000 红色 #ff0000   很强
 2000-5000  橙色 #ff8000   强
 1000-2000  黄色 #ffff00   较强
  500-1000  浅绿 #80ff80   适中
  200-500   青色 #00ffff   一般
  100-200   浅蓝 #0080ff   较暗
   50-100   蓝色 #0000ff   暗
   <50      深蓝 #000080   极暗
```

---

## 明堂建筑数据

### 建筑形制

- **建造年代**：西汉元始四年（公元4年）
- **遗址位置**：陕西省西安市未央区（34.265°N, 108.954°E）
- **形制**：十字对称的"亞"字形平面
- **尺寸**：主体建筑约20m × 20m，总高约13m

### 建筑结构

- **中心主殿**：约10m × 10m，高约8m
- **四向室**：东、南、西、北各一室，每室约8m × 8m
- **围墙**：四周环墙，每面设一门
- **重檐屋顶**：四阿顶，上有金盘装饰

### 传感器监测点

| 位置 | 坐标(x, y, z) | 说明 |
|------|---------------|------|
| 主殿中心 | (0, 0, 0) | 建筑几何中心，1.5m高 |
| 东室 | (8, 0, 0) | 东侧室中心 |
| 西室 | (-8, 0, 0) | 西侧室中心 |
| 南室 | (0, 0, 8) | 南侧室中心 |
| 北室 | (0, 0, -8) | 北侧室中心 |
| 中心祭台 | (0, 2, 0) | 中心祭台上方，2.0m高 |

---

## 常见问题

### Q: InfluxDB初始化失败怎么办？

A: 检查`.env`文件中的连接参数是否正确，确认InfluxDB容器是否正常启动，首次初始化需要创建初始bucket和token。

### Q: MQTT连接不上怎么办？

A: 确认Mosquitto是否开启了WebSocket端口（9001），前端通过WebSocket连接MQTT，需要正确的端口配置。

### Q: 仿真速度太慢怎么办？

A: 可以降低网格分辨率（默认10，可降至5），减少时间步长，或者减少反射次数。

### Q: 粒子群优化不收敛怎么办？

A: 增加种群大小（默认30，可增至50-100），增加迭代次数，调整惯性权重递减策略。

---

## 研究团队

本系统由建筑史研究团队与计算机科学团队联合开发，用于古代建筑数字化复原研究。

---

## 许可证

本项目仅用于学术研究用途。

---

## 联系方式

如有问题或合作意向，请通过项目仓库提交Issue。
