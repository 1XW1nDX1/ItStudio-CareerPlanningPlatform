# ItStudio 职业规划平台 / Career Planning Platform

本仓库为统一整理后的主仓库，包含前端、后端和算法服务的全部内容。

## 目录结构

```
ItStudio-CareerPlanningPlatform/
├─ backend/     # 后端服务（Kotlin + Spring Boot）
├─ frontend/    # 前端应用（Vue / React + TypeScript + Vite）
├─ algorithm/   # 算法服务（Python，职位推荐模型）
├─ careeer/     # 职业路径推荐服务（Python）
├─ .gitignore
└─ README.md
```

## 各模块说明

### backend/
基于 Kotlin + Spring WebFlux 构建的后端 API 服务，包含用户认证、文件上传等功能。

### frontend/
基于 Vue/React + TypeScript + Vite 构建的前端单页应用。

### algorithm/
职位推荐算法服务，基于 Python，使用预训练模型进行推理。

### careeer/
职业路径规划推荐服务，基于 Python，与 algorithm 模块结构类似。

## 分支说明

- `main`（本分支整理结果）：统一目录结构，供作为新主分支使用
- `backend-dev`：后端开发分支（内容已整合至 `backend/`）
- `frontend-dev`：前端开发分支（内容已整合至 `frontend/`）
- `algorithms`：算法开发分支（内容已整合至 `algorithm/` 和 `careeer/`）
