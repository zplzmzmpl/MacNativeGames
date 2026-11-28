# 更新记录

## 2026-11-28 · 本机版 Launcher 1.1.11

- 《时之笛》卡片在已安装的源码提交和着色器、管线清单均匹配时显示「已是最新」，更新入口不可用。任一项有变化仍可更新。

## 2026-11-28 · 《时之笛》上游同步

- **着色器清单。** 新增 3 个着色器变体、1 个绑定状态、64 条渲染管线和 6 条 Tile 读取管线。已用项目工具核对新增管线的绑定状态并导出两份预热清单。 [上游清单](https://github.com/ly05010419/MacNativeGames/commit/cae491f769223be1c8961bac8035fb58c9459fbc)
- **打包图标。** 更新官方图标的固定地址和哈希。图标提取失败时清理工作目录里的残留图标，继续打包并使用系统默认图标。设备版构建记录在有图标时才收录图标信息。已验证无网络时能从 Launcher 离线包生成新图标。 [上游打包修复](https://github.com/ly05010419/MacNativeGames/commit/04e848efae505869cbdae60ae7fd08d1f5e19b29)
- **同步范围。** 本批跳过 VR、《旷野之息》HDR、Pokopia 内存池跟踪和其他游戏的构建与启动选项。《时之笛》已启用内存池重叠跟踪，Launcher 的游戏卡片可以直接启动游戏。 [Issue #3](https://github.com/zplzmzmpl/MacNativeGames/issues/3)

### 本机版 Launcher 1.1.10

- 从 `94b28a5a` 重编 `oot-native` 和 `oot-pool-sources-list`，最低系统版本均为 macOS 26.0。内置源码与离线包通过完整性校验，新版已在 `/Applications` 安装并启动。 [内置源码提交](https://github.com/zplzmzmpl/MacNativeGames/commit/94b28a5ac4f5e616fec30329616b8bd748c02950)
- `make check` 的 987 项 Python 测试中，970 项通过、17 项跳过。14 项 C 检查全部通过。外接构建卷未挂载，完整游戏打包和实机游玩尚待验证。 [仓库测试入口](Makefile#L44)

## 2026-11-27 · 《时之笛》上游同步

- **VR。** 合入随手部动作判定的剑刃命中、双手瞄准、手腕状态面板、道具轮盘和舒适遮罩。ARM64 探针覆盖了运行时钩子和交互计算，头显实机验证待完成。 [上游 VR 改动](https://github.com/ly05010419/MacNativeGames/commit/9c2554bc7452aa6dad1e106fb2c79b4862fe7146)
- **水面与着色器。** 水面模拟在 60 FPS 以上仍执行子步，暂停时保持零步。着色器翻译子进程从空信号掩码和默认信号处理方式启动。 [水面 PR](https://github.com/ly05010419/MacNativeGames/pull/2400) · [信号 PR](https://github.com/ly05010419/MacNativeGames/pull/2384)
- **macOS 26 打包。** 《时之笛》运行时和管线资源工具固定以 26.0 为最低版本，打包时核对 Mach-O 版本和离线 libvpx 的 NEON 实现。Launcher 使用离线包中登记的依赖替换本机过期缓存。 [上游打包改动](https://github.com/ly05010419/MacNativeGames/commit/17416fee1a8ab3e74042fb15cbca765cda609d88)
- **路线录制。** 《时之笛》改用共享的手柄录制和回放代码，继续优先读取 `OOT_INPUT_*`，也支持上游的 `TOTK_INPUT_*` 别名。 [路线录制 PR](https://github.com/ly05010419/MacNativeGames/pull/2402)

[Issue #2](https://github.com/zplzmzmpl/MacNativeGames/issues/2) 同时命中了《动物森友会》的岛屿账户支持。相关账户分支和该分支所需的上游测试补丁不适用于本 fork。

### 本机版 Launcher 1.1.9

- 随附本次同步的源码、`oot-native` 和 `oot-pool-sources-list`，沿用现有 Launcher 界面和离线依赖包。Launcher 更新完成后，可按需从游戏卡片应用新运行时。 [本机 Launcher 构建方法](README.md#构建本机版-launcher)
- Python 回归共 1,026 项，含复测 1,009 项通过、17 项跳过，另有 14 项 C 检查通过。 [仓库测试入口](Makefile#L41)

## 2026-11-26 · GitHub 回归检查

- 只改 Markdown 的推送和 PR 跳过 macOS 回归。包含代码或其他文件改动时仍会触发，Actions 页面也可以手动运行全套检查。对同一分支和同一触发事件，新运行会取消已被替代的旧运行。 [触发配置](.github/workflows/tests.yml)
- 将 macOS 测试时限从 15 分钟延长至 30 分钟，日志逐项显示测试名称。APFS 数据包回归测试会解析比较双方的路径，消除 macOS 临时目录经 `/var` 或 `/private/var` 访问时产生的误报。 [调整提交](https://github.com/zplzmzmpl/MacNativeGames/commit/3c5143a6)

## 2026-11-26 · 本机版 Launcher 1.1.8

审查了上游 `7ef42f53…786ddc00` 范围内 Action 命中的 5 个提交。和《时之笛》运行时、Launcher 更新及离线发布相关的改动已移植到 fork。Issue #1 已回复并标记为已完成。 [上游比较](https://github.com/ly05010419/MacNativeGames/compare/7ef42f53bf62e4646919b599256b39a9ae3f23ad...786ddc00880cacad63d3bd45497544d7edc50045) · [审查与处理结果](https://github.com/zplzmzmpl/MacNativeGames/issues/1#issuecomment-7191416973)

### 渲染

- **Mesh 渲染通道分割。** 上游模式 2 让连续的 mesh 绘制共享一个通道，在 mesh 绘制和普通绘制切换时才分割。原实现提前标记通道，遇到附件切换等操作导致通道重开时，标记可能丢失。Fork 在实际编码时记录绘制类型，也处理了作为普通绘制提交的颜色和深度清除，以及切到 mesh 前的延迟绘制回放。模式 2 可通过 `OOT_MESH_PASS_SPLIT=2` 显式启用。M1/M2 的默认模式为 1，每次 mesh 绘制单独成通道，模式 2 的 M1/M2 实机验证待完成。 [Fork 提交 `64d44b5c`](https://github.com/zplzmzmpl/MacNativeGames/commit/64d44b5c) · [上游 PR #2324](https://github.com/ly05010419/MacNativeGames/pull/2324)
- **MetalFX 缩放缓存。** 缓存满时，如果两种输入配置在相邻帧交替使用，刚构建的缩放器可能在第一次使用前就被淘汰。现在淘汰时同时考虑条目入缓存和最近使用的时间，两种配置可以留在缓存里。一并移植了在真实 Metal 设备上交替使用两种配置的回归测试。 [Fork 提交 `512984c4`](https://github.com/zplzmzmpl/MacNativeGames/commit/512984c4) · [上游缓存修复](https://github.com/ly05010419/MacNativeGames/commit/91495f66e4338a5b26f887f9a1e2807184930af7)

### Launcher 与打包

- **外接卷和工作目录。** Launcher 更新、完整打包和「存储」页共用工作卷检查。已挂载的卷允许在原处重建工作目录及缺失的上层目录。卷未挂载时，即使挂载点下还有同名父目录或工作目录，也会提示重新挂载。「存储」页也会拒绝统计和清理该路径，避免把系统盘上的残留目录当成外接盘内容。命令行可以用 `--work <目录>` 指定可用路径。 [Fork 提交 `62cb886b`](https://github.com/zplzmzmpl/MacNativeGames/commit/62cb886b) · [上游工作目录修复](https://github.com/ly05010419/MacNativeGames/commit/3b0eae42f4924775056ccd74df35245ef13ef586)
- **离线依赖包发布校验。** `tools.deps.offline_pack check` 在 macOS 网络沙箱下重新启动校验，确认外部连接被系统拒绝后，才从空依赖缓存验证离线包。校验全部通过才写入与依赖清单哈希关联的记录。这个变更作用于发布校验，常规打包继续使用 Launcher 随附的离线依赖包。 [Fork 提交 `4ef637d3`](https://github.com/zplzmzmpl/MacNativeGames/commit/4ef637d3) · [上游离线校验改动](https://github.com/ly05010419/MacNativeGames/commit/8c5a54a4f3ebc3ea32cb7eba183294d613cef86f)

### 本机安装与验证

- **本机版 Launcher 1.1.8** 已替换 `/Applications/MNG Launcher.app` 中的 1.1.7。它使用原有 Launcher 界面和离线依赖包，嵌入 `5a81796c` 的源码快照，并从该快照重编 `oot-native` 和 `oot-pool-sources-list`。已核对应用签名、源码与离线包的 SHA-256，以及两个预编译程序的签名。 [README 构建方法](README.md#构建本机版-launcher) · [内置源码提交](https://github.com/zplzmzmpl/MacNativeGames/commit/5a81796cd32398e147b2b0b59ba53b7166b4dc1e)
- **Apple M5 本机回归。** Python 测试共 1,016 项，999 项通过，17 项跳过。`make check-c` 的 14 项测试通过，图形代码编译为 arm64 对象。另用通道状态测试重现并验证了通道重开场景，用 Launcher 测试覆盖了挂载卷、未挂载但留有目录、完整打包和存储页操作。 [仓库测试入口](Makefile#L41)
