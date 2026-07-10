# 優化規劃路線圖

> 分析基礎：`docs/architecture_analysis.md`
> 建立日期：2026-07-10

---

## 總覽

三個階段，依風險與收益排序。每項任務標記預估工作量（S: <2h, M: 2–8h, L: 1–3d）。

---

## 第一階段：安全與穩定性

> 目標：消除已知崩潰風險與資料遺失問題。不改變外部 API 形狀。

| ID | 任務 | 檔案 | 工作量 |
|----|------|------|--------|
| **S1** | 加入 graceful shutdown | `app.py`, `kinect_service.py`, `attendance_pipeline.py` | M |
| **S2** | 修復 face_recognition_db 讀寫競爭 | `face_recognition_db.py` | S |
| **S3** | 移除 `_export_once` bare except | `app.py` | S |
| **S4** | 假資料與真實資料分流 | `app.py` | S |
| **S5** | 加入 Flask error handler | `app.py` | S |

### S1 — Graceful Shutdown

**現況**：daemon thread 被強制終止 → Kinect 硬體未釋放、出席記錄未寫入。

**方案**：

```python
# app.py — 模組層級
import atexit
import signal

def _shutdown():
    """依序清理所有背景服務"""
    logging.info("shutdown initiated")
    AUTO_CSV_EXPORTER.stop()
    RECOGNITION_PIPELINE.stop()    # 新增方法：_running=False, 儲存出席, 釋放資源
    KINECT_SERVICE.disconnect()     # 釋放硬體
    logging.info("shutdown complete")

atexit.register(_shutdown)
signal.signal(signal.SIGINT, lambda *_: _shutdown())
signal.signal(signal.SIGTERM, lambda *_: _shutdown())
```

**`attendance_pipeline.py`** — 新增 `stop()`:

```python
def stop(self):
    self._running = False
    self._wake_event.set()
    if self._thread.is_alive():
        self._thread.join(timeout=5.0)
    with self._lock:
        self._save_presence_records_locked()
```

### S2 — 修復 face_recognition_db 讀寫競爭

**現況**：`load_database()` 不持鎖（讀取），`build_database()` 持鎖（寫入）→ TOCTOU。

**方案**：引入 `threading.RLock`，`load_database()` 也持有鎖，或使用 `RWLock`（`readerwriterlock` 套件）：

```python
# 方案 A：RLock（最簡單，與現有設計一致）
def load_database(self):
    with self._lock:
        if self._cached_time == self._db_path.stat().st_mtime:
            return
        self._embeddings = json.loads(self._db_path.read_text())
        self._cached_time = self._db_path.stat().st_mtime
```

### S3 — 移除 bare except

**現況**：`_export_once()` 內 `except Exception: pass`。

**方案**：改為 `logging.exception("CSV export failed, will retry")`。

### S4 — 假資料分流

**現況**：`_export_once()` 中 `assignment_score`, `attendance_rate`, `submission_punctuality` 為偽隨機模擬資料，與真實管線資料混在同一 CSV。

**方案**：
1. 在 `get_status()` 回傳值中加入 `is_mock` flag 標記缺值欄位
2. CSV 中將無真實資料的欄位留空或標註 `"N/A"`
3. 或將模擬欄位移至獨立輸出（如 `mock_metrics.csv`）

### S5 — Flask Error Handler

**現況**：無 error handler，任何未捕捉異常直接回傳 Flask 預設 500 頁面。

**方案**：

```python
@app.errorhandler(Exception)
def handle_exception(e):
    logging.exception("unhandled exception")
    return jsonify(error=str(e)), 500
```

---

## 第二階段：架構重構

> 目標：拆分巨型類別、消除死碼、改善模組化。

| ID | 任務 | 工作量 |
|----|------|--------|
| **R1** | 刪除死碼 `recognition_pipeline.py` | S |
| **R2** | 將 `config.py` 重構為 Dataclass 驗證模型 | M |
| **R3** | 拆分 `attendance_pipeline.py` | L |
| **R4** | 引入依賴注入取代全域變數 | M |
| **R5** | 引入 Blueprint 路由分組 | M |
| **R6** | 同步移除 `requirements.txt` | S |

### R3 — 拆分 `attendance_pipeline.py`（最關鍵）

**目標結構**：

```
src/vision/
  detection/
    __init__.py
    detector.py          # YOLO 模型管理與人物偵測
    tracker.py           # IoU + center-distance 追蹤器
  recognition/
    __init__.py
    face_linker.py       # 嵌入匹配 + 身分連結
    identity_manager.py  # TemporaryPerson / ConfirmedPerson 生命週期
  metrics/
    __init__.py
    engine.py            # PoseDepthMetricEngine（現有，移動）
  rendering/
    __init__.py
    annotator.py         # 畫面標註 / PIL 繪圖
  pipeline.py            # 剩餘的 Orchestrator（串接上述模組）
  streaming.py           # MJPEG 串流
```

**拆分原則**：
- 每個新模組 ≤ 500 行
- 每個類別單一職責
- 透過建構子注入相依，而非直接 import
- 保留現有 `RecognitionPipeline` public API 形狀不變（向後相容）

### R4 — 依賴注入

**現況**：

```python
# app.py 模組層級
FACE_DB = FaceRecognitionDB(BASE_DIR)
KINECT_SERVICE = KinectService(BASE_DIR)
RECOGNITION_PIPELINE = RecognitionPipeline(BASE_DIR, KINECT_SERVICE, FACE_DB)
```

路由函數直接存取這些全域變數。

**方案**：使用 Flask `g` 物件 + `app.config`：

```python
# app.py
def create_app():
    app = Flask(__name__)
    app.config.from_mapping(...)

    with app.app_context():
        g.face_db = FaceRecognitionDB(app.config['BASE_DIR'])
        g.kinect = KinectService(app.config['BASE_DIR'])
        g.pipeline = RecognitionPipeline(...)
    return app

# 路由
@app.route('/api/attendance/status')
def attendance_status():
    return jsonify(g.pipeline.get_status())
```

---

## 第三階段：前端與測試

| ID | 任務 | 工作量 |
|----|------|--------|
| **T1** | 拆分 `dashboard.html` → HTML / CSS / JS | L |
| **T2** | 為核心管線加入單元測試 | L |
| **T3** | 用錄製影片建立整合測試 | M |

### T1 — 前端拆解

```
static/
  css/
    base.css            # CSS 變數、重設
    theme_light.css     # 淺色主題
    theme_dark.css      # 深色主題
    dashboard.css       # 佈局與元件
  js/
    api.js              # API 呼叫封裝
    charts.js           # SVG 圖表繪製
    dashboard.js        # 視圖切換與輪詢
    enrollment.js       # 學生註冊流程
    chat.js             # 對話元件
templates/
  index.html            # 登入頁（不變）
  dashboard.html        # 儀表板（僅 HTML 結構）
```

每個 JS 模組以 IIFE 或 ES module 方式隔離作用域。

### T2 — 測試規劃

優先測試順序（依風險）：

1. `PoseDepthMetricEngine` — 所有 8 項指標（現有僅 hand-raise）
2. `FaceRecognitionDB` — 嵌入匹配、資料庫重建、多執行緒安全
3. `KinectService` — 後端切換、frame 擷取（可用影片 mock）
4. 人物追蹤器 — IoU 匹配、track ID 分配、timeout 過期
5. 管線整合 — 用錄製影片驗證端到端

```python
# 建議測試結構
tests/
  test_pose_depth_metrics.py    # 擴充
  test_face_recognition_db.py   # 新增
  test_kinect_service.py        # 新增
  test_tracker.py               # 新增
  test_integration.py           # 新增
```

### T3 — 整合測試

使用 `scripts/` 中已有的影片錄製功能作為測試輸入：

```python
def test_end_to_end_with_video():
    """用錄製影片驗證完整管線"""
    pass  # 確認 pipeline 輸出 frame_count、detected_count、presence_records
```

---

## 執行優先級矩陣

```
            高風險
              │
    S1  S2    │   S3  S4  S5
    (立即)    │   (本週)
              │
  ────────────┼────────────
              │
    R3  R4    │   R1  R2  R5  R6
    (本月)    │   (本月)
              │
    T1  T2    │   T3
    (下月)    │   (下月)
              │
            低風險
```

---

## 不變原則

1. **不改變現有 HTTP API 形狀**（路徑、方法、回應格式）
2. **不改變 `config.toml` 結構**（可新增，不移除）
3. **不改變 `dashboard.html` 的使用者介面行為**
4. **每次重構後執行現有測試確保不回歸**
5. **階段性合併，不一次巨型 PR**

---

## 進度追蹤

| ID | 狀態 | 開始日 | 完成日 | 備註 |
|----|------|--------|--------|------|
| S1 | ⬜ 待辦 | - | - | |
| S2 | ⬜ 待辦 | - | - | |
| S3 | ⬜ 待辦 | - | - | |
| S4 | ⬜ 待辦 | - | - | |
| S5 | ⬜ 待辦 | - | - | |
| R1 | ⬜ 待辦 | - | - | |
| R2 | ⬜ 待辦 | - | - | |
| R3 | ⬜ 待辦 | - | - | |
| R4 | ⬜ 待辦 | - | - | |
| R5 | ⬜ 待辦 | - | - | |
| R6 | ⬜ 待辦 | - | - | |
| T1 | ⬜ 待辦 | - | - | |
| T2 | ⬜ 待辦 | - | - | |
| T3 | ⬜ 待辦 | - | - | |
