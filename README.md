# 时之笛 · MacNativeGames

这个 fork 维护 **Switch 2 版《塞尔达传说 时之笛》** 的 Apple Silicon macOS 移植。支持的游戏更新为 **v131072**。运行和打包使用你自己导出的游戏，仓库保留《时之笛》构建所需的上游共享源码。

游戏源码在 `games/oot`。上游共用的 NVN 图形后端和部分工具仍在 `games/totk`，沿用原路径以便同步。

## 安装与更新

- 使用 Apple Silicon Mac 和 macOS 26 或更新版本。首次打包需要完整 Xcode 和 Metal Toolchain。
- 在 **MNG Launcher** 中选择《时之笛》。首次打包或 Launcher 要求完整打包时，导入自己的 v131072 游戏导出。
- 已安装的游戏从 Launcher 卡片更新。Launcher 使用它随附的源代码和着色器清单。要使用本仓库的新代码，先安装包含这些改动的 Launcher 构建。

[中文安装和排错文档](games/oot/docs/install.zh-CN.md) · [游戏功能与设置](games/oot/README.md) · [本机 Launcher 更新流程](maintenance.zh-CN.md)

## 存储与更新

游戏数据可以保留在 App 内，同时把构建工作目录放在外接 APFS 卷。这样平时可以拔盘游玩，更新时再挂载工作卷来复用着色器和管线。已安装 App 和工作目录的签名数据包匹配时，更新会优先在 App 所在的 APFS 卷上克隆已有 RomFS，省去约 26 GB 的跨盘复制。

## 上游同步

[GitHub Actions](https://github.com/zplzmzmpl/MacNativeGames/actions/workflows/watch-oot-upstream.yml) 每六小时检查一次上游 `main`。它关注《时之笛》本身及可能影响它的共享运行时和 Launcher 构建代码。发现新改动时，会在本 fork 开一个 Issue 并提醒维护者。上游改动经核对后再融合。

公共仓库连续 60 天没有活动时，GitHub 可能停用定时工作流。可在 Actions 页面重新启用。 [GitHub 定时工作流说明](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/disable-and-enable-workflows)

## 上游与许可

上游是 [ly05010419/MacNativeGames](https://github.com/ly05010419/MacNativeGames)。项目许可、第三方组件和《时之笛》的来源记录见下列文件。构建的游戏 App 供本人使用。

[LICENSE](LICENSE) · [第三方声明](THIRD_PARTY_NOTICES.md) · [《时之笛》源码来源](games/oot/third_party/COPIES.md)
