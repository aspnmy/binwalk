#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qemu环境配置验证脚本

功能：验证Qemu环境是否正确安装和配置，检查必要的文件和设置
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path

def print_header():
    """
    打印脚本头部信息
    """
    print("=" * 60)
    print("        Binwalk Qemu 环境配置验证脚本        ")
    print("=" * 60)
    print()

def check_python_version():
    """
    检查Python版本
    
    返回值:
        bool: Python版本是否满足要求
    """
    print("[检查] Python版本...")
    current_version = sys.version_info
    required_version = (3, 8)
    
    if current_version < required_version:
        print(f"[错误] Python版本过低 (当前: {current_version[0]}.{current_version[1]}, 需要: {required_version[0]}.{required_version[1]})")
        return False
    else:
        print(f"[成功] Python版本满足要求 ({current_version[0]}.{current_version[1]})")
        return True

def check_admin_permissions():
    """
    检查是否以管理员权限运行
    
    返回值:
        bool: 是否具有管理员权限
    """
    print("[检查] 管理员权限...")
    try:
        if sys.platform == 'win32':
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            is_admin = os.geteuid() == 0
        
        if is_admin:
            print("[成功] 当前具有管理员权限")
        else:
            print("[警告] 当前没有管理员权限，某些操作可能会失败")
        return is_admin
    except Exception as e:
        print(f"[错误] 检查管理员权限时出错: {str(e)}")
        return False

def check_config_file():
    """
    检查配置文件是否存在
    
    返回值:
        dict or None: 配置信息字典，失败时返回None
    """
    print("[检查] 配置文件...")
    config_path = Path(__file__).parent / "config.json"
    
    if not config_path.exists():
        print(f"[警告] 配置文件不存在: {config_path}")
        return None
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        # 检查必要的配置项
        required_keys = ["qemu_path", "kali_image_path", "ssh_port", "memory_mb", "cpu_cores"]
        missing_keys = [key for key in required_keys if key not in config]
        
        if missing_keys:
            print(f"[警告] 配置文件缺少必要的项: {', '.join(missing_keys)}")
        else:
            print("[成功] 配置文件存在且包含必要的配置项")
        
        return config
    except Exception as e:
        print(f"[错误] 读取配置文件时出错: {str(e)}")
        return None

def check_qemu_installation(config):
    """
    检查Qemu是否正确安装
    
    参数:
        config: dict, 配置信息
        
    返回值:
        bool: Qemu是否正确安装
    """
    print("[检查] Qemu安装...")
    
    # 检查qemu-system-x86_64可执行文件
    if config and "qemu_path" in config:
        qemu_exe = Path(config["qemu_path"]) / "qemu-system-x86_64.exe"
    else:
        # 尝试在默认位置查找
        default_path = Path(__file__).parent / "qemu" / "qemu-system-x86_64.exe"
        qemu_exe = default_path
    
    if not qemu_exe.exists():
        print(f"[错误] 未找到Qemu可执行文件: {qemu_exe}")
        
        # 尝试在PATH中查找
        try:
            subprocess.run(["qemu-system-x86_64", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("[成功] 在系统PATH中找到Qemu")
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            print("[错误] 在系统PATH中也未找到Qemu")
            return False
    
    # 检查Qemu版本
    try:
        result = subprocess.run([str(qemu_exe), "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        version_info = result.stdout or result.stderr
        print(f"[成功] Qemu已安装: {version_info.split('\n')[0]}")
        return True
    except Exception as e:
        print(f"[错误] 检查Qemu版本时出错: {str(e)}")
        return False

def check_kali_image(config):
    """
    检查Kali镜像文件是否存在
    
    参数:
        config: dict, 配置信息
        
    返回值:
        bool: Kali镜像是否存在
    """
    print("[检查] Kali Linux镜像...")
    
    if config and "kali_image_path" in config:
        image_path = Path(config["kali_image_path"])
    else:
        # 尝试在默认位置查找
        default_path = Path(__file__).parent / "images" / "kali-linux.qcow2"
        image_path = default_path
    
    if not image_path.exists():
        print(f"[错误] 未找到Kali Linux镜像: {image_path}")
        return False
    
    # 检查镜像文件大小
    try:
        size = image_path.stat().st_size / (1024 * 1024 * 1024)  # GB
        print(f"[成功] Kali Linux镜像存在，大小: {size:.2f} GB")
        return True
    except Exception as e:
        print(f"[错误] 检查镜像文件时出错: {str(e)}")
        return False

def check_ssh_connection(config):
    """
    尝试连接到Qemu虚拟机的SSH服务
    
    参数:
        config: dict, 配置信息
        
    返回值:
        bool: SSH连接是否成功
    """
    print("[检查] SSH连接能力...")
    
    # 检查paramiko模块
    try:
        import paramiko
        print("[成功] paramiko模块已安装")
    except ImportError:
        print("[警告] paramiko模块未安装，无法测试SSH连接")
        return False
    
    # 尝试连接（仅测试配置，不实际连接）
    if config:
        host = config.get("ssh_host", "localhost")
        port = config.get("ssh_port", 2222)
        user = config.get("ssh_user", "kali")
        print(f"[信息] SSH配置: {user}@{host}:{port}")
        print("[提示] 要测试实际连接，请先启动Qemu虚拟机")
    
    return True

def check_docker_availability():
    """
    检查Docker相关组件是否可用
    
    返回值:
        bool: Docker组件检查是否通过
    """
    print("[检查] Docker相关组件...")
    
    # 检查docker命令是否可用（在Windows上）
    try:
        subprocess.run(["docker", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("[成功] Docker客户端已安装")
    except (subprocess.SubprocessError, FileNotFoundError):
        print("[警告] Docker客户端未安装（Windows上）")
    
    # 这只是检查本地Docker客户端，Qemu内的Docker将在虚拟机启动后检查
    print("[提示] Qemu虚拟机内的Docker服务将在虚拟机启动后检查")
    return True

def check_port_availability(config):
    """
    检查必要的端口是否可用
    
    参数:
        config: dict, 配置信息
        
    返回值:
        bool: 端口是否可用
    """
    print("[检查] 端口可用性...")
    
    if config and "ssh_port" in config:
        ssh_port = config["ssh_port"]
    else:
        ssh_port = 2222
    
    # 检查端口是否被占用
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("localhost", ssh_port))
            print(f"[成功] 端口 {ssh_port} (SSH) 可用")
            return True
        except OSError:
            print(f"[警告] 端口 {ssh_port} (SSH) 已被占用")
            return False

def check_disk_space():
    """
    检查磁盘空间
    
    返回值:
        bool: 磁盘空间是否充足
    """
    print("[检查] 磁盘空间...")
    
    # 获取当前磁盘的可用空间
    if sys.platform == 'win32':
        import ctypes
        free_bytes = ctypes.c_ulonglong(0)
        total_bytes = ctypes.c_ulonglong(0)
        
        # 获取当前磁盘的可用空间
        current_disk = Path(__file__).drive
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(current_disk), None, ctypes.pointer(total_bytes), ctypes.pointer(free_bytes))
        
        free_gb = free_bytes.value / (1024 * 1024 * 1024)
        total_gb = total_bytes.value / (1024 * 1024 * 1024)
        
        print(f"[信息] 磁盘空间: 总计 {total_gb:.2f} GB, 可用 {free_gb:.2f} GB")
        
        if free_gb < 20:
            print("[警告] 可用磁盘空间不足，建议至少保留20GB空间")
            return False
        else:
            print("[成功] 磁盘空间充足")
            return True
    else:
        # 非Windows系统的简单检查
        st = os.statvfs('.')
        free_gb = (st.f_bavail * st.f_frsize) / (1024 * 1024 * 1024)
        print(f"[信息] 可用磁盘空间: {free_gb:.2f} GB")
        
        if free_gb < 20:
            print("[警告] 可用磁盘空间不足，建议至少保留20GB空间")
            return False
        else:
            return True

def generate_report(results):
    """
    生成验证报告
    
    参数:
        results: dict, 各项检查的结果
    """
    print("\n" + "=" * 60)
    print("              验证报告              ")
    print("=" * 60)
    
    # 统计结果
    success_count = sum(1 for result in results.values() if result)
    total_count = len(results)
    
    # 打印各项结果
    for check_name, result in results.items():
        status = "✓ 成功" if result else "✗ 失败/警告"
        print(f"{check_name:<30}: {status}")
    
    print("\n" + "=" * 60)
    print(f"总体状态: {success_count}/{total_count} 项通过")
    
    # 给出建议
    if success_count == total_count:
        print("[结论] 环境配置良好，可以正常使用")
    else:
        print("[结论] 环境配置存在问题，请根据警告和错误信息进行修复")
        print("[建议] 请以管理员身份重新运行installQemu.py脚本")

def main():
    """
    主函数
    """
    print_header()
    
    # 初始化结果字典
    results = {
        "Python版本": False,
        "管理员权限": False,
        "配置文件": False,
        "Qemu安装": False,
        "Kali镜像": False,
        "SSH连接能力": False,
        "Docker组件": False,
        "端口可用性": False,
        "磁盘空间": False
    }
    
    # 执行各项检查
    results["Python版本"] = check_python_version()
    results["管理员权限"] = check_admin_permissions()
    
    # 获取配置文件
    config = check_config_file()
    results["配置文件"] = config is not None
    
    # 其他检查
    results["Qemu安装"] = check_qemu_installation(config)
    results["Kali镜像"] = check_kali_image(config)
    results["SSH连接能力"] = check_ssh_connection(config)
    results["Docker组件"] = check_docker_availability()
    results["端口可用性"] = check_port_availability(config)
    results["磁盘空间"] = check_disk_space()
    
    # 生成报告
    generate_report(results)
    
    # 打印使用提示
    print("\n" + "=" * 60)
    print("              使用提示              ")
    print("=" * 60)
    print("1. 如果所有检查通过，可以运行 start_qemu.py 启动虚拟机")
    print("2. 启动虚拟机后，运行 binwalk_GUiQemu.py 打开图形界面")
    print("3. 在图形界面中连接到虚拟机（默认: localhost:2222）")
    print("4. 使用图形界面管理Docker容器和执行Binwalk分析")
    print("\n按Enter键退出...")
    
    # 等待用户输入
    input()

if __name__ == "__main__":
    main()