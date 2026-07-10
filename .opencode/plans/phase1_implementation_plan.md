# 第一階段實作計畫：安全與穩定性

> 基於 `docs/optimization_roadmap.md`，本文件為第一階段任務的具體實作計畫。
> 建立日期：2026-07-10
> 更新：整合 over-engineering audit 結果

---

## 任務總覽

| ID | 任務 | 修改檔案 | 預估 | 可移除行數 |
|----|------|----------|------|-----------|
| S1 | Graceful shutdown | `app.py`, `attendance_pipeline.py` | M | 0 |
| S2 | 修復讀寫競爭（長鎖問題） | `face_recognition_db.py` | S | 0 |
| S3 | 移除 bare except | `app.py` | S | 0 |
| S4 | 假資料分流（加 `source` 欄位） | `app.py` | S | 0 |
| S5 | 刪除死碼 `recognition_pipeline.py` | 刪除檔案 | S | **509** |
| S6 | 簡化 `_sanitize_file_segment` | `app.py` | S | **19** |

**不變原則**：不改變任何 HTTP API 形狀、不改變 `config.toml` 結構、不改變前端行為。

---

## S1 — Graceful Shutdown

### 現況分析

| 組件 | 現有清理機制 | 問題 |
|------|-------------|------|
| `MinuteStudentCsvExporter` | `stop()` 方法 + `atexit` 註冊 | 正常 |
| `KinectService` | `close()` 方法（設 `_running=False`、join thread） | 未在 `app.py` 呼叫 |
| `RecognitionPipeline` | **無 `stop()` 方法** | `_running` 永遠為 `True`，出席記錄未儲存 |

### 實作步驟

#### 步驟 1：`attendance_pipeline.py` — 新增 `stop()` 方法

在 `_loop()` 方法之後（line 3237 之後）新增：

```python
def stop(self):
    self._running = False
    self._wake_event.set()
    if self._thread.is_alive():
        self._thread.join(timeout=5.0)
    with self._lock:
        self._save_presence_records_locked()
```

**說明**：
- `_running = False` → `_loop()` 的 `while self._running` 迴圈結束
- `_wake_event.set()` → 立即中斷 `_wake_event.wait()` 等待
- `join(timeout=5.0)` → 等待執行緒結束，最多 5 秒
- `_save_presence_records_locked()` → 將出席記錄寫入 `data/presence_records.json`

#### 步驟 2：`app.py` — 新增 `_shutdown()` 函數

在 `AUTO_CSV_EXPORTER` 初始化之後（約 line 634）新增：

```python
def _shutdown():
    AUTO_CSV_EXPORTER.stop()
    RECOGNITION_PIPELINE.stop()
    KINECT_SERVICE.close()

atexit.register(_shutdown)
```

**移除**原本的 `atexit.register(AUTO_CSV_EXPORTER.stop)`（line 634）。

**清理順序**：
1. CSV 匯出器先停（避免在管線停止後還嘗試讀取狀態）
2. 管線停止（儲存出席記錄）
3. Kinect 最後關閉（釋放硬體）

---

## S2 — 修復讀寫競爭（長鎖問題）

### 現況分析

**更正**：先前分析認為 `load_database()` 不持鎖是錯誤的。實際上 `load_database()` 已持有 `self._lock`。

**真正的問題**：`build_database()` 在持鎖期間執行耗時操作（讀取圖片、運行 InsightFace 提取嵌入向量、計算平均），導致所有 `match_embedding()` 呼叫被阻塞。

```
build_database() 持鎖時間線：
  [lock] → 讀圖片 → InsightFace → 計算平均 → 寫 JSON → [unlock]
             ↑ 這段可能耗時數秒到數十秒
```

在此期間，管線的 `match_embedding()` 完全無法執行，人臉辨識凍結。

### 實作步驟

#### 修改 `build_database()` — 將耗時操作移出鎖外

**現況**（`face_recognition_db.py:429-483`）：

```python
def build_database(self):
    self.ensure_storage()
    students = []
    profiles = self.load_user_profiles()

    with self._lock:                          # ← 鎖在這裡開始
        for student_dir in sorted(...):
            # 讀圖片、跑 InsightFace（耗時）
            ...
        # 寫 JSON
        ...
    return students
```

**修改後**：

```python
def build_database(self):
    self.ensure_storage()
    profiles = self.load_user_profiles()

    # 階段 1：不持鎖，處理所有圖片
    students = []
    for student_dir in sorted(path for path in self.photo_root.iterdir() if path.is_dir()):
        embeddings = []
        image_count = 0

        for image_path in sorted(student_dir.iterdir()):
            if image_path.suffix.lower() not in {'.jpg', '.jpeg', '.png', '.bmp'}:
                continue

            image = self._read_image(image_path)
            embedding = self._extract_embedding(image)
            image_count += 1
            if embedding is not None:
                embeddings.append(embedding)

        if embeddings:
            embedding_size = len(embeddings[0])
            mean_embedding = [
                sum(item[index] for item in embeddings) / len(embeddings)
                for index in range(embedding_size)
            ]

            profile = profiles.get(student_dir.name, {})
            students.append({
                'label': student_dir.name,
                'display_name': profile.get('name', student_dir.name),
                'student_id': profile.get('student_id', ''),
                'college': profile.get('college', ''),
                'department': profile.get('department', ''),
                'title': profile.get('title', ''),
                'image_count': image_count,
                'matched_images': len(embeddings),
                'embedding': mean_embedding,
            })

    # 階段 2：持鎖，寫入檔案 + 更新快取
    with self._lock:
        payload = {
            'students': students,
            'photo_root': str(self.photo_root),
        }
        with self.embedding_file.open('w', encoding='utf-8') as db_file:
            json.dump(payload, db_file, ensure_ascii=False, indent=2)
        self._embedding_cache = students
        try:
            self._embedding_cache_mtime = self.embedding_file.stat().st_mtime
        except OSError:
            self._embedding_cache_mtime = None

    return students
```

**效果**：
- 圖片處理期間，`match_embedding()` 可繼續使用舊的快取資料
- 鎖僅在最終寫入時持有（毫秒級）
- 不改變輸出格式、不改變 API 形狀

---

## S3 — 移除 bare except

### 現況

`app.py:620-630`：

```python
def _loop(self):
    while not self._stop_event.is_set():
        now = time.time()
        if now >= self._next_export_at:
            self._next_export_at = now + self.INTERVAL_SECONDS
            try:
                self._export_once(now)
            except Exception:
                # Auto export should never interrupt the dashboard runtime.
                pass
        self._stop_event.wait(1.0)
```

### 修改

```python
import logging

# 在 MinuteStudentCsvExporter 類別中
def _loop(self):
    while not self._stop_event.is_set():
        now = time.time()
        if now >= self._next_export_at:
            self._next_export_at = now + self.INTERVAL_SECONDS
            try:
                self._export_once(now)
            except Exception:
                logging.exception('MinuteStudentCsvExporter._export_once failed, will retry next interval')
        self._stop_event.wait(1.0)
```

**說明**：
- 保留 `try/except` 結構（避免中斷背景執行緒）
- 改為 `logging.exception()` 記錄完整堆疊追蹤
- 在檔案頂部加入 `import logging`（若尚未存在）

---

## S4 — 假資料分流

### 現況

`_build_export_rows()` 輸出三類資料到同一 CSV：

| 資料來源 | 指標 | 真實性 |
|---------|------|--------|
| `person.get('presence_points')` | `presence` | 感測器真實資料 |
| `person.get('classroom_metrics')` | 8 項行為指標 | 感測器真實資料 |
| `_build_student_history_rows()` | `assignment-score`, `attendance-rate`, `submission-punctuality` | **偽隨機模擬** |

### 目標

- 不改變假資料的產生邏輯
- 不改變最終輸出內容（CSV 仍包含所有資料）
- 新增 `source` 欄位區分來源

### 實作步驟

#### 步驟 1：修改 `CSV_HEADERS`

```python
CSV_HEADERS = [
    'course_id',
    'course_name',
    'student_id',
    'student_name',
    'metric_key',
    'metric_name',
    'chart_type',
    'recorded_at',
    'label',
    'value',
    'source',         # ← 新增
]
```

#### 步驟 2：在 `_build_export_rows()` 中標記來源

**真實資料**（presence + classroom_metrics）加入 `'source': 'sensor'`：

```python
# presence 資料（約 line 522-535）
rows.append({
    'course_id': course_id,
    'course_name': course_name,
    'student_id': student_id,
    'student_name': student_name,
    'metric_key': 'presence',
    'metric_name': self.METRIC_METADATA['presence']['name'],
    'chart_type': self.METRIC_METADATA['presence']['chart_type'],
    'recorded_at': recorded_at,
    'label': '在場中' if point_value > 0 else '已離開',
    'value': point_value,
    'source': 'sensor',          # ← 新增
})

# classroom_metrics 資料（約 line 546-559）
rows.append({
    'course_id': course_id,
    'course_name': course_name,
    'student_id': student_id,
    'student_name': student_name,
    'metric_key': metric_key,
    'metric_name': metadata['name'],
    'chart_type': metadata['chart_type'],
    'recorded_at': recorded_at,
    'label': metric_row.get('label', ''),
    'value': metric_row.get('value', ''),
    'source': 'sensor',          # ← 新增
})
```

**模擬資料**（history metrics）加入 `'source': 'simulated'`：

```python
# HISTORY_METRIC_KEYS 資料（約 line 587-600）
rows.append({
    'course_id': course_id,
    'course_name': course_name,
    'student_id': student_id,
    'student_name': student_name,
    'metric_key': history_metric_key,
    'metric_name': metadata['name'],
    'chart_type': metadata['chart_type'],
    'recorded_at': recorded_at,
    'label': label_text,
    'value': history_row.get('value', ''),
    'source': 'simulated',       # ← 新增
})
```

#### 步驟 3：修改 `_normalize_json_row()`

```python
def _normalize_json_row(self, row):
    return {
        'course_id': str(row.get('course_id') or '').strip(),
        'course_name': str(row.get('course_name') or '').strip(),
        'student_id': str(row.get('student_id') or '').strip(),
        'student_name': str(row.get('student_name') or '').strip(),
        'metric_key': str(row.get('metric_key') or '').strip(),
        'metric_name': str(row.get('metric_name') or '').strip(),
        'chart_type': str(row.get('chart_type') or '').strip(),
        'recorded_at': str(row.get('recorded_at') or '').strip(),
        'label': str(row.get('label') or '').strip(),
        'value': self._coerce_json_integer(row.get('value')),
        'source': str(row.get('source') or 'sensor').strip(),   # ← 新增
    }
```

### 效果

- CSV 新增 `source` 欄位，值為 `sensor` 或 `simulated`
- JSON 輸出同步新增 `source` 欄位
- 下游可依據 `source` 過濾或分別處理
- 假資料產生邏輯完全不變
- 現有 `clustering/k_means.py` 不受影響（它讀取的是 `assignment_score` 欄位，不檢查 `source`）

---

## S5 — 刪除死碼 `recognition_pipeline.py`

### 現況

- `src/vision/recognition_pipeline.py`（509 行）從未被任何檔案匯入
- 類別名也是 `RecognitionPipeline`，與 `attendance_pipeline.py` 中的同名類別完全獨立
- 已在 `docs/architecture_analysis.md` 標記為死碼

### 實作

```bash
rm src/vision/recognition_pipeline.py
```

### 驗證

```bash
# 確認無任何匯入
grep -r "recognition_pipeline" --include="*.py" | grep -v "attendance_pipeline"
# 應無輸出

# 執行測試
uv run python -m unittest discover tests
```

---

## S6 — 簡化 `_sanitize_file_segment`

### 現況

`app.py:225-243` 實作了 19 行的檔案名稱清理邏輯：

```python
def _sanitize_file_segment(self, value, fallback='未指定課程'):
    normalized = str(value or '').strip()
    if not normalized:
        normalized = fallback
    safe_chars = []
    for char in normalized:
        if char in '<>:"/\\|?*':
            safe_chars.append('-')
        elif ord(char) < 32:
            safe_chars.append('-')
        elif char.isspace():
            safe_chars.append('-')
        else:
            safe_chars.append(char)
    safe = ''.join(safe_chars)
    while '--' in safe:
        safe = safe.replace('--', '-')
    safe = safe.strip('-')
    return safe or fallback
```

### 問題

`app.py:19` 已匯入 `from werkzeug.utils import secure_filename`，但 `_sanitize_file_segment` 重新實作了類似功能。

### 修改

```python
from werkzeug.utils import secure_filename

def _sanitize_file_segment(self, value, fallback='未指定課程'):
    normalized = str(value or '').strip()
    if not normalized:
        return fallback
    safe = secure_filename(normalized)
    return safe or fallback
```

**效果**：19 行 → 5 行，減少 14 行。使用已匯入的標準工具。

---

## 驗證清單

完成後執行以下驗證：

```bash
# 1. 執行現有測試
uv run python -m unittest discover tests

# 2. 檢查 graceful shutdown（啟動後 Ctrl+C）
uv run python app.py
# 觀察日誌是否顯示 "shutdown initiated" / "shutdown complete"
# 確認 data/presence_records.json 被更新

# 3. 檢查 CSV 輸出格式
# 啟動 attendance mode，等待 60 秒後檢查 history/classroom-metrics-*.csv
# 確認新增 source 欄位，值為 sensor 或 simulated

# 4. 檢查 JSON 輸出
# 確認 history/classroom-metrics-*.json 包含 source 欄位

# 5. 檢查 rebuild 期間辨識不中斷
# 呼叫 /api/face-recognition/rebuild，同時觀察 /api/attendance/status
# 確認辨識狀態在 rebuild 期間仍可回應

# 6. 確認死碼已刪除
grep -r "from src.vision.recognition_pipeline" --include="*.py"
# 應無輸出

# 7. 確認 _sanitize_file_segment 行為不變
# 測試：未指定課程 → 未指定課程，課程A/B → 課程A-B
```

---

## 修改檔案清單

| 檔案 | 修改內容 | 行數變化 |
|------|----------|----------|
| `app.py` | 新增 `_shutdown()`、修改 `atexit` 註冊、修改 `CSV_HEADERS`、修改 `_build_export_rows()`、修改 `_normalize_json_row()`、修改 `_loop()` bare except、簡化 `_sanitize_file_segment` | +30 / -20 |
| `src/vision/attendance_pipeline.py` | 新增 `stop()` 方法 | +6 |
| `src/vision/face_recognition_db.py` | 修改 `build_database()` 將圖片處理移出鎖外 | 0 (重排) |
| `src/vision/recognition_pipeline.py` | **刪除** | **-509** |

**Phase 1 淨移除：528 行**

---

## Over-Engineering Audit 摘要

> 完整 audit 結果見對話記錄。以下為本專案的可移除項目總覽。

### Phase 1 可執行（已納入本計畫）

| 項目 | 行數 | 說明 |
|------|------|------|
| `src/vision/recognition_pipeline.py` | 509 | 死碼，從未被匯入 |
| `_sanitize_file_segment` 簡化 | 19 | 已有 `secure_filename` 可用 |

### Phase 2 待評估（非本次範圍）

| 項目 | 行數 | 說明 |
|------|------|------|
| `scripts/tune_with_video.py` | 848 | 一次性調參腳本，未被 app 引用 |
| `scripts/eval_rgb_depth_keypoint_fusion.py` | 715 | 一次性評估腳本 |
| `scripts/evaluate_video_identity_flow.py` | 534 | 一次性評估腳本 |
| `scripts/tune_face_threshold_with_videos.py` | 321 | 一次性調參腳本 |
| `scripts/calibrate_quad_alignment.py` | 261 | 一次性校正腳本 |
| `scripts/tune_quad_recordings.py` | 223 | 一次性調參腳本 |
| `scripts/compare_recognition_snapshots.py` | 178 | 一次性比較腳本 |
| `scripts/test_kinect.py` | 69 | 一次性硬體測試 |
| `reels/record_rgb_nir.py` | 775 | 錄影工具，非 app 核心 |
| `clustering/k_means.py` | 691 | 獨立分析腳本，合成假學生資料 |
| `templates/dashboard.html` inline CSS | 3,354 | 應拆至 `static/css/` |
| `templates/dashboard.html` inline JS | 2,511 | 應拆至 `static/js/` |
| `attendance_pipeline.py` 渲染方法 | ~200 | `_draw_*`/`_annotate_*` 應抽離 |

**Phase 2 潛在可移除：~10,500 行**（需逐一評估是否仍被使用）

---

## 執行順序建議

1. **S5** — 刪除死碼（最安全，零風險）
2. **S6** — 簡化 `_sanitize_file_segment`（低風險）
3. **S3** — 移除 bare except（低風險）
4. **S4** — 假資料分流（中風險，需驗證 CSV/JSON 格式）
5. **S2** — 修復長鎖問題（中風險，需驗證 rebuild 行為）
6. **S1** — Graceful shutdown（最高風險，涉及多執行緒清理順序）
