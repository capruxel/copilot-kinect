# YOLO Models

Place local YOLO model weights in this folder. The weights are ignored by git
because they are large runtime artifacts.

Current primary pose model:

- `yolo26x-pose.pt`

You can point the attendance pipeline at a different pose model with the
`YOLO_POSE_MODEL` environment variable, for example:

```powershell
$env:YOLO_POSE_MODEL="models/yolo/your-model.pt"
```
