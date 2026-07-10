# 架構分析報告

> 分析日期：2026-07-10

---

## 1. 專案概覽

基於 Flask 的 Kinect 教室行為分析系統。核心管線：

```
Kinect 硬體 → 影像擷取 → YOLO 姿態檢測 + InsightFace 人臉辨識 → 行為指標計算 → Web 儀表板
```

| 項目 | 值 |
|------|-----|
| 語言 | Python 3.11–3.12 |
| Web 框架 | Flask 3.1.3（threaded 模式） |
| 硬體 | Kinect v1 / v2 / 影片回退 |
| GPU | NVIDIA CUDA 13.0 (PyTorch cu130) |
| 套件管理 | uv（pyproject.toml） |
| 總 Python 程式碼 | ~9,000 行 |
| 測試覆蓋 | <1%（僅 hand-raise 判斷 5 案例） |

---

## 2. 模組結構

```
app.py                          # Flask 入口 (997 行)
src/
  config.py                     # TOML → env var (94 行)
  vision/
    kinect_service.py           # 硬體抽象層 (764 行)
    attendance_pipeline.py      # 主管線 (3,237 行) ← God Class
    recognition_pipeline.py     # 舊版管線 (509 行) ← 死碼
    face_recognition_db.py      # 人臉嵌入資料庫 (495 行)
    pose_depth_metrics.py       # 行為指標引擎 (585 行)
    rgb_depth_alignment.py      # RGB-D 對齊 (267 行)
templates/
  index.html                    # 登入頁 (235 行)
  dashboard.html                # 儀表板 (6,318 行) ← 巨型單體
scripts/                        # CLI 工具 (10 個)
clustering/k_means.py           # K-means 分群 (691 行)
tests/test_pose_depth_metrics.py # 唯一測試 (43 行)
```

---

## 3. 資料流

```
┌─────────────┐    frame_bundle     ┌──────────────────┐
│ KinectService│ ─────────────────→ │ RecognitionPipeline│
│ _capture_loop│   (color+depth)    │   _loop()         │
│ (daemon)     │                    │   (daemon)        │
└─────────────┘                    │                    │
                                   │ YOLO 姿態檢測      │
┌─────────────┐                    │ IoU 追蹤           │
│FaceRecogDB  │ ←── embedding ────→ │ InsightFace 嵌入   │
│ (JSON 檔案) │                    │ 身分連結           │
└─────────────┘                    │ PoseDepthMetric    │
                                   │ FrameRenderer      │
┌──────────────────┐               │                    │
│MinuteStudentCSV  │ ← get_status()│                    │
│_loop() (daemon)  │               └────────┬───────────┘
│每 60 秒輸出 CSV   │                        │
└──────────────────┘               ┌────────▼───────────┐
                                   │ Flask /api/* routes │
                                   │ MJPEG streams       │
                                   │ dashboard.html      │
                                   └────────────────────┘
```

---

## 4. 組件職責分析

### 4.1 `KinectService` — 硬體抽象層

| 項 | 評 |
|----|-----|
| 職責 | 清晰：擷取、編碼、連接管理 |
| 執行緒 | 單一 daemon thread，Lock 保護 frame |
| 問題 | 後端選擇邏輯分散（v1/v2/video），可引入策略模式 |
| 問題 | 無 `close()` 呼叫，硬體資源依賴 daemon 強制終止 |

### 4.2 `RecognitionPipeline` — 主管線（主要問題來源）

| 項 | 評 |
|----|-----|
| 職責 | **過多**：偵測、追蹤、辨識、身分連結、指標、渲染、串流、CSS 動畫 |
| 行數 | 3,237 → 建議拆分為 5–6 個模組 |
| 執行緒 | RLock + Lock + Event + daemon thread |
| 狀態 | `_temporary_people`, `_confirmed_people`, `_status`, `_current_course` 全混在一個類別 |
| 參數 | 30+ 個可調參數，分散在類別屬性 / JSON / 環境變數三處 |

### 4.3 `FaceRecognitionDB` — 人臉資料庫

| 項 | 評 |
|----|-----|
| 儲存 | JSON 檔案 (`face_embeddings.json`) |
| 競爭 | `load_database()` 讀取時不持鎖，`build_database()` 寫入時持鎖 → TOCTOU |
| 初始化 | InsightFace lazy-load，雙重檢查鎖定模式正確 |
| 問題 | 重建資料庫時阻擋所有辨識請求 |

### 4.4 `PoseDepthMetricEngine` — 行為指標

| 項 | 評 |
|----|-----|
| 職責 | 清晰，單一類別計算 8 項指標 |
| 耦合 | 只依賴 numpy + 座標輸入，耦合度低 |
| 測試 | 僅 `_is_hand_raised()` 有測試 |

### 4.5 死碼：`src/vision/recognition_pipeline.py`

- 509 行，類別名也是 `RecognitionPipeline`
- 從未被任何檔案匯入
- 與 `attendance_pipeline.py` 中的同名類別完全獨立，無繼承關係
- 已造成混淆（app.py 的 import 看似來自此檔案，實則來自 attendance_pipeline）

---

## 5. 已識別問題清單

### P0 — 關鍵（可能造成崩潰或資料遺失）

| ID | 問題 | 位置 | 影響 |
|----|------|------|------|
| P0-1 | God Class：RecognitionPipeline 3,237 行 | `attendance_pipeline.py` | 無法維護、無法測試 |
| P0-2 | TOCTOU 競爭條件 | `face_recognition_db.py:411 vs 475` | 讀寫同時可能崩潰 |
| P0-3 | 無 graceful shutdown | `KinectService`, `RecognitionPipeline` | 硬體資源洩漏、出席記錄遺失 |
| P0-4 | 假資料混入正式 CSV 輸出 | `app.py:_export_once()` | 資料完整性 |
| P0-5 | `_export_once` bare except 吞掉錯誤 | `app.py:628` | 無法發現管線異常 |

### P1 — 重要（降低品質與效率）

| ID | 問題 | 位置 |
|----|------|------|
| P1-1 | 死碼 509 行 | `src/vision/recognition_pipeline.py` |
| P1-2 | `requirements.txt` 與 pyproject.toml 不同步 | 根目錄 |
| P1-3 | 巨型前端單體 6,318 行 | `templates/dashboard.html` |
| P1-4 | 模組級全局變數（無依賴注入） | `app.py:27-30` |
| P1-5 | 無 Flask middleware（無 CORS、無錯誤處理、無認證層） | `app.py` |
| P1-6 | `/login` 路由直接寫入檔案與管線競爭 | `app.py:665` |
| P1-7 | 參數分散三處（類別屬性 / JSON / env） | `attendance_pipeline.py` |

### P2 — 建議改進

| ID | 問題 |
|----|------|
| P2-1 | 測試覆蓋率 <1% |
| P2-2 | 無 CI/CD |
| P2-3 | 日誌系統缺失（僅 print） |
| P2-4 | 配置驗證缺失 |
| P2-5 | `clustering/k_means.py` 合成 200 名學生資料（非真實資料） |

---

## 6. 執行緒模型圖

```
主執行緒 (Flask)
├── daemon: KinectService._capture_loop()     # 硬體擷取
├── daemon: RecognitionPipeline._loop()       # 處理管線
├── daemon: MinuteStudentCsvExporter._loop()  # CSV 匯出 (每60秒)
└── Flask threaded workers                   # HTTP 請求處理
    └── 直接讀寫全域 FACE_DB / KINECT_SERVICE / RECOGNITION_PIPELINE

鎖定層次：
  PENDING_TRAINING_LOCK (outer)
    └── 呼叫 pipeline.capture_temporary_person_frame()
          └── pipeline._lock (RLock) ← 隱式、脆弱

  pipeline._lock (RLock) ← 保護狀態
  pipeline._frame_lock (Lock) ← 保護 JPEG frame
  pipeline._model_lock (Lock) ← 保護 YOLO 延遲初始化
  face_db._lock (Lock) ← 保護 build_database，但 load_database 不持鎖
  kinect_service._frame_lock (Lock) ← 保護 frame bundle
```

---

## 7. 相依關係圖

```
app.py ──→ config.py
app.py ──→ kinect_service.py
app.py ──→ attendance_pipeline.py ──→ kinect_service.py
         │                          ├──→ face_recognition_db.py
         │                          └──→ pose_depth_metrics.py
         │                               └──→ rgb_depth_alignment.py
         └──→ face_recognition_db.py

recognition_pipeline.py ← 無任何檔案引用（死碼）

外部相依：
  ultralytics (YOLO) | insightface | onnxruntime-gpu
  Flask | numpy | opencv | pillow | pandas | matplotlib | scikit-learn
```

無循環相依，但 `attendance_pipeline.py` 對所有 vision 模組形成星形強耦合。

---

## 8. 前端架構現況

`dashboard.html` (6,318 行) 內容分佈：

| 區段 | 約行數 | 說明 |
|------|--------|------|
| CSS 主題 (淺色+深色) | ~3,300 | 兩個完整主題重複定義 |
| JS 儀表板邏輯 | ~3,000 | 視圖切換、輪詢、SVG 圖表、模擬指標 |
| HTML 結構 | ~600 | Jinja2 模板 |

無前端框架、無建置工具、無模組化、無測試。
