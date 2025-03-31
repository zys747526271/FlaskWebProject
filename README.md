# Flask 电商平台项目

## 项目概述

这是一个基于Flask框架开发的电商平台，包含完整的前后端功能模块。项目采用前后端分离架构，前端使用Vue.js，后端使用Flask提供RESTful API接口。

## 主要功能

- 用户认证系统（注册/登录/权限管理）
- 商品管理系统（CRUD/分类/搜索）
- 购物车功能
- 订单系统
- 支付集成
- 后台管理

## 技术栈

### 后端
- Python 3
- Flask
- SQLAlchemy
- Flask-Caching

### 前端
- Vue.js 3
- Vite
- Pinia

## 安装指南

### 后端

1. 创建虚拟环境
```bash
python -m venv .venv
```

2. 激活虚拟环境
```bash
# Windows
.venv\Scripts\activate
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置环境变量
复制`.env.example`为`.env`并修改配置

5. 运行开发服务器
```bash
flask run
```

### 前端

1. 安装依赖
```bash
npm install
```

2. 运行开发服务器
```bash
npm run dev
```

## API文档

项目提供完整的RESTful API接口，主要接口包括：

### 用户认证
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录

### 商品管理
- `GET /api/products` - 获取商品列表
- `POST /api/products` - 创建商品
- `GET /api/products/:id` - 获取商品详情

### 购物车
- `GET /api/cart` - 获取购物车
- `POST /api/cart` - 添加商品到购物车

### 订单
- `GET /api/orders` - 获取订单列表
- `POST /api/orders` - 创建订单

## 开发文档

项目使用标准化的代码结构和命名规范，主要模块说明：

### 后端目录结构

- `backend/app.py` - 应用入口
- `backend/models/` - 数据模型
- `backend/routes/` - API路由
- `backend/utils/` - 工具类

### 前端目录结构

- `frontend/src/views/` - 页面组件
- `frontend/src/components/` - 公共组件
- `frontend/src/stores/` - 状态管理

## 贡献指南

1. Fork项目仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 发起Pull Request

## 许可证

MIT