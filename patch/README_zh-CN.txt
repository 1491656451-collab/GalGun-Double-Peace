GalGun Double Peace 繁体中文资源补丁

这是按当前已测试游戏目录整理的未压缩补丁目录。请先用 Steam 将游戏初始化安装或验证为干净状态，再安装本补丁。

包含：

- 316 个普通 INT / _ENG 本地化文件
- 1 个 GG2Game.u（商店名称、SerialSize 与 WindowState_I1 贴图文字修复）
- 1 个商店配置文件
- 1 个字体包
- 4 个界面地图资源
- 1 个 Opening.umap

不包含：

- StaffCreditArcheType.* 制作人员名单
- 任何 .bak、临时文件或旧补丁文件

安装：

1. 完全退出游戏和 Steam 游戏进程。
2. 在 PowerShell 中运行：

   .\install_patch.ps1 -GameRoot "D:\SteamLibrary\steamapps\common\GalGun Double Peace"

   也可以双击 install_patch.bat，然后输入游戏根目录。
3. 脚本会先把原文件备份到本目录的 backup\时间戳 文件夹，再复制资源并逐个校验。

Opening.umap 使用指定的汉化源文件替换游戏原文件：

   GG2Game\CookedPC\Maps\Opening\Opening.umap

卸载恢复：

   .\uninstall_restore.ps1 -GameRoot "D:\SteamLibrary\steamapps\common\GalGun Double Peace"

卸载脚本默认使用 backup 下最新的一次安装备份，也可以用 -BackupPath 指定备份目录。

补丁目标必须是游戏根目录：

   ...\GalGun Double Peace\

不要把文件复制到补丁目录本身，也不要把 GameRoot 指向 GG2CNPatch_Distribution_Final_20260809。
