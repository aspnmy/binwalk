# WSL2纯净开发环境规则说明

## 概述

WSL2纯净开发环境规则旨在为开发者提供一个隔离、干净、可重复的开发环境，确保项目编译和调试不受宿主机环境配置的污染，同时支持跨平台开发和部署。

## 设计原因

### 1. 环境隔离需求
- **避免污染**：宿主机环境可能包含各种已安装的软件包、环境变量和配置，容易与项目需求产生冲突
- **版本冲突**：不同项目可能需要不同版本的依赖库和工具链
- **系统差异**：Windows、Linux、macOS系统环境差异导致开发体验不一致

### 2. 开发一致性需求
- **团队协作**：确保团队成员使用相同的开发环境
- **持续集成**：与CI/CD环境保持一致，减少"在我机器上能运行"的问题
- **环境可复制**：新成员可以快速搭建相同的开发环境

### 3. 容器化趋势
- **云原生开发**：适应容器化和云原生开发模式
- **微服务架构**：支持微服务架构下的独立开发环境
- **DevOps实践**：符合现代DevOps开发和运维一体化理念

## 核心特点

### 🔒 **纯净隔离**
- 完全隔离的WSL2环境，不受宿主机配置影响
- 独立的文件系统、网络配置和进程空间
- 可销毁重建，确保环境一致性

### 🚀 **快速部署**
- 基于容器技术，秒级启动开发环境
- 预配置常用开发工具和依赖
- 支持一键环境初始化和清理

### 🔄 **版本控制**
- 环境配置版本化，支持回滚和对比
- 代码变更与WSL环境同步管理
- 支持多分支并行开发

### 🎯 **精准匹配**
- 根据项目需求定制开发环境
- 支持多种操作系统版本选择
- 自动适配项目依赖和工具链

## 技术优势

### 1. **跨平台兼容性**
```
支持环境：
- Windows 11 专业版 (win11)
- Windows 11 LTS版 (win11l) 
- Windows 7 专业版 (win7u)
- Windows Server 2025 (win2025)
```

### 2. **标准化配置**
```
默认配置：
- 用户名：devman
- 密码：devman
- 端口：RDP(4489), HTTP(4818), VNC(4777)
- 路径：$HOME/git_data/${gitbranch}
```

### 3. **容器化支持**
```
集成功能：
- Podman容器运行时
- PortainerEE可视化管理
- 自动域名网关配置
- 跨平台镜像支持
```

## 使用方式

### 1. **环境初始化**

#### 查看当前配置
```bash
# 查看WSL发行版信息
cat .trae/rules/wsl-distro.info

# 查看环境配置
cat .trae/rules/wsl_config.json
```

#### 启动开发环境
```bash
# 进入项目目录
cd ${gitbranch}

# 运行WSL开发管理器
python .trae/rules/wsl_dev_manager.py
```

### 2. **日常开发流程**

#### 代码同步
```bash
# 将代码同步到WSL环境
python .trae/rules/wsl_ide_integrator.py sync

# 在WSL环境中编译调试
python .trae/rules/wsl_ide_integrator.py build
```

#### 环境管理
```bash
# 重启WSL环境
python .trae/rules/wsl_dev_manager.py res-win11

# 停止WSL环境  
python .trae/rules/wsl_dev_manager.py stop-win11

# 销毁WSL环境
python .trae/rules/wsl_dev_manager.py del-win11
```

### 3. **高级配置**

#### 自定义工具安装
编辑 `.trae/rules/build-image-tools` 文件：
```
buildah,git,curl,wget,portainerEE,custom-tool
```

#### 域名网关配置
编辑相关网关文件：
- `.trae/rules/download-gateway` - 下载域名
- `.trae/rules/dockerimage-gateway` - 镜像域名

#### 路径配置
修改 `.trae/rules/wsl_dev_path_manager.py` 来自定义路径映射规则。

## 最佳实践

### 1. **环境生命周期管理**
```
建议流程：
1. 项目启动时创建WSL环境
2. 开发过程中保持环境运行
3. 代码提交前进行环境同步
4. 项目结束后销毁环境
5. 需要时重新创建干净环境
```

### 2. **代码同步策略**
```
同步原则：
- 修改前先在宿主机进行
- 编译调试时同步到WSL环境
- 测试通过后提交到git仓库
- 保持宿主机和WSL环境代码一致
```

### 3. **版本控制配合**
```
git工作流：
1. 主分支保持与WSL环境同步
2. 功能分支在WSL环境中测试
3. 合并前确保环境一致性
4. 标签发布时记录环境版本
```

## 故障排除

### 常见问题

#### WSL环境无法启动
```bash
# 检查WSL服务状态
wsl --status

# 重启WSL服务
wsl --shutdown
```

#### 网络连接问题
```bash
# 检查网络配置
wsl -d <distro-name> ip addr

# 重启网络服务
wsl -d <distro-name> service network-manager restart
```

#### 容器运行失败
```bash
# 检查Podman状态
podman system info

# 清理容器缓存
podman system prune -a
```

### 日志查看
```bash
# WSL日志
Get-WinEvent -LogName "Microsoft-Windows-Lxss" | Select-Object -Last 20

# 容器日志
podman logs <container-name>
```

## 相关文件说明

### 核心配置文件
- `wsl-distro.info` - WSL发行版配置
- `wsl_config.json` - 环境详细配置
- `build-image-tools` - 开发工具列表
- `registerConfig.json` - 容器仓库配置

### 管理脚本
- `wsl_dev_manager.py` - WSL环境管理器
- `wsl_ide_integrator.py` - IDE集成工具
- `wsl_dev_path_manager.py` - 路径管理器
- `rules_manager.py` - 全局规则管理器

### 网管配置
- `download-gateway` - 下载域名配置
- `dockerimage-gateway` - 镜像域名配置
- `portainerEE-Compose` - PortainerEE配置

## 总结

WSL2纯净开发环境规则通过容器化技术为开发者提供了隔离、一致、可重复的开发环境，有效解决了传统开发环境中的环境冲突、版本不一致、系统差异等问题。配合完善的规则体系和自动化工具，能够显著提升开发效率和代码质量，是现代软件开发的最佳实践之一。