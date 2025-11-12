#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Binwalk GUI 构建脚本

此脚本用于将 binwalk_gui.py 编译为可执行文件，提供更友好的用户界面和错误处理。
"""

import os
import sys
import subprocess
import time
import shutil
import importlib.util

def print_header():
    """
    打印程序头部信息
    """
    header = """
    ============================================
            Binwalk GUI 构建工具
    ============================================
    用于将 binwalk_gui.py 编译为可执行文件
    ============================================
    """
    print(header)

def check_python():
    """
    检查Python版本
    
    Returns:
        bool: Python版本是否满足要求
    """
    print("[+] 检查Python版本...")
    if sys.version_info < (3, 6):
        print("[-] 错误：需要Python 3.6或更高版本")
        return False
    print(f"[+] Python版本: {sys.version}")
    return True

def install_package(package_name):
    """
    安装指定的Python包
    
    Args:
        package_name (str): 要安装的包名
    
    Returns:
        bool: 安装是否成功
    """
    print(f"[+] 正在安装 {package_name}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"[+] {package_name} 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[-] 安装 {package_name} 失败: {e}")
        return False

def check_package(package_name):
    """
    检查包是否已安装
    
    Args:
        package_name (str): 包名
    
    Returns:
        bool: 是否已安装
    """
    spec = importlib.util.find_spec(package_name)
    return spec is not None

def check_pyinstaller():
    """
    检查并安装PyInstaller和Pillow库（用于图标格式转换）
    
    Returns:
        bool: 是否成功安装或已存在
    """
    print("[+] 检查PyInstaller...")
    if not check_package("PyInstaller"):
        if not install_package("PyInstaller"):
            return False
    print("[+] PyInstaller 已安装")
    
    # 安装Pillow库用于自动转换图标格式
    print("[+] 检查Pillow库（用于图标格式转换）...")
    if not check_package("Pillow"):
        if not install_package("Pillow"):
            print("[-] 警告：Pillow安装失败，可能无法自动转换JPG图标")
    else:
        print("[+] Pillow 已安装，支持自动转换JPG图标")
    
    return True

def check_gui_file():
    """
    检查binwalk_gui.py文件是否存在
    
    Returns:
        bool: 文件是否存在
    """
    print("[+] 检查binwalk_gui.py文件...")
    if not os.path.exists("binwalk_gui.py"):
        print("[-] 错误：未找到binwalk_gui.py文件")
        return False
    print("[+] 找到binwalk_gui.py文件")
    return True

def compile_to_exe():
    """
    使用PyInstaller将Python脚本编译为可执行文件
    
    Returns:
        bool: 编译是否成功
    """
    print("[+] 开始编译为可执行文件...")
    
    # 清理之前的构建结果
    if os.path.exists("build"):
        print("[+] 清理之前的构建目录...")
        shutil.rmtree("build")
    
    if os.path.exists("dist"):
        print("[+] 清理之前的发布目录...")
        shutil.rmtree("dist")
    
    # 构建命令 - 确保创建完全独立的可执行文件
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--onefile",        # 创建单一可执行文件
        "--windowed",       # 无控制台窗口
        "--icon=devROM.jpg",
        "--name=binwalk_gui",
        "--hidden-import=tkinter",  # 确保tkinter被包含
        "--hidden-import=tkinter.ttk",  # 确保ttk被包含
        "--hidden-import=tkinter.font",  # 确保字体模块被包含
        "--collect-all=tkinter",  # 收集所有tkinter相关模块
        "--clean",           # 清理PyInstaller缓存
        "--noconfirm",       # 不询问确认
        # 优化打包选项
        "--optimize=2",      # 代码优化级别2
        "--exclude-module=FixTk",  # 排除不必要的模块
        "binwalk_gui.py"
    ]
    
    # 记录构建配置信息
    print("[+] 构建配置:")
    print(f"[+] - Python路径: {sys.executable}")
    print("[+] - 构建模式: 单文件独立可执行")
    print("[+] - 窗口模式: 启用")
    print("[+] - 应用图标: devROM.jpg")
    print("[+] - 依赖收集: 自动收集所有tkinter相关组件")
    print("[+] - 优化级别: 2")
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # 实时显示输出
        for line in process.stdout:
            print(line.strip())
        
        process.wait()
        
        if process.returncode == 0:
            print("[+] 编译成功！")
            return True
        else:
            print("[-] 编译失败！")
            return False
    except Exception as e:
        print(f"[-] 编译过程出错: {e}")
        return False

def copy_to_binwalk_directory():
    """
    将编译后的可执行文件复制到当前目录
    
    Returns:
        bool: 复制是否成功
    """
    exe_path = os.path.join("dist", "binwalk_gui.exe")
    if os.path.exists(exe_path):
        try:
            shutil.copy2(exe_path, ".")
            print("[+] 已将binwalk_gui.exe复制到当前目录")
            return True
        except Exception as e:
            print(f"[-] 复制可执行文件失败: {e}")
            return False
    return False

def main():
    """
    主函数
    
    Returns:
        int: 退出码
    """
    print_header()
    
    try:
        # 检查环境
        if not check_python():
            return 1
        
        if not check_pyinstaller():
            return 1
        
        if not check_gui_file():
            return 1
        
        # 编译
        if compile_to_exe():
            # 复制到当前目录
            copy_to_binwalk_directory()
            
            print("\n[+] 构建完成！")
            print("[+] 可执行文件位置:")
            print(f"[+] - 发布目录: {os.path.abspath('dist/binwalk_gui.exe')}")
            print(f"[+] - 当前目录: {os.path.abspath('binwalk_gui.exe')}")
            print("\n[+] 提示: binwalk_gui.exe需要与binwalk.exe在同一目录下运行")
            return 0
        else:
            print("[-] 构建失败，请查看错误信息")
            return 1
    
    except KeyboardInterrupt:
        print("\n[-] 操作被用户中断")
        return 1
    except Exception as e:
        print(f"[-] 发生未知错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        print("\n[+] 按回车键退出...")
        input()

if __name__ == "__main__":
    sys.exit(main())