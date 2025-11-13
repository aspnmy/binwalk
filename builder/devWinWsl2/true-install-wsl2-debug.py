#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WSL2/WSL环境安装脚本（调试版本）

本脚本是原始安装脚本的调试版本，添加了更详细的错误处理和日志输出，
用于诊断原始脚本闪退的问题。

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
import traceback
import logging
from datetime import datetime

# 配置日志记录
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"wsl_install_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# 配置logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def log_exception(e, context="未知位置"):
    """
    记录异常信息
    
    参数:
        e: Exception, 异常对象
        context: str, 异常发生的上下文
    """
    logger.error(f"在{context}发生异常: {str(e)}")
    logger.debug(f"异常详细信息:\n{traceback.format_exc()}")

# 确保以管理员权限运行
def is_admin():
    """
    检查当前脚本是否以管理员权限运行
    
    返回:
        bool: True表示以管理员权限运行，False表示不是
    """
    try:
        logger.debug("检查管理员权限...")
        result = ctypes.windll.shell32.IsUserAnAdmin()
        logger.debug(f"管理员权限检查结果: {result}")
        return bool(result)
    except Exception as e:
        log_exception(e, "检查管理员权限时")
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
            # 以管理员权限重新运行PowerShell
            cmd = f'powershell -Command "Start-Process powershell -ArgumentList \"-NoExit -Command {command}\" -Verb RunAs"'
        else:
            cmd = f'powershell -Command "{command}"'
        
        logger.info(f"执行命令: {cmd}")
        
        if wait:
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()
            output = stdout + stderr
            logger.debug(f"命令返回码: {process.returncode}")
            logger.debug(f"命令输出: {output}")
            return process.returncode, output
        else:
            subprocess.Popen(cmd, shell=True)
            logger.debug("命令已启动，不等待完成")
            return None, None
    except Exception as e:
        log_exception(e, f"执行PowerShell命令 '{command}' 时")
        return -1, str(e)

def check_windows_version():
    """
    检查Windows版本，确保支持WSL
    
    返回:
        tuple: (是否支持WSL2, 系统信息)
    """
    try:
        logger.info("检查Windows版本...")
        # 获取Windows版本信息
        win_version = platform.win32_ver()
        logger.debug(f"原始Windows版本信息: {win_version}")
        
        # 安全地解析构建号
        build_number = 0
        try:
            version_str = win_version[2]
            logger.debug(f"版本字符串: {version_str}")
            parts = version_str.split('.')
            logger.debug(f"版本部分: {parts}")
            if len(parts) > 2:
                build_number = int(parts[2])
                logger.debug(f"解析出的构建号: {build_number}")
            else:
                logger.warning(f"无法从版本字符串 '{version_str}' 解析构建号")
        except Exception as e:
            log_exception(e, "解析Windows构建号时")
            build_number = 0
        
        logger.info(f"Windows版本: {win_version[0]} {win_version[1]} 构建 {build_number}")
        
        # Windows 10 1903以上或Windows 11支持WSL2
        supports_wsl2 = False
        try:
            if win_version[0] == '10':
                supports_wsl2 = build_number >= 18362
            elif win_version[0] == '11':
                supports_wsl2 = True
            logger.info(f"是否支持WSL2: {supports_wsl2}")
        except Exception as e:
            log_exception(e, "判断WSL2支持时")
            supports_wsl2 = False
        
        return supports_wsl2, f"Windows {win_version[0]} {win_version[1]} Build {build_number}"
    except Exception as e:
        log_exception(e, "检查Windows版本时")
        return False, f"未知系统: {str(e)}"

def enable_wsl_features():
    """
    启用WSL和虚拟机平台功能
    
    返回:
        bool: True表示启用成功，False表示失败
    """
    try:
        logger.info("启用WSL和虚拟机平台功能...")
        
        # 启用适用于Linux的Windows子系统
        logger.info("启用WSL功能...")
        code, output = run_powershell_command("dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart", admin=True)
        if code != 0:
            logger.error(f"启用WSL功能失败: {output}")
            return False
        logger.info("WSL功能启用成功")
        
        # 启用虚拟机平台（WSL2需要）
        logger.info("启用虚拟机平台功能...")
        code, output = run_powershell_command("dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart", admin=True)
        if code != 0:
            logger.warning(f"启用虚拟机平台功能失败: {output}")
            logger.warning("继续尝试，但WSL可能只能以WSL1模式运行")
        else:
            logger.info("虚拟机平台功能启用成功")
        
        return True
    except Exception as e:
        log_exception(e, "启用WSL功能时")
        return False

def set_wsl_default_version(version=2):
    """
    设置WSL默认版本
    
    参数:
        version: int, WSL版本(1或2)
    
    返回:
        bool: True表示设置成功，False表示失败
    """
    try:
        logger.info(f"设置WSL默认版本为{version}...")
        
        code, output = run_powershell_command(f"wsl --set-default-version {version}")
        if code != 0:
            logger.warning(f"设置WSL默认版本失败: {output}")
            logger.warning(f"将继续以WSL{1 if version == 2 else 2}模式运行")
            return False
        
        logger.info(f"WSL默认版本设置为{version}成功")
        return True
    except Exception as e:
        log_exception(e, f"设置WSL默认版本为{version}时")
        return False

def install_kali_linux():
    """
    安装Kali Linux WSL发行版
    
    返回:
        bool: True表示安装成功，False表示失败
    """
    try:
        logger.info("检查Kali Linux是否已安装...")
        code, output = run_powershell_command("wsl -l -v")
        
        if "kali" in output.lower():
            logger.info("Kali Linux已安装")
            return True
        
        logger.info("安装Kali Linux...")
        # 从Microsoft Store安装Kali Linux
        code, output = run_powershell_command("wsl --install -d Kali-Linux")
        if code != 0:
            logger.error(f"从Microsoft Store安装Kali Linux失败: {output}")
            logger.warning("尝试通过手动下载方式安装...")
            
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
                logger.error("安装Kali Linux失败，请确保已正确安装")
                return False
        
        logger.info("Kali Linux安装成功")
        return True
    except Exception as e:
        log_exception(e, "安装Kali Linux时")
        return False

def configure_kali_linux():
    """
    配置Kali Linux，安装Docker
    
    返回:
        bool: True表示配置成功，False表示失败
    """
    try:
        logger.info("配置Kali Linux并安装Docker...")
        
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
        temp_script_path = "kali_setup.sh"
        logger.debug(f"保存临时脚本到: {temp_script_path}")
        with open(temp_script_path, "w", encoding="utf-8") as f:
            f.write(docker_install_script)
        
        # 在Kali Linux中执行脚本
        logger.info("在Kali Linux中执行Docker安装脚本...")
        code, output = run_powershell_command(f"wsl -d kali-linux -e bash -c 'cat > setup.sh && chmod +x setup.sh && ./setup.sh' < {temp_script_path}")
        
        # 清理临时文件
        try:
            if os.path.exists(temp_script_path):
                os.remove(temp_script_path)
                logger.debug(f"已删除临时脚本: {temp_script_path}")
        except Exception as e:
            log_exception(e, f"删除临时脚本 {temp_script_path} 时")
        
        if code != 0:
            logger.error(f"配置Kali Linux失败: {output}")
            return False
        
        logger.info("Kali Linux配置和Docker安装成功")
        return True
    except Exception as e:
        log_exception(e, "配置Kali Linux时")
        # 尝试清理临时文件
        try:
            if os.path.exists("kali_setup.sh"):
                os.remove("kali_setup.sh")
        except:
            pass
        return False

def pull_binwalk_docker_image():
    """
    拉取binwalk Docker镜像
    
    返回:
        bool: True表示拉取成功，False表示失败
    """
    try:
        logger.info("拉取binwalk Docker镜像...")
        
        # 在Kali Linux的Docker中拉取binwalk镜像
        code, output = run_powershell_command("wsl -d kali-linux -e docker pull refirmlabs/binwalk:latest")
        if code != 0:
            logger.error(f"拉取binwalk Docker镜像失败: {output}")
            logger.warning("可以稍后在GUI中重试")
            return False
        
        logger.info("binwalk Docker镜像拉取成功")
        return True
    except Exception as e:
        log_exception(e, "拉取binwalk Docker镜像时")
        return False

def create_binwalk_volume():
    """
    创建binwalk Docker卷
    
    返回:
        bool: True表示创建成功，False表示失败
    """
    try:
        logger.info("创建binwalk Docker卷...")
        
        # 在Kali Linux的Docker中创建卷
        code, output = run_powershell_command("wsl -d kali-linux -e docker volume create binwalkv3")
        if code != 0:
            logger.error(f"创建binwalk Docker卷失败: {output}")
            logger.warning("可以稍后在GUI中重试")
            return False
        
        logger.info("binwalk Docker卷创建成功")
        return True
    except Exception as e:
        log_exception(e, "创建binwalk Docker卷时")
        return False

def setup_completion():
    """
    设置完成后的操作
    
    返回:
        None
    """
    try:
        logger.info("安装和配置完成")
        print("\n[+] 安装和配置完成！")
        print("[+] 您现在可以运行binwalk_GUi.py来使用图形界面管理WSL Docker环境")
        print("[+] 请注意：首次运行GUI时可能需要初始化WSL环境")
        print(f"[+] 调试日志已保存到: {log_file}")
        input("\n按任意键退出...")
    except Exception as e:
        log_exception(e, "完成设置时")

def main():
    """
    主函数，协调整个安装流程
    
    返回:
        int: 退出代码
    """
    try:
        logger.info("===== WSL2/WSL环境安装脚本开始执行 =====")
        print("=" * 60)
        print("        WSL2/WSL环境安装脚本 (调试版本)")
        print("        用于配置Kali Linux和Docker环境")
        print("=" * 60)
        print(f"调试日志将保存到: {log_file}")
        
        # 检查是否以管理员权限运行
        logger.info("检查管理员权限...")
        if not is_admin():
            logger.error("请以管理员权限运行此脚本！")
            print("[-] 请以管理员权限运行此脚本！")
            # 尝试以管理员权限重新运行
            logger.info("尝试以管理员权限重新运行...")
            print("[+] 尝试以管理员权限重新运行...")
            try:
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
                logger.debug("已尝试以管理员权限重新启动")
            except Exception as e:
                log_exception(e, "尝试以管理员权限重新运行时")
                print(f"[-] 无法以管理员权限重新运行: {str(e)}")
            sys.exit(1)
        logger.info("已确认管理员权限")
        
        # 解析命令行参数
        logger.info("解析命令行参数...")
        parser = argparse.ArgumentParser(description='WSL2环境安装脚本')
        parser.add_argument('--wsl1', action='store_true', help='强制使用WSL1模式')
        args = parser.parse_args()
        logger.debug(f"命令行参数: {args}")
        
        # 检查Windows版本
        logger.info("检查Windows版本兼容性...")
        supports_wsl2, os_info = check_windows_version()
        logger.info(f"系统信息: {os_info}")
        print(f"[+] 系统信息: {os_info}")
        
        # 如果强制使用WSL1或者系统不支持WSL2，则使用WSL1
        use_wsl2 = supports_wsl2 and not args.wsl1
        logger.info(f"将使用WSL{2 if use_wsl2 else 1}")
        print(f"[+] 将使用WSL{2 if use_wsl2 else 1}")
        
        # 启用WSL功能
        logger.info("开始启用WSL功能...")
        if not enable_wsl_features():
            logger.error("启用WSL功能失败，安装无法继续")
            print("[-] 启用WSL功能失败，安装无法继续")
            return 1
        
        # 设置WSL版本
        logger.info("设置WSL默认版本...")
        if use_wsl2:
            set_wsl_default_version(2)
        else:
            set_wsl_default_version(1)
        
        # 安装Kali Linux
        logger.info("安装Kali Linux...")
        if not install_kali_linux():
            logger.error("安装Kali Linux失败，安装无法继续")
            print("[-] 安装Kali Linux失败，安装无法继续")
            return 1
        
        logger.info("初始化Kali Linux...")
        print("[+] 初始化Kali Linux中...")
        print("[!] 请在弹出的Kali Linux窗口中设置用户名和密码")
        print("[!] 设置完成后关闭Kali Linux窗口继续安装")
        
        # 启动Kali Linux进行初始化
        logger.info("启动Kali Linux进行初始化...")
        run_powershell_command("wsl -d kali-linux", wait=False)
        
        # 等待用户完成Kali初始化
        logger.info("等待用户完成Kali Linux初始化...")
        print("[+] 等待Kali Linux初始化完成...")
        input("[+] 完成Kali Linux初始化后按任意键继续...")
        
        # 配置Kali Linux，安装Docker
        logger.info("配置Kali Linux，安装Docker...")
        if not configure_kali_linux():
            logger.error("配置Kali Linux失败，但将继续安装其他组件")
            print("[-] 配置Kali Linux失败，但将继续安装其他组件")
        
        # 拉取binwalk Docker镜像
        logger.info("拉取binwalk Docker镜像...")
        pull_binwalk_docker_image()
        
        # 创建binwalk Docker卷
        logger.info("创建binwalk Docker卷...")
        create_binwalk_volume()
        
        # 安装完成
        logger.info("安装流程完成")
        setup_completion()
        
        return 0
    except KeyboardInterrupt:
        logger.info("用户中断安装过程")
        print("\n[-] 安装过程被用户中断")
        return 1
    except Exception as e:
        log_exception(e, "主函数执行时")
        print(f"\n[-] 发生未预期的错误: {str(e)}")
        print(f"[-] 详细错误信息请查看日志文件: {log_file}")
        input("\n按任意键退出...")
        return 1
    finally:
        logger.info("===== WSL2/WSL环境安装脚本执行结束 =====")

if __name__ == "__main__":
    sys.exit(main())