#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WSL2/WSL环境安装脚本

本脚本用于在Windows系统上自动安装WSL2或WSL环境，
拉取Kali Linux镜像，并配置Docker/Podman环境以运行binwalk-docker。

参数：
    --wsl1: 强制使用WSL1模式

返回值：
    0: 安装成功
    非0: 安装失败
"""

import os
import sys
import subprocess
import time
import ctypes
import platform
import argparse
import re
import logging
from datetime import datetime

# 导入网关域名管理模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from gateway_manager import get_download_gateway, get_dockerimage_gateway
    GATEWAY_AVAILABLE = True
except ImportError:
    GATEWAY_AVAILABLE = False
    def get_download_gateway():
        return "gateway.cf.shdrr.org"
    def get_dockerimage_gateway():
        return "drrpull.shdrr.org"

# 导入IP检测模块
try:
    from check_ip_location import check_network_environment, get_smart_url
    IP_DETECTION_AVAILABLE = True
except ImportError:
    IP_DETECTION_AVAILABLE = False
    print("[-] IP检测模块不可用，将使用默认配置")

# 配置日志记录
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"wsl_install_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# 配置logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 确保以管理员权限运行
def is_admin():
    """
    检查当前脚本是否以管理员权限运行
    
    返回:
        bool: True表示以管理员权限运行，False表示不是
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_powershell_command(command, admin=False, wait=True):
    """
    运行PowerShell命令
    
    参数:
        command: str, 要执行的PowerShell命令
        admin: bool, 是否以管理员权限运行
        wait: bool, 是否等待命令执行完成
    
    返回:
        tuple: (返回码, 输出内容) 如果wait=True，否则返回(None, None)
    """
    try:
        if admin:
            # 使用更可靠的方法运行管理员权限命令
            import tempfile
            import os
            
            # 创建临时脚本文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False, encoding='utf-8') as f:
                f.write(command)
                script_path = f.name
            
            try:
                # 使用更简单的方法：直接调用powershell.exe以管理员权限运行脚本
                # 避免复杂的参数转义问题
                cmd = f'powershell -ExecutionPolicy Bypass -File "{script_path}"'
                
                logger.info(f"执行管理员命令: {cmd}")
                
                if wait:
                    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    stdout, stderr = process.communicate()
                    
                    # 清理临时文件
                    try:
                        os.unlink(script_path)
                    except:
                        pass
                    
                    # 处理编码问题
                    try:
                        output = stdout.decode('utf-8', errors='ignore') + stderr.decode('utf-8', errors='ignore')
                    except:
                        try:
                            output = stdout.decode('gbk', errors='ignore') + stderr.decode('gbk', errors='ignore')
                        except:
                            output = str(stdout) + str(stderr)
                            
                    return process.returncode, output
                else:
                    subprocess.Popen(cmd, shell=True)
                    # 异步模式下稍后清理临时文件
                    return None, None
                    
            except Exception as e:
                # 清理临时文件
                try:
                    os.unlink(script_path)
                except:
                    pass
                logger.error(f"执行管理员命令失败: {str(e)}")
                return -1, str(e)
        else:
            # 普通权限命令
            cmd = f'powershell -Command "{command}"'
            
            logger.info(f"执行命令: {cmd}")
            
            if wait:
                process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = process.communicate()
                
                # 处理编码问题
                try:
                    output = stdout.decode('utf-8', errors='ignore') + stderr.decode('utf-8', errors='ignore')
                except:
                    try:
                        output = stdout.decode('gbk', errors='ignore') + stderr.decode('gbk', errors='ignore')
                    except:
                        output = str(stdout) + str(stderr)
                        
                return process.returncode, output
            else:
                subprocess.Popen(cmd, shell=True)
                return None, None
                
    except Exception as e:
        logger.error(f"执行命令时出错: {str(e)}")
        return -1, str(e)

def check_windows_version():
    """
    检查Windows版本，确保支持WSL
    
    返回:
        tuple: (是否支持WSL2, 系统信息)
    """
    try:
        # 获取Windows版本信息
        win_version = platform.win32_ver()
        version_str = win_version[0]
        version_detail = win_version[1]
        
        # 更安全地解析构建号
        build_number = 0
        try:
            # 尝试从version_detail中获取构建号（Windows 10/11格式通常为10.0.xxxxx）
            if '.' in version_detail:
                parts = version_detail.split('.')
                if len(parts) >= 3:
                    build_number = int(parts[2])
        except (ValueError, IndexError):
            # 如果解析失败，默认为0
            build_number = 0
        
        logger.info(f"Windows版本: {version_str} {version_detail} 构建 {build_number}")
        
        # Windows 10 1903以上或Windows 11支持WSL2
        # 对于Windows 11，直接认为支持WSL2
        supports_wsl2 = False
        if version_str == '11':
            supports_wsl2 = True
        elif version_str == '10' and build_number >= 18362:
            supports_wsl2 = True
        
        return supports_wsl2, f"Windows {version_str} {version_detail} Build {build_number}"
    except Exception as e:
        logger.error(f"检查Windows版本时出错: {e}")
        return False, f"未知系统: {str(e)}"

def detect_wsl2():
    """
    检测WSL2环境是否已存在
    
    返回:
        bool: True表示WSL2已存在，False表示不存在
    """
    logger.info("检测WSL2环境...")
    try:
        code, output = run_powershell_command("wsl --status")
        # 检查输出中是否包含WSL2相关信息
        if code == 0 and "默认版本" in output and ("2" in output or "Default Version: 2" in output):
            return True
        return False
    except Exception as e:
        logger.error(f"检测WSL2时出错: {str(e)}")
        return False

def ask_user_choice(prompt, options, default):
    """
    询问用户选择
    
    参数:
        prompt: str, 提示信息
        options: dict, 选项字典，格式为 {选项键: 选项描述}
        default: str, 默认选项键
    
    返回:
        str: 用户选择的选项键
    """
    print(f"\n{prompt}")
    for key, desc in options.items():
        default_mark = " [默认]" if key == default else ""
        print(f"  {key}: {desc}{default_mark}")
    
    while True:
        choice = input("请输入您的选择: ").strip().lower()
        if not choice:
            return default
        if choice in options:
            return choice
        print("无效的选择，请重新输入")

def ask_component_install(component_name, exists):
    """
    询问用户是否安装组件
    
    参数:
        component_name: str, 组件名称
        exists: bool, 组件是否已存在
    
    返回:
        str: 用户选择（"skip", "reinstall", "overwrite", "manual"）
    """
    if exists:
        prompt = f"{component_name} 已检测到，您希望如何处理？"
        options = {
            "skip": f"跳过 {component_name} 的安装",
            "reinstall": f"重新完整安装 {component_name}",
            "overwrite": f"覆盖安装 {component_name}",
            "manual": f"手动处理后再继续"
        }
        return ask_user_choice(prompt, options, "skip")
    return "install"  # 不存在时直接安装

def enable_wsl_features():
    """
    启用WSL和虚拟机平台功能
    
    返回:
        bool: True表示启用成功，False表示失败
    """
    logger.info("启用WSL和虚拟机平台功能...")
    print("[+] 启用WSL和虚拟机平台功能...")
    
    # 启用适用于Linux的Windows子系统
    code, output = run_powershell_command("dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart", admin=True)
    if code != 0:
        print(f"[-] 启用WSL功能失败: {output}")
        return False
    
    # 启用虚拟机平台（WSL2需要）
    code, output = run_powershell_command("dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart", admin=True)
    if code != 0:
        logger.error(f"启用虚拟机平台功能失败: {output}")
        print(f"[-] 启用虚拟机平台功能失败: {output}")
        logger.warning("继续尝试，但WSL可能只能以WSL1模式运行")
        print("[!] 继续尝试，但WSL可能只能以WSL1模式运行")
    
    return True

def set_wsl_default_version(version=2):
    """
    设置WSL默认版本
    
    参数:
        version: int, WSL版本(1或2)
    
    返回:
        bool: True表示设置成功，False表示失败
    """
    print(f"[+] 设置WSL默认版本为{version}...")
    
    code, output = run_powershell_command(f"wsl --set-default-version {version}")
    if code != 0:
        print(f"[-] 设置WSL默认版本失败: {output}")
        print(f"[!] 将继续以WSL{1 if version == 2 else 2}模式运行")
        return False
    
    return True

def install_kali_linux():
    """
    安装Kali Linux WSL发行版
    
    返回:
        bool: True表示安装成功，False表示失败
    """
    # 检查Kali Linux是否已安装
    exists = check_kali_linux_exists()
    
    # 询问用户是否安装
    action = ask_component_install("Kali Linux", exists)
    
    if action == "skip":
        logger.info("跳过Kali Linux安装")
        print("[+] 跳过Kali Linux安装")
        return True
    elif action == "manual":
        logger.info("请手动处理Kali Linux，完成后按任意键继续...")
        print("[+] 请手动处理Kali Linux，完成后按任意键继续...")
        input()
        return check_kali_linux_exists()
    
    print("[+] 安装Kali Linux...")
    # 从Microsoft Store安装Kali Linux
    code, output = run_powershell_command("wsl --install -d Kali-Linux")
    if code != 0:
        print(f"[-] 从Microsoft Store安装Kali Linux失败: {output}")
        logger.warning("尝试通过手动下载方式安装...")
        print("[!] 尝试通过手动下载方式安装...")
        
        # 提供手动安装指导
        print("\n请手动执行以下步骤:")
        print("1. 打开Microsoft Store")
        print("2. 搜索并安装'Kali Linux'")
        print("3. 安装完成后启动Kali Linux并完成初始设置")
        print("4. 完成后按任意键继续...")
        
        input()
        
        # 再次检查是否安装成功
        if not check_kali_linux_exists():
            logger.error("安装Kali Linux失败，请确保已正确安装")
            print("[-] 安装Kali Linux失败，请确保已正确安装")
            return False
    
    return True

def fetch_latest_docker_config(network_info=None):
    """
    从GitHub拉取最新的Docker配置文件
    
    参数:
        network_info: dict, 网络环境信息
    
    返回:
        list: 镜像加速地址列表，如果拉取失败则返回None
    """
    logger.info("尝试从GitHub拉取最新Docker配置...")
    print("[+] 尝试从GitHub拉取最新Docker配置...")
    
    try:
        import urllib.request
        import json
        
        # 原始URL
        original_url = "https://raw.githubusercontent.com/aspnmy/BestHostsMonitor/refs/heads/devbox/CN/docker.list"
        
        # 根据网络环境选择智能URL
        if network_info and IP_DETECTION_AVAILABLE:
            url = get_smart_url(original_url, network_info)
        else:
            url = original_url
        
        # 设置超时时间为10秒
        with urllib.request.urlopen(url, timeout=10) as response:
            if response.status == 200:
                content = response.read().decode('utf-8')
                
                # 解析配置文件内容
                mirrors = []
                for line in content.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # 提取URL
                        if 'registry-mirrors' in line or 'mirror' in line:
                            # 尝试提取URL
                            import re
                            urls = re.findall(r'https?://[^\s\'"]+', line)
                            mirrors.extend(urls)
                
                if mirrors:
                    print(f"[+] 成功拉取到 {len(mirrors)} 个镜像加速地址")
                    return mirrors
                else:
                    logger.warning("配置文件格式不符合预期，使用内置参数")
                    print("[-] 配置文件格式不符合预期，使用内置参数")
                    
    except urllib.error.URLError as e:
        print(f"[-] 网络连接失败: {e}")
    except Exception as e:
        print(f"[-] 拉取配置文件失败: {e}")
    
    logger.info("使用内置镜像加速参数")
    print("[!] 使用内置镜像加速参数")
    return None

def update_container_config(container_tool, network_info=None):
    """
    更新容器配置文件，添加镜像加速和优化配置
    
    参数:
        container_tool: str, 容器工具，可选值为"podman"或"docker"
        network_info: dict, 网络环境信息
    
    返回:
        bool: True表示更新成功，False表示失败
    """
    print(f"[+] 更新{container_tool}配置文件...")
    
    # 尝试拉取最新配置
    latest_mirrors = fetch_latest_docker_config(network_info)
    
    # 获取网关域名
    dockerimage_gateway = get_dockerimage_gateway()
    
    config_data = {
        "bip": "172.17.0.1/24",
        "log-level": "warn",
        "iptables": True,
        "api-cors-header": "*",
        "registry-mirrors": latest_mirrors if latest_mirrors else [
            f"https://{dockerimage_gateway}",
            "https://docker.shdrr.org", 
            "https://docker.1panelproxy.com"
        ]
    }
    
    if container_tool.lower() == "docker":
        # Docker配置文件路径
        config_script = f'''
        #!/bin/bash
        echo "创建Docker配置文件..."
        sudo mkdir -p /etc/docker
        
        cat > /tmp/daemon.json << 'EOF'
{{
    "bip": "{config_data['bip']}",
    "log-level": "{config_data['log-level']}",
    "iptables": {str(config_data['iptables']).lower()},
    "api-cors-header": "{config_data['api-cors-header']}",
    "registry-mirrors": {str(config_data['registry-mirrors']).replace("'", '"')}
}}
EOF
        
        sudo mv /tmp/daemon.json /etc/docker/daemon.json
        sudo chmod 644 /etc/docker/daemon.json
        
        echo "重启Docker服务以应用配置..."
        sudo systemctl restart docker 2>/dev/null || sudo service docker restart
        
        echo "Docker配置更新完成"
        '''
    else:
        # Podman配置文件路径
        config_script = f'''
        #!/bin/bash
        echo "创建Podman配置文件..."
        sudo mkdir -p /etc/containers
        
        cat > /tmp/containers.conf << 'EOF'
[engine]
env = ["REGISTRIES_SEARCH_TAG='docker.io'"]

[engine.registry.mirror]
"docker.io" = {str(config_data['registry-mirrors']).replace("'", '"')}
EOF
        
        sudo mv /tmp/containers.conf /etc/containers/containers.conf
        sudo chmod 644 /etc/containers/containers.conf
        
        # 创建registry配置文件
        dockerimage_gateway = get_dockerimage_gateway()
        
        cat > /tmp/registries.conf << 'EOF'
[[registry]]
prefix = "docker.io"
location = "docker.io"
[[registry.mirror]]
location = "https://{dockerimage_gateway}"
[[registry.mirror]]
location = "https://docker.shdrr.org"
[[registry.mirror]]
location = "https://docker.1panelproxy.com"
EOF
        
        sudo mv /tmp/registries.conf /etc/containers/registries.conf.d/mirrors.conf
        sudo chmod 644 /etc/containers/registries.conf.d/mirrors.conf
        
        echo "重启Podman服务以应用配置..."
        sudo systemctl restart podman 2>/dev/null || sudo pkill -f podman
        
        echo "Podman配置更新完成"
        '''
    
    # 将脚本保存到临时文件
    with open("update_config.sh", "w") as f:
        f.write(config_script)
    
    # 在Kali Linux中执行脚本
    code, output = run_powershell_command("wsl -d kali-linux -e bash -c 'cat > update_config.sh && chmod +x update_config.sh && ./update_config.sh' < update_config.sh")
    
    # 清理临时文件
    os.remove("update_config.sh")
    
    if code != 0:
        print(f"[-] 更新{container_tool}配置失败: {output}")
        return False
    
    print(f"[+] {container_tool}配置更新成功！")
    return True

def generate_random_password(length=6):
    """
    生成指定长度的随机密码
    
    参数:
        length: int, 密码长度，默认为6位
    
    返回:
        str: 生成的随机密码
    """
    import random
    import string
    
    # 使用字母和数字生成密码
    characters = string.ascii_letters + string.digits
    password = ''.join(random.choice(characters) for _ in range(length))
    return password

def create_config_file(username, password):
    """
    创建name.config配置文件
    
    参数:
        username: str, 用户名
        password: str, 密码
    
    返回:
        bool: True表示创建成功，False表示失败
    """
    try:
        # 获取脚本同级目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, "name.config")
        
        # 创建配置文件内容
        config_content = f"""# Kali Linux WSL 配置信息
# 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}

[KaliLinux]
username = {username}
password = {password}
wsl_distro = kali-linux

# GUI程序连接信息
connection_info = wsl://{username}@kali-linux
"""
        
        # 写入配置文件
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        print(f"[+] 配置文件已创建: {config_path}")
        return True
        
    except Exception as e:
        print(f"[-] 创建配置文件失败: {str(e)}")
        return False

def setup_kali_linux_user():
    """
    自动设置Kali Linux用户名和密码（非交互式）
    
    返回:
        tuple: (用户名, 密码) 如果成功，否则返回 (None, None)
    """
    username = "binwalk"
    password = generate_random_password(6)
    
    print(f"[+] 自动配置Kali Linux用户...")
    print(f"[+] 用户名: {username}")
    print(f"[+] 密码: {password}")
    
    # 创建用户配置脚本（非交互式）
    setup_script = f'''#!/bin/bash
set -e  # 遇到错误立即退出

echo "开始自动配置Kali Linux用户..."

# 确保以root身份运行
if [ "$EUID" -ne 0 ]; then 
    echo "需要root权限，正在切换..."
    exec sudo "$0" "$@"
fi

# 检查是否已经存在用户
if id "{username}" &>/dev/null; then
    echo "用户 {username} 已存在"
else
    echo "创建用户 {username}..."
    # 创建用户
    useradd -m -s /bin/bash {username}
    echo "{username}:{password}" | chpasswd
    usermod -aG sudo {username}
    echo "用户 {username} 创建成功"
fi

# 设置WSL默认用户
echo "配置WSL默认用户..."
# 创建wsl.conf文件
cat > /etc/wsl.conf << 'EOF'
[user]
default={username}

[boot]
systemd=true
EOF

# 配置sudo免密码
echo "配置sudo权限..."
echo "{username} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/{username}
chmod 440 /etc/sudoers.d/{username}

echo "用户配置完成"
echo "用户名: {username}"
echo "密码: {password}"
'''
    
    try:
        # 将脚本保存到临时文件
        with open("kali_user_setup.sh", "w", encoding='utf-8') as f:
            f.write(setup_script)
        
        # 使用非交互式方式执行脚本
        print("[+] 正在配置Kali Linux用户...")
        # 使用wsl -u root以root身份执行，避免交互式登录
        code, output = run_powershell_command(f"wsl -d kali-linux -u root -e bash -c 'cat > /tmp/user_setup.sh && chmod +x /tmp/user_setup.sh && /tmp/user_setup.sh' < kali_user_setup.sh")
        
        # 清理临时文件
        os.remove("kali_user_setup.sh")
        
        if code != 0:
            print(f"[-] 配置Kali Linux用户失败: {output}")
            return None, None
        
        print("[+] Kali Linux用户配置成功")
        
        # 创建配置文件
        if create_config_file(username, password):
            print("[+] 配置文件创建成功")
        else:
            print("[-] 配置文件创建失败")
        
        return username, password
        
    except Exception as e:
        print(f"[-] 配置Kali Linux用户时出错: {str(e)}")
        return None, None

def configure_kali_linux(container_tool="podman", network_info=None):
    """
    配置Kali Linux，安装Docker或Podman
    
    参数:
        container_tool: str, 容器工具，可选值为"docker"或"podman"
        network_info: dict, 网络环境信息，包含IP、地区和使用镜像源的标志
    
    返回:
        bool: True表示配置成功，False表示失败
    """
    print(f"[+] 配置Kali Linux并安装{container_tool}...")

    if container_tool.lower() == "podman":
        # 安装Podman
        podman_install_script = '''
        #!/bin/bash
        echo "更新Kali Linux软件包..."
        sudo apt update
        sudo apt upgrade -y
        
        echo "安装Podman..."
        sudo apt install -y podman podman-compose
        
        echo "将当前用户添加到相关组..."
        sudo usermod -aG docker $USER
        
        echo "启用并启动Podman服务..."
        systemctl --user enable podman.socket
        systemctl --user start podman.socket
        
        echo "验证Podman安装..."
        podman --version
        podman-compose --version
        '''
        
        # 将脚本保存到临时文件
        with open("kali_setup.sh", "w") as f:
            f.write(podman_install_script)
    else:
        # 更新软件包并安装Docker
        docker_install_script = '''
        #!/bin/bash
        echo "更新Kali Linux软件包..."
        sudo apt update
        sudo apt upgrade -y
        
        echo "安装Docker依赖..."
        sudo apt install -y apt-transport-https ca-certificates curl gnupg2 software-properties-common
        
        echo "添加Docker GPG密钥..."
        # 根据网络环境选择Docker GPG密钥地址
        gpg_key_url = get_smart_url("https://download.docker.com/linux/debian/gpg", network_info) if IP_DETECTION_AVAILABLE else "https://download.docker.com/linux/debian/gpg"
        curl -fsSL $gpg_key_url | sudo apt-key add -
        
        echo "添加Docker源..."
        docker_repo_url = get_smart_url("https://download.docker.com/linux/debian", network_info) if IP_DETECTION_AVAILABLE else "https://download.docker.com/linux/debian"
        echo "deb [arch=amd64] $docker_repo_url buster stable" | sudo tee /etc/apt/sources.list.d/docker.list
        
        echo "安装Docker..."
        sudo apt update
        sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose
        
        echo "将当前用户添加到docker组..."
        sudo usermod -aG docker $USER
        
        echo "启动Docker服务..."
        sudo service docker start
        
        echo "验证Docker安装..."
        docker --version
        docker-compose --version
        '''
        
        # 将脚本保存到临时文件
        with open("kali_setup.sh", "w") as f:
            f.write(docker_install_script)
    
    # 在Kali Linux中执行脚本
    code, output = run_powershell_command("wsl -d kali-linux -e bash -c 'cat > setup.sh && chmod +x setup.sh && ./setup.sh' < kali_setup.sh")
    
    # 清理临时文件
    os.remove("kali_setup.sh")
    
    if code != 0:
        print(f"[-] 配置Kali Linux失败: {output}")
        return False
    
    # 更新容器配置文件
    if not update_container_config(container_tool, global_network_info):
        print(f"[-] 更新{container_tool}配置失败，但将继续安装")
    
    return True

def ask_container_tool():
    """
    询问用户选择容器工具
    
    返回:
        str: "podman" 或 "docker"
    """
    prompt = "请选择要安装的容器工具："
    options = {
        "podman": "安装Podman容器工具（推荐）",
        "docker": "安装Docker容器工具"
    }
    return ask_user_choice(prompt, options, "podman")

def pull_binwalk_container_image(container_tool="podman", network_info=None):
    """
    拉取binwalk容器镜像
    
    参数:
        container_tool: str, 容器工具，可选值为"docker"或"podman"
        network_info: dict, 网络环境信息，包含IP、地区和使用镜像源的标志
    
    返回:
        bool: True表示拉取成功，False表示失败
    """
    print(f"[+] 拉取binwalk {container_tool}镜像...")
    
    # 检查镜像是否已存在
    code, output = run_powershell_command(f"wsl -d kali-linux -e {container_tool} images")
    image_exists = "refirmlabs/binwalk" in output.lower() if code == 0 else False
    
    # 询问用户是否拉取
    action = ask_component_install(f"binwalk {container_tool}镜像", image_exists)
    if action == "skip":
        print(f"[+] 跳过拉取binwalk {container_tool}镜像")
        return True
    elif action == "manual":
        logger.info("请手动处理镜像，完成后按任意键继续...")
        print("[+] 请手动处理镜像，完成后按任意键继续...")
        input()
        return True
    
    # 拉取镜像
    # 根据网络环境选择镜像地址
    if IP_DETECTION_AVAILABLE and network_info:
        image_url = get_smart_url("refirmlabs/binwalk:latest", network_info)
        pull_command = f"wsl -d kali-linux -e {container_tool} pull {image_url}"
    else:
        pull_command = f"wsl -d kali-linux -e {container_tool} pull refirmlabs/binwalk:latest"
    
    code, output = run_powershell_command(pull_command)
    if code != 0:
        print(f"[-] 拉取binwalk {container_tool}镜像失败: {output}")
        print(f"[!] 可以稍后在GUI中重试")
        return False
    
    return True

def create_binwalk_volume(container_tool="podman"):
    """
    创建binwalk容器卷
    
    参数:
        container_tool: str, 容器工具，可选值为"docker"或"podman"
    
    返回:
        bool: True表示创建成功，False表示失败
    """
    print(f"[+] 创建binwalk {container_tool}卷...")
    
    # 检查卷是否已存在
    code, output = run_powershell_command(f"wsl -d kali-linux -e {container_tool} volume ls")
    volume_exists = "binwalkv3" in output.lower() if code == 0 else False
    
    # 询问用户是否创建
    action = ask_component_install(f"binwalk {container_tool}卷", volume_exists)
    if action == "skip":
        print(f"[+] 跳过创建binwalk {container_tool}卷")
        return True
    elif action == "manual":
        logger.info("请手动处理卷，完成后按任意键继续...")
        print("[+] 请手动处理卷，完成后按任意键继续...")
        input()
        return True
    
    # 创建卷
    code, output = run_powershell_command(f"wsl -d kali-linux -e {container_tool} volume create binwalkv3")
    if code != 0:
        print(f"[-] 创建binwalk {container_tool}卷失败: {output}")
        print(f"[!] 可以稍后在GUI中重试")
        return False
    
    return True

def ask_portainer_install():
    """
    询问用户是否安装Portainer
    
    返回:
        bool: True表示安装，False表示不安装
    """
    prompt = "是否安装Portainer（容器管理工具）？"
    options = {
        "yes": "安装Portainer",
        "no": "不安装Portainer（默认）"
    }
    choice = ask_user_choice(prompt, options, "no")
    return choice == "yes"

def ask_portainer_version():
    """
    询问用户选择的Portainer版本
    
    返回:
        str: "ce", "ee" 或 "agent"
    """
    prompt = "请选择要安装的Portainer版本："
    options = {
        "ce": "Portainer CE（社区版，免费）",
        "ee": "Portainer EE（商业版）",
        "agent": "Portainer Agent（监管网关）"
    }
    return ask_user_choice(prompt, options, "ce")

def get_socket_path(container_tool):
    """
    根据容器工具获取socket路径
    
    参数:
        container_tool: str, 容器工具（podman或docker）
    
    返回:
        str: socket路径
    """
    if container_tool.lower() == "podman":
        return "/run/podman/podman.sock"
    else:
        return "/var/run/docker.sock"

def get_image_tag(portainer_version, network_info=None):
    """
    根据Portainer版本获取镜像标签
    
    参数:
        portainer_version: str, Portainer版本（ce或ee）
        network_info: dict, 网络环境信息，包含IP、地区和使用镜像源的标志
    
    返回:
        str: 镜像标签
    """
    if portainer_version.lower() == "ce":
        base_image = "portainer/portainer-ce:lts"
    else:
        base_image = "ghcr.io/aspnmy/portainer-ee:2.34.0-alpine"
    
    # 根据网络环境选择镜像地址
    if IP_DETECTION_AVAILABLE and network_info:
        return get_smart_url(base_image, network_info)
    else:
        return base_image

def install_portainer(portainer_version, container_tool, network_info=None):
    """
    安装Portainer
    
    参数:
        portainer_version: str, Portainer版本（ce、ee或agent）
        container_tool: str, 容器工具（podman或docker）
        network_info: dict, 网络环境信息，包含IP、地区和使用镜像源的标志
    
    返回:
        bool: True表示安装成功，False表示失败
    """
    print(f"[+] 安装Portainer {portainer_version.upper()}...")
    
    # 根据版本选择配置文件
    if portainer_version.lower() == "agent":
        compose_file = "u:\\git\\binwalk\\builder\\agent-Compose"
    else:
        compose_file = "u:\\git\\binwalk\\builder\\portainerEE-Compose"
    
    # 获取socket路径
    socket_path = get_socket_path(container_tool)
    
    # 读取配置文件
    try:
        with open(compose_file, 'r') as f:
            compose_content = f.read()
    except Exception as e:
        print(f"[-] 读取配置文件失败: {str(e)}")
        return False
    
    # 替换变量
    compose_content = compose_content.replace("${socket_path}", socket_path)
    
    # 如果不是agent版本，还需要替换image_tag
    if portainer_version.lower() != "agent":
        image_tag = get_image_tag(portainer_version, network_info)
        compose_content = compose_content.replace("${image_tag}", image_tag)
    
    # 将修改后的配置保存到临时文件
    temp_compose_file = "wsl_portainer_compose.yml"
    try:
        with open(temp_compose_file, 'w') as f:
            f.write(compose_content)
    except Exception as e:
        print(f"[-] 写入临时配置文件失败: {str(e)}")
        return False
    
    # 确保卷存在
    if portainer_version.lower() == "agent":
        volume_name = "portainer_agent_data"
    else:
        volume_name = "portainerEE_data"
    
    # 创建卷
    code, output = run_powershell_command(f"wsl -d kali-linux -e {container_tool} volume create {volume_name}")
    if code != 0:
        print(f"[-] 创建{volume_name}卷失败，但将继续安装: {output}")
    
    # 使用compose文件启动容器
    print(f"[+] 使用{container_tool}启动Portainer...")
    compose_command = "docker-compose" if container_tool.lower() == "docker" else "podman-compose"
    
    # 将临时文件复制到WSL环境并执行
    code, output = run_powershell_command(f"wsl -d kali-linux -e bash -c 'cat > portainer_compose.yml && {compose_command} -f portainer_compose.yml up -d' < {temp_compose_file}")
    
    # 清理临时文件
    try:
        os.remove(temp_compose_file)
    except:
        pass
    
    if code != 0:
        print(f"[-] 启动Portainer失败: {output}")
        print(f"[!] 请检查{container_tool}服务是否正常运行")
        return False
    
    print(f"[+] Portainer {portainer_version.upper()} 安装成功！")
    
    # 显示访问信息
    if portainer_version.lower() == "agent":
        logger.info("Portainer Agent已启动，等待被Portainer管理端连接")
        print("[+] Portainer Agent已启动，等待被Portainer管理端连接")
    else:
        print("[+] 访问地址:")
        print("  - HTTPS: https://localhost:11866")
        print("  - HTTP: http://localhost:11868")
        print("  - API: http://localhost:11862")
    
    return True

def check_kali_linux_exists():
    """
    检查Kali Linux是否已安装
    
    返回:
        bool: True表示已安装，False表示未安装
    """
    code, output = run_powershell_command("wsl -l -v")
    if code != 0:
        return False
    
    # 处理UTF-16编码的输出，移除空字符
    try:
        # 尝试解码UTF-16编码的输出
        if '\x00' in output:
            # 移除空字符并转换为正常字符串
            clean_output = output.replace('\x00', '')
            return "kali" in clean_output.lower()
        else:
            return "kali" in output.lower()
    except Exception:
        # 如果处理失败，尝试原始方法
        return "kali" in output.lower()

def setup_completion():
    """
    设置完成后的操作
    
    返回:
        None
    """
    print("\n[+] 安装和配置完成！")
    logger.info("您现在可以运行binwalk_GUi.py来使用图形界面管理WSL Docker环境")
    print("[+] 您现在可以运行binwalk_GUi.py来使用图形界面管理WSL Docker环境")
    logger.info("请注意：首次运行GUI时可能需要初始化WSL环境")
    print("[+] 请注意：首次运行GUI时可能需要初始化WSL环境")
    # 自动继续，不等待用户输入
    print("[+] 安装流程已完成，程序将自动退出...")
    time.sleep(2)  # 给用户2秒时间查看完成信息

def display_install_menu(network_info=None):
    """
    显示安装模式菜单
    
    参数:
        network_info: dict, 网络环境信息，包含IP和地区信息
    
    返回:
        str: 用户选择的安装模式
    """
    print("\n" + "=" * 50)
    print("        选择安装模式")
    print("=" * 50)
    
    # 显示网络信息（如果可用）
    if network_info:
        print(f"网络信息:")
        print(f"  IP地址: {network_info.get('ip', '未知')}")
        print(f"  地区: {network_info.get('country', '未知')}")
        print(f"  镜像源: {'启用' if network_info.get('use_mirror', False) else '禁用'}")
        print("-" * 50)
    
    print("1. 标准安装 - 按步骤安装并询问")
    print("2. 快速安装 - 一次性询问所有选项后无人干预执行")
    print("3. 分项安装 - 除WSL2外每个项目可单独安装")
    print("4. 退出")
    print("=" * 50)
    
    while True:
        choice = input("请选择安装模式 (1-4): ").strip()
        if choice in ['1', '2', '3', '4']:
            return choice
        logger.error("无效选择，请重新输入")
        print("[-] 无效选择，请重新输入")

def collect_all_options():
    """
    收集快速安装模式所需的所有选项
    
    返回:
        dict: 包含所有安装选项的字典
    """
    options = {}
    
    print("\n[快速安装模式] 请一次性配置所有选项:")
    
    # WSL2相关选项
    options['use_wsl2'] = input("是否使用WSL2? (y/n) [默认y]: ").strip().lower() != 'n'
    
    # 容器工具选项
    print("选择容器工具:")
    print("1. Docker")
    print("2. Podman")
    container_choice = input("请选择 (1-2) [默认1]: ").strip()
    options['container_tool'] = 'docker' if container_choice != '2' else 'podman'
    
    # Portainer选项
    options['install_portainer'] = input("是否安装Portainer? (y/n) [默认n]: ").strip().lower() == 'y'
    if options['install_portainer']:
        print("选择Portainer版本:")
        print("1. CE (社区版)")
        print("2. EE (企业版)")
        print("3. Agent")
        portainer_choice = input("请选择 (1-3) [默认1]: ").strip()
        version_map = {'1': 'ce', '2': 'ee', '3': 'agent'}
        options['portainer_version'] = version_map.get(portainer_choice, 'ce')
    
    print(f"[+] 快速安装配置完成: WSL2={options['use_wsl2']}, 容器工具={options['container_tool']}, Portainer={options['install_portainer']}")
    return options

def display_component_menu():
    """
    显示分项安装菜单
    
    返回:
        dict: 用户选择的组件安装选项
    """
    options = {}
    
    try:
        print("\n[分项安装模式] 请选择要安装的组件:")
        print("注意: WSL2环境必须首先安装，其他组件可单独选择")
        print("-" * 50)
        
        # WSL2环境（必须）
        try:
            wsl2_input = input("1. WSL2环境 (必须) - 是否安装? (y/n) [默认y]: ").strip().lower()
            options['wsl2'] = wsl2_input != 'n' if wsl2_input else True
        except (EOFError, KeyboardInterrupt):
            options['wsl2'] = True
            print()  # 换行
        
        # Kali Linux（推荐）
        try:
            kali_input = input("2. Kali Linux - 是否安装? (y/n) [默认y]: ").strip().lower()
            options['kali'] = kali_input != 'n' if kali_input else True
        except (EOFError, KeyboardInterrupt):
            options['kali'] = True
            print()  # 换行
        
        # 容器工具
        print("3. 容器工具:")
        print("   1. Docker")
        print("   2. Podman")
        print("   3. 跳过")
        try:
            container_choice = input("   请选择 (1-3) [默认1]: ").strip()
            if container_choice == '':
                container_choice = '1'
        except (EOFError, KeyboardInterrupt):
            container_choice = '1'
            print()  # 换行
        
        if container_choice == '1':
            options['container_tool'] = 'docker'
        elif container_choice == '2':
            options['container_tool'] = 'podman'
        else:
            options['container_tool'] = None
        
        # binwalk容器
        try:
            binwalk_input = input("4. binwalk容器 - 是否安装? (y/n) [默认y]: ").strip().lower()
            options['binwalk'] = binwalk_input != 'n' if binwalk_input else True
        except (EOFError, KeyboardInterrupt):
            options['binwalk'] = True
            print()  # 换行
        
        # Portainer
        try:
            portainer_input = input("5. Portainer - 是否安装? (y/n) [默认n]: ").strip().lower()
            options['portainer'] = portainer_input == 'y' if portainer_input else False
        except (EOFError, KeyboardInterrupt):
            options['portainer'] = False
            print()  # 换行
            
        if options['portainer']:
            print("   选择Portainer版本:")
            print("   1. CE (社区版)")
            print("   2. EE (企业版)")
            print("   3. Agent")
            try:
                portainer_choice = input("   请选择 (1-3) [默认1]: ").strip()
                if portainer_choice == '':
                    portainer_choice = '1'
            except (EOFError, KeyboardInterrupt):
                portainer_choice = '1'
                print()  # 换行
            version_map = {'1': 'ce', '2': 'ee', '3': 'agent'}
            options['portainer_version'] = version_map.get(portainer_choice, 'ce')
        else:
            options['portainer_version'] = 'ce'  # 默认值
        
        return options
        
    except Exception as e:
        print(f"[-] 显示分项安装菜单时出错: {str(e)}")
        # 返回默认选项
        return {
            'wsl2': True,
            'kali': True,
            'container_tool': 'docker',
            'binwalk': True,
            'portainer': False,
            'portainer_version': 'ce'
        }

def standard_installation(args):
    """
    标准安装模式 - 按步骤安装并询问
    
    参数:
        args: 命令行参数
        
    返回:
        int: 退出代码
    """
    print("\n[+] 开始标准安装模式...")
    
    # 检查Windows版本
    supports_wsl2, os_info = check_windows_version()
    print(f"[+] 系统信息: {os_info}")
    
    # 检测WSL2是否已存在
    wsl2_exists = detect_wsl2()
    
    # 处理WSL2安装
    wsl_action = ask_component_install("WSL2环境", wsl2_exists)
    
    if wsl_action == "manual":
        print("[+] 请手动处理WSL2环境，完成后按任意键继续...")
        input()
    elif wsl_action != "skip":
        # 如果不是跳过，则执行WSL安装/配置
        # 如果强制使用WSL1或者系统不支持WSL2，则使用WSL1
        use_wsl2 = supports_wsl2 and not args.wsl1
        print(f"[+] 将使用WSL{2 if use_wsl2 else 1}")
        
        # 启用WSL功能
        if not enable_wsl_features():
            print("[-] 启用WSL功能失败，安装无法继续")
            return 1
        
        # 设置WSL版本
        if use_wsl2:
            set_wsl_default_version(2)
        else:
            set_wsl_default_version(1)
    else:
        print("[+] 跳过WSL2环境安装")
    
    # 安装Kali Linux
    if not install_kali_linux():
        print("[-] 安装Kali Linux失败，安装无法继续")
        return 1
    
    print("[+] 初始化Kali Linux中...")
    print("[!] 请在弹出的Kali Linux窗口中设置用户名和密码")
    print("[!] 设置完成后关闭Kali Linux窗口继续安装")
    
    # 启动Kali Linux进行初始化
    run_powershell_command("wsl -d kali-linux", wait=False)
    
    # 等待用户完成Kali初始化
    print("[+] 等待Kali Linux初始化完成...")
    input("[+] 完成Kali Linux初始化后按任意键继续...")
    
    # 询问用户选择容器工具
    container_tool = ask_container_tool()
    
    # 配置Kali Linux，安装选择的容器工具
    if not configure_kali_linux(container_tool):
        print(f"[-] 配置Kali Linux失败，但将继续安装其他组件")
    
    # 拉取binwalk容器镜像
    pull_binwalk_container_image(container_tool, global_network_info)
    
    # 创建binwalk容器卷
    create_binwalk_volume(container_tool)
    
    # 询问是否安装Portainer
    if ask_portainer_install():
        # 询问Portainer版本
        portainer_version = ask_portainer_version()
        # 安装Portainer
        install_portainer(portainer_version, container_tool, global_network_info)
    
    return 0

def quick_installation(args, options):
    """
    快速安装模式 - 一次性询问所有选项后无人干预执行
    
    参数:
        args: 命令行参数
        options: 快速安装选项
        
    返回:
        int: 退出代码
    """
    print("\n[+] 开始快速安装模式...")
    print("[+] 将按照预设选项自动执行，无需人工干预")
    
    # 检查Windows版本
    supports_wsl2, os_info = check_windows_version()
    print(f"[+] 系统信息: {os_info}")
    
    # 处理WSL2安装
    if options['use_wsl2'] and supports_wsl2 and not args.wsl1:
        print("[+] 自动安装WSL2环境...")
        if not enable_wsl_features():
            print("[-] 启用WSL功能失败，安装无法继续")
            return 1
        set_wsl_default_version(2)
    else:
        print("[+] 自动安装WSL1环境...")
        if not enable_wsl_features():
            print("[-] 启用WSL功能失败，安装无法继续")
            return 1
        set_wsl_default_version(1)
    
    # 安装Kali Linux
    print("[+] 自动安装Kali Linux...")
    if not install_kali_linux():
        print("[-] 安装Kali Linux失败，安装无法继续")
        return 1
    
    print("[+] Kali Linux初始化中...")
    print("[!] 请在弹出的Kali Linux窗口中设置用户名和密码")
    print("[!] 设置完成后关闭Kali Linux窗口继续安装")
    
    # 启动Kali Linux进行初始化
    run_powershell_command("wsl -d kali-linux", wait=False)
    
    # 等待用户完成Kali初始化
    print("[+] 等待Kali Linux初始化完成...")
    input("[+] 完成Kali Linux初始化后按任意键继续...")
    
    # 配置Kali Linux和容器工具
    print(f"[+] 自动配置Kali Linux和{options['container_tool']}...")
    if not configure_kali_linux(options['container_tool'], global_network_info):
        print(f"[-] 配置Kali Linux失败，但将继续安装其他组件")
    
    # 拉取binwalk容器镜像
    print("[+] 自动拉取binwalk容器镜像...")
    pull_binwalk_container_image(options['container_tool'], global_network_info)
    
    # 创建binwalk容器卷
    print("[+] 自动创建binwalk容器卷...")
    create_binwalk_volume(options['container_tool'])
    
    # 安装Portainer
    if options['install_portainer']:
        print(f"[+] 自动安装Portainer {options['portainer_version'].upper()}...")
        install_portainer(options['portainer_version'], options['container_tool'], global_network_info)
    
    return 0

def component_installation(args, options):
    """
    分项安装模式 - 除WSL2外每个项目可单独安装
    
    参数:
        args: 命令行参数
        options: 分项安装选项
        
    返回:
        int: 退出代码
    """
    try:
        print("\n[+] 开始分项安装模式...")
        
        # 验证选项参数
        if not isinstance(options, dict):
            print("[-] 无效的选项参数")
            return 1
        
        # 检查Windows版本
        try:
            supports_wsl2, os_info = check_windows_version()
            print(f"[+] 系统信息: {os_info}")
        except Exception as e:
            print(f"[-] 检查Windows版本失败: {str(e)}")
            return 1
        
        # WSL2环境安装（必须）
        if options.get('wsl2', True):
            print("[+] 安装WSL2环境...")
            try:
                if not enable_wsl_features():
                    print("[-] 启用WSL功能失败")
                    return 1
                
                # 根据用户选择设置WSL版本
                use_wsl2 = supports_wsl2 and not args.wsl1
                if use_wsl2:
                    set_wsl_default_version(2)
                else:
                    set_wsl_default_version(1)
            except Exception as e:
                print(f"[-] 安装WSL2环境失败: {str(e)}")
                return 1
        else:
            print("[!] 跳过了必需的WSL2环境安装，无法继续")
            return 1
        
        # Kali Linux安装
        if options.get('kali', True):
            logger.info("安装Kali Linux...")
            print("[+] 安装Kali Linux...")
            try:
                if not install_kali_linux():
                    print("[-] 安装Kali Linux失败")
                    return 1
                
                print("[+] Kali Linux初始化中...")
                
                # 自动配置Kali Linux用户，跳过手动输入
                username, password = setup_kali_linux_user()
                if username and password:
                    print(f"[+] Kali Linux用户自动配置完成")
                    print(f"[+] 用户名: {username}")
                    print(f"[+] 密码: {password}")
                else:
                    print("[-] Kali Linux用户自动配置失败")
                    print("[-] 无法继续安装流程")
                    return 1
                
            except Exception as e:
                print(f"[-] 安装Kali Linux过程失败: {str(e)}")
                return 1
        else:
            print("[+] 跳过Kali Linux安装")
        
        # 容器工具安装
        container_tool = options.get('container_tool')
        if container_tool:
            print(f"[+] 安装{container_tool}...")
            try:
                if not configure_kali_linux(container_tool, global_network_info):
                    print(f"[-] 配置{container_tool}失败")
            except Exception as e:
                print(f"[-] 安装{container_tool}失败: {str(e)}")
        else:
            print("[+] 跳过容器工具安装")
        
        # binwalk容器安装
        if options.get('binwalk', True):
            print("[+] 安装binwalk容器...")
            try:
                container_tool = options.get('container_tool', 'docker')
                pull_binwalk_container_image(container_tool, global_network_info)
                create_binwalk_volume(container_tool)
            except Exception as e:
                print(f"[-] 安装binwalk容器失败: {str(e)}")
        else:
            print("[+] 跳过binwalk容器安装")
        
        # Portainer安装
        if options.get('portainer', False):
            try:
                portainer_version = options.get('portainer_version', 'ce')
                print(f"[+] 安装Portainer {portainer_version.upper()}...")
                container_tool = options.get('container_tool', 'docker')
                install_portainer(portainer_version, container_tool, global_network_info)
            except Exception as e:
                print(f"[-] 安装Portainer失败: {str(e)}")
        else:
            print("[+] 跳过Portainer安装")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n[!] 用户取消安装")
        return 1
    except Exception as e:
        print(f"[-] 分项安装模式执行失败: {str(e)}")
        return 1

def main():
    """
    主函数，协调整个安装流程
    
    返回:
        int: 退出代码
    """
    # 全局网络环境信息
    global_network_info = {
        'ip': '未知',
        'country': 'UNKNOWN',
        'use_mirror': False,
        'gateway_url': 'https://gateway.cf.shdrr.org'
    }
    
    try:
        logger.info("===== WSL2/WSL环境安装脚本开始执行 =====")
        print("=" * 60)
        print("        WSL2/WSL环境安装脚本")
        print("        用于配置Kali Linux和容器环境")
        print("=" * 60)
        print(f"[+] 日志文件将保存到: {log_file}")
        
        # 检查是否以管理员权限运行
        if not is_admin():
            logger.error("请以管理员权限运行此脚本！")
            print("[-] 请以管理员权限运行此脚本！")
            # 尝试以管理员权限重新运行
            logger.info("尝试以管理员权限重新运行...")
            print("[+] 尝试以管理员权限重新运行...")
            try:
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            except Exception as e:
                logger.error(f"无法以管理员权限重新运行: {str(e)}")
                print(f"[-] 无法以管理员权限重新运行: {str(e)}")
            sys.exit(1)
        
        # 解析命令行参数
        parser = argparse.ArgumentParser(description='WSL2环境安装脚本')
        parser.add_argument('--wsl1', action='store_true', help='强制使用WSL1模式')
        args = parser.parse_args()
        
        # 检测网络环境和IP地区
        print("\n[+] 正在检测网络环境...")
        if IP_DETECTION_AVAILABLE:
            try:
                network_info = check_network_environment()
                global_network_info.update(network_info)
                
                # 显示网络检测结果
                print(f"[+] 网络检测完成:")
                print(f"    IP地址: {global_network_info['ip']}")
                print(f"    地区: {global_network_info['country']}")
                print(f"    使用镜像源: {'是' if global_network_info['use_mirror'] else '否'}")
                
                if global_network_info['use_mirror']:
                    print(f"    镜像网关: {global_network_info['gateway_url']}")
                
            except Exception as e:
                logger.error(f"网络环境检测失败: {str(e)}")
                print(f"[-] 网络环境检测失败，将使用默认配置: {str(e)}")
        else:
            print("[!] IP检测模块不可用，将使用默认网络配置")
        
        # 显示安装模式菜单（现在会显示IP地区信息）
        install_mode = display_install_menu(global_network_info)
        
        if install_mode == '4':
            print("[+] 用户选择退出安装")
            return 0
        
        # 根据选择的模式执行相应的安装流程
        if install_mode == '1':
            # 标准安装模式
            logger.info("开始标准安装模式")
            result = standard_installation(args)
        elif install_mode == '2':
            # 快速安装模式
            logger.info("开始快速安装模式")
            options = collect_all_options()
            result = quick_installation(args, options)
        elif install_mode == '3':
            # 分项安装模式
            logger.info("开始分项安装模式")
            options = display_component_menu()
            result = component_installation(args, options)
        else:
            logger.error("无效的安装模式")
            print("[-] 无效的安装模式")
            return 1
        
        # 安装完成
        if result == 0:
            logger.info("安装流程完成")
            setup_completion()
        else:
            logger.error(f"安装流程失败，返回码: {result}")
        
        return result
    except KeyboardInterrupt:
        logger.warning("安装过程被用户中断")
        print("\n[-] 安装过程被用户中断")
        return 1
    except Exception as e:
        import traceback
        logger.error(f"发生未预期的错误: {str(e)}")
        logger.error(f"详细错误信息:\n{traceback.format_exc()}")
        print(f"\n[-] 发生未预期的错误: {str(e)}")
        print("\n详细错误信息:")
        traceback.print_exc()
        print(f"\n[+] 详细日志已保存到: {log_file}")
        # 自动继续，不等待用户输入
        print("[+] 程序将自动退出...")
        time.sleep(3)  # 给用户3秒时间查看错误信息
        return 1

if __name__ == "__main__":
    try:
        result = main()
        if result == 0:
            logger.info("===== WSL2/WSL环境安装脚本执行成功 =====")
        else:
            logger.error(f"===== WSL2/WSL环境安装脚本执行失败，返回码: {result} =====")
        sys.exit(result)
    except SystemExit:
        # 正常退出，不记录日志
        raise
    except Exception as e:
        logger.error(f"脚本执行失败: {str(e)}")
        logger.error("===== WSL2/WSL环境安装脚本执行异常结束 =====")
        sys.exit(1)