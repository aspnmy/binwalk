# Binwalk Qemu Docker 管理工具

本工具集提供了在Windows环境中通过Qemu虚拟化技术运行Binwalk Docker容器的完整解决方案，支持文件传输、容器管理和Binwalk分析操作的图形化界面。

## 功能特性

### installQemu.py
- 自动检测并安装Qemu环境（隔离模式，不污染系统PATH）
- 下载并配置Kali Linux最小化镜像
- 自动设置网络、共享文件夹和SSH访问
- 配置Docker环境和必要的权限
- 创建便捷的启动和管理脚本

### binwalk_GUiQemu.py
- 图形化SSH连接管理，连接到Qemu中的Kali系统
- 文件管理器，支持本地和远程文件的上传、下载和删除
- Docker容器管理，支持镜像拉取、容器启动、停止、重启和删除
- Binwalk分析功能，可视化执行Binwalk命令并显示结果
- 系统日志记录和Docker容器日志查看
- 多标签页界面设计，操作直观便捷

## 系统要求

- Windows 10/11 64位系统
- 至少8GB RAM（推荐16GB）
- 至少50GB可用磁盘空间
- 支持虚拟化的CPU（需要在BIOS中启用VT-x/AMD-V）
- Python 3.8或更高版本

## 安装依赖

在使用本工具前，请确保安装了以下Python依赖包：

```bash
pip install paramiko scp tkinter
```

## 使用流程

### 1. 安装Qemu环境

1. 以管理员身份运行命令提示符或PowerShell
2. 执行安装脚本：
   ```bash
   python installQemu.py
   ```
3. 按照提示完成Qemu和Kali镜像的安装
4. 安装完成后，系统会自动创建必要的配置文件

### 2. 启动Qemu虚拟机

安装完成后，可以通过以下方式启动Qemu虚拟机：

```bash
python start_qemu.py
```

或者直接运行生成的批处理文件：

```bash
start_qemu.bat
```

### 3. 使用图形界面管理工具

1. 确保Qemu虚拟机已启动
2. 运行图形界面工具：
   ```bash
   python binwalk_GUiQemu.py
   ```
3. 在"连接设置"标签页中，点击"连接"按钮连接到虚拟机
   - 默认连接参数：
     - 主机：localhost
     - 端口：2222
     - 用户名：kali
     - 密码：kali
4. 连接成功后，可以使用其他标签页的功能

### 4. 文件管理

- 在"文件管理"标签页中，可以浏览本地和远程文件
- 选择文件后，点击相应按钮进行上传、下载或删除操作
- 远程文件默认位于Docker容器的`/analysis`目录，对应Kali系统中的`/var/lib/docker/volumes/binwalkv3/_data`

### 5. Docker管理

- 在"Docker管理"标签页中，可以查看Docker服务和容器状态
- 点击相应按钮拉取镜像、启动、停止、重启或删除容器
- 可以查看容器的日志输出

### 6. Binwalk分析

- 在"Binwalk分析"标签页中，选择要分析的目标文件
- 设置分析选项（提取文件、详细输出、熵图等）
- 点击"执行Binwalk"开始分析
- 分析结果将实时显示在结果输出区域

## 配置文件说明

工具会在首次运行时自动创建`config.json`配置文件，包含以下设置：

- `ssh_host`：SSH服务器主机地址
- `ssh_port`：SSH服务器端口
- `ssh_user`：SSH用户名
- `ssh_password`：SSH密码
- `docker_image`：Docker镜像名称
- `docker_container`：Docker容器名称
- `analysis_dir`：分析目录路径
- `local_data_dir`：本地数据目录路径

您可以手动编辑此文件或通过图形界面的"保存配置"按钮更新设置。

## 常见问题

### 1. 无法连接到SSH服务器

- 确认Qemu虚拟机已启动
- 检查防火墙设置，确保2222端口已开放
- 验证连接参数是否正确

### 2. Docker命令执行失败

- 确保Kali系统中的Docker服务已启动
- 检查用户是否具有sudo权限
- 查看系统日志获取详细错误信息

### 3. 文件传输失败

- 检查文件权限设置
- 确保目标路径存在且有写入权限
- 对于大文件，请预留足够的传输时间

### 4. Qemu虚拟机启动失败

- 确认CPU虚拟化功能已在BIOS中启用
- 检查磁盘空间是否充足
- 查看启动日志获取详细错误信息

## 注意事项

- Qemu虚拟机默认配置了2GB内存和2个CPU核心，可以根据需要在`config.json`中调整
- 共享文件夹功能默认启用，本地目录映射到Kali系统的`/mnt/share`
- 为了保证性能，建议将大文件分析任务的文件放在SSD上
- 使用完成后，请及时关闭Qemu虚拟机以释放系统资源

## 卸载方法

要完全卸载本工具：

1. 停止并关闭Qemu虚拟机
2. 删除`devWinQemu`目录
3. 删除可能在用户目录下创建的相关文件和文件夹

## 许可证

本工具集基于MIT许可证开源。

## 联系方式

如有问题或建议，请联系项目维护者。