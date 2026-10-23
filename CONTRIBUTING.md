# 从 GitHub 接手

本仓负责本机剪映草稿构建、独立副本编辑、组件核验、发布与导出交接。自有多轨渲染、字幕对齐、模型任务及画布接口在 [haoyong-video](https://github.com/Milllkey/haoyong-video)。两仓通过计划和明确的转换损失报告衔接，不能把原生私有字段默认为自有引擎已实现的能力。

先按 [入门教程](docs/GETTING-STARTED.md) 准备 Python、FFmpeg、匹配的官方应用和本地桥接组件；仓库不会附带官方应用、模型权重或用户素材。克隆源码后首先运行 doctor，按明确缺项处理；不要通过放宽固定哈希来通过体检。

| 范围 | 入口 |
| --- | --- |
| CLI 与构建/发布入口 | `skills/agent-jianying-edit/scripts/headless_draft.py` |
| 计划与草稿语义 | `skills/agent-jianying-edit/references/plan-format.md`、`engine/` |
| 固定桥接重建 | `tools/build_native_codec.py`、`bridge/` |
| 离线边界回归 | `tests/` |
| 本机原生实验 | `engine/test_native_*.py`，仅在准备好的环境运行 |
| 官方 UI 导出 | CLI `ui-export plan` 与 `ui-export verify`，详见导出参考 |

```sh
python3 -m unittest discover -s tests -v
python3 skills/agent-jianying-edit/scripts/headless_draft.py doctor
```

11.6 的实际链路是 build → verify-build → 退出官方应用 → publish → 正常 UI 打开/保存/导出 → ui-export verify。UI 导出的实测容器可以通过 `--video` 明确指定，不能据此声称与计划里未经执行的格式设置一致。无界面原生导出仍需单独解决 ABI 和运行时环境问题。

主仓 0.8 增加静态旋转、有界纯色文字样式、显式字体绑定，以及仅适用于 native 189 的可选字号经验 profile。字号近似、字体实际字面未知、多行行距、不同描边定义及源帧采样差异均保留报告。两档文字与四档恒速校准使用自制素材；结果仅适用于各报告的范围。详见主仓 `integrations/jianying/CONTRACT.md` 和 `docs/research/`。

继续改动时，把具体问题分成草稿数据、实际保存结果、实际导出画面/声音三层验收。保留输入摘要、参数、应用版本、完整解码和字段差异。通过离线测试不等于原生应用质量一致。
