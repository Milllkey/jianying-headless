# 独立组件就绪检查

`python3 tools/runtime_report.py --components-only` 现在能一次列出每个固定组件和 ffmpeg/ffprobe 的状态，不调用原生程序或读取用户草稿。默认的完整应用报告也附带 `native_prerequisites`。这只改善诊断；运行时的 `doctor()`、精确哈希、官方签名和导出 ABI 限制均未改变。

2026-10-22 实测结果在 [JSON](2026-10-22-component-readiness.json)：源码清单和 IO 文件哈希匹配，媒体工具可用，审定的 `jy14_codec_hardened_11_4` 缺失。组件模式返回退出码 1，同时保留全部检查结果。没有导入 `runtime_io.py`、执行 codec、修改 pins 或重建工具链。

`prerequisites-matched` 也只是文件前提符合，不证明原生工作流成功。应用身份、签名与合成草稿验证仍应由正式门禁和后续流程完成。

```sh
python3 -m unittest discover -s tests -p 'test_runtime_report.py' -v
python3 -m unittest discover -s tests -p 'test_runtime_profiles.py' -v
```

8 个新测试覆盖全部缺失、匹配但未执行、单项篡改不掩盖其他结果、符号链接、目录伪装、媒体工具缺失、路径去身份化、读取期间文件变化；10 个既有版本/导出门禁测试继续通过。
