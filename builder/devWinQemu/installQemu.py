#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Binwalk Qemu安装脚本

功能: 在Windows系统上安装Qemu环境并配置Kali Linux镜像，为Binwalk提供运行环境

使用方法: 以管理员权限运行此脚本
"""

import os
import sys
import subprocess
import shutil
import requests
import zipfile
import tempfile
import time
from pathlib import Path

# 确保脚本以管理员权限运行
def is_admin():
    """
    检查当前进程是否以管理员权限运行
    
    返回值:
        bool: True表示以管理员权限运行，False表示不是
    """
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# 获取脚本所在目录的绝对路径
def get_script_dir():
    """
    获取脚本所在目录的绝对路径
    
    返回值:
        Path: 脚本所在目录的Path对象
    """
    return Path(os.path.dirname(os.path.abspath(__file__)))

# 创建必要的目录
def create_directories(base_dir):
    """
    创建安装所需的目录结构
    
    参数:
        base_dir: Path对象，表示基础目录
    
    返回值:
        dict: 包含所有创建目录路径的字典
    """
    directories = {
        'qemu': base_dir / 'qemu',
        'images': base_dir / 'images',
        'data': base_dir / 'data',
        'scripts': base_dir / 'scripts'
    }
    
    for dir_path in directories.values():
        dir_path.mkdir(parents=True, exist_ok=True)
    
    return directories

# 下载文件
def download_file(url, dest_path, show_progress=True):
    """
    下载文件并显示进度
    
    参数:
        url: str, 文件下载链接
        dest_path: Path, 目标文件路径
        show_progress: bool, 是否显示下载进度
    
    返回值:
        bool: True表示下载成功，False表示失败
    """
    try:
        print(f"正在下载 {url} 到 {dest_path}...")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if show_progress and total_size > 0:
                        progress = downloaded / total_size * 100
                        sys.stdout.write(f"\r下载进度: {progress:.1f}%")
                        sys.stdout.flush()
        
        if show_progress:
            print("\r下载完成!")
            
        return True
    except Exception as e:
        print(f"下载失败: {str(e)}")
        return False

# 解压ZIP文件
def extract_zip(zip_path, dest_dir):
    """
    解压ZIP文件到指定目录
    
    参数:
        zip_path: Path, ZIP文件路径
        dest_dir: Path, 目标目录路径
    
    返回值:
        bool: True表示解压成功，False表示失败
    """
    try:
        print(f"正在解压 {zip_path} 到 {dest_dir}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(dest_dir)
        print("解压完成!")
        return True
    except Exception as e:
        print(f"解压失败: {str(e)}")
        return False

# 运行PowerShell命令
def run_powershell_command(command, admin=False):
    """
    运行PowerShell命令
    
    参数:
        command: str, 要执行的PowerShell命令
        admin: bool, 是否以管理员权限运行
    
    返回值:
        tuple: (成功标志, 输出内容)
    """
    try:
        print(f"执行PowerShell命令: {command}")
        
        if admin:
            # 以管理员权限运行命令
            cmd = ["powershell", "Start-Process", "powershell", 
                  "-ArgumentList", f"'-Command', '{command}'", 
                  "-Verb", "RunAs", "-Wait"]
        else:
            cmd = ["powershell", "-Command", command]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        
        if result.returncode != 0:
            print(f"命令执行失败，返回码: {result.returncode}")
            print(f"错误输出: {result.stderr}")
            return False, result.stderr
        
        return True, result.stdout
    except Exception as e:
        print(f"执行命令异常: {str(e)}")
        return False, str(e)

# 安装Qemu
def install_qemu(qemu_dir):
    """
    安装Qemu到指定目录
    
    参数:
        qemu_dir: Path, Qemu安装目录
    
    返回值:
        bool: True表示安装成功，False表示失败
    """
    # 检查Qemu是否已安装
    if (qemu_dir / "qemu-system-x86_64.exe").exists():
        print("Qemu已存在，跳过安装")
        return True
    
    # Qemu Windows下载链接（使用稳定版本）
    qemu_url = "https://qemu.weilnetz.de/w64/qemu-w64-setup-20231019.exe"
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        installer_path = temp_path / "qemu-installer.exe"
        
        # 下载Qemu安装程序
        if not download_file(qemu_url, installer_path):
            return False
        
        # 创建静默安装配置
        unattended_file = temp_path / "unattended.txt"
        with open(unattended_file, "w") as f:
            f.write(f"/S /D={qemu_dir}")
        
        # 运行安装程序
        print(f"正在安装Qemu到 {qemu_dir}...")
        try:
            subprocess.run([str(installer_path), f"/S", f"/D={qemu_dir}"], 
                          check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("Qemu安装成功!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Qemu安装失败: {str(e)}")
            return False

# 下载Kali Linux云镜像
def download_kali_image(images_dir):
    """
    下载Kali Linux云镜像
    
    参数:
        images_dir: Path, 镜像保存目录
    
    返回值:
        Path: 下载的镜像文件路径，失败返回None
    """
    # 检查镜像是否已存在
    image_file = images_dir / "kali-linux-cloud-amd64.img"
    if image_file.exists():
        print(f"Kali镜像已存在: {image_file}")
        return image_file
    
    # Kali Linux云镜像下载链接
    kali_url = "https://cdimage.kali.org/kali-cloud-images/kali-2023.4/kali-linux-2023.4-cloud-amd64.img.xz"
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        compressed_image = temp_path / "kali-image.img.xz"
        
        # 下载压缩镜像
        if not download_file(kali_url, compressed_image):
            return None
        
        # 解压镜像（需要安装7zip或其他解压工具）
        print("正在解压Kali镜像...")
        try:
            # 使用PowerShell的Expand-Archive或其他方法解压
            # 这里使用7zip命令行（如果已安装）
            result, output = run_powershell_command(
                f"if (Test-Path 'C:\\Program Files\\7-Zip\\7z.exe') {{ & 'C:\\Program Files\\7-Zip\\7z.exe' x '{compressed_image}' -o'{images_dir}' -y }} else {{ Write-Error '7zip未安装，无法解压xz文件' }}")
            
            if not result:
                # 尝试使用其他方法解压
                print("尝试使用PowerShell原生方法解压...")
                # 注意：PowerShell可能无法直接解压xz格式，这里提供一个备选方案
                return None
            
            # 重命名解压后的文件
            extracted_files = list(images_dir.glob("*.img"))
            if extracted_files:
                extracted_files[0].rename(image_file)
                print(f"Kali镜像已下载并解压到: {image_file}")
                return image_file
            else:
                print("无法找到解压后的镜像文件")
                return None
                
        except Exception as e:
            print(f"解压Kali镜像失败: {str(e)}")
            return None

# 创建Qemu启动脚本
def create_qemu_start_script(scripts_dir, qemu_dir, image_path, data_dir):
    """
    创建Qemu启动脚本
    
    参数:
        scripts_dir: Path, 脚本保存目录
        qemu_dir: Path, Qemu安装目录
        image_path: Path, 镜像文件路径
        data_dir: Path, 数据目录路径
    
    返回值:
        Path: 创建的脚本文件路径
    """
    script_path = scripts_dir / "start_kali.bat"
    
    # 创建数据盘镜像文件
    data_disk_path = data_dir / "data_disk.img"
    if not data_disk_path.exists():
        print("创建数据盘镜像...")
        qemu_img_path = qemu_dir / "qemu-img.exe"
        subprocess.run([str(qemu_img_path), "create", "-f", "qcow2", 
                       str(data_disk_path), "20G"], check=True)
    
    with open(script_path, "w") as f:
        f.write(f"@echo off\n")
        f.write(f"cd /d {qemu_dir}\n")
        f.write(f"qemu-system-x86_64.exe ^\n")
        f.write(f"  -m 4G ^\n")  # 分配4GB内存
        f.write(f"  -smp 2 ^\n")  # 2个CPU核心
        f.write(f"  -hda {image_path} ^\n")
        f.write(f"  -hdb {data_disk_path} ^\n")
        f.write(f"  -device virtio-net-pci,netdev=net0 ^\n")
        f.write(f"  -netdev user,id=net0,hostfwd=tcp::2222-:22,hostfwd=tcp::8080-:80 ^\n")
        f.write(f"  -display gtk ^\n")
        f.write(f"  -accel tcg\n")
    
    print(f"Qemu启动脚本已创建: {script_path}")
    return script_path

# 配置Kali Linux中的Docker环境
def configure_kali_docker(scripts_dir):
    """
    创建配置Kali Linux Docker环境的脚本
    
    参数:
        scripts_dir: Path, 脚本保存目录
    
    返回值:
        Path: 创建的配置脚本路径
    """
    script_path = scripts_dir / "configure_docker.sh"
    
    with open(script_path, "w") as f:
        f.write("#!/bin/bash\n")
        f.write("\n")
        f.write("# 更新系统并安装Docker\n")
        f.write("sudo apt-get update\n")
        f.write("sudo apt-get install -y docker.io docker-compose\n")
        f.write("\n")
        f.write("# 启动Docker服务\n")
        f.write("sudo systemctl enable docker\n")
        f.write("sudo systemctl start docker\n")
        f.write("\n")
        f.write("# 将当前用户添加到docker组\n")
        f.write("sudo usermod -aG docker $USER\n")
        f.write("\n")
        f.write("# 创建分析目录\n")
        f.write("mkdir -p ~/analysis\n")
        f.write("\n")
        f.write("# 拉取binwalk镜像\n")
        f.write("docker pull refirmlabs/binwalk:latest\n")
        f.write("\n")
        f.write("echo 'Docker环境配置完成! 请重新登录以应用docker组权限。'\n")
    
    # 创建Windows上运行此脚本的批处理文件
    win_script_path = scripts_dir / "run_docker_setup.bat"
    with open(win_script_path, "w") as f:
        f.write("@echo off\n")
        f.write("echo 请确保Kali虚拟机已启动且SSH服务正在运行\n")
        f.write("echo 默认用户名: kali, 密码: kali\n")
        f.write("set /p username=输入Kali用户名 [kali]: ")
        f.write("if "%username%"=="" set username=kali\n")
        f.write("\n")
        f.write("rem 上传配置脚本到Kali\n")
        f.write("pscp -scp -P 2222 configure_docker.sh %username%@localhost:/home/%username%/\n")
        f.write("\n")
        f.write("rem 连接到Kali并执行配置脚本\n")
        f.write("putty -ssh -P 2222 %username%@localhost -m run_config.txt\n")
    
    # 创建PuTTY命令文件
    putty_cmd_path = scripts_dir / "run_config.txt"
    with open(putty_cmd_path, "w") as f:
        f.write("chmod +x configure_docker.sh\n")
        f.write("./configure_docker.sh\n")
    
    print(f"Docker配置脚本已创建: {script_path}")
    print(f"Windows运行脚本已创建: {win_script_path}")
    return win_script_path

# 创建README文件
def create_readme(base_dir):
    """
    创建README文件，提供使用说明
    
    参数:
        base_dir: Path, 基础目录
    
    返回值:
        Path: 创建的README文件路径
    """
    readme_path = base_dir / "README.md"
    
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("# Binwalk Qemu 环境配置\n\n")
        f.write("## 简介\n\n")
        f.write("本工具集用于在Windows系统上通过Qemu虚拟机运行Kali Linux，并在其中配置Docker环境以运行Binwalk。\n\n")
        f.write("## 目录结构\n\n")
        f.write("- `qemu/`: Qemu虚拟机软件\n")
        f.write("- `images/`: 包含Kali Linux镜像\n")
        f.write("- `data/`: 数据目录，用于存储分析文件\n")
        f.write("- `scripts/`: 各种脚本文件\n\n")
        f.write("## 使用方法\n\n")
        f.write("### 1. 安装Qemu和配置Kali\n\n")
        f.write("运行 `installQemu.py` 脚本（需要管理员权限）以安装Qemu并下载Kali镜像。\n\n")
        f.write("### 2. 启动Kali虚拟机\n\n")
        f.write("运行 `scripts/start_kali.bat` 启动Kali Linux虚拟机。\n\n")
        f.write("### 3. 配置Docker环境\n\n")
        f.write("1. 在Kali虚拟机中设置网络并确保SSH服务正在运行\n")
        f.write("2. 运行 `scripts/run_docker_setup.bat` 配置Docker环境\n\n")
        f.write("### 4. 使用binwalk_GUiQemu.py\n\n")
        f.write("运行 `binwalk_GUiQemu.py` 图形界面工具管理Docker容器和文件传输。\n\n")
        f.write("## 注意事项\n\n")
        f.write("- 首次启动Kali时需要设置用户名和密码\n")
        f.write("- 确保系统有足够的内存和磁盘空间\n")
        f.write("- 数据文件将保存在`data/`目录中\n\n")
    
    print(f"README文件已创建: {readme_path}")
    return readme_path

# 主函数
def main():
    """
    主函数，协调整个安装过程
    """
    print("===== Binwalk Qemu 环境安装程序 =====")
    
    # 检查管理员权限
    if not is_admin():
        print("错误: 请以管理员权限运行此脚本！")
        sys.exit(1)
    
    # 获取基础目录
    base_dir = get_script_dir()
    print(f"安装目录: {base_dir}")
    
    # 创建必要的目录
    directories = create_directories(base_dir)
    
    # 安装Qemu
    if not install_qemu(directories['qemu']):
        print("Qemu安装失败，退出程序")
        sys.exit(1)
    
    # 下载Kali镜像
    image_path = download_kali_image(directories['images'])
    if not image_path:
        print("警告: Kali镜像下载失败，请手动下载并放入images目录")
    
    # 创建Qemu启动脚本
    start_script = create_qemu_start_script(
        directories['scripts'], 
        directories['qemu'], 
        image_path or directories['images'] / "kali-linux-cloud-amd64.img",
        directories['data']
    )
    
    # 配置Docker环境脚本
    docker_script = configure_kali_docker(directories['scripts'])
    
    # 创建README文件
    create_readme(base_dir)
    
    print("\n===== 安装完成 =====")
    print(f"1. 启动Kali: 运行 {start_script}")
    print(f"2. 配置Docker: 运行 {docker_script}")
    print("3. 然后运行 binwalk_GUiQemu.py 开始使用")
    print("\n请查看README.md获取详细使用说明")

if __name__ == "__main__":
    main()