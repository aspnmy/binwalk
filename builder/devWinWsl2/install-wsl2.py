#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WSL2/WSL环境安装脚本

本脚本用于在Windows系统上自动安装WSL2或WSL环境，
拉取Kali Linux镜像，并配置Docker环境以运行binwalk-docker。

参数：
    无

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
    if admin:
        # 以管理员权限重新运行PowerShell，正确格式化参数列表
        cmd = f'powershell -Command "Start-Process powershell -ArgumentList \'-NoExit -Command {command}\' -Verb RunAs"'
    else:
        cmd = f'powershell -Command "{command}"'
    
    print(f"[+] 执行命令: {cmd}")
    
    try:
        if wait:
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()
            return process.returncode, stdout + stderr
        else:
            subprocess.Popen(cmd, shell=True)
            return None, None
    except Exception as e:
        print(f"[-] 执行命令时出错: {str(e)}")
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
        
        print(f"[+] Windows版本: {version_str} {version_detail} 构建 {build_number}")
        
        # Windows 10 1903以上或Windows 11支持WSL2
        # 对于Windows 11，直接认为支持WSL2
        supports_wsl2 = False
        if version_str == '11':
            supports_wsl2 = True
        elif version_str == '10' and build_number >= 18362:
            supports_wsl2 = True
        
        return supports_wsl2, f"Windows {version_str} {version_detail} Build {build_number}"
    except Exception as e:
        print(f"[-] 检查Windows版本时出错: {e}")
        return False, f"未知系统: {str(e)}"

def enable_wsl_features():
    """
    启用WSL和虚拟机平台功能
    
    返回:
        bool: True表示启用成功，False表示失败
    """
    print("[+] 启用WSL和虚拟机平台功能...")
    
    # 启用适用于Linux的Windows子系统
    code, output = run_powershell_command("dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart", admin=True)
    if code != 0:
        print(f"[-] 启用WSL功能失败: {output}")
        return False
    
    # 启用虚拟机平台（WSL2需要）
    code, output = run_powershell_command("dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart", admin=True)
    if code != 0:
        print(f"[-] 启用虚拟机平台功能失败: {output}")
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
    print("[+] 检查Kali Linux是否已安装...")
    code, output = run_powershell_command("wsl -l -v")
    
    if "kali" in output.lower():
        print("[+] Kali Linux已安装")
        return True
    
    print("[+] 安装Kali Linux...")
    # 从Microsoft Store安装Kali Linux
    code, output = run_powershell_command("wsl --install -d Kali-Linux")
    if code != 0:
        print(f"[-] 从Microsoft Store安装Kali Linux失败: {output}")
        print("[!] 尝试通过手动下载方式安装...")
        
        # 提供手动安装指导
        print("\n请手动执行以下步骤:")
        print("1. 打开Microsoft Store")
        print("2. 搜索并安装'Kali Linux'")
        print("3. 安装完成后启动Kali Linux并完成初始设置")
        print("4. 完成后按任意键继续...")
        
        input()
        
        # 再次检查是否安装成功
        code, output = run_powershell_command("wsl -l -v")
        if "kali" not in output.lower():
            print("[-] 安装Kali Linux失败，请确保已正确安装")
            return False
    
    return True

def configure_kali_linux():
    """
    配置Kali Linux，安装Docker
    
    返回:
        bool: True表示配置成功，False表示失败
    """
    print("[+] 配置Kali Linux并安装Docker...")
    
    # 更新软件包并安装Docker
    docker_install_script = '''
    #!/bin/bash
    echo "更新Kali Linux软件包..."
    sudo apt update
    sudo apt upgrade -y
    
    echo "安装Docker依赖..."
    sudo apt install -y apt-transport-https ca-certificates curl gnupg2 software-properties-common
    
    echo "添加Docker GPG密钥..."
    curl -fsSL https://download.docker.com/linux/debian/gpg | sudo apt-key add -
    
    echo "添加Docker源..."
    echo "deb [arch=amd64] https://download.docker.com/linux/debian buster stable" | sudo tee /etc/apt/sources.list.d/docker.list
    
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
    
    return True

def pull_binwalk_docker_image():
    """
    拉取binwalk Docker镜像
    
    返回:
        bool: True表示拉取成功，False表示失败
    """
    print("[+] 拉取binwalk Docker镜像...")
    
    # 在Kali Linux的Docker中拉取binwalk镜像
    code, output = run_powershell_command("wsl -d kali-linux -e docker pull refirmlabs/binwalk:latest")
    if code != 0:
        print(f"[-] 拉取binwalk Docker镜像失败: {output}")
        print("[!] 可以稍后在GUI中重试")
        return False
    
    return True

def create_binwalk_volume():
    """
    创建binwalk Docker卷
    
    返回:
        bool: True表示创建成功，False表示失败
    """
    print("[+] 创建binwalk Docker卷...")
    
    # 在Kali Linux的Docker中创建卷
    code, output = run_powershell_command("wsl -d kali-linux -e docker volume create binwalkv3")
    if code != 0:
        print(f"[-] 创建binwalk Docker卷失败: {output}")
        print("[!] 可以稍后在GUI中重试")
        return False
    
    return True

def setup_completion():
    """
    设置完成后的操作
    
    返回:
        None
    """
    print("\n[+] 安装和配置完成！")
    print("[+] 您现在可以运行binwalk_GUi.py来使用图形界面管理WSL Docker环境")
    print("[+] 请注意：首次运行GUI时可能需要初始化WSL环境")
    input("\n按任意键退出...")

def main():
    """
    主函数，协调整个安装流程
    
    返回:
        int: 退出代码
    """
    try:
        print("=" * 60)
        print("        WSL2/WSL环境安装脚本")
        print("        用于配置Kali Linux和Docker环境")
        print("=" * 60)
        
        # 检查是否以管理员权限运行
        if not is_admin():
            print("[-] 请以管理员权限运行此脚本！")
            # 尝试以管理员权限重新运行
            print("[+] 尝试以管理员权限重新运行...")
            try:
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            except Exception as e:
                print(f"[-] 无法以管理员权限重新运行: {str(e)}")
            sys.exit(1)
        
        # 解析命令行参数
        parser = argparse.ArgumentParser(description='WSL2环境安装脚本')
        parser.add_argument('--wsl1', action='store_true', help='强制使用WSL1模式')
        args = parser.parse_args()
        
        # 检查Windows版本
        supports_wsl2, os_info = check_windows_version()
        print(f"[+] 系统信息: {os_info}")
        
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
        
        # 配置Kali Linux，安装Docker
        if not configure_kali_linux():
            print("[-] 配置Kali Linux失败，但将继续安装其他组件")
        
        # 拉取binwalk Docker镜像
        pull_binwalk_docker_image()
        
        # 创建binwalk Docker卷
        create_binwalk_volume()
        
        # 安装完成
        setup_completion()
        
        return 0
    except KeyboardInterrupt:
        print("\n[-] 安装过程被用户中断")
        return 1
    except Exception as e:
        import traceback
        print(f"\n[-] 发生未预期的错误: {str(e)}")
        print("\n详细错误信息:")
        traceback.print_exc()
        input("\n按任意键退出...")
        return 1

if __name__ == "__main__":
    sys.exit(main())