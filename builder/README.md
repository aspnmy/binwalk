# Binwalk Wsl2 构建脚本使用说明

## 简介

此分支专注于Windows平台上的Wsl2功能集成，提供Wsl2安装和管理功能。构建脚本在`builder`目录下创建完全隔离的构建环境，包括MinGW64和Rust工具链，**不依赖**系统中已安装的环境，确保构建过程的一致性和可靠性。

## 特性

- **完全隔离的构建环境**：所有依赖都安装在`builder/local_env`目录下
- **跨平台支持**：兼容Windows、Linux和macOS
- **自动下载和配置**：自动下载并安装所需的MinGW64和Rust工具链
- **详细的日志输出**：提供清晰的进度指示和错误信息
- **健壮的错误处理**：遇到问题时提供详细的排查建议
- **路径规范化**：自动处理不同操作系统的路径分隔符问题

## 工作原理

1. 在`builder/local_env`目录下创建隔离的构建环境
2. 下载并安装MinGW64（仅Windows系统需要）
3. 下载并安装Rust工具链到本地环境
4. 配置GNU工具链和目标三元组
5. 创建Cargo配置文件，指定正确的链接器路径
6. 构建项目并输出结果

## 使用方法

### Windows系统

1. 确保已安装Python 3.6或更高版本
2. 打开命令提示符或PowerShell
3. 导航到项目的`builder`目录
4. 运行命令：`python build.py`

> **注意**：脚本会自动下载和安装7z工具到本地环境，无需预先安装系统7z

### Linux/macOS系统

1. 确保已安装Python 3.6或更高版本
2. 打开终端
3. 导航到项目的`builder`目录
4. 给脚本添加执行权限：`chmod +x build.py`
5. 运行脚本：`./build.py` 或 `python3 build.py`

## 目录结构

```
binwalk/
├── builder/
│   ├── build.py         # 主构建脚本
│   ├── README.md        # 本文档
│   └── local_env/       # 本地构建环境（自动创建）
│       ├── mingw64/     # MinGW64工具链（Windows）
│       └── rust/        # Rust工具链
│           ├── cargo/   # Cargo配置和缓存
│           └── rustup/  # Rustup数据
├── .cargo/              # 自动创建的Cargo配置目录
└── target/              # 构建输出目录
```

## 常见问题

### 1. 下载依赖失败

**症状**：脚本无法下载MinGW64、Rust或7-Zip

**解决方案**：
- 检查网络连接
- 确保防火墙允许访问GitHub、Rust官网和7-Zip官网
- 手动下载并放到指定目录：
  - MinGW64: 下载到 `builder/local_env/mingw64.7z`
  - Rust: 可以手动安装到 `builder/local_env/rust` 目录
  - 7-Zip: 下载到 `builder/local_env/7z` 目录，并确保包含7z.exe文件

### 2. 权限不足

**症状**：无法创建目录或写入文件

**解决方案**：
- Windows: 以管理员身份运行命令提示符或PowerShell
- Linux/macOS: 使用sudo或以root用户运行脚本

### 3. 构建失败

**症状**：Cargo构建过程报错或解压失败

**解决方案**：
- 查看详细的错误输出
- 确保磁盘有足够空间（至少需要2GB）
- 检查项目的Cargo.toml文件是否正确
- 尝试删除`builder/local_env`目录后重新运行脚本
- 对于解压问题，脚本会自动尝试使用Python的py7zr库作为备选方案

## 清理构建环境

如果需要清理构建环境，只需删除`builder/local_env`目录即可：

```bash
# Windows
del /s /q builder\local_env

# Linux/macOS
rm -rf builder/local_env
```

## 注意事项

1. 首次运行会下载大量依赖，需要较长时间和稳定的网络连接
2. 本地环境占用约2-3GB磁盘空间
3. 构建脚本不会修改系统环境变量
4. 所有构建产物都位于项目根目录的`target`文件夹中
5. 脚本会自动下载和安装7z工具到本地环境，无需预先安装系统7z
6. 对于解压操作，脚本采用三级解压策略：优先使用本地7z工具 → 尝试系统7z → 使用Python的py7zr库

## 故障排除

如果遇到问题，请查看脚本输出的详细日志，日志中包含了完整的执行过程和错误信息。

对于Windows系统，构建失败后的排查步骤：
1. 检查是否有足够权限访问`builder`目录
2. 尝试手动解压`builder/local_env/mingw64.7z`（如果脚本下载了但解压失败）
3. 以管理员身份运行脚本
4. 尝试使用Python的测试脚本验证7z功能：`python test_7z_extract.py`

### 查看日志文件

脚本会生成详细的日志文件，可以帮助排查问题：
- 日志文件位置：`builder/build.log`
- 包含完整的执行过程和错误详细信息

## 联系方式

如有其他问题，请在项目仓库提交Issue。

---

*此构建脚本设计用于创建隔离的构建环境，确保在任何系统上都能获得一致的构建结果。*