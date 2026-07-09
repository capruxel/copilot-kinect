# Copilot Kinect

Kinect + YOLO + Flask 的課堂出席與姿態分析系統。專案整合 Kinect RGB / 深度影像、YOLO 姿態偵測、InsightFace 人臉辨識，以及 Flask 儀表板，用來追蹤學生到場狀態、互動行為與課堂專注度指標。

## 功能重點

- Kinect v1 / v2 影像擷取與 RGB / 深度資料對齊
- YOLO pose detection，用於人體框、關節點、舉手與姿態狀態分析
- InsightFace 人臉資料庫與學生身分辨識
- Flask dashboard 即時顯示出席、辨識、影像串流與課堂指標
- 課堂紀錄輸出為 CSV / JSON，支援後續分析
- 可選 Power Automate webhook，上傳課堂報表或紀錄
- `clustering/k_means.py` 與 `clustering/` 用於學生行為特徵分群分析

## 專案結構

```text
app.py                         Flask app 與主要 API
src/vision/                    Kinect、辨識流程、姿態與深度指標
templates/                     Dashboard 頁面模板
static/                        前端樣式與靜態資源
scripts/                       校正、評估、臉部資料庫重建等工具
reels/                         Kinect 錄影工具
data/                          設定範例、驗證資料與執行資料
models/yolo/                   本機 YOLO 權重放置位置
tests/                         單元測試
clustering/                    K-Means 分群腳本、輸出、圖表與分析報告
```

## 環境需求

建議環境：

- Windows
- Python 3.10
- NVIDIA GPU + CUDA 12.6
- Kinect SDK / PyKinect2 可用的 Kinect v1 或 v2 裝置
- Visual C++ Redistributable for Visual Studio 2015-2022 (x64)

若尚未安裝 VC++ Redistributable，請從以下連結下載並安裝 x64 版本後重新開機：

```
https://aka.ms/vc14/vc_redist.x64.exe
```

PyTorch 底層依賴 `vcruntime140.dll` 等 VC++ Runtime DLL，缺少時會導致 `c10.dll` 載入失敗、YOLO 模型無法初始化。

使用 `uv` 建立專案環境並安裝套件：

```powershell
uv python install 3.10
uv sync
```

專案使用 `pyproject.toml` 與 `uv.lock` 管理依賴，並透過 `tool.uv.index` 指向 CUDA 12.6 的 PyTorch wheel。`uv` 預設會建立專案內的 `.venv/`，這也符合目前 Kinect DLL 搜尋邏輯。若要在沒有 NVIDIA GPU 的環境執行，請改裝符合環境的 `torch` / `torchvision` / `onnxruntime` 版本。

## 初始設定

複製並編輯專案設定檔：

```powershell
Copy-Item config.example.toml config.toml
```

`config.toml` 統一管理所有執行環境變數（YOLO 模型路徑、推論裝置、Kinect 後端等），啟動時自動載入，不需要每次手動打 `$env:`。結構化設定位於各區塊（`[models]`、`[kinect]`、`[insightface]`、`[webhook]`），也可以用 `[env]` 區塊直接覆蓋任意環境變數。詳見 `config.example.toml` 內註解。

複製管理者設定範例：

```powershell
Copy-Item data\administrators.example.json data\administrators.json
```

大型模型檔、影片、embedding database、學生臉部資料與本機設定不會進入 Git。請勿把真實學生個資、webhook URL、課堂影片或模型權重直接提交到 GitHub。

## 執行

啟動 Flask app：

```powershell
uv run python app.py
```

常用頁面：

```text
http://127.0.0.1:5000/
http://127.0.0.1:5000/dashboard
```

## 常用工具

重建人臉辨識資料庫：

```powershell
uv run python scripts\rebuild_face_db.py
```

檢查 VC++ Runtime、config.toml、GPU、CUDA、PyTorch、ONNX 與依賴匯入：

```powershell
uv run python scripts\check_gpu_runtime.py
```

執行 K-Means 分群分析：

```powershell
uv run python clustering\k_means.py
```

## 測試

```powershell
uv run python -m unittest discover tests
```

目前測試以姿態與深度指標邏輯為主，不需要接上實體 Kinect。

## GitHub 注意事項

推送前可先確認狀態：

```powershell
git status --short
git ls-files
```

這個 repo 已忽略常見大型或敏感檔案，例如 `.venv/`、影片、YOLO `.pt` 權重、臉部 embedding、執行輸出與本機管理者設定。若新增資料夾或輸出格式，請同步檢查 `.gitignore`。
