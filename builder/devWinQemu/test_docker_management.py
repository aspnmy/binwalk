#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Docker容器管理功能测试脚本

功能：测试Docker容器管理相关功能，模拟Docker命令执行和容器管理
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
import tempfile

def print_header():
    """
    打印脚本头部信息
    """
    print("=" * 60)
    print("        Docker容器管理功能测试脚本        ")
    print("=" * 60)
    print()

def check_docker_compose_config():
    """
    检查docker-compose配置文件
    
    返回值:
        dict: 配置检查结果
    """
    print("[测试] 检查docker-compose配置...")
    
    # 检查是否存在docker-compose.yml
    compose_path = Path(__file__).parent / "docker-compose.yml"
    
    if not compose_path.exists():
        print(f"[警告] docker-compose.yml文件不存在: {compose_path}")
        print("[测试] 创建模拟的docker-compose.yml文件...")
        
        # 创建模拟配置
        mock_compose = """
version: '3'
services:
  binwalkv3:
    image: refirmlabs/binwalk:latest
    stdin_open: true
    tty: true
    mem_limit: 4g
    cpus: 2
    volumes:
      - binwalkv3:/analysis
    ports:
      - "8080:8080"
      - "8081:8081"
volumes:
  binwalkv3:
"""
        
        try:
            with open(compose_path, "w", encoding="utf-8") as f:
                f.write(mock_compose)
            print(f"[成功] 创建模拟docker-compose.yml: {compose_path}")
        except Exception as e:
            print(f"[错误] 创建模拟文件时出错: {str(e)}")
            return {"status": False, "error": str(e)}
    else:
        print(f"[成功] 找到docker-compose.yml文件: {compose_path}")
    
    # 读取并验证配置
    try:
        with open(compose_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # 检查关键字段
        required_fields = ["binwalkv3", "image", "volumes", "mem_limit", "cpus"]
        missing_fields = [field for field in required_fields if field not in content]
        
        if missing_fields:
            print(f"[警告] 配置缺少以下字段: {', '.join(missing_fields)}")
            return {"status": True, "warnings": missing_fields}
        else:
            print("[成功] docker-compose配置包含所有必要字段")
            return {"status": True}
    
    except Exception as e:
        print(f"[错误] 读取配置时出错: {str(e)}")
        return {"status": False, "error": str(e)}

def test_docker_client_install():
    """
    测试Docker客户端安装情况
    
    返回值:
        dict: Docker客户端状态
    """
    print("[测试] 检查Docker客户端安装...")
    
    # 检查docker命令
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"[成功] Docker客户端已安装: {version}")
            docker_installed = True
        else:
            print("[警告] Docker客户端未安装或不可用")
            docker_installed = False
    except (subprocess.SubprocessError, FileNotFoundError):
        print("[警告] Docker客户端未安装或不可用")
        docker_installed = False
    
    # 检查docker-compose命令
    try:
        result = subprocess.run(["docker-compose", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"[成功] docker-compose已安装: {version}")
            compose_installed = True
        else:
            print("[警告] docker-compose未安装或不可用")
            compose_installed = False
    except (subprocess.SubprocessError, FileNotFoundError):
        print("[警告] docker-compose未安装或不可用")
        compose_installed = False
    
    return {
        "docker_installed": docker_installed,
        "compose_installed": compose_installed
    }

def simulate_docker_commands():
    """
    模拟Docker命令执行
    
    返回值:
        list: 命令执行结果列表
    """
    print("\n[测试] 模拟Docker命令执行...")
    
    commands = [
        {"cmd": "docker images", "desc": "列出镜像"},
        {"cmd": "docker ps -a", "desc": "列出所有容器"},
        {"cmd": "docker-compose up -d", "desc": "启动服务"},
        {"cmd": "docker-compose ps", "desc": "查看服务状态"},
        {"cmd": "docker-compose exec binwalkv3 binwalk --version", "desc": "查看Binwalk版本"}
    ]
    
    results = []
    for cmd_info in commands:
        cmd = cmd_info["cmd"]
        desc = cmd_info["desc"]
        
        print(f"[模拟] {desc}: {cmd}")
        
        # 模拟执行
        time.sleep(0.5)
        
        # 模拟结果
        if "binwalkv3" in cmd and "up" in cmd:
            output = "Creating network 'binwalkv3_default' with the default driver\nCreating binwalkv3... done"
        elif "binwalkv3" in cmd and "version" in cmd:
            output = "Binwalk v2.3.4"
        elif "images" in cmd:
            output = "REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE\nrefirmlabs/binwalk   latest              abc123def456        2 weeks ago         500MB"
        elif "ps" in cmd and "-a" in cmd:
            output = "CONTAINER ID        IMAGE                   COMMAND             CREATED             STATUS                      PORTS               NAMES\n1234567890ab        refirmlabs/binwalk:latest   \"/bin/bash\"         10 minutes ago      Exited (0) 5 minutes ago                        binwalkv3"
        elif "compose" in cmd and "ps" in cmd:
            output = "   Name                 Command             State           Ports         \n--------------------------------------------------------------------------------\nbinwalkv3           /bin/bash             Up             8080->8080/tcp, 8081->8081/tcp"
        else:
            output = "模拟命令执行成功"
        
        results.append({
            "command": cmd,
            "description": desc,
            "output": output,
            "simulated": True
        })
        
        print(f"  模拟输出: {output.split('\n')[0]}...")
    
    return results

def test_docker_manager_functionality():
    """
    测试DockerManager类的功能（如果存在）
    
    返回值:
        dict: 功能测试结果
    """
    print("\n[测试] 检查DockerManager类功能...")
    
    # 检查GUI脚本中的DockerManager
    gui_path = Path(__file__).parent / "binwalk_GUiQemu.py"
    
    try:
        # 创建测试代码
        check_code = f"""
import sys
import importlib.util

# 导入模块
spec = importlib.util.spec_from_file_location("binwalk_GUiQemu", "{gui_path}")
gui_module = importlib.util.module_from_spec(spec)
sys.modules["binwalk_GUiQemu"] = gui_module
spec.loader.exec_module(gui_module)

# 检查DockerManager类
if hasattr(gui_module, "DockerManager"):
    print("[SUCCESS] DockerManager类存在")
    
    # 获取类
    DockerManager = gui_module.DockerManager
    
    # 检查方法
    required_methods = ["start_container", "stop_container", "list_containers", 
                       "get_container_status", "exec_command", "get_binwalk_version"]
    
    found_methods = []
    missing_methods = []
    
    for method in required_methods:
        if hasattr(DockerManager, method):
            found_methods.append(method)
        else:
            missing_methods.append(method)
    
    print(f"找到的方法 ({len(found_methods)}): {', '.join(found_methods)}")
    if missing_methods:
        print(f"缺少的方法 ({len(missing_methods)}): {', '.join(missing_methods)}")
    
    # 检查初始化参数
    import inspect
    sig = inspect.signature(DockerManager.__init__)
    print(f"初始化参数: {sig}")
    
    sys.exit(0 if found_methods else 1)
else:
    print("[ERROR] DockerManager类不存在")
    sys.exit(1)
"""
        
        temp_script = Path(__file__).parent / "temp_docker_test.py"
        with open(temp_script, "w", encoding="utf-8") as f:
            f.write(check_code)
        
        result = subprocess.run([sys.executable, str(temp_script)], capture_output=True, text=True)
        
        if temp_script.exists():
            temp_script.unlink()
        
        print(result.stdout.strip())
        if result.stderr:
            print("\n警告:", result.stderr.strip())
        
        return {
            "status": result.returncode == 0,
            "has_manager": "[SUCCESS] DockerManager类存在" in result.stdout
        }
    
    except Exception as e:
        print(f"[错误] 测试DockerManager功能时出错: {str(e)}")
        return {
            "status": False,
            "error": str(e)
        }

def create_docker_test_config():
    """
    创建Docker测试配置
    
    返回值:
        bool: 创建是否成功
    """
    print("\n[测试] 创建Docker测试配置...")
    
    try:
        docker_config = {
            "docker_compose_path": str(Path(__file__).parent / "docker-compose.yml"),
            "container_name": "binwalkv3",
            "image_name": "refirmlabs/binwalk:latest",
            "volumes": [
                {"name": "binwalkv3", "path": "/analysis"}
            ],
            "ports": [
                {"host": 8080, "container": 8080},
                {"host": 8081, "container": 8081}
            ],
            "resources": {
                "memory_limit": "4g",
                "cpus": 2
            }
        }
        
        # 保存配置
        config_path = Path(__file__).parent / "docker_test_config.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(docker_config, f, indent=4, ensure_ascii=False)
        
        print(f"[成功] 创建Docker测试配置: {config_path}")
        return True
    except Exception as e:
        print(f"[错误] 创建Docker测试配置时出错: {str(e)}")
        return False

def simulate_binwalk_analysis():
    """
    模拟Binwalk分析过程
    
    返回值:
        dict: 模拟分析结果
    """
    print("\n[测试] 模拟Binwalk分析过程...")
    
    # 创建测试文件
    try:
        with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as test_file:
            # 写入一些模拟二进制数据
            test_file.write(b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\x03BINWALK TEST FILE\x00\xff\xff")
            test_file_path = test_file.name
        
        print(f"[模拟] 创建测试文件: {test_file_path}")
        
        # 模拟分析命令
        print("[模拟] 执行: binwalk -B test.bin")
        time.sleep(1)
        
        # 模拟分析输出
        mock_output = """
DECIMAL       HEXADECIMAL     DESCRIPTION
--------------------------------------------------------------------------------
0             0x0             gzip compressed data, was "test.txt", from Unix, last modified: 2023-01-01
10            0xA             ASCII cpio archive (SVR4 with no CRC), file name: "test", file name length: 0x4, file size: 0x20
"""
        
        print("[模拟分析结果]")
        print(mock_output)
        
        # 清理
        if Path(test_file_path).exists():
            Path(test_file_path).unlink()
        
        return {
            "status": True,
            "command": "binwalk -B test.bin",
            "output": mock_output
        }
    
    except Exception as e:
        print(f"[错误] 模拟分析过程时出错: {str(e)}")
        return {
            "status": False,
            "error": str(e)
        }

def generate_docker_report(results):
    """
    生成Docker管理功能测试报告
    
    参数:
        results: dict, 测试结果
    """
    print("\n" + "=" * 60)
    print("          Docker管理功能测试报告          ")
    print("=" * 60)
    
    # 打印各项结果
    for test_name, result in results.items():
        if isinstance(result, bool):
            status = "✓ 通过" if result else "✗ 失败"
            print(f"{test_name:<30}: {status}")
        elif isinstance(result, dict):
            if "status" in result:
                status = "✓ 通过" if result["status"] else "✗ 失败"
                print(f"{test_name:<30}: {status}")
                
                # 打印详细信息
                if "docker_installed" in result and "compose_installed" in result:
                    print(f"          Docker: {'已安装' if result['docker_installed'] else '未安装'}")
                    print(f"          docker-compose: {'已安装' if result['compose_installed'] else '未安装'}")
            else:
                print(f"{test_name:<30}: ✓ 完成")
        else:
            print(f"{test_name:<30}: ✓ 完成")
    
    print("\n" + "=" * 60)
    print("          Docker功能总结          ")
    print("=" * 60)
    print("1. docker-compose配置: 检查并创建了必要的配置文件")
    print("2. Docker客户端: 检查了本地Docker客户端安装状态")
    print("3. 容器管理: 模拟了容器启动、停止和状态查询")
    print("4. Binwalk集成: 模拟了通过容器执行Binwalk分析")
    print("\n注意: 这是模拟测试，实际功能需要在Qemu虚拟机运行时测试")
    print("在真实环境中，Docker将在Qemu虚拟机内部运行")

def main():
    """
    主函数
    """
    print_header()
    
    # 初始化测试结果
    test_results = {
        "docker-compose配置检查": {},
        "Docker客户端检查": {},
        "Docker命令模拟": [],
        "DockerManager功能检查": {},
        "Docker测试配置创建": False,
        "Binwalk分析模拟": {}
    }
    
    # 执行各项测试
    test_results["docker-compose配置检查"] = check_docker_compose_config()
    test_results["Docker客户端检查"] = test_docker_client_install()
    test_results["Docker命令模拟"] = simulate_docker_commands()
    test_results["DockerManager功能检查"] = test_docker_manager_functionality()
    test_results["Docker测试配置创建"] = create_docker_test_config()
    test_results["Binwalk分析模拟"] = simulate_binwalk_analysis()
    
    # 生成报告
    generate_docker_report(test_results)
    
    print("\n[完成] Docker容器管理功能测试完成")
    print("提示: 要测试实际功能，请确保Qemu虚拟机已启动且内部Docker可用")
    print("\n按Enter键退出...")
    
    # 等待用户输入
    input()

if __name__ == "__main__":
    main()