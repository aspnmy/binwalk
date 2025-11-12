#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Binwalk GUI 构建脚本

此脚本用于将 binwalk_gui.py 编译为可执行文件，提供更友好的用户界面和错误处理，
并自动完成文件复制、清理和验证流程。
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
# 检查binwalk_gui.py文件
    print("[+] 检查binwalk_gui.py文件...")
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    binwalk_gui_path = os.path.join(script_dir, "binwalk_gui.py")
    if not os.path.exists(binwalk_gui_path):
        print(f"[-] 错误：未找到binwalk_gui.py文件，路径: {binwalk_gui_path}")
        return False
    else:
        print(f"[+] 找到binwalk_gui.py文件: {binwalk_gui_path}")
        # 更新binwalk_gui_file变量为正确路径
        global binwalk_gui_file
        binwalk_gui_file = binwalk_gui_path
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
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 获取devROM.jpg的绝对路径
    icon_path = os.path.join(script_dir, "devROM.jpg")
    
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--onefile",        # 创建单一可执行文件
        "--windowed",       # 无控制台窗口
        f"--icon={icon_path}",
        "--name=binwalk_gui",
        f"--add-data={icon_path};."  # 添加图标文件作为资源（Windows格式）
        , "--hidden-import=tkinter",  # 确保tkinter被包含
        "--hidden-import=tkinter.ttk",  # 确保ttk被包含
        "--hidden-import=tkinter.font",  # 确保字体模块被包含
        "--collect-all=tkinter",  # 收集所有tkinter相关模块
        "--clean",           # 清理PyInstaller缓存
        "--noconfirm",       # 不询问确认
        # 优化打包选项
        "--optimize=2",      # 代码优化级别2
        "--exclude-module=FixTk",  # 排除不必要的模块
        binwalk_gui_file  # 使用绝对路径的主脚本文件
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

def copy_files_to_dist():
    """
    将必要的文件复制到dist目录，确保所有发布文件都在正确位置
    
    Returns:
        bool: 复制是否成功
    """
    print("[+] 开始复制必要文件到dist目录...")
    
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 确保dist目录存在
    if not os.path.exists("dist"):
        print("[-] 错误：dist目录不存在")
        return False
    
    # 确保sqfs_for_win子目录存在
    sqfs_dist_dir = os.path.join("dist", "sqfs_for_win")
    if not os.path.exists(sqfs_dist_dir):
        os.makedirs(sqfs_dist_dir)
        print(f"[+] 创建目录: {sqfs_dist_dir}")
    
    # 要复制的文件列表 - 使用脚本所在目录作为源目录
    files_to_copy = [
        (os.path.join(script_dir, "binwalk.exe"), "dist"),
        (os.path.join(script_dir, "devROM.jpg"), "dist")
    ]
    
    # 找到项目根目录（假设binwalk目录是项目根目录）
    # 从builder\build-WinGui向上两级目录到达binwalk根目录
    project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
    
    # 重构目录复制结构，为每个目标目录提供多个可能的源路径
    # 根据用户需求，优先尝试从dependencies目录复制
    dirs_to_copy = {
        "dist\\Tests": [
            os.path.join(project_root, "dependencies", "Tests"),  # 优先尝试dependencies目录
            os.path.join(script_dir, "Tests")  # 备选源目录
        ],
        "dist\\sqfs_for_win": [
            os.path.join(project_root, "dependencies", "sqfs_for_win"),  # 优先尝试dependencies目录
            os.path.join(script_dir, "sqfs_for_win")  # 备选源目录
        ]
    }
    
    success = True
    
    # 跟踪已复制的文件，避免重复
    copied_files = set()
    copied_dirs = set()
    
    # 复制文件
    for src, dest in files_to_copy:
        filename = os.path.basename(src)
        if filename in copied_files:
            continue
            
        dest_path = os.path.abspath(os.path.join(dest, filename))
        
        if os.path.exists(src):
            try:
                shutil.copy2(src, dest_path)
                print(f"[+] 复制文件: {src} -> {dest_path}")
                copied_files.add(filename)
            except Exception as e:
                print(f"[-] 复制文件失败 {src}: {e}")
        else:
            print(f"[-] 警告: 未找到文件 {src}")
    
    # 确保所有必要文件都已复制
    required_files = ["binwalk.exe", "devROM.jpg"]
    for req_file in required_files:
        if req_file not in copied_files:
            print(f"[-] 错误：无法找到并复制必要文件 {req_file}")
            success = False
    
    # 复制目录 - 尝试每个目标目录的所有可能源路径
    required_dirs_found = {}
    
    for dst_dir, possible_src_dirs in dirs_to_copy.items():
        dir_copied = False
        
        for src_dir in possible_src_dirs:
            try:
                if os.path.exists(src_dir) and os.path.isdir(src_dir):
                    # 确保目标目录存在
                    dst_path = os.path.abspath(dst_dir)
                    if os.path.exists(dst_path):
                        shutil.rmtree(dst_path)
                    
                    shutil.copytree(src_dir, dst_path)
                    print(f"[+] 复制目录: {src_dir} -> {dst_path}")
                    copied_dirs.add(os.path.basename(src_dir))
                    required_dirs_found[dst_dir] = True
                    dir_copied = True
                    break  # 成功复制后跳出循环
                else:
                    print(f"[-] 警告: 未找到目录 {src_dir}")
            except Exception as e:
                print(f"[-] 复制目录失败 {src_dir}: {e}")
        
        if not dir_copied:
            required_dirs_found[dst_dir] = False
    
    # 检查是否复制了所有必要的项目
    missing_dirs = [dir_name for dir_name, found in required_dirs_found.items() if not found]
    if missing_dirs:
        print(f"[-] 错误：无法找到并复制必要目录 {', '.join(missing_dirs)}")
        success = False
    
    return success

def clean_intermediate_files():
    """
    清理构建过程中产生的中间文件和目录
    
    Returns:
        bool: 清理是否成功
    """
    print("[+] 开始清理中间文件...")
    
    # 要删除的目录列表
    dirs_to_remove = ["build", "extractions", "sqfs_for_win", "Tests"]
    # 要删除的文件列表
    files_to_remove = ["binwalk_gui.spec"]
    
    success = True
    
    # 删除目录
    for dir_name in dirs_to_remove:
        dir_path = os.path.abspath(dir_name)
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            try:
                shutil.rmtree(dir_path)
                print(f"[+] 删除目录: {dir_path}")
            except Exception as e:
                print(f"[-] 删除目录失败 {dir_name}: {e}")
                success = False
    
    # 删除文件
    for file_name in files_to_remove:
        file_path = os.path.abspath(file_name)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            try:
                os.remove(file_path)
                print(f"[+] 删除文件: {file_path}")
            except Exception as e:
                print(f"[-] 删除文件失败 {file_name}: {e}")
                success = False
    
    return success

def verify_file_structure():
    """
    验证dist目录的文件结构是否符合要求
    
    Returns:
        bool: 文件结构是否符合要求
    """
    print("[+] 验证文件结构...")
    
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(script_dir, "dist")
    
    # 验证dist目录是否存在
    if not os.path.exists(dist_dir):
        print("[-] 错误：dist目录不存在")
        return False
    
    # 必需的文件和目录
    required_items = {
        "files": ["binwalk_gui.exe", "binwalk.exe", "devROM.jpg"],
        "dirs": ["Tests", "sqfs_for_win"]
    }
    
    all_present = True
    
    # 检查必需的文件
    for file_name in required_items["files"]:
        file_path = os.path.join(dist_dir, file_name)
        if os.path.exists(file_path):
            print(f"[+] 找到必需文件: {file_path}")
        else:
            print(f"[-] 缺失必需文件: {file_path}")
            # binwalk_gui.exe是必须的，其他文件如果缺失但build成功则设为警告而非错误
            if file_name == "binwalk_gui.exe":
                all_present = False
    
    # 检查必需的目录
    for dir_name in required_items["dirs"]:
        dir_path = os.path.join(dist_dir, dir_name)
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            print(f"[+] 找到必需目录: {dir_path}")
            
            # 对于sqfs_for_win目录，检查是否有7z文件
            if dir_name == "sqfs_for_win":
                has_7z = False
                for item in os.listdir(dir_path):
                    if item.endswith(".7z"):
                        has_7z = True
                        print(f"[+] 找到压缩包: {os.path.join(dir_path, item)}")
                        break
                if not has_7z:
                    print(f"[-] 警告: sqfs_for_win目录中未找到.7z文件")
                    # .7z文件是必需的，缺失则验证失败
                    all_present = False
        else:
            print(f"[-] 缺失必需目录: {dir_path}")
            all_present = False
    
    # 打印验证结果
    if all_present:
        print("[+] 文件结构验证成功！")
        print(f"[+] 构建完成！最终输出位于: {dist_dir}")
    else:
        print("[-] 文件结构验证失败，但binwalk_gui.exe可能已成功构建")
    
    return all_present

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
            print("\n[+] 开始完整构建流程...")
            
            # 1. 复制所有必要文件到dist目录
            if not copy_files_to_dist():
                print("[-] 复制文件到dist目录失败")
                return 1
            
            # 2. 清理中间文件
            if not clean_intermediate_files():
                print("[-] 清理中间文件失败")
                # 继续执行，因为这不是致命错误
            
            # 3. 验证文件结构
            if not verify_file_structure():
                print("[-] 文件结构验证失败")
                return 1
            
            print("\n[+] 构建完成！")
            print("[+] 可执行文件位置:")
            print(f"[+] - 发布目录: {os.path.abspath('dist/binwalk_gui.exe')}")
            print(f"[+] - 发布目录: {os.path.abspath('dist/binwalk.exe')}")
            print("\n[+] 提示: binwalk_gui.exe需要与binwalk.exe在同一目录下运行")
            print("[+] 发布文件已准备就绪在 dist 目录中")
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