# 清空按钮功能实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在推荐岗位和岗位列表面板中添加"清空"按钮，允许用户快速清空列表内容

**Architecture:** 后端添加两个清空API端点，前端添加对应的API客户端函数和UI按钮，使用confirm()进行确认

**Tech Stack:** FastAPI, React, SQLite (SQLModel)

---

## 文件结构

- `backend/app/routes/recommendations.py` - 添加清空推荐岗位API
- `backend/app/routes/jobs.py` - 添加清空岗位列表API
- `frontend/src/lib/api.js` - 添加清空API客户端函数
- `frontend/src/App.jsx` - 添加清空按钮和事件处理

---

### Task 1: 后端 - 清空推荐岗位API

**Files:**
- Modify: `backend/app/routes/recommendations.py`

- [ ] **Step 1: 添加清空推荐岗位端点**

在 `recommendations.py` 文件末尾添加以下代码：

```python
@router.post("/clear")
def clear_recommendations(session: Session = Depends(get_session)):
    records = session.exec(
        select(RecommendedJobRecord).where(RecommendedJobRecord.status != "dismissed")
    ).all()
    for record in records:
        record.status = "dismissed"
        session.add(record)
    session.commit()
    return {"ok": True}
```

- [ ] **Step 2: 验证代码语法**

运行：`cd F:/make_jobs/backend && python -c "from app.routes.recommendations import router; print('OK')"`
预期：输出 "OK"

- [ ] **Step 3: Commit**

```bash
git add backend/app/routes/recommendations.py
git commit -m "feat: add clear recommendations API endpoint"
```

---

### Task 2: 后端 - 清空岗位列表API

**Files:**
- Modify: `backend/app/routes/jobs.py`

- [ ] **Step 1: 添加清空岗位列表端点**

在 `jobs.py` 文件末尾添加以下代码：

```python
@router.post("/clear")
def clear_jobs(session: Session = Depends(get_session)):
    records = session.exec(select(JobRecord)).all()
    for record in records:
        session.delete(record)
    session.commit()
    return {"ok": True}
```

- [ ] **Step 2: 验证代码语法**

运行：`cd F:/make_jobs/backend && python -c "from app.routes.jobs import router; print('OK')"`
预期：输出 "OK"

- [ ] **Step 3: Commit**

```bash
git add backend/app/routes/jobs.py
git commit -m "feat: add clear jobs API endpoint"
```

---

### Task 3: 前端 - 添加API客户端函数

**Files:**
- Modify: `frontend/src/lib/api.js`

- [ ] **Step 1: 添加清空推荐岗位函数**

在 `api.js` 文件中 `dismissRecommendation` 函数后添加：

```javascript
export function clearRecommendations() {
  return request('/recommendations/clear', {
    method: 'POST',
  });
}
```

- [ ] **Step 2: 添加清空岗位列表函数**

在 `api.js` 文件中 `clearRecommendations` 函数后添加：

```javascript
export function clearJobs() {
  return request('/jobs/clear', {
    method: 'POST',
  });
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/lib/api.js
git commit -m "feat: add clear recommendations and jobs API client functions"
```

---

### Task 4: 前端 - 添加推荐岗位清空按钮

**Files:**
- Modify: `frontend/src/App.jsx`

- [ ] **Step 1: 导入新的API函数**

在 `App.jsx` 文件顶部的 import 语句中添加 `clearRecommendations`：

```javascript
import {
  confirmApplication,
  clearRecommendations,  // 添加这行
  dismissRecommendations,
  // ... 其他导入
} from './lib/api';
```

- [ ] **Step 2: 添加清空推荐岗位的事件处理函数**

在 `App.jsx` 文件中 `handleDismissRecommendation` 函数后添加：

```javascript
const handleClearRecommendations = useCallback(async () => {
  if (!window.confirm('确定要清空所有推荐岗位吗？此操作不可撤销。')) return;
  setBusy(true);
  setError('');
  setMessage('');
  try {
    await clearRecommendations();
    await refresh();
    setMessage('推荐岗位已清空。');
  } catch (err) {
    setError(err.message || '清空推荐岗位失败');
  } finally {
    setBusy(false);
  }
}, [refresh]);
```

- [ ] **Step 3: 在推荐岗位面板添加清空按钮**

在 `App.jsx` 文件中推荐岗位面板标题栏（第822-825行）添加清空按钮：

```jsx
<div className="panel-header">
  <h2>推荐岗位</h2>
  <div style={{ display: 'flex', gap: 8 }}>
    <button type="button" className="secondary" disabled={busy} onClick={handleRefreshRecommendations}>
      {btnStatus.refresh === 'loading' ? <><span className="spinner" /> 刷新中…</> : btnStatus.refresh === 'done' ? '刷新成功' : '刷新推荐岗位'}
    </button>
    <button type="button" className="ghost" disabled={busy} onClick={handleClearRecommendations}>
      🗑️ 清空
    </button>
  </div>
</div>
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/App.jsx
git commit -m "feat: add clear button to recommendations panel"
```

---

### Task 5: 前端 - 添加岗位列表清空按钮

**Files:**
- Modify: `frontend/src/App.jsx`

- [ ] **Step 1: 导入新的API函数**

在 `App.jsx` 文件顶部的 import 语句中添加 `clearJobs`：

```javascript
import {
  confirmApplication,
  clearJobs,  // 添加这行
  clearRecommendations,
  dismissRecommendations,
  // ... 其他导入
} from './lib/api';
```

- [ ] **Step 2: 添加清空岗位列表的事件处理函数**

在 `App.jsx` 文件中 `handleClearRecommendations` 函数后添加：

```javascript
const handleClearJobs = useCallback(async () => {
  if (!window.confirm('确定要清空所有岗位吗？此操作不可撤销。')) return;
  setBusy(true);
  setError('');
  setMessage('');
  try {
    await clearJobs();
    await refresh();
    setMessage('岗位列表已清空。');
  } catch (err) {
    setError(err.message || '清空岗位列表失败');
  } finally {
    setBusy(false);
  }
}, [refresh]);
```

- [ ] **Step 3: 在岗位列表面板添加清空按钮**

在 `App.jsx` 文件中岗位列表面板标题（第1084行）添加清空按钮：

```jsx
<div className="panel-header">
  <h2>岗位列表</h2>
  <button type="button" className="ghost" disabled={busy} onClick={handleClearJobs}>
    🗑️ 清空
  </button>
</div>
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/App.jsx
git commit -m "feat: add clear button to jobs list panel"
```

---

### Task 6: 测试验证

**Files:**
- Test: 手动测试

- [ ] **Step 1: 启动后端服务**

运行：`cd F:/make_jobs/backend && .venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000`

- [ ] **Step 2: 启动前端服务**

运行：`cd F:/make_jobs/frontend && npx vite`

- [ ] **Step 3: 测试推荐岗位清空功能**

1. 打开 http://127.0.0.1:5173
2. 保存简历资料
3. 点击"刷新推荐岗位"获取推荐岗位
4. 点击"清空"按钮
5. 确认对话框显示，点击确定
6. 验证推荐岗位列表被清空

- [ ] **Step 4: 测试岗位列表清空功能**

1. 导入几个岗位到岗位列表
2. 点击"清空"按钮
3. 确认对话框显示，点击确定
4. 验证岗位列表被清空

- [ ] **Step 5: 测试取消清空功能**

1. 点击"清空"按钮
2. 在确认对话框中点击取消
3. 验证列表保持不变

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "test: verify clear buttons functionality"
```
