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

主仓 0.9 增加显式 `sourceFrameSampling:'jianying-11.6-cfr30-floor-v1'` 导入选项，并由独立渲染器重新核验真实源视频的逐帧时钟。范围限定为11.6保存的189明文、源/工程30fps、源入点0及0.75/1.25/1.5/1.75倍。自制120帧对照的源帧索引全部吻合官方导出；旧默认输出的59帧差异与原始报告仍保留。该结果不能推广为所有画面像素或其他速度/帧率等价，也不能把调用方提供的时钟JSON当成已读取文件。新报告见 [显式采样验证](https://github.com/Milllkey/haoyong-video/blob/main/docs/research/JIANYING-CFR-FLOOR-OPT-IN-VALIDATION.md)。

主仓 0.10 增加实际源帧提取、带回执的素材发布、有界单视频定格插入和静态源裁切。同一有声自制素材在第1秒插入3秒定格，原生与独立引擎的180个输出源帧索引全部一致；AAC切点附近残留和音频尾长不同，见 [定格插入](https://github.com/Milllkey/haoyong-video/blob/main/docs/FREEZE-INSERTION.md)。另有两组原生裁切导出，每组90帧核验，见 [裁切研究](https://github.com/Milllkey/haoyong-video/blob/main/docs/research/NATIVE-CROP-VALIDATION-11.6.md)。自有裁切按源像素整数边界执行，原生浮点纹理采样仍有未解释残差；互转里的原生crop损失报告继续保留，不能直接删除警告或推定两种坐标算法等价。本仓本轮仅同步接手文档，原生桥与无界面导出支持范围未扩大。

继续改动时，把具体问题分成草稿数据、实际保存结果、实际导出画面/声音三层验收。保留输入摘要、参数、应用版本、完整解码和字段差异。通过离线测试不等于原生应用质量一致。

主仓0.11继续完善连续恒速音频与具体视频模型适配，原生侧新增非1倍旋转关键帧时钟研究。0.5×/2×两个真实导出共487帧，其中187个活动几何样本支持本例旋转按连续源时间求值；慢放重复画面之间动画仍插值。原始字段、像素残差、2倍时长量化单例和数字识别分歧见 [旋转时钟](https://github.com/Milllkey/haoyong-video/blob/main/docs/research/NATIVE-ANIMATION-CLOCK-11.6.md)。这批证据尚未扩大本仓原生桥或互转支持范围；自有音频和模型行为见主仓合同。

主仓0.12新增独立旋转/等比缩放关键帧、默认视频有界片尾保持和固定配置配音接入。原生侧另有[组合动画与半透明叠层](https://github.com/Milllkey/haoyong-video/blob/main/docs/research/NATIVE-ANIMATION-COMPOSITE-11.6.md)四次真实导出，共359帧：90帧opaque、90帧半透明黑底、89帧双层合成及90帧底层对照。几何与覆盖区域实测支持本例中心等比动画和局部Alpha；89帧合成没有擅自补成90，原因仍未知。等比缩放与同中心旋转可交换，不能从本例判断原生内部先后顺序。自有动画采用输出时间，原生已观测子集采用源时间，关键帧互转仍保留损失提示；本仓只更新研究接手入口，未扩大桥接ABI支持范围。

主仓0.13把[双语字幕](https://github.com/Milllkey/haoyong-video/blob/main/docs/BILINGUAL-SUBTITLES.md)、[整段音频处理](https://github.com/Milllkey/haoyong-video/blob/main/docs/LOCAL-AUDIO-PROCESSING.md)、[独立RGB曲线](https://github.com/Milllkey/haoyong-video/blob/main/docs/COLOR-CURVES.md)和[审核后的纹理区域平移消除](https://github.com/Milllkey/haoyong-video/blob/main/docs/TRACKED-REGION-ERASE.md)整合到同一工作台，实际组合成片与完整回归见[0.13验证](https://github.com/Milllkey/haoyong-video/blob/main/docs/research/RELEASE-VALIDATION-0.13.md)。这些是独立实现，不能把字段直接当作原生草稿的等价参数。互转仍报告未映射的曲线、双语关系与处理回执；先明确损失，或把独立渲染得到的新媒体作为素材交接。跟踪仅限纹理平移，LaMa仍逐帧；曲线仅限8位SDR。本仓本版只更新接手文档，原生桥、固定身份校验与无界面导出ABI均未扩大。

主仓0.14新增[动画分割与向内裁切](https://github.com/Milllkey/haoyong-video/blob/main/docs/MOTION-EDITS.md)、[独立音乐压低](https://github.com/Milllkey/haoyong-video/blob/main/docs/AUDIO-DUCKING.md)、[显式贝塞尔RGB](https://github.com/Milllkey/haoyong-video/blob/main/docs/BEZIER-COLOR-CURVES.md)及[极短视频区间修复](https://github.com/Milllkey/haoyong-video/blob/main/docs/SHORT-VIDEO-INTERVALS.md)。自有 `motionWindow` 只表示自有曲线相位，不能直接转换成原生源时钟；音乐压低依赖分析回执和真实素材摘要，互转默认报告不支持，明确允许损失时仍保留报告。贝塞尔的独立字节映射也不证明原生控制柄算法等价。最终整合结果见[0.14验证](https://github.com/Milllkey/haoyong-video/blob/main/docs/research/RELEASE-VALIDATION-0.14.md)。本仓同步接手文档，原生执行和ABI能力须依据各自实测继续推进。

[原生调色实测](https://github.com/Milllkey/haoyong-video/blob/main/docs/research/NATIVE-COLOR-CURVES-11.6.md)完成4次官方导出、240帧测量，确认R曲线会联动G/B；55条调色入口/参数/行为登记明确区分实际输出、仅UI与静态线索。发现的功能均须登记，当前实现、访问或许可条件写为状态和依赖，不以这些条件删除功能项。均值模型仍有残差，不把自有曲线直接映射为原生等价处理。
