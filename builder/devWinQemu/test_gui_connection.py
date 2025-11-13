#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
binwalk_GUiQemu.py 连接和文件传输功能测试脚本

功能：测试GUI的SSH连接和文件传输功能，模拟连接过程
"""

import os
import sys
import subprocess
import json
import time
import socket
from pathlib import Path
import tempfile

def print_header():
    """
    打印脚本头部信息
    """
    print("=" * 60)
    print("       GUI连接和文件传输功能测试脚本       ")
    print("=" * 60)
    print()

def get_gui_path():
    """
    获取binwalk_GUiQemu.py的路径
    
    返回值:
        Path: GUI脚本的路径对象
    """
    return Path(__file__).parent / "binwalk_GUiQemu.py"

def check_gui_file_exists():
    """
    检查GUI脚本是否存在
    
    返回值:
        bool: 文件是否存在
    """
    print("[测试] 检查binwalk_GUiQemu.py文件是否存在...")
    gui_path = get_gui_path()
    
    if not gui_path.exists():
        print(f"[错误] 未找到GUI脚本: {gui_path}")
        return False
    else:
        print(f"[成功] 找到GUI脚本: {gui_path}")
        return True

def check_config_exists():
    """
    检查配置文件是否存在
    
    返回值:
        dict or None: 配置信息，失败时返回None
    """
    print("[测试] 检查配置文件是否存在...")
    config_path = Path(__file__).parent / "config.json"
    
    if not config_path.exists():
        print(f"[错误] 未找到配置文件: {config_path}")
        return None
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        print(f"[成功] 找到配置文件并读取配置信息")
        return config
    except Exception as e:
        print(f"[错误] 读取配置文件时出错: {str(e)}")
        return None

def check_ssh_dependencies():
    """
    检查SSH相关依赖是否安装
    
    返回值:
        bool: 依赖是否满足
    """
    print("[测试] 检查SSH相关依赖...")
    
    dependencies = ["paramiko", "tkinter"]
    missing_deps = []
    
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"[成功] {dep}模块已安装")
        except ImportError:
            print(f"[警告] {dep}模块未安装")
            missing_deps.append(dep)
    
    if missing_deps:
        print(f"[警告] 缺少以下依赖: {', '.join(missing_deps)}")
        return False
    else:
        return True

def test_ssh_connection_simulator(config):
    """
    模拟SSH连接测试
    
    参数:
        config: dict, 配置信息
        
    返回值:
        dict: 连接测试结果
    """
    print("\n[测试] 模拟SSH连接...")
    
    if not config:
        print("[错误] 缺少配置信息，无法模拟SSH连接")
        return {"status": False, "error": "缺少配置"}
    
    # 获取连接参数
    host = config.get("ssh_host", "localhost")
    port = config.get("ssh_port", 2222)
    user = config.get("ssh_user", "kali")
    password = config.get("ssh_password", "kali")
    
    print(f"[信息] 连接参数: {user}@{host}:{port}")
    
    # 模拟连接过程
    print("[模拟] 正在建立SSH连接...")
    time.sleep(1)
    
    # 检查端口是否被占用
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            result = s.connect_ex((host, port))
            if result == 0:
                print(f"[信息] 端口 {port} 正在监听中")
            else:
                print(f"[信息] 端口 {port} 未被占用（虚拟机可能未启动）")
    except Exception as e:
        print(f"[警告] 检查端口时出错: {str(e)}")
    
    # 返回模拟结果
    return {
        "status": True,
        "message": "SSH连接模拟成功",
        "host": host,
        "port": port,
        "user": user
    }

def test_file_transfer_simulator():
    """
    模拟文件传输功能测试
    
    返回值:
        dict: 文件传输测试结果
    """
    print("\n[测试] 模拟文件传输功能...")
    
    # 创建临时文件用于测试
    try:
        # 创建源文件
        with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as src_file:
            src_file.write(b"BINWALK TEST FILE\x00\x01\x02\x03")
            src_path = src_file.name
        
        print(f"[模拟] 创建测试文件: {src_path}")
        
        # 模拟上传
        print(f"[模拟] 上传文件到远程目录: /tmp/")
        time.sleep(1)
        
        # 模拟下载
        print(f"[模拟] 从远程目录下载文件: /tmp/test.bin -> test_download.bin")
        time.sleep(1)
        
        # 清理
        if Path(src_path).exists():
            Path(src_path).unlink()
        
        return {
            "status": True,
            "message": "文件传输模拟成功",
            "upload": "/tmp/",
            "download": "./"
        }
    
    except Exception as e:
        print(f"[错误] 模拟文件传输时出错: {str(e)}")
        return {
            "status": False,
            "error": str(e)
        }

def test_docker_command_simulator():
    """
    模拟Docker命令执行测试
    
    返回值:
        dict: Docker命令测试结果
    """
    print("\n[测试] 模拟Docker命令执行...")
    
    # 模拟Docker命令
    docker_commands = [
        "docker --version",
        "docker ps -a",
        "docker images",
        "docker-compose version"
    ]
    
    results = []
    for cmd in docker_commands:
        print(f"[模拟] 执行命令: {cmd}")
        time.sleep(0.5)
        results.append({
            "command": cmd,
            "status": "success",
            "simulated": True
        })
    
    return {
        "status": True,
        "message": "Docker命令模拟成功",
        "commands": results
    }

def test_gui_imports():
    """
    测试GUI脚本中的关键导入
    
    返回值:
        bool: 关键导入是否存在
    """
    print("\n[测试] 检查GUI脚本中的关键导入...")
    
    # 检查是否包含关键类和函数
    try:
        gui_path = get_gui_path()
        check_code = f"""
import sys
import importlib.util

# 导入模块
spec = importlib.util.spec_from_file_location("binwalk_GUiQemu", "{gui_path}")
gui_module = importlib.util.module_from_spec(spec)
sys.modules["binwalk_GUiQemu"] = gui_module
spec.loader.exec_module(gui_module)

# 检查关键组件
found_components = []
missing_components = []

# 检查类
required_classes = ["BinwalkGUI", "SSHManager", "FileTransferManager", "DockerManager"]
for cls_name in required_classes:
    if hasattr(gui_module, cls_name):
        found_components.append(f"类: {cls_name}")
    else:
        missing_components.append(f"类: {cls_name}")

# 检查函数
required_functions = ["connect_to_ssh", "upload_file", "download_file", "run_docker_command"]
for func_name in required_functions:
    # 检查是否在模块中或在类中
    found = False
    for name, obj in gui_module.__dict__.items():
        if hasattr(obj, func_name):
            found = True
            found_components.append(f"函数: {func_name} (在{name}中)")
            break
    if not found and hasattr(gui_module, func_name):
        found_components.append(f"函数: {func_name}")
    elif not found:
        missing_components.append(f"函数: {func_name}")

# 打印结果
print(f"找到的组件 ({len(found_components)}):")
for component in found_components:
    print(f"  {component}")

if missing_components:
    print(f"\n未找到的组件 ({len(missing_components)}):")
    for component in missing_components:
        print(f"  {component}")

# 返回结果
sys.exit(0 if not missing_components else 1)
"""
        
        temp_script = Path(__file__).parent / "temp_gui_test.py"
        with open(temp_script, "w", encoding="utf-8") as f:
            f.write(check_code)
        
        result = subprocess.run([sys.executable, str(temp_script)], capture_output=True, text=True)
        
        if temp_script.exists():
            temp_script.unlink()
        
        print(result.stdout.strip())
        if result.stderr:
            print("\n警告:", result.stderr.strip())
        
        return result.returncode == 0
    
    except Exception as e:
        print(f"[错误] 测试GUI导入时出错: {str(e)}")
        return False

def create_test_config():
    """
    创建测试专用配置
    
    返回值:
        bool: 创建是否成功
    """
    print("\n[测试] 创建测试专用配置...")
    
    try:
        # 创建测试配置
        test_config = {
            "ssh_host": "localhost",
            "ssh_port": 2222,
            "ssh_user": "kali",
            "ssh_password": "kali",
            "remote_working_dir": "/analysis",
            "docker_compose_path": "docker-compose.yml",
            "local_temp_dir": str(Path(__file__).parent / "temp"),
            "log_level": "INFO"
        }
        
        # 保存测试配置
        test_config_path = Path(__file__).parent / "test_config.json"
        with open(test_config_path, "w", encoding="utf-8") as f:
            json.dump(test_config, f, indent=4, ensure_ascii=False)
        
        print(f"[成功] 创建测试配置文件: {test_config_path}")
        
        # 创建临时目录
        temp_dir = Path(test_config["local_temp_dir"])
        temp_dir.mkdir(exist_ok=True)
        print(f"[成功] 创建临时目录: {temp_dir}")
        
        return True
    except Exception as e:
        print(f"[错误] 创建测试配置时出错: {str(e)}")
        return False

def generate_connection_report(results):
    """
    生成连接和文件传输测试报告
    
    参数:
        results: dict, 测试结果
    """
    print("\n" + "=" * 60)
    print("          连接和文件传输测试报告          ")
    print("=" * 60)
    
    # 打印各项结果
    for test_name, result in results.items():
        if isinstance(result, bool):
            status = "✓ 通过" if result else "✗ 失败"
            print(f"{test_name:<30}: {status}")
        elif isinstance(result, dict) and "status" in result:
            status = "✓ 通过" if result["status"] else "✗ 失败"
            message = result.get("message", "")
            print(f"{test_name:<30}: {status}")
            if message:
                print(f"          {message}")
        else:
            print(f"{test_name:<30}: ✓ 完成")
    
    print("\n" + "=" * 60)
    print("          功能验证总结          ")
    print("=" * 60)
    print("1. GUI脚本检查: 验证了binwalk_GUiQemu.py的存在和基本结构")
    print("2. 配置文件: 检查并创建了必要的配置信息")
    print("3. 依赖检查: 验证了SSH和GUI相关依赖")
    print("4. SSH连接: 模拟了SSH连接过程")
    print("5. 文件传输: 模拟了上传和下载功能")
    print("6. Docker命令: 模拟了Docker管理命令执行")
    print("\n注意: 这是模拟测试，实际功能需要在Qemu虚拟机运行时测试")

def main():
    """
    主函数
    """
    print_header()
    
    # 初始化测试结果
    test_results = {
        "GUI脚本存在检查": False,
        "配置文件检查": False,
        "SSH依赖检查": False,
        "GUI导入测试": False,
        "SSH连接模拟": {},
        "文件传输模拟": {},
        "Docker命令模拟": {},
        "测试配置创建": False
    }
    
    # 执行各项测试
    test_results["GUI脚本存在检查"] = check_gui_file_exists()
    config = check_config_exists()
    test_results["配置文件检查"] = config is not None
    test_results["SSH依赖检查"] = check_ssh_dependencies()
    
    if test_results["GUI脚本存在检查"]:
        test_results["GUI导入测试"] = test_gui_imports()
    
    # 模拟功能测试
    test_results["SSH连接模拟"] = test_ssh_connection_simulator(config)
    test_results["文件传输模拟"] = test_file_transfer_simulator()
    test_results["Docker命令模拟"] = test_docker_command_simulator()
    
    # 创建测试配置
    test_results["测试配置创建"] = create_test_config()
    
    # 生成报告
    generate_connection_report(test_results)
    
    print("\n[完成] GUI连接和文件传输功能测试完成")
    print("提示: 要测试实际功能，请确保Qemu虚拟机已启动并运行")
    print("\n按Enter键退出...")
    
    # 等待用户输入
    input()

if __name__ == "__main__":
    main()