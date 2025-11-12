# Binwalk WSL Docker 管理工具

本目录包含在Windows系统上通过WSL2/WSL环境运行Binwalk Docker的工具集。

## 工具说明

### 1. install-wsl2.py

该脚本用于在Windows系统上自动安装WSL2或WSL环境，拉取Kali Linux镜像，并配置Docker环境。

**功能特性：**
- 自动检测Windows版本并启用相应的WSL功能
- 安装Kali Linux WSL发行版
- 配置Kali Linux并安装Docker
- 拉取binwalk Docker镜像
- 创建必要的Docker卷

**使用方法：**
```bash
# 以管理员权限运行PowerShell，然后执行以下命令
python install-wsl2.py

# 如需强制使用WSL1模式（适用于不支持WSL2的系统）
python install-wsl2.py --wsl1
```

### 2. binwalk_GUi.py

该图形界面工具用于管理WSL环境中的binwalk-docker容器，支持文件管理、命令执行和容器操作。

**功能特性：**
- 状态监控：显示WSL、Docker、Docker卷和容器的运行状态
- 文件管理：上传文件到Docker卷或从Docker卷下载文件
- 命令执行：在Docker容器中执行Binwalk命令并实时显示输出
- 容器管理：启动、停止、重启和移除容器

**使用方法：**
```bash
# 确保已安装Python和必要的依赖
# 运行图形界面
python binwalk_GUi.py
```

## 系统要求

- Windows 10 1903版本及以上或Windows 11（推荐）
- 至少4GB内存
- 至少20GB可用磁盘空间
- Python 3.6或更高版本

## 安装依赖

```bash
# 安装Python依赖
pip install tkinter
```

## 使用流程

1. 首先运行 `install-wsl2.py` 配置WSL和Docker环境
2. 完成初始化后，运行 `binwalk_GUi.py` 使用图形界面管理Binwalk Docker环境
3. 在GUI中，您可以上传固件文件、执行binwalk命令、查看结果和下载提取的文件

## 注意事项

- 安装WSL和Kali Linux时需要管理员权限
- 首次运行Kali Linux时，需要设置用户名和密码
- 文件传输功能需要Docker容器正在运行
- 如遇到WSL版本兼容性问题，可以使用`--wsl1`参数强制使用WSL1模式