# Fix
可直接下载 v3.1.1-rc2-devWin版本，目前在Win系统中重构使用7-zip与LZMA本身的API实现了解压业务
<img width="1093" height="368" alt="企业微信截图_1762937594774" src="https://github.com/user-attachments/assets/0c933a85-442a-4e98-8473-49dcecb477aa" />


# Binwalk v3

这是 Binwalk 固件分析工具的更新版本，使用 Rust 重写以提高速度和准确性。

![binwalk v3](images/binwalk_animated.svg)

## 功能介绍

Binwalk 可以识别并选择性地提取嵌入在其他文件中的文件和数据。

虽然其主要重点是固件分析，但它支持[多种](https://github.com/ReFirmLabs/binwalk/wiki/Supported-Signatures)文件和数据类型。

通过[熵分析](https://github.com/ReFirmLabs/binwalk/wiki/Generating-Entropy-Graphs)，它甚至可以帮助识别未知的压缩或加密！

Binwalk 可以自定义并[集成](https://github.com/ReFirmLabs/binwalk/wiki/Using-the-Rust-Library)到您自己的 Rust 项目中。

## 跨平台支持

Binwalk v3 支持多个操作系统平台：
- Linux
- macOS
- **Windows**（包括对 7-Zip 作为 SquashFS 提取备选工具的支持）

## Windows 平台增强

在 Windows 平台上，我们特别优化了以下功能：

1. **SquashFS 提取增强**：当标准的 unsquashfs 工具不可用时，会自动回退到使用 7-Zip 进行提取，提高了兼容性
2. **LZMA 压缩检测优化**：增强了对 LZMA 压缩文件的检测能力
3. **构建脚本支持**：提供了专门的 Python 构建脚本，简化 Windows 环境下的编译过程
4. **图形用户界面**：提供了适用于 Windows 的图形界面，简化操作流程（详情请参阅 README_GUI.md）

## 安装方法

最简单的安装 Binwalk 及其所有依赖的方法是[构建 Docker 镜像](https://github.com/ReFirmLabs/binwalk/wiki/Building-A-Binwalk-Docker-Image)。

也可以通过 Rust 包管理器[安装](https://github.com/ReFirmLabs/binwalk/wiki/Cargo-Installation)。

或者，您可以[从源代码编译](https://github.com/ReFirmLabs/binwalk/wiki/Compile-From-Source)！

## Windows 构建指南

在 Windows 平台上，可以使用我们提供的构建脚本来简化编译过程：

```
python builder/build.py
```

该脚本会自动：
- 下载必要的依赖（MinGW、Rust、7-Zip）
- 配置编译环境
- 编译项目
- 生成可执行文件

## 使用方法

使用简单，分析快速，结果详细：

```
binwalk DIR-890L_AxFW110b07.bin
```
![example output](images/output.png)

使用 `--help` 或查看[Wiki](https://github.com/ReFirmLabs/binwalk/wiki#usage)了解更多高级选项！
