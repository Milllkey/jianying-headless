# Jianying Headless

剪映专业版的本地自动化工具：生成可编辑草稿、修改多轨工程副本，并通过本机引擎导出 MP4。

开发交接入口：[AGENTS.md](AGENTS.md)、[CLAUDE.md](CLAUDE.md)、[贡献说明](CONTRIBUTING.md)。自有剪辑引擎、模型任务和画布接入集中在 [haoyong-video](https://github.com/Milllkey/haoyong-video)，本仓保留原生草稿互通职责。

剪映 11.6 研究与主仓 0.19 独立能力从[统一交接入口](https://github.com/Milllkey/haoyong-video/blob/main/docs/CLAUDE-RESEARCH-HANDOFF.md)开始，按功能查看证据、接口和未知项。Claude 负责后续画布产品集成；本仓提供可选原生草稿交接，独立导出不依赖剪映。11.6 已验证的构建、独立副本编辑、发布和正常 UI 导出，与尚未支持的原生无界面导出 ABI 分开。详见[贡献说明](CONTRIBUTING.md)。

## 功能

- 视频分段、多轨组合、变速、音量、画中画、字幕和标题。
- 导入本地视频、图片、GIF、配音、音乐和音效。
- 位置、缩放、旋转、透明度和音量关键帧。
- 静态蒙版、叠化转场、基础视觉效果和本地字体。
- 在独立副本中编辑已有草稿，检查素材、组件身份和保存结果。
- 可选的 Windows FFmpeg 导出后端，详见 [Windows 使用说明](docs/windows-ffmpeg.md)。

## 环境

- Apple Silicon Mac，macOS 26.0+。
- 剪映专业版 11.5.0；11.4.2 有兼容配置。11.6.0 支持新建和编辑草稿，当前主分支不支持该版本的原生导出。
- Python 3.9+、FFmpeg / ffprobe、Xcode Command Line Tools。
- 桥接组件需通过版本、签名和固定哈希校验；已验证工具链为 Apple clang 21.0.0 / macOS SDK 26.5。

剪映程序、官方资源和用户素材需单独准备。详细安装流程见 [入门教程](docs/GETTING-STARTED.md)。

## 开始使用

```bash
git clone https://github.com/Milllkey/jianying-headless.git
cd jianying-headless
python3 tools/build_native_codec.py
python3 skills/agent-jianying-edit/scripts/headless_draft.py doctor
```

准备剪辑计划，生成并检查草稿：

```bash
python3 skills/agent-jianying-edit/scripts/headless_draft.py build \
  --plan /absolute/path/to/plan.json --out "$PWD/work/new-build"
python3 skills/agent-jianying-edit/scripts/headless_draft.py verify-build \
  --build "$PWD/work/new-build"
```

保存工作并退出剪映后，将草稿登记到本机首页：

```bash
python3 skills/agent-jianying-edit/scripts/headless_draft.py publish \
  --build "$PWD/work/new-build" --audit "$PWD/work/new-publish-audit"
```

打开草稿检查画面、声音和保存结果。导出方式取决于实际版本：

- **剪映11.6.0**：使用[官方界面导出与核验](docs/UI-EXPORT.md)。先生成 `ui-export plan`，按照计划在剪映正常导出，再运行 `ui-export verify` 检查真实文件。此版本的 `export` 命令会明确拒绝；UI导出不是无界面导出ABI。
- **已核验的11.5.0或11.4.2运行环境**：可执行以下原生无界面导出，版本与库身份检查仍须全部通过。

```bash
python3 skills/agent-jianying-edit/scripts/headless_draft.py export \
  --build "$PWD/work/new-build" --out "$PWD/work/new-export"
```

上述无界面路线输出 `render.mp4`，输出目录需使用新路径；11.6界面路线使用计划记录的路径。

## 文档

- [计划格式](skills/agent-jianying-edit/references/plan-format.md)与[基础示例](examples/basic.plan.json)
- [独立 Skill 安装](skills/agent-jianying-edit/README.md)
- [已有草稿编辑](skills/agent-jianying-edit/references/edit-existing-macos.md)
- [导出说明](skills/agent-jianying-edit/references/export-macos.md)
- [本地字体](docs/LOCAL-FONTS.md)
- [兼容性与验证](docs/VERIFICATION.md)
- [工程交接示例](docs/HYPIT-COLLABORATION.md)
- [11.6 工程互转研究与验证边界](docs/research/2026-10-22-draft-interchange.md)
- [第三方依赖与许可](THIRD_PARTY_NOTICES.md)

配套技能仓库：[Milllkey/agent-skills](https://github.com/Milllkey/agent-skills)。

## 开发检查

```bash
python3 tools/check_package.py
python3 -m unittest discover -s tests -v
```

实际剪映打开、保存和导出需在匹配的本机环境验收。

只读检查已解码的明文工程结构，可使用 `tools/inspect_draft_schema.py`。
它输出去内容化的字段、引用和特征清单，不读取密钥、不解密草稿、不调用原生引擎。
与自有工作台的转换适配器及损失报告位于
[haoyong-video](https://github.com/Milllkey/haoyong-video/tree/main/integrations/jianying)。
