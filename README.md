# Jianying Headless

剪映专业版的本地自动化工具：生成可编辑草稿、修改多轨工程副本，并通过本机引擎导出 MP4。

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

打开草稿检查画面、声音和保存结果。需要 MP4 时：

```bash
python3 skills/agent-jianying-edit/scripts/headless_draft.py export \
  --build "$PWD/work/new-build" --out "$PWD/work/new-export"
```

输出为 `render.mp4`。输出目录需使用新路径。

## 文档

- [计划格式](skills/agent-jianying-edit/references/plan-format.md)与[基础示例](examples/basic.plan.json)
- [独立 Skill 安装](skills/agent-jianying-edit/README.md)
- [已有草稿编辑](skills/agent-jianying-edit/references/edit-existing-macos.md)
- [导出说明](skills/agent-jianying-edit/references/export-macos.md)
- [本地字体](docs/LOCAL-FONTS.md)
- [兼容性与验证](docs/VERIFICATION.md)
- [工程交接示例](docs/HYPIT-COLLABORATION.md)
- [第三方依赖与许可](THIRD_PARTY_NOTICES.md)

配套技能仓库：[Milllkey/agent-skills](https://github.com/Milllkey/agent-skills)。

## 开发检查

```bash
python3 tools/check_package.py
python3 -m unittest discover -s tests -v
```

实际剪映打开、保存和导出需在匹配的本机环境验收。
