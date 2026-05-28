# QtCloud HR — 招聘系统 MVP

基于 FastAPI + SQLite 的招聘管理系统。

依赖两个上游系统：
- **QtCloud Org**（`../qtadmin-org`）— 岗位定义
- **QtCloud Auth**（`../qtadmin-auth`）— 用户档案

## 数据模型

```
Auth:  UserProfile ── 身份档案（real_name, email, phone, school）

Org:   Position ── 岗位定义

HR:    Plan ── 招聘计划（org_position_id, headcount, period, status）
         │
         Recruitment ── 招聘活动（plan_id, recruiter, target_date, status）
           │
           Talent ── 人才（user_profile_id, stage, assigned_to）
```

- **Talent** 只存招聘进度，身份信息通过 `user_profile_id` 从 Auth 读取
- **Talent.stage** 覆盖 seeker / applicant / candidate 三个阶段

## 快速开始

```bash
# 终端 1：Org（岗位定义）
cd ../qtadmin-org && uvicorn app.main:app --reload --port 8001

# 终端 2：Auth（用户档案）
cd ../qtadmin-auth && uvicorn app.main:app --reload --port 8002

# 终端 3：HR（招聘系统）
cd ../qtadmin-hr
QTCLOUD_HR_ORG_API_URL=http://127.0.0.1:8001 \
QTCLOUD_HR_AUTH_API_URL=http://127.0.0.1:8002 \
uvicorn app.main:app --reload --port 8000
```

## API 概览

| 端点 | 方法 | 说明 |
|------|------|------|
| `/plans` | GET/POST | 计划列表/创建 |
| `/plans/{id}` | GET/PATCH/DELETE | 计划详情/更新/删除 |
| `/recruitments` | GET/POST | 活动列表/创建 |
| `/recruitments/{id}` | GET/PATCH/DELETE | 活动详情/更新/删除 |
| `/recruitments/{id}/applicants` | GET/POST | 活动的申请者列表/创建 |
| `/recruitments/{id}/applicants/{aid}` | GET/PATCH/DELETE | 申请者详情/更新/删除 |
| `/recruitments/{id}/applicants/{aid}/transition` | POST | 推进阶段 |
| `/pipeline` | GET | 看板（按 Applicant.stage 聚合） |

## 状态流转

```
new → contacted → exam_sent → exam_received → evaluating → interview → offer → closed
```

## 一站式创建

```bash
# 1. Auth 创建用户档案
curl -X POST http://127.0.0.1:8002/user-profiles \
  -d '{"real_name":"张三","email":"zs@test.com","school":"某大学"}'

# 2. Org 创建岗位
curl -X POST http://127.0.0.1:8001/positions \
  -d '{"name":"技术实习生","department":"技术部"}'

# 3. HR 创建计划
curl -X POST http://127.0.0.1:8000/plans \
  -d '{"org_position_id":1,"headcount":3}'

# 4. HR 创建招聘活动
curl -X POST http://127.0.0.1:8000/recruitments \
  -d '{"plan_id":1,"name":"5月招聘","recruiter":"刘婧怡"}'

# 5. HR 添加 Talent（引用 Auth 的用户）
curl -X POST http://127.0.0.1:8000/recruitments/1/talents \
  -d '{"user_profile_id":1}'
```
