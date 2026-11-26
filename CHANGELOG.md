# 更新记录

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
