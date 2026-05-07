---
name: Vigor Client Design
description: Vigor 数据分析平台 Web 客户端完整设计方案 - Vue 3 + TypeScript 实现
type: spec
created: 2026-05-07
---

# Vigor Client 设计文档

## 一、项目概述

### 1.1 项目定位
Vigor Client 是 Vigor 数据分析平台的 Web 前端,基于 Vue 3 + TypeScript 构建,提供抖音视频数据分析和可视化功能。

### 1.2 用户角色
- **普通用户**: 浏览热门视频、查看数据分析、AI 领域专家分析
- **管理员用户**: 管理关键词、视频、爬取任务等后台配置

### 1.3 平台支持
- 纯 Web 应用
- 响应式设计,兼容桌面端和移动端
- 支持 PWA (渐进式 Web 应用)

## 二、技术栈

### 2.1 核心框架
- **Vue 3.4+**: Composition API
- **TypeScript 5.0+**: 类型安全
- **Vite 5.0+**: 构建工具

### 2.2 状态管理与路由
- **Pinia 2.x**: 状态管理
- **Vue Router 4.x**: 路由管理

### 2.3 UI 组件库
- **Naive UI**: 桌面端主要组件库(简洁现代)
- **Vant 4**: 移动端组件
- **ECharts 5.x**: 数据可视化

### 2.4 样式方案
- **UnoCSS**: 原子化 CSS
- **CSS Variables**: 主题切换

### 2.5 网络请求
- **Axios**: HTTP 客户端

### 2.6 开发工具
- **ESLint + Prettier**: 代码规范
- **Vitest**: 单元测试
- **TypeScript strict mode**: 严格类型检查

## 三、项目结构

```
vigor-client/
├── public/              # 静态资源
│   ├── favicon.ico
│   └── logo.svg
├── src/
│   ├── api/            # API 接口封装
│   │   ├── index.ts    # Axios 配置
│   │   ├── video.ts    # 视频接口
│   │   ├── keyword.ts  # 关键词接口
│   │   ├── stats.ts    # 统计接口
│   │   └── admin.ts    # 管理后台接口
│   ├── assets/         # 资源文件
│   │   ├── images/
│   │   └── icons/
│   ├── components/     # 通用组件
│   │   ├── common/     # 基础组件
│   │   │   ├── ThemeToggle.vue
│   │   │   └── Loading.vue
│   │   ├── video/      # 视频相关
│   │   │   ├── VideoCard.vue
│   │   │   ├── VideoList.vue
│   │   │   └── VideoDetail.vue
│   │   ├── dashboard/  # 数据看板
│   │   │   ├── InteractionChart.vue
│   │   │   ├── CommentSummary.vue
│   │   │   ├── AIAnalysis.vue
│   │   │   └── TrendComparison.vue
│   │   └── charts/     # 图表组件
│   │       ├── LineChart.vue
│   │       ├── PieChart.vue
│   │       └── RadarChart.vue
│   ├── composables/    # 组合式函数
│   │   ├── useResponsive.ts
│   │   ├── useTheme.ts
│   │   └── useInfiniteScroll.ts
│   ├── layouts/        # 布局组件
│   │   ├── DefaultLayout.vue
│   │   └── AdminLayout.vue
│   ├── router/         # 路由配置
│   │   └── index.ts
│   ├── stores/         # Pinia 状态管理
│   │   ├── user.ts     # 用户状态
│   │   ├── video.ts    # 视频状态
│   │   ├── keyword.ts  # 关键词状态
│   │   ├── theme.ts    # 主题状态
│   │   └── stats.ts    # 统计状态
│   ├── styles/         # 全局样式
│   │   ├── variables.css
│   │   ├── theme.css
│   │   └── reset.css
│   ├── types/          # TypeScript 类型定义
│   │   ├── video.ts
│   │   ├── keyword.ts
│   │   ├── stats.ts
│   │   └── api.ts
│   ├── utils/          # 工具函数
│   │   ├── format.ts
│   │   ├── request.ts
│   │   └── storage.ts
│   ├── views/          # 页面组件
│   │   ├── home/       # 普通用户主页
│   │   │   └── HomePage.vue
│   │   └── admin/      # 管理后台
│   │       ├── LoginPage.vue
│   │       ├── DashboardPage.vue
│   │       ├── KeywordsPage.vue
│   │       ├── VideosPage.vue
│   │       └── TasksPage.vue
│   ├── App.vue
│   └── main.ts
├── .env.development    # 开发环境配置
├── .env.production     # 生产环境配置
├── .eslintrc.js
├── .prettierrc
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── uno.config.ts
```

## 四、功能模块设计

### 4.1 普通用户主页

#### 4.1.1 布局结构

**桌面端 (≥1024px):**
```
┌─────────────────────────────────────────────────────┐
│  [Logo]  [财经 ▼]  [美食]  [科技]  ...  [🌙 主题]  │
├──────────────┬──────────────────────────────────────┤
│              │                                      │
│  视频列表    │         数据看板                     │
│  (40%)       │         (60%)                        │
│              │                                      │
└──────────────┴──────────────────────────────────────┘
```

**移动端 (<768px):**
- 视频列表全屏显示
- 点击视频卡片进入详情页(全屏)
- 顶部导航栏固定

#### 4.1.2 核心组件

**TopNavBar - 顶部导航**
- Logo
- 领域切换下拉菜单(沉浸式设计)
- 主题切换按钮(浅色/深色)

**VideoList - 视频列表**
- 虚拟滚动(处理大量数据)
- 下拉刷新
- 上拉加载更多
- 排序选项(热度/时间)
- 时间窗口筛选(1d/3d/7d/15d/30d)

**VideoCard - 视频卡片**
- 封面图(16:9 比例,懒加载)
- 标题(最多 2 行,超出省略)
- 作者名
- 点赞/评论/分享数(图标 + 数字)
- 热度评分(带颜色标识: 高-红色,中-橙色,低-灰色)
- 悬停效果: 轻微放大 + 阴影加深
- 选中状态: 蓝色边框 + 背景高亮

**DataDashboard - 数据看板**

分为 5 个区块:

**① 视频详情区**
- 大封面图
- 完整标题
- 作者信息(头像 + 名称)
- 发布时间
- 完整互动数据(点赞/评论/分享)
- 热度评分(大号显示 + 趋势箭头)

**② 互动数据图表**
- 时间序列图表(点赞/评论增长趋势)
- ECharts 折线图
- 支持时间范围切换(24h/7d/30d)

**③ 评论摘要**
- AI 生成的评论总结
- 热门关键词标签云
- 情感分析(正面/中性/负面比例饼图)
- 评论数量统计

**④ AI 领域专家分析**
- 行业洞察: 从专业角度解读视频内容的行业意义
- 数据解读: 解释为什么这个视频热度高/低
- 趋势预测: 基于当前数据预测该话题的发展趋势
- 综合分析报告
- 卡片式布局,支持展开/收起

**⑤ 趋势对比**
- 该视频 vs 同领域平均水平
- 雷达图展示多维度对比
- 排名信息(Top X%)

### 4.2 管理后台

#### 4.2.1 路由设计
- `/admin/login` - 登录页
- `/admin/dashboard` - 管理首页
- `/admin/keywords` - 关键词管理
- `/admin/videos` - 视频管理
- `/admin/tasks` - 任务管理

#### 4.2.2 布局结构
```
┌─────────────────────────────────────────────────────┐
│  [Vigor Admin]              [管理员] [退出登录]     │
├──────┬──────────────────────────────────────────────┤
│ 📊   │                                              │
│ 🔑   │              主内容区                        │
│ 🎬   │                                              │
│ ⚙️   │                                              │
└──────┴──────────────────────────────────────────────┘
```

#### 4.2.3 功能模块

**登录页 (/admin/login)**
- 简洁的登录表单
- 用户名 + 密码
- 记住登录状态(7天)
- 错误提示
- Apple 风格的卡片设计

**管理首页 (/admin/dashboard)**
- 数据概览卡片:
  - 总视频数
  - 总评论数
  - 活跃关键词数
  - 今日新增视频数
- 最近任务执行记录(表格)
- 系统状态监控
- 快捷操作按钮

**关键词管理 (/admin/keywords)**
- 关键词列表(表格)
  - 列: ID、关键词、分类、状态、优先级、爬取阈值、创建时间
  - 操作: 编辑、删除、启用/禁用
- 添加关键词(对话框)
- 批量操作
- 搜索和筛选

**视频管理 (/admin/videos)**
- 视频列表(表格)
  - 列: 封面、标题、作者、热度、发布时间、爬取时间
  - 操作: 查看详情、删除、重新分析
- 高级筛选
- 批量删除
- 导出数据(CSV/Excel)

**任务管理 (/admin/tasks)**
- 任务触发面板
- 任务历史记录(表格)
- 任务详情查看(日志)

## 五、状态管理设计

### 5.1 Store 设计

**useUserStore - 用户状态**
```typescript
interface UserState {
  isAdmin: boolean
  username: string | null
  token: string | null
  isLoggedIn: boolean
}
```

**useVideoStore - 视频数据状态**
```typescript
interface VideoState {
  videos: Video[]
  selectedVideo: Video | null
  total: number
  loading: boolean
  currentKeywordId: number | null
  sortBy: 'heat_score' | 'publish_time'
  timeWindow: '1d' | '3d' | '7d' | '15d' | '30d' | null
}
```

**useKeywordStore - 关键词状态**
```typescript
interface KeywordState {
  keywords: Keyword[]
  activeKeywordId: number | null
  loading: boolean
}
```

**useThemeStore - 主题状态**
```typescript
interface ThemeState {
  mode: 'light' | 'dark'
  primaryColor: string
}
```

**useStatsStore - 统计数据状态**
```typescript
interface StatsState {
  keywordStats: KeywordStats[]
  trends: TrendStats[]
  loading: boolean
}
```

## 六、API 接口设计

### 6.1 基础配置
- baseURL: 从环境变量读取
- timeout: 30000ms
- 请求拦截器: 添加 API Key / Token
- 响应拦截器: 统一错误处理

### 6.2 接口列表

**视频相关 (api/video.ts)**
- `listVideos(params)`: 获取视频列表
- `getVideo(videoId)`: 获取视频详情
- `getVideoComments(videoId, params)`: 获取视频评论
- `getVideoSummary(videoId)`: 获取视频摘要和AI分析

**关键词相关 (api/keyword.ts)**
- `listKeywords()`: 获取关键词列表
- `getKeyword(keywordId)`: 获取关键词详情
- `createKeyword(data)`: 创建关键词
- `updateKeyword(keywordId, data)`: 更新关键词
- `deleteKeyword(keywordId)`: 删除关键词

**统计相关 (api/stats.ts)**
- `getKeywordStats()`: 获取关键词统计
- `getTrends()`: 获取趋势数据

**管理后台 (api/admin.ts)**
- `login(username, password)`: 管理员登录
- `logout()`: 登出
- `listTasks(params)`: 获取任务列表
- `triggerCrawl(keywordId)`: 触发爬取任务
- `triggerUpdate(tier)`: 触发更新任务
- `getTaskDetail(taskId)`: 获取任务详情
- `listAdminVideos(params)`: 管理后台视频列表
- `deleteVideo(videoId)`: 删除视频

## 七、主题和样式设计

### 7.1 双主题系统

**浅色主题:**
- 背景: #ffffff, #f5f5f7, #e8e8ed
- 文字: #1d1d1f, #6e6e73, #86868b
- 主色: #007aff

**深色主题:**
- 背景: #000000, #1c1c1e, #2c2c2e
- 文字: #ffffff, #ebebf5, #8e8e93
- 主色: #0a84ff

### 7.2 Apple 风格规范

**字体:**
- 主字体: -apple-system, BlinkMacSystemFont, "SF Pro Text", "PingFang SC"
- 标题字重: 600
- 正文字重: 400

**圆角:**
- 卡片: 12px
- 按钮: 8px
- 输入框: 8px

**间距:**
- 基础单位: 4px
- 常用间距: 8px, 12px, 16px, 24px, 32px

**阴影:**
- 卡片悬浮: 0 2px 8px rgba(0, 0, 0, 0.08)
- 卡片激活: 0 4px 16px rgba(0, 0, 0, 0.12)

**动画:**
- 过渡时间: 0.3s
- 缓动函数: cubic-bezier(0.4, 0, 0.2, 1)

### 7.3 响应式断点
- xs: 0 (手机竖屏)
- sm: 640 (手机横屏)
- md: 768 (平板竖屏)
- lg: 1024 (平板横屏/小笔记本)
- xl: 1280 (桌面)
- xxl: 1536 (大屏)

## 八、开发规范

### 8.1 代码规范
- 使用 Composition API
- 使用 TypeScript strict mode
- 组件命名: PascalCase
- 文件命名: kebab-case
- 变量命名: camelCase
- 常量命名: UPPER_SNAKE_CASE

### 8.2 Git 提交规范
- feat: 新功能
- fix: 修复 bug
- docs: 文档更新
- style: 代码格式调整
- refactor: 重构
- test: 测试相关
- chore: 构建/工具相关

### 8.3 注释规范
- 只说明 Why,不说明 What
- 复杂逻辑必须注释
- 公共组件必须有 JSDoc

## 九、部署方案

### 9.1 构建配置
- 生产环境: `npm run build`
- 输出目录: `dist/`
- 资源压缩: Gzip + Brotli
- 代码分割: 按路由自动分割

### 9.2 环境变量
- `VITE_API_BASE_URL`: API 基础地址
- `VITE_API_KEY`: API 密钥(普通用户)

### 9.3 部署方式
- 静态文件托管(Nginx/CDN)
- Docker 容器化部署
- CI/CD 自动化部署

## 十、后续优化方向

### 10.1 性能优化
- 图片懒加载和 WebP 格式
- 虚拟滚动优化
- 路由懒加载
- 组件按需加载

### 10.2 功能扩展
- 用户个性化推荐
- 视频收藏功能
- 数据导出功能
- 多语言支持

### 10.3 AI 功能增强
- 对应上下文 AI 问答(TODO)
- 更深度的领域专家分析
- 实时数据更新推送

## 十一、技术决策说明

### 11.1 为什么选择 Vue 3 而不是 Flutter Web?

**Vue 3 的优势:**
1. **性能**: 首次加载快(200-500KB vs 2-3MB)
2. **生态**: 组件库成熟,图表库强大(ECharts)
3. **开发体验**: 热更新快,浏览器原生渲染
4. **移动端**: 响应式布局更灵活,手势操作更自然
5. **适用场景**: 纯 Web 应用,不需要跨平台

**Flutter Web 的劣势:**
1. 首次加载慢
2. 文本选择、右键菜单等浏览器原生功能体验差
3. 输入法支持不如原生 HTML
4. 跨平台优势在纯 Web 场景下无法发挥

### 11.2 为什么选择 Naive UI?

1. **设计风格**: 简洁现代,符合 Apple 风格要求
2. **TypeScript**: 完整的类型支持
3. **性能**: 轻量级,按需加载
4. **文档**: 中文文档完善
5. **主题**: 支持深色模式,易于定制

### 11.3 为什么选择 UnoCSS?

1. **性能**: 比 Tailwind CSS 更快
2. **灵活**: 支持自定义规则
3. **体积**: 按需生成,体积更小
4. **兼容**: 支持 Tailwind CSS 语法

## 十二、风险和挑战

### 12.1 技术风险
- ECharts 图表在移动端的性能优化
- 大量数据的虚拟滚动实现
- AI 分析内容的实时生成

### 12.2 解决方案
- 使用 ECharts 的移动端优化配置
- 使用成熟的虚拟滚动库(如 vue-virtual-scroller)
- AI 分析采用异步加载,显示加载状态

## 十三、时间规划

### 13.1 第一阶段: 基础框架搭建(1-2天)
- 项目初始化
- 路由配置
- 状态管理
- API 封装
- 主题系统

### 13.2 第二阶段: 普通用户功能(3-4天)
- 视频列表
- 视频卡片
- 数据看板
- 图表组件
- 响应式适配

### 13.3 第三阶段: 管理后台(2-3天)
- 登录功能
- 关键词管理
- 视频管理
- 任务管理

### 13.4 第四阶段: 优化和测试(1-2天)
- 性能优化
- 样式调整
- 测试和修复

**总计: 7-11 天**

---

**设计完成日期**: 2026-05-07
**设计者**: Claude Opus 4.7
**版本**: v1.0
