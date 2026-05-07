# Vigor Client Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Vue 3 + TypeScript web application for Vigor data analysis platform with user-facing video browsing and admin management features.

**Architecture:** Single-page application with Vue Router for navigation, Pinia for state management, Axios for API communication. Desktop layout uses left-right split (video list + dashboard), mobile uses full-screen with navigation. Admin backend is a separate route tree with authentication.

**Tech Stack:** Vue 3.4+, TypeScript 5.0+, Vite 5.0+, Pinia 2.x, Vue Router 4.x, Naive UI, Vant 4, ECharts 5.x, UnoCSS, Axios

---

## File Structure Overview

### Core Files
- `vigor-client/package.json` - Dependencies and scripts
- `vigor-client/vite.config.ts` - Vite configuration
- `vigor-client/tsconfig.json` - TypeScript configuration
- `vigor-client/uno.config.ts` - UnoCSS configuration
- `vigor-client/index.html` - HTML entry point
- `vigor-client/src/main.ts` - Application entry
- `vigor-client/src/App.vue` - Root component

### Configuration & Environment
- `vigor-client/.env.development` - Development environment variables
- `vigor-client/.env.production` - Production environment variables
- `vigor-client/.eslintrc.js` - ESLint configuration
- `vigor-client/.prettierrc` - Prettier configuration

### Type Definitions
- `vigor-client/src/types/video.ts` - Video related types
- `vigor-client/src/types/keyword.ts` - Keyword related types
- `vigor-client/src/types/stats.ts` - Statistics types
- `vigor-client/src/types/api.ts` - API response types

### API Layer
- `vigor-client/src/api/index.ts` - Axios instance and interceptors
- `vigor-client/src/api/video.ts` - Video API endpoints
- `vigor-client/src/api/keyword.ts` - Keyword API endpoints
- `vigor-client/src/api/stats.ts` - Statistics API endpoints
- `vigor-client/src/api/admin.ts` - Admin API endpoints

### State Management
- `vigor-client/src/stores/user.ts` - User authentication state
- `vigor-client/src/stores/video.ts` - Video data state
- `vigor-client/src/stores/keyword.ts` - Keyword state
- `vigor-client/src/stores/theme.ts` - Theme state
- `vigor-client/src/stores/stats.ts` - Statistics state

### Router
- `vigor-client/src/router/index.ts` - Route definitions and guards

### Styles
- `vigor-client/src/styles/variables.css` - CSS variables for theming
- `vigor-client/src/styles/theme.css` - Theme styles
- `vigor-client/src/styles/reset.css` - CSS reset

### Utilities
- `vigor-client/src/utils/format.ts` - Formatting utilities
- `vigor-client/src/utils/request.ts` - Request utilities
- `vigor-client/src/utils/storage.ts` - LocalStorage utilities

### Composables
- `vigor-client/src/composables/useResponsive.ts` - Responsive breakpoint detection
- `vigor-client/src/composables/useTheme.ts` - Theme management
- `vigor-client/src/composables/useInfiniteScroll.ts` - Infinite scroll logic

### Components - Common
- `vigor-client/src/components/common/ThemeToggle.vue` - Theme toggle button
- `vigor-client/src/components/common/Loading.vue` - Loading spinner

### Components - Video
- `vigor-client/src/components/video/VideoCard.vue` - Video card component
- `vigor-client/src/components/video/VideoList.vue` - Video list with infinite scroll
- `vigor-client/src/components/video/VideoDetail.vue` - Video detail section

### Components - Dashboard
- `vigor-client/src/components/dashboard/DataDashboard.vue` - Main dashboard container
- `vigor-client/src/components/dashboard/InteractionChart.vue` - Interaction data chart
- `vigor-client/src/components/dashboard/CommentSummary.vue` - Comment summary card
- `vigor-client/src/components/dashboard/AIAnalysis.vue` - AI expert analysis card
- `vigor-client/src/components/dashboard/TrendComparison.vue` - Trend comparison chart

### Components - Charts
- `vigor-client/src/components/charts/LineChart.vue` - Line chart wrapper
- `vigor-client/src/components/charts/PieChart.vue` - Pie chart wrapper
- `vigor-client/src/components/charts/RadarChart.vue` - Radar chart wrapper

### Layouts
- `vigor-client/src/layouts/DefaultLayout.vue` - Default layout for home page
- `vigor-client/src/layouts/AdminLayout.vue` - Admin layout with sidebar

### Views - Home
- `vigor-client/src/views/home/HomePage.vue` - Main home page

### Views - Admin
- `vigor-client/src/views/admin/LoginPage.vue` - Admin login
- `vigor-client/src/views/admin/DashboardPage.vue` - Admin dashboard
- `vigor-client/src/views/admin/KeywordsPage.vue` - Keyword management
- `vigor-client/src/views/admin/VideosPage.vue` - Video management
- `vigor-client/src/views/admin/TasksPage.vue` - Task management

---

## Task 1: Project Initialization

**Files:**
- Create: `vigor-client/package.json`
- Create: `vigor-client/vite.config.ts`
- Create: `vigor-client/tsconfig.json`
- Create: `vigor-client/uno.config.ts`
- Create: `vigor-client/index.html`
- Create: `vigor-client/.env.development`
- Create: `vigor-client/.env.production`
- Create: `vigor-client/.eslintrc.js`
- Create: `vigor-client/.prettierrc`
- Create: `vigor-client/.gitignore`

- [ ] **Step 1: Create project directory**

```bash
mkdir -p vigor-client
cd vigor-client
```

- [ ] **Step 2: Initialize package.json**

Create `vigor-client/package.json`:

```json
{
  "name": "vigor-client",
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext .vue,.js,.jsx,.cjs,.mjs,.ts,.tsx,.cts,.mts --fix",
    "format": "prettier --write src/"
  },
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.2.0",
    "pinia": "^2.1.0",
    "axios": "^1.6.0",
    "naive-ui": "^2.38.0",
    "vant": "^4.8.0",
    "echarts": "^5.5.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "@vue/tsconfig": "^0.5.0",
    "typescript": "^5.3.0",
    "vue-tsc": "^1.8.0",
    "vite": "^5.0.0",
    "@unocss/reset": "^0.58.0",
    "unocss": "^0.58.0",
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "@typescript-eslint/parser": "^6.0.0",
    "eslint": "^8.0.0",
    "eslint-plugin-vue": "^9.0.0",
    "prettier": "^3.0.0",
    "vitest": "^1.0.0"
  }
}
```

- [ ] **Step 3: Create vite.config.ts**

Create `vigor-client/vite.config.ts`:

```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import UnoCSS from 'unocss/vite'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue(), UnoCSS()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

- [ ] **Step 4: Create tsconfig.json**

Create `vigor-client/tsconfig.json`:

```json
{
  "extends": "@vue/tsconfig/tsconfig.dom.json",
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "preserve",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src/**/*.ts", "src/**/*.tsx", "src/**/*.vue"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

- [ ] **Step 5: Create tsconfig.node.json**

Create `vigor-client/tsconfig.node.json`:

```json
{
  "extends": "@vue/tsconfig/tsconfig.node.json",
  "include": ["vite.config.*", "uno.config.*"],
  "compilerOptions": {
    "composite": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "types": ["node"]
  }
}
```

- [ ] **Step 6: Create uno.config.ts**

Create `vigor-client/uno.config.ts`:

```typescript
import { defineConfig, presetUno, presetAttributify } from 'unocss'

export default defineConfig({
  presets: [presetUno(), presetAttributify()],
  theme: {
    breakpoints: {
      xs: '0px',
      sm: '640px',
      md: '768px',
      lg: '1024px',
      xl: '1280px',
      xxl: '1536px'
    }
  }
})
```

- [ ] **Step 7: Create index.html**

Create `vigor-client/index.html`:

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/logo.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Vigor - 数据分析平台</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
```

- [ ] **Step 8: Create environment files**

Create `vigor-client/.env.development`:

```
VITE_API_BASE_URL=http://localhost:8000
VITE_API_KEY=dev-api-key
```

Create `vigor-client/.env.production`:

```
VITE_API_BASE_URL=https://api.vigor.example.com
VITE_API_KEY=prod-api-key
```

- [ ] **Step 9: Create ESLint configuration**

Create `vigor-client/.eslintrc.js`:

```javascript
module.exports = {
  root: true,
  env: {
    browser: true,
    es2021: true,
    node: true
  },
  extends: [
    'eslint:recommended',
    'plugin:vue/vue3-recommended',
    'plugin:@typescript-eslint/recommended'
  ],
  parser: 'vue-eslint-parser',
  parserOptions: {
    ecmaVersion: 'latest',
    parser: '@typescript-eslint/parser',
    sourceType: 'module'
  },
  plugins: ['vue', '@typescript-eslint'],
  rules: {
    'vue/multi-word-component-names': 'off',
    '@typescript-eslint/no-explicit-any': 'warn'
  }
}
```

- [ ] **Step 10: Create Prettier configuration**

Create `vigor-client/.prettierrc`:

```json
{
  "semi": false,
  "singleQuote": true,
  "trailingComma": "none",
  "printWidth": 100,
  "tabWidth": 2,
  "endOfLine": "lf"
}
```

- [ ] **Step 11: Create .gitignore**

Create `vigor-client/.gitignore`:

```
# Dependencies
node_modules

# Build output
dist
dist-ssr
*.local

# Editor
.vscode/*
!.vscode/extensions.json
.idea
.DS_Store
*.suo
*.ntvs*
*.njsproj
*.sln
*.sw?

# Environment
.env.local
.env.*.local

# Logs
logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
lerna-debug.log*
```

- [ ] **Step 12: Install dependencies**

```bash
cd vigor-client
npm install
```

Expected: Dependencies installed successfully

- [ ] **Step 13: Commit**

```bash
git add vigor-client/
git commit -m "feat(client): initialize Vue 3 project with Vite, TypeScript, and UnoCSS"
```

---

## Task 2: TypeScript Type Definitions

**Files:**
- Create: `vigor-client/src/types/video.ts`
- Create: `vigor-client/src/types/keyword.ts`
- Create: `vigor-client/src/types/stats.ts`
- Create: `vigor-client/src/types/api.ts`

- [ ] **Step 1: Create video types**

Create `vigor-client/src/types/video.ts`:

```typescript
export interface Video {
  id: number
  douyin_id: string
  title: string
  author_name: string | null
  author_id: string | null
  cover_url: string | null
  video_url: string | null
  like_count: number
  comment_count: number
  share_count: number
  heat_score: number | null
  publish_time: string | null
  summary: string | null
  comment_summary?: CommentSummary
}

export interface CommentSummary {
  summary: string
  top_keywords: string[]
  sentiment: 'positive' | 'neutral' | 'negative'
  generated_at: string
  comment_count: number
}

export interface Comment {
  id: number
  video_id: number
  content: string
  author_name: string | null
  like_count: number
  created_at: string
}

export interface VideoListParams {
  keyword_id?: number
  time_window?: '1d' | '3d' | '7d' | '15d' | '30d'
  sort?: 'heat_score' | 'publish_time'
  limit?: number
  offset?: number
}

export interface VideoListResponse {
  total: number
  data: Video[]
}
```

- [ ] **Step 2: Create keyword types**

Create `vigor-client/src/types/keyword.ts`:

```typescript
export interface Keyword {
  id: number
  keyword: string
  category: string | null
  status: 'active' | 'inactive'
  crawl_threshold: number
  priority: number
  created_at: string
  updated_at: string
}

export interface KeywordCreateInput {
  keyword: string
  category?: string
  crawl_threshold?: number
  priority?: number
}

export interface KeywordUpdateInput {
  keyword?: string
  category?: string
  status?: 'active' | 'inactive'
  crawl_threshold?: number
  priority?: number
}
```

- [ ] **Step 3: Create stats types**

Create `vigor-client/src/types/stats.ts`:

```typescript
export interface KeywordStats {
  keyword_id: number
  keyword: string
  video_count: number
  avg_heat_score: number
}

export interface TrendStats {
  date: string
  video_count: number
  avg_heat_score: number
}
```

- [ ] **Step 4: Create API response types**

Create `vigor-client/src/types/api.ts`:

```typescript
export interface ApiResponse<T = any> {
  data: T
  message?: string
  code?: number
}

export interface ApiError {
  message: string
  code: number
  details?: any
}

export interface PaginationParams {
  limit?: number
  offset?: number
}

export interface PaginationResponse<T> {
  total: number
  data: T[]
}
```

- [ ] **Step 5: Commit**

```bash
git add vigor-client/src/types/
git commit -m "feat(client): add TypeScript type definitions for API models"
```

---

## Task 3: Styles and Theme System

**Files:**
- Create: `vigor-client/src/styles/variables.css`
- Create: `vigor-client/src/styles/theme.css`
- Create: `vigor-client/src/styles/reset.css`

- [ ] **Step 1: Create CSS variables**

Create `vigor-client/src/styles/variables.css`:

```css
:root {
  /* Light theme */
  --bg-primary: #ffffff;
  --bg-secondary: #f5f5f7;
  --bg-tertiary: #e8e8ed;
  --text-primary: #1d1d1f;
  --text-secondary: #6e6e73;
  --text-tertiary: #86868b;
  --border-color: #d2d2d7;
  --primary-color: #007aff;
  --success-color: #34c759;
  --warning-color: #ff9500;
  --error-color: #ff3b30;
  --shadow: rgba(0, 0, 0, 0.1);
  
  /* Spacing */
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 12px;
  --spacing-lg: 16px;
  --spacing-xl: 24px;
  --spacing-xxl: 32px;
  
  /* Border radius */
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  
  /* Transitions */
  --transition-fast: 0.15s cubic-bezier(0.4, 0, 0.2, 1);
  --transition-base: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  --transition-slow: 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

[data-theme='dark'] {
  --bg-primary: #000000;
  --bg-secondary: #1c1c1e;
  --bg-tertiary: #2c2c2e;
  --text-primary: #ffffff;
  --text-secondary: #ebebf5;
  --text-tertiary: #8e8e93;
  --border-color: #38383a;
  --primary-color: #0a84ff;
  --success-color: #30d158;
  --warning-color: #ff9f0a;
  --error-color: #ff453a;
  --shadow: rgba(255, 255, 255, 0.1);
}
```

- [ ] **Step 2: Create theme styles**

Create `vigor-client/src/styles/theme.css`:

```css
body {
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'PingFang SC', sans-serif;
  background-color: var(--bg-primary);
  color: var(--text-primary);
  transition: background-color var(--transition-base), color var(--transition-base);
}

/* Card styles */
.card {
  background-color: var(--bg-secondary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  box-shadow: 0 2px 8px var(--shadow);
  transition: box-shadow var(--transition-base), transform var(--transition-base);
}

.card:hover {
  box-shadow: 0 4px 16px var(--shadow);
  transform: translateY(-2px);
}

/* Button styles */
.btn {
  padding: var(--spacing-sm) var(--spacing-lg);
  border-radius: var(--radius-md);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
  border: none;
  outline: none;
}

.btn-primary {
  background-color: var(--primary-color);
  color: white;
}

.btn-primary:hover {
  opacity: 0.9;
}

.btn-secondary {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}

.btn-secondary:hover {
  background-color: var(--border-color);
}

/* Input styles */
.input {
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background-color: var(--bg-primary);
  color: var(--text-primary);
  transition: border-color var(--transition-fast);
}

.input:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.1);
}

/* Scrollbar */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--bg-secondary);
}

::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--text-tertiary);
}
```

- [ ] **Step 3: Create CSS reset**

Create `vigor-client/src/styles/reset.css`:

```css
*,
*::before,
*::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html {
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  min-height: 100vh;
  line-height: 1.5;
}

img,
picture,
video,
canvas,
svg {
  display: block;
  max-width: 100%;
}

input,
button,
textarea,
select {
  font: inherit;
}

p,
h1,
h2,
h3,
h4,
h5,
h6 {
  overflow-wrap: break-word;
}

a {
  text-decoration: none;
  color: inherit;
}

ul,
ol {
  list-style: none;
}
```

- [ ] **Step 4: Commit**

```bash
git add vigor-client/src/styles/
git commit -m "feat(client): add CSS variables and theme system for light/dark modes"
```

---

## Task 4: Utilities

**Files:**
- Create: `vigor-client/src/utils/format.ts`
- Create: `vigor-client/src/utils/storage.ts`

- [ ] **Step 1: Create format utilities**

Create `vigor-client/src/utils/format.ts`:

```typescript
export function formatNumber(num: number): string {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'w'
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'k'
  }
  return num.toString()
}

export function formatDate(dateString: string | null): string {
  if (!dateString) return '-'
  
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)
  
  if (minutes < 60) {
    return `${minutes}分钟前`
  }
  if (hours < 24) {
    return `${hours}小时前`
  }
  if (days < 7) {
    return `${days}天前`
  }
  
  return date.toLocaleDateString('zh-CN')
}

export function formatHeatScore(score: number | null): {
  text: string
  color: string
} {
  if (score === null) {
    return { text: '-', color: 'gray' }
  }
  
  if (score >= 80) {
    return { text: score.toFixed(1), color: 'red' }
  }
  if (score >= 60) {
    return { text: score.toFixed(1), color: 'orange' }
  }
  return { text: score.toFixed(1), color: 'gray' }
}

export function formatSentiment(sentiment: string): {
  text: string
  color: string
} {
  const map: Record<string, { text: string; color: string }> = {
    positive: { text: '正面', color: 'green' },
    neutral: { text: '中性', color: 'gray' },
    negative: { text: '负面', color: 'red' }
  }
  return map[sentiment] || { text: '未知', color: 'gray' }
}
```

- [ ] **Step 2: Create storage utilities**

Create `vigor-client/src/utils/storage.ts`:

```typescript
const STORAGE_PREFIX = 'vigor_'

export const storage = {
  get<T>(key: string): T | null {
    try {
      const item = localStorage.getItem(STORAGE_PREFIX + key)
      return item ? JSON.parse(item) : null
    } catch {
      return null
    }
  },

  set<T>(key: string, value: T): void {
    try {
      localStorage.setItem(STORAGE_PREFIX + key, JSON.stringify(value))
    } catch (error) {
      console.error('Storage set error:', error)
    }
  },

  remove(key: string): void {
    localStorage.removeItem(STORAGE_PREFIX + key)
  },

  clear(): void {
    const keys = Object.keys(localStorage)
    keys.forEach((key) => {
      if (key.startsWith(STORAGE_PREFIX)) {
        localStorage.removeItem(key)
      }
    })
  }
}

export const TOKEN_KEY = 'token'
export const THEME_KEY = 'theme'
export const USER_KEY = 'user'
```

- [ ] **Step 3: Commit**

```bash
git add vigor-client/src/utils/
git commit -m "feat(client): add utility functions for formatting and storage"
```

---

