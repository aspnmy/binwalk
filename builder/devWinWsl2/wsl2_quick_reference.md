# WSL2开发环境快速参考卡

## 🚀 快速启动命令

### 环境管理
```bash
# 启动WSL开发环境
python .trae/rules/wsl_dev_manager.py

# 重启环境
python .trae/rules/wsl_dev_manager.py res-win11

# 停止环境
python .trae/rules/wsl_dev_manager.py stop-win11

# 销毁环境
python .trae/rules/wsl_dev_manager.py del-win11
```

### 代码同步
```bash
# 同步代码到WSL环境
python .trae/rules/wsl_ide_integrator.py sync

# 在WSL环境中编译
python .trae/rules/wsl_ide_integrator.py build

# 运行测试
python .trae/rules/wsl_ide_integrator.py test
```

## ⚙️ 配置文件速查

### 核心配置
| 文件 | 作用 |
|------|------|
| `wsl-distro.info` | WSL发行版选择 |
| `wsl_config.json` | 环境详细配置 |
| `build-image-tools` | 开发工具列表 |

### 网关配置
| 文件 | 用途 |
|------|------|
| `download-gateway` | 下载域名配置 |
| `dockerimage-gateway` | 镜像域名配置 |

## 🔧 默认设置

### 连接信息
```
用户名: devman
密码: devman
RDP端口: 4489
HTTP端口: 4818  
VNC端口: 4777
```

### 路径映射
```
Windows: c:\devman\git_data\${gitbranch}
Linux: $HOME/git_data/${gitbranch}
```

## 🎯 环境变量

### 自动设置
```bash
DOWNLOAD_GATEWAY      # 下载网关域名
DOCKERIMAGE_GATEWAY   # 镜像网关域名
```

### 手动检查
```bash
echo $DOWNLOAD_GATEWAY
echo $DOCKERIMAGE_GATEWAY
```

## 🔍 故障排查

### 常见问题
```bash
# WSL状态检查
wsl --status

# 容器状态检查  
podman system info

# 网络连接检查
wsl -d <distro> ip addr
```

### 日志查看
```bash
# WSL事件日志
Get-WinEvent -LogName "Microsoft-Windows-Lxss" | Select-Object -Last 20

# 容器日志
podman logs <container-name>
```

## 📚 更多帮助

- 📖 完整文档: `wsl2_dev_environment_guide.md`
- 🔧 规则管理器: `rules_manager.py`
- 🧪 测试脚本: `check_rules_manager.py`

## 💡 提示

1. **环境隔离**: 每个项目使用独立的WSL环境
2. **版本控制**: 环境配置纳入git版本管理
3. **定期清理**: 不用的环境及时销毁释放资源
4. **备份重要**: 销毁前确保代码已提交到git