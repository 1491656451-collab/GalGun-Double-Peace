# GalGun: Double Peace 中文补丁源码归档

这是《GalGun: Double Peace》中文补丁的源码与可编辑文本归档，包含第二版补丁的本地化文本、安装脚本，以及制作过程中使用的提取、转换、字体、贴图和 Unreal Engine 3 资源处理脚本。

## 目录

- `patch/`：第二版补丁中可直接版本管理的 `.int`、`.ini`、安装脚本、校验清单和说明文件。
- `tools/`：补丁制作过程中编写的 Python、PowerShell 和 C 工具。
- `data/`：小型索引、字符串提取结果和中间文本数据。
- `docs/LARGE_FILES.md`：未纳入 Git 历史、需要作为 Release 资源另行上传的二进制补丁文件。

## 环境

- Windows 10/11
- Python 3.10 或更高版本
- PowerShell 5.1 或更高版本
- 可选 Python 包见 `requirements.txt`

大量脚本是针对本项目制作过程保留的研究工具，部分脚本仍包含当时机器上的绝对路径。运行前请先调整脚本顶部的 `Path`、`ROOT`、`SRC` 或工具路径变量。

## 安装补丁

Git 仓库只保存可编辑源码和小型文本文件。完整安装需要先取得 `docs/LARGE_FILES.md` 中列出的 cooked 二进制文件，并按 `patch/README_zh-CN.txt` 的说明放回补丁目录，再运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\patch\install_patch.ps1
```

## 说明

本仓库不包含游戏本体、ROM、NCA、NSP、原版备份、第三方工具二进制或大体积 cooked 游戏资源。使用者需要自行拥有合法游戏副本。

