# 《时之笛》本机更新与维护

本机安装的是 **v131072 完整着色器版**。以后从 [MNG Launcher](</Applications/MNG Launcher.app>) 的《时之笛》卡片更新游戏。Launcher 会使用它随附的构建源码和着色器清单。要更新到较新的源码或清单，先安装包含它们的 Launcher，再在卡片上更新游戏。

## 本机布局

| 内容 | 位置 |
| --- | --- |
| 游戏 App | `/Applications/The Legend of Zelda - Ocarina of Time.app` |
| 游戏数据、离线着色器和 Metal 管线 | 游戏 App 内的 `Contents/Helpers/`，其中 GameData 包含约 26 GB 的 RomFS |
| 外接构建工作目录 | `/Volumes/MNG-OoT-Work/build` |
| 工作卷的磁盘映像 | `/Volumes/thinkplus/tmp/oot-rebuild.nGqXkF/work.sparsebundle` |
| 原始游戏导出 | `/Volumes/thinkplus/The Legend of Zelda Ocarina of Time/The Legend of Zelda Ocarina of Time [0400486024dec000][v131072].nup` |
| 存档和游玩缓存 | `~/Library/Application Support/MacNativeGames/OcarinaOfTime/` 下的 `profile/` 和 `shader-cache/` |

游戏数据留在 App 内，**平时拔掉外接盘也能游玩**。更新时保留外接工作目录里的已验证游戏数据、着色器、管线缓存和 `venv`，供 Launcher 复用。

## 在 Launcher 里更新

1. 退出游戏，接上 `thinkplus`。在访达打开上表中的 `work.sparsebundle`，确认 `MNG-OoT-Work` 已挂载。
2. 打开 MNG Launcher，进入《时之笛》卡片。在「存储」确认工作目录为 `/Volumes/MNG-OoT-Work/build`。
3. 按卡片显示的更新方式操作，等待 Launcher 完成打包和安装。

| 卡片显示 | 怎么做 |
| --- | --- |
| **极速更新** | 直接点击。Launcher 复用工作目录里的游戏数据和仍匹配的着色器，更新运行时和管线。 |
| **快速更新** | 直接点击，预留更多时间。Launcher 会按新运行时的要求重新准备着色器。 |
| **完整打包** | 按 Launcher 的提示拖入上表的 v131072 `.nup`。沿用已安装 App 的位置和现有工作目录。 |

从本机版 Launcher 1.1.6 起，已安装 App 内的 GameData 和工作目录的已签名数据包匹配时，Launcher 会在内置 APFS 卷上克隆数据到临时 App。这样保留内嵌数据布局，也省去重新从外接盘传输约 26 GB 的 RomFS。首次安装、数据变化，或同卷克隆不可用时，Launcher 会按正常方式组装数据包。新的着色器和管线仍会按需打包。

## 验证与排错

- Launcher 显示完成后，从卡片启动游戏，确认能进入标题并读取原来的存档。
- 打包停下时，先点「打开日志」，查看具体失败的步骤。各步骤的日志在 `/Volumes/MNG-OoT-Work/build/logs/`。
- 如果日志提示工作目录找不到，检查外接盘和 APFS 工作卷是否都已挂载。若提示缺少 Metal 编译器，在 Xcode 的组件设置中检查 Metal Toolchain。
- 解决报错后，回到同一张游戏卡片重试，沿用同一工作目录复用已有结果。

更多错误说明见[《时之笛》中文安装文档](games/oot/docs/install.zh-CN.md#打包停下时)。
