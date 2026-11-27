# 时之笛 · MacNativeGames

这个 fork 维护 **Switch 2 版《塞尔达传说 时之笛》** 的 Apple Silicon macOS 移植。支持的游戏更新为 **v131072**。本 fork 面向键盘和鼠标玩家，维护 macOS 桌面版。运行和打包使用你自己导出的游戏，仓库保留《时之笛》构建所需的上游共享源码。

游戏源码在 `games/oot`。上游共用的 NVN 图形后端和部分工具仍在 `games/totk`，沿用原路径以便同步。

## 安装与更新

- 使用 Apple Silicon Mac 和 macOS 26 或更新版本。首次打包需要完整 Xcode 和 Metal Toolchain。
- 在 **MNG Launcher** 中选择《时之笛》。首次打包或 Launcher 要求完整打包时，导入自己的 v131072 游戏导出。
- 已安装的游戏从 Launcher 卡片更新。Launcher 使用它随附的源代码和着色器清单。要使用本仓库的新代码，先安装包含这些改动的 Launcher 构建。

[中文安装和排错文档](games/oot/docs/install.zh-CN.md) · [游戏功能与设置](games/oot/README.md) · [本机 Launcher 更新流程](maintenance.zh-CN.md)

## 构建本机版 Launcher

Launcher 界面源码在独立仓库。要更新本机版，准备一个可运行的 `/Applications/MNG Launcher.app`，使用现有界面和离线依赖包，重新编译本仓库的《时之笛》运行时并替换随附源码。需要 Apple Silicon、完整 Xcode、`uv` 和 Python 3.14。构建从 Git 提交取源码，请先提交要打包的改动。

在仓库根目录执行以下命令。所有构建文件都放在同一个临时目录中。

```sh
output=$(mktemp -d "$PWD/.launcher-build.XXXXXX")
commit=$(git rev-parse HEAD)
app="$output/MNG Launcher.app"
mkdir "$output/source" "$output/temp" "$output/offline"
export TMPDIR="$output/temp" UV_CACHE_DIR="$output/uv-cache"
export MNG_DEPS_CACHE="$output/deps-cache" PYTHONDONTWRITEBYTECODE=1
uv venv --python 3.14 "$output/.venv"
ditto "/Applications/MNG Launcher.app" "$app"
resources="$app/Contents/Resources"
info="$app/Contents/Info.plist"

uv run --python "$output/.venv/bin/python" python -B tools/launcher_source.py \
  pathspecs "$commit" > "$output/pathspecs"
archive_specs=()
while IFS= read -r spec; do archive_specs+=("$spec"); done < "$output/pathspecs"
git archive "$commit" -- "${archive_specs[@]}" | tar -xf - -C "$output/source"
printf '%s\n' "$commit" > "$output/source/.mng-source-commit"

offline_sha=$(/usr/libexec/PlistBuddy -c 'Print MNGOfflineStoreSHA256' "$info")
printf '%s  %s\n' "$offline_sha" "$resources/offline.tar" | shasum -a 256 -c -
tar -xf "$resources/offline.tar" -C "$output/offline"
(
  cd "$output/source"
  MNG_OFFLINE_STORE="$output/offline/offline" uv run --offline \
    --python "$output/.venv/bin/python" python -B tools/prebuilt.py build "$output/source"
)
tar --disable-copyfile --exclude='./.mng-source-commit' \
  -czf "$resources/source.tar.gz" -C "$output/source" .
```

把 `version` 设为新版本号，并在签名前按 [更新记录](CHANGELOG.md) 更新 `$resources/whats-new.json` 中的版本和说明。

```sh
version=1.1.9
source_sha=$(shasum -a 256 "$resources/source.tar.gz" | awk '{print $1}')
plutil -replace CFBundleVersion -string "$version" "$info"
plutil -replace CFBundleShortVersionString -string "$version" "$info"
plutil -replace MNGSourceCommit -string "$commit" "$info"
plutil -replace MNGSourceArchiveSHA256 -string "$source_sha" "$info"
codesign --force --sign - "$app"
codesign --verify --deep --strict "$app"
```

签名验证通过后，退出 Launcher，备份旧版，再把临时目录里的 App 放进 `/Applications`。确认新版能打开、版本号正确后，清理临时目录和旧版备份。本机版使用 ad hoc 签名，公开发行版走 Developer ID 签名和 Apple 公证流程。 [Launcher 发行说明](docs/builder-app.md)

## 存储与更新

游戏数据可以保留在 App 内，同时把构建工作目录放在外接 APFS 卷。这样平时可以拔盘游玩，更新时再挂载工作卷来复用着色器和管线。已安装 App 和工作目录的签名数据包匹配时，更新会优先在 App 所在的 APFS 卷上克隆已有 RomFS，省去约 26 GB 的跨盘复制。

## 上游同步与维护

1. **工作流检查上游并创建 Issue。** GitHub Actions 每天北京时间 09:17 检查上游 `main`。命中《时之笛》或相关的共享运行时、构建工具改动时，工作流会在本 fork 创建 Issue，附上比较范围和相关提交，并提醒维护者。 [上游监测工作流](https://github.com/zplzmzmpl/MacNativeGames/actions/workflows/watch-oot-upstream.yml)
2. **处理 Issue 并融合代码。** 逐项核对上游提交和本 fork 的差异，将适用于《时之笛》的改动合入本仓库，运行 `make check` 和改动涉及的专项测试。
3. **记录更新并回复 Issue。** 在 `CHANGELOG.md` 记录融合范围、取舍和验证结果。在原 Issue 回复处理结果，注明已处理并附上相关提交。 [更新记录](CHANGELOG.md)
4. **构建并替换本机 Launcher。** 从本次同步的 Git 提交构建新版 Launcher，核对签名和内置资源后，备份并替换 `/Applications/MNG Launcher.app`。打开新版确认能启动且版本正确，再清理构建文件和旧版备份。 [本机 Launcher 构建步骤](#构建本机版-launcher)

公共仓库连续 60 天没有活动时，GitHub 可能停用定时工作流。可在 Actions 页面重新启用。 [GitHub 定时工作流说明](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/disable-and-enable-workflows)

## 上游与许可

上游是 [ly05010419/MacNativeGames](https://github.com/ly05010419/MacNativeGames)。项目许可、第三方组件和《时之笛》的来源记录见下列文件。构建的游戏 App 供本人使用。

[LICENSE](LICENSE) · [第三方声明](THIRD_PARTY_NOTICES.md) · [《时之笛》源码来源](games/oot/third_party/COPIES.md)
