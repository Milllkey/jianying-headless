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


主仓0.15新增[声音处理历史](https://github.com/Milllkey/haoyong-video/blob/main/docs/AUDIO-HISTORY.md)、[保留音乐压低的本机复制](https://github.com/Milllkey/haoyong-video/blob/main/docs/AUDIO-DUCKING-CLONE.md)和[静态蒙版缓存](https://github.com/Milllkey/haoyong-video/blob/main/docs/STATIC-MASK-CACHE.md)。`audioHistory` 保存原始解码与恒速处理范围、实际源SHA及整数样本窗口；压低v2迁移包装保留根分析的原始字节。这些都是自有引擎协议，plaintext/headless互转须保留 `UNMAPPED_FIELD` 等损失并默认拒绝，不能删除字段后声称声音保持一致。需要有声成片交接时，可先由主仓验证并渲染新媒体，再以新素材身份导入；不把该过程描述为可继续编辑的参数等价转换。

[联动调色研究](https://github.com/Milllkey/haoyong-video/blob/main/docs/research/NATIVE-COLOR-LINKED-11.6.md)另完成8份官方导出、480帧及固定数学假设比较。链条按钮本身未改变已保存曲线，联动拖动后的L/R/G/B锚点及跨通道输出有实际证据。共同亮度补偿候选仍有非零残差，不能据此确认原厂内部顺序。调色、HSL、色轮、蒙版等[扩展登记](https://github.com/Milllkey/haoyong-video/blob/main/docs/research/NATIVE-COLOR-EXPANDED-REGISTER-11.6.md)包含147条控件/参数/行为子记录，按UI、保存状态和实际导出区分；不是147项已实现功能。本仓只更新这次交接文档，未扩大原生桥和无界面导出ABI范围。

随后完成的[HSL四带研究](https://github.com/Milllkey/haoyong-video/blob/main/docs/research/NATIVE-HSL-11.6.md)包含16份官方输出、960帧及60帧源对照，记录色带重叠、不同增益、同终态的两种黄绿操作顺序和92组固定数学比较。逐帧字节仍不同，静态色卡的输出帧间变化尚未隔离原因。40行参数/控制/静态声明子登记包含12个已测单值单元与其余未验证项，不与此前147行相加，不表示独立产品已经实现HSL或桥接可以无损转换。


主仓0.16新增[音量函数保形](https://github.com/Milllkey/haoyong-video/blob/main/docs/AUDIO-GAIN-WINDOW.md)、[可调合成蒙版](https://github.com/Milllkey/haoyong-video/blob/main/docs/ADJUSTABLE-MASKS.md)与[单次声音历史PCM缓存](https://github.com/Milllkey/haoyong-video/blob/main/docs/AUDIO-HISTORY-PCM-CACHE.md)。`audio[].audioGainWindow`先绑定声音历史再显式捕获，分割/内裁保留原函数样本窗口；对象蒙版支持四种静态形状及羽化等参数。二者须经主仓完整工程HTTP/SDK保存和导出，不能直接解释为原生字段。互转的`AUDIO_GAIN_WINDOW_UNSUPPORTED`及蒙版`UNMAPPED_FIELD`损失继续保留并默认拒绝，不能静默丢掉参数。

[同工程真实验收](https://github.com/Milllkey/haoyong-video/blob/main/docs/research/CREATIVE-PRESERVATION-INTEGRATION-0.16.md)覆盖裁切、RGB、蒙版、动画、声音历史、增益根与无关v2压低关系，分割、内裁、检查点与再次复制的保留区间逐字节一致。它证明记录的自有渲染场景，不表示原生像素/声音或所有格式等价。新PCM缓存位于增益之前，仅本次多分段导出复用，未知处理器或输入格式仍走原图；不把私有缓存文件当成素材或工程迁移依赖。

需要向原生侧交接这些效果时，保留完整自有工程；另外明确导出新媒体，以新素材身份导入原生草稿。渲染后媒体能够交接，不代表原参数仍可在原生侧独立编辑。下一步继续验证原生参数映射、视觉/音频时钟及实际原生输出，再调整相应损失合同。


[静态色卡的时间对照](https://github.com/Milllkey/haoyong-video/blob/main/docs/research/NATIVE-COLOR-TEMPORAL-CONTROL-11.6.md)继续追查HSL研究中的帧间波动：新增3份官方导出、180帧，以及固定YUV输入的无损/有损编码控制。源内部色块恒定，PNG单图仍波动，相同timeline重复导出只有第6帧像素不同。公开有损编码链路已能产生波动，但未证明剪映实际编码器、参数或编码前图像；旧16份HSL输出保留。下一步原生低损设置与编码前观测仍登记，不把误差自动归为某一内部算法。

0.16发布后补充的[原生导出质量目录](https://github.com/Milllkey/haoyong-video/blob/main/docs/research/NATIVE-EXPORT-QUALITY-11.6.md)逐项保留7类36个菜单标签、22条周边控件及路由负例。本轮0次新导出，ProRes/Alpha/PCM、8K/120fps、分数帧率与码率选择尚未实际验收；本仓原生桥和主仓导出规格均不因此扩大。
