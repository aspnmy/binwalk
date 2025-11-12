#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Binwalk 构建脚本

此脚本在builder目录下创建隔离的构建环境，包括MinGW64和Rust工具链，
不依赖系统中已安装的环境，确保构建过程的一致性和可靠性。
"""

import os
import sys
import shutil
import subprocess
import zipfile
import tarfile
import stat
import platform
import time
import logging
from urllib.request import urlretrieve

# 确保路径分隔符正确处理
def get_normalized_path(path):
    """
    获取规范化的路径，处理不同操作系统的路径分隔符
    
    参数:
        path (str): 原始路径
    
    返回:
        str: 规范化后的路径
    """
    return os.path.normpath(path)

# 设置脚本目录为工作目录，确保路径正确
sCRIPT_DIR = get_normalized_path(os.path.dirname(os.path.abspath(__file__)))
print(f"初始化: 脚本目录 = {sCRIPT_DIR}")
try:
    os.chdir(sCRIPT_DIR)
    print(f"初始化: 当前工作目录已设置为 = {os.getcwd()}")
except Exception as e:
    print(f"警告: 无法更改工作目录: {e}")

# 定义本地环境路径，使用绝对路径确保一致性
# 定义关键目录路径
LOCAL_ENV_DIR = get_normalized_path(os.path.join(sCRIPT_DIR, 'local_env'))
MINGW_DIR = get_normalized_path(os.path.join(LOCAL_ENV_DIR, 'mingw64'))
RUST_DIR = get_normalized_path(os.path.join(LOCAL_ENV_DIR, 'rust'))
CARGO_HOME = get_normalized_path(os.path.join(RUST_DIR, 'cargo'))
RUSTUP_HOME = get_normalized_path(os.path.join(RUST_DIR, 'rustup'))
PROJECT_ROOT = get_normalized_path(os.path.dirname(sCRIPT_DIR))  # 项目根目录在builder的上一级

# 配置日志
os.makedirs(LOCAL_ENV_DIR, exist_ok=True)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(os.path.join(LOCAL_ENV_DIR, 'build.log')),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger('binwalk-builder')

# 7-Zip相关配置
SEVEN_ZIP_DIR = get_normalized_path(os.path.join(LOCAL_ENV_DIR, '7z'))
SEVEN_ZIP_EXE = get_normalized_path(os.path.join(SEVEN_ZIP_DIR, '7z.exe'))
SEVEN_ZIP_URL = "https://www.7-zip.org/a/7z2407-x64.exe"  # 最新版本的7-Zip下载链接
SEVEN_ZIP_INSTALLER = get_normalized_path(os.path.join(LOCAL_ENV_DIR, '7z-installer.exe'))

# 验证项目根目录是否存在
if not os.path.exists(PROJECT_ROOT):
    print(f"错误: 无法确定项目根目录: {PROJECT_ROOT}")
    print("请确保脚本位于builder目录中")
    sys.exit(1)

print(f"初始化: 项目根目录 = {PROJECT_ROOT}")
# 验证项目根目录中是否有Cargo.toml文件
if not os.path.exists(os.path.join(PROJECT_ROOT, 'Cargo.toml')):
    print("警告: 在项目根目录中未找到Cargo.toml文件")
    print("请确保脚本位于正确的位置")

# 7-Zip工具下载信息 (Windows)
SEVEN_ZIP_URL = "https://www.7-zip.org/a/7z2402-extra.7z"
SEVEN_ZIP_ARCHIVE = os.path.join(LOCAL_ENV_DIR, '7z-extra.7z')
SEVEN_ZIP_DIR = get_normalized_path(os.path.join(LOCAL_ENV_DIR, '7z'))
SEVEN_ZIP_EXE = get_normalized_path(os.path.join(SEVEN_ZIP_DIR, '7z.exe'))

# MinGW64 下载信息 (Windows)
MINGW_URL = "https://github.com/niXman/mingw-builds-binaries/releases/download/13.2.0-rt_v11-rev0/x86_64-13.2.0-release-posix-seh-ucrt-rt_v11-rev0.7z"
MINGW_ARCHIVE = os.path.join(LOCAL_ENV_DIR, 'mingw64.7z')

# Rustup 下载信息
if platform.system() == 'Windows':
    RUSTUP_URL = "https://win.rustup.rs/x86_64"
    RUSTUP_EXE = os.path.join(LOCAL_ENV_DIR, 'rustup-init.exe')
else:
    RUSTUP_URL = "https://sh.rustup.rs"
    RUSTUP_SCRIPT = os.path.join(LOCAL_ENV_DIR, 'rustup-init.sh')


def run_command(cmd, env=None, cwd=None, capture_output=False):
    """
    执行命令并返回结果
    
    参数:
        cmd (list): 要执行的命令
        env (dict): 环境变量字典，如果为None则创建干净的环境
        cwd (str): 工作目录
        capture_output (bool): 是否捕获输出
    
    返回:
        tuple: (returncode, stdout, stderr)
    """
    try:
        # 创建干净的环境变量，不继承系统PATH，避免使用系统程序
        clean_env = {}
        if env is None:
            # 创建最基本的环境变量
            if platform.system() == 'Windows':
                # Windows基本环境变量
                clean_env['TEMP'] = os.environ.get('TEMP', os.path.join(LOCAL_ENV_DIR, 'temp'))
                clean_env['TMP'] = os.environ.get('TMP', os.path.join(LOCAL_ENV_DIR, 'temp'))
            else:
                # Linux/macOS基本环境变量
                clean_env['HOME'] = os.environ.get('HOME', '/tmp')
                clean_env['PATH'] = ''
        else:
            # 使用提供的环境变量，但确保不包含系统PATH
            clean_env = env.copy()
            if 'PATH' in clean_env:
                del clean_env['PATH']
        
        # 确保必要的目录存在
        os.makedirs(os.path.join(LOCAL_ENV_DIR, 'temp'), exist_ok=True)
        
        # 确保命令路径正确，使用相对路径而不是系统PATH
        if isinstance(cmd, list) and len(cmd) > 0:
            # 检查命令是否是本地工具
            if cmd[0] in ['rustup', 'cargo', 'gcc', 'g++', '7z']:
                # 强制使用本地环境中的工具，不依赖系统PATH
                if cmd[0] == 'rustup' or cmd[0] == 'cargo':
                    # 使用相对路径的Rust工具
                    local_bin = os.path.join(CARGO_HOME, 'bin', cmd[0])
                    if platform.system() == 'Windows':
                        local_bin += '.exe'
                    # 确保文件存在
                    if os.path.exists(local_bin):
                        cmd[0] = local_bin
                        logger.info(f"使用相对路径的 {cmd[0]} 工具")
                    else:
                        logger.warning(f"本地工具不存在: {local_bin}")
                elif (cmd[0] == 'gcc' or cmd[0] == 'g++') and platform.system() == 'Windows':
                    # Windows上使用MinGW工具
                    local_bin = os.path.join(MINGW_DIR, 'bin', cmd[0])
                    if platform.system() == 'Windows':
                        local_bin += '.exe'
                    if os.path.exists(local_bin):
                        cmd[0] = local_bin
                        logger.info(f"使用相对路径的 {cmd[0]} 工具")
                    else:
                        logger.warning(f"本地MinGW工具不存在: {local_bin}")
                elif cmd[0] == '7z' and os.path.exists(SEVEN_ZIP_EXE):
                    # 使用相对路径的7z工具
                    cmd[0] = SEVEN_ZIP_EXE
                    logger.info(f"使用相对路径的 7z 工具: {SEVEN_ZIP_EXE}")
                else:
                    logger.warning(f"未配置本地工具路径: {cmd[0]}")
            else:
                logger.warning(f"未处理的命令: {cmd[0]}")
        
        # 设置环境变量以确保使用正确的工具链
        clean_env['RUSTUP_HOME'] = RUSTUP_HOME
        clean_env['CARGO_HOME'] = CARGO_HOME
        clean_env['LOCAL_ENV_DIR'] = LOCAL_ENV_DIR
        
        # Windows特定设置
        if platform.system() == 'Windows':
            # 添加MinGW到环境变量
            if os.path.exists(MINGW_DIR):
                mingw_bin = os.path.join(MINGW_DIR, 'bin')
                # 只包含必要的路径，不包含系统PATH
                clean_env['PATH'] = mingw_bin
                # 添加Rust工具路径
                cargo_bin = os.path.join(CARGO_HOME, 'bin')
                if os.path.exists(cargo_bin):
                    clean_env['PATH'] += ';' + cargo_bin
        
        # 确保工作目录正确
        if cwd:
            cwd = get_normalized_path(cwd)
            # 确保工作目录存在
            if not os.path.exists(cwd):
                os.makedirs(cwd, exist_ok=True)
        
        command_str = ' '.join(cmd)
        logger.info(f"执行命令: {command_str}")
        if cwd:
            logger.info(f"工作目录: {cwd}")
        print(f"执行命令: {command_str}")
        if cwd:
            print(f"工作目录: {cwd}")
        
        # 使用清理后的环境变量，确保不使用系统PATH
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE if capture_output else None,
            stderr=subprocess.PIPE if capture_output else None,
            text=True,
            env=clean_env,  # 使用清理后的环境变量
            cwd=cwd
        )
        
        if capture_output:
            stdout, stderr = process.communicate()
            if process.returncode != 0:
                logger.error(f"命令执行失败: {command_str}")
                logger.error(f"错误输出: {stderr}")
            else:
                logger.info(f"命令执行成功: {command_str}")
            return process.returncode, stdout.strip(), stderr.strip()
        else:
            process.wait()
            if process.returncode != 0:
                logger.error(f"命令执行失败，返回码: {process.returncode}")
            else:
                logger.info(f"命令执行成功: {command_str}")
            return process.returncode, "", ""
    except Exception as e:
        error_msg = f"执行命令出错: {e}"
        logger.error(error_msg)
        logger.error(f"命令: {' '.join(cmd)}")
        if cwd:
            logger.error(f"工作目录: {cwd}")
        print(error_msg)
        print(f"命令: {' '.join(cmd)}")
        if cwd:
            print(f"工作目录: {cwd}")
        return -1, "", str(e)


def download_file(url, output_path):
    """
    下载文件到指定路径，并提供详细的进度反馈
    
    参数:
        url (str): 下载URL
        output_path (str): 输出文件路径
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 如果文件已存在，先删除
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
            logger.info(f"删除已存在的文件: {output_path}")
        except Exception as e:
            logger.warning(f"无法删除已存在的文件: {e}")
    
    def reporthook(count, block_size, total_size):
        if total_size > 0:
            percent = min(int(count * block_size * 100 / total_size), 100)
            downloaded_mb = (count * block_size) / (1024 * 1024)
            total_mb = total_size / (1024 * 1024)
            sys.stdout.write(f"\r下载中: {percent}% - {downloaded_mb:.1f} MB / {total_mb:.1f} MB ")
            sys.stdout.flush()
    
    file_name = os.path.basename(output_path)
    logger.info(f"开始下载 {file_name} 从 {url} 到 {output_path}")
    print(f"下载 {file_name} 从 {url}")
    
    try:
        start_time = time.time()
        urlretrieve(url, output_path, reporthook)
        elapsed_time = time.time() - start_time
        file_size = os.path.getsize(output_path) / (1024 * 1024) if os.path.exists(output_path) else 0
        speed_mb_s = file_size / elapsed_time if elapsed_time > 0 else 0
        
        print(f"\n下载完成")
        logger.info(f"下载完成: {file_name}, 大小: {file_size:.2f} MB, 耗时: {elapsed_time:.2f} 秒, 速度: {speed_mb_s:.2f} MB/s")
    except Exception as e:
        error_msg = f"下载失败: {e}"
        logger.error(error_msg)
        print(f"\n{error_msg}")
        # 清理下载失败的文件
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
                logger.info(f"删除下载失败的文件: {output_path}")
            except:
                pass
        raise


def install_seven_zip():
    """
    下载并安装7-Zip工具到本地环境，强制使用相对路径，不依赖系统PATH
    
    返回:
        bool: 安装是否成功
    """
    print("=== 步骤 0: 安装7-Zip工具到本地环境 ===")
    logger.info("开始安装7-Zip工具")
    
    # 检查7z工具是否已存在
    if os.path.exists(SEVEN_ZIP_EXE):
        logger.info(f"7-Zip工具已存在: {SEVEN_ZIP_EXE}")
        print(f"7-Zip 已安装在本地环境中: {SEVEN_ZIP_EXE}")
        return True
    
    # 创建7z目录
    os.makedirs(SEVEN_ZIP_DIR, exist_ok=True)
    
    # 多次尝试下载安装7-Zip便携版，不依赖系统工具
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            logger.info(f"尝试 {attempt}/{max_attempts}: 下载7-Zip便携版")
            print(f"尝试 {attempt}/{max_attempts}: 下载7-Zip便携版...")
            
            # 使用便携版7zr.exe
            SEVEN_ZIP_PORTABLE_URL = "https://www.7-zip.org/a/7zr.exe"
            SEVEN_ZIP_PORTABLE = get_normalized_path(os.path.join(SEVEN_ZIP_DIR, '7zr.exe'))
            
            # 确保下载目录存在
            os.makedirs(os.path.dirname(SEVEN_ZIP_PORTABLE), exist_ok=True)
            
            # 下载7zr.exe (便携版7-Zip)
            download_file(SEVEN_ZIP_PORTABLE_URL, SEVEN_ZIP_PORTABLE)
            
            # 检查下载是否成功且文件大小合理
            if os.path.exists(SEVEN_ZIP_PORTABLE) and os.path.getsize(SEVEN_ZIP_PORTABLE) > 100000:
                # 复制或重命名为7z.exe，确保脚本可以找到它
                if SEVEN_ZIP_PORTABLE != SEVEN_ZIP_EXE:
                    shutil.copy2(SEVEN_ZIP_PORTABLE, SEVEN_ZIP_EXE)
                    # 确保复制成功
                    if os.path.exists(SEVEN_ZIP_EXE):
                        logger.info(f"7-Zip便携版安装成功: {SEVEN_ZIP_EXE}")
                        print(f"7-Zip 便携版已成功安装到 {SEVEN_ZIP_DIR}")
                        # 设置可执行权限
                        if platform.system() != 'Windows':
                            os.chmod(SEVEN_ZIP_EXE, os.stat(SEVEN_ZIP_EXE).st_mode | stat.S_IEXEC)
                        return True
                else:
                    logger.warning(f"7-Zip便携版路径与目标路径相同: {SEVEN_ZIP_PORTABLE}")
            else:
                logger.error(f"7-Zip便携版下载失败或文件大小异常: {os.path.getsize(SEVEN_ZIP_PORTABLE) if os.path.exists(SEVEN_ZIP_PORTABLE) else '不存在'}")
                print("7-Zip便携版下载失败或文件大小异常")
                # 清理下载失败的文件
                if os.path.exists(SEVEN_ZIP_PORTABLE):
                    os.remove(SEVEN_ZIP_PORTABLE)
        except Exception as e:
            logger.error(f"安装7-Zip便携版出错: {e}")
            print(f"安装7-Zip便携版出错: {e}")
        
        # 如果不是最后一次尝试，等待一会再重试
        if attempt < max_attempts:
            wait_time = 5
            logger.info(f"等待 {wait_time} 秒后重试...")
            time.sleep(wait_time)
    
    # 如果主要方法失败，尝试使用备用URL
    try:
        logger.info("尝试使用备用URL下载7-Zip便携版")
        print("尝试使用备用URL下载7-Zip便携版...")
        SEVEN_ZIP_ALTERNATE_URL = "https://www.7-zip.org/a/7za.exe"  # 7za是另一个便携版本
        SEVEN_ZIP_ALTERNATE = get_normalized_path(os.path.join(SEVEN_ZIP_DIR, '7za.exe'))
        
        download_file(SEVEN_ZIP_ALTERNATE_URL, SEVEN_ZIP_ALTERNATE)
        
        if os.path.exists(SEVEN_ZIP_ALTERNATE):
            shutil.copy2(SEVEN_ZIP_ALTERNATE, SEVEN_ZIP_EXE)
            logger.info(f"7-Zip备用版本安装成功: {SEVEN_ZIP_EXE}")
            print(f"7-Zip 备用版本已成功安装到 {SEVEN_ZIP_DIR}")
            return True
    except Exception as e:
        logger.error(f"安装7-Zip备用版本出错: {e}")
        print(f"安装7-Zip备用版本出错: {e}")
    
    logger.error("所有7-Zip安装方法都失败了")
    print("所有7-Zip安装方法都失败了")
    return False


def extract_7z(archive_path, extract_dir):
    """
    解压7z文件，强制使用本地7z工具，不依赖系统PATH
    
    参数:
        archive_path (str): 7z文件路径
        extract_dir (str): 解压目录
    
    返回:
        bool: 解压是否成功
    """
    print(f"解压 {os.path.basename(archive_path)} 到 {extract_dir}")
    
    # 确保解压目录存在
    os.makedirs(extract_dir, exist_ok=True)
    
    # 强制使用本地7z工具，不使用系统PATH
    if os.path.exists(SEVEN_ZIP_EXE):
        print(f"使用本地7-Zip工具: {SEVEN_ZIP_EXE}")
        
        # 使用相对路径调用本地7z工具
        cmd = [SEVEN_ZIP_EXE, 'x', archive_path, f'-o{extract_dir}', '-y']
        
        # 使用干净的环境变量，确保不使用系统PATH
        clean_env = {}
        if platform.system() == 'Windows':
            clean_env['TEMP'] = os.environ.get('TEMP', os.path.join(LOCAL_ENV_DIR, 'temp'))
            clean_env['TMP'] = os.environ.get('TMP', os.path.join(LOCAL_ENV_DIR, 'temp'))
            # 添加7z所在目录到PATH，确保可以找到相关DLL
            clean_env['PATH'] = os.path.dirname(SEVEN_ZIP_EXE)
        else:
            clean_env['HOME'] = os.environ.get('HOME', '/tmp')
            clean_env['PATH'] = os.path.dirname(SEVEN_ZIP_EXE)
        
        # 多次尝试解压，确保可靠性
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            print(f"尝试 {attempt}/{max_attempts}: 使用本地7z解压...")
            code, stdout, stderr = run_command(cmd, env=clean_env, capture_output=True)
            
            if code == 0:
                print("使用本地7-Zip工具解压成功")
                return True
            else:
                print(f"本地7-Zip工具解压失败 (尝试 {attempt}/{max_attempts}): {stderr}")
                # 如果不是最后一次尝试，等待一会再重试
                if attempt < max_attempts:
                    wait_time = 3
                    print(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
    else:
        print(f"错误: 本地7-Zip工具不存在: {SEVEN_ZIP_EXE}")
        # 尝试重新安装7-Zip
        print("尝试重新安装7-Zip工具...")
        if install_seven_zip():
            # 安装成功后重新尝试解压
            return extract_7z(archive_path, extract_dir)
    
    # 如果本地7z工具失败，尝试使用Python的py7zr库作为备选
    print("本地7-Zip工具失败，尝试使用py7zr库解压...")
    try:
        # 使用相对路径调用Python的pip安装py7zr
        print("使用相对路径安装py7zr库...")
        # 使用sys.executable确保调用正确的Python解释器
        install_cmd = [sys.executable, "-m", "pip", "install", "py7zr"]
        # 使用干净的环境
        code, stdout, stderr = run_command(install_cmd, capture_output=True)
        
        if code != 0:
            print(f"安装py7zr库失败: {stderr}")
            return False
        
        # 尝试导入并使用py7zr
        import py7zr
        print("使用py7zr库解压...")
        with py7zr.SevenZipFile(archive_path, 'r') as z:
            z.extractall(extract_dir)
        print("使用py7zr库解压成功")
        return True
    except Exception as e:
        print(f"使用py7zr库解压失败: {e}")
        return False
    
    return False


def install_mingw():
    """
    安装MinGW64到本地环境，使用相对路径，不依赖系统PATH
    
    返回:
        bool: 安装是否成功
    """
    # 验证目录是否已存在且包含必要文件
    if os.path.exists(MINGW_DIR) and os.path.exists(os.path.join(MINGW_DIR, 'bin', 'gcc.exe')):
        print(f"MinGW64 已安装在本地环境中: {MINGW_DIR}")
        return True
    
    print("=== 步骤 1: 安装MinGW64到本地环境 ===")
    
    # 确保本地环境目录存在
    try:
        os.makedirs(LOCAL_ENV_DIR, exist_ok=True)
        print(f"确保本地环境目录存在: {LOCAL_ENV_DIR}")
    except Exception as e:
        print(f"错误: 无法创建本地环境目录: {e}")
        return False
    
    # 清理旧的安装目录（如果存在）
    if os.path.exists(MINGW_DIR):
        print(f"清理旧的MinGW安装: {MINGW_DIR}")
        try:
            shutil.rmtree(MINGW_DIR)
        except Exception as e:
            print(f"警告: 无法删除旧的MinGW目录: {e}")
    
    # 下载MinGW64，带重试机制
    max_download_attempts = 3
    for attempt in range(1, max_download_attempts + 1):
        if os.path.exists(MINGW_ARCHIVE):
            # 检查文件大小是否合理
            if os.path.getsize(MINGW_ARCHIVE) > 100 * 1024 * 1024:  # 大于100MB
                print(f"MinGW64 安装包已存在: {os.path.basename(MINGW_ARCHIVE)}")
                break
            else:
                print(f"MinGW64 安装包存在但大小异常，重新下载...")
                try:
                    os.remove(MINGW_ARCHIVE)
                except:
                    pass
        
        print(f"尝试 {attempt}/{max_download_attempts}: 下载MinGW64...")
        try:
            download_file(MINGW_URL, MINGW_ARCHIVE)
            # 验证下载是否成功
            if os.path.exists(MINGW_ARCHIVE) and os.path.getsize(MINGW_ARCHIVE) > 100 * 1024 * 1024:
                print(f"MinGW64 下载成功: {os.path.basename(MINGW_ARCHIVE)}")
                break
        except Exception as e:
            print(f"MinGW64 下载失败 (尝试 {attempt}/{max_download_attempts}): {e}")
        
        if attempt < max_download_attempts:
            wait_time = 5
            print(f"等待 {wait_time} 秒后重试...")
            time.sleep(wait_time)
    
    # 验证下载是否成功
    if not os.path.exists(MINGW_ARCHIVE):
        print("错误: MinGW64 下载失败")
        return False
    
    # 解压MinGW64
    temp_extract_dir = os.path.join(LOCAL_ENV_DIR, 'temp_mingw')
    
    # 清理临时目录
    if os.path.exists(temp_extract_dir):
        print(f"清理临时解压目录: {temp_extract_dir}")
        try:
            shutil.rmtree(temp_extract_dir)
        except Exception as e:
            print(f"警告: 无法清理临时目录: {e}")
    
    # 创建临时目录
    try:
        os.makedirs(temp_extract_dir, exist_ok=True)
    except Exception as e:
        print(f"错误: 无法创建临时解压目录: {e}")
        return False
    
    print("解压MinGW64安装包...")
    if extract_7z(MINGW_ARCHIVE, temp_extract_dir):
        # 查找解压后的mingw64目录
        extracted_mingw = os.path.join(temp_extract_dir, 'mingw64')
        
        # 如果直接找不到，尝试查找子目录中的mingw64
        if not os.path.exists(extracted_mingw):
            print("在临时目录中直接找不到mingw64，尝试查找子目录...")
            for root, dirs, files in os.walk(temp_extract_dir):
                if 'mingw64' in dirs:
                    extracted_mingw = os.path.join(root, 'mingw64')
                    break
        
        if os.path.exists(extracted_mingw):
            print(f"找到解压后的mingw64目录: {extracted_mingw}")
            # 确保目标目录不存在
            if os.path.exists(MINGW_DIR):
                try:
                    shutil.rmtree(MINGW_DIR)
                except Exception as e:
                    print(f"警告: 无法删除目标目录: {e}")
            
            # 移动mingw64目录
            try:
                shutil.move(extracted_mingw, MINGW_DIR)
                print(f"MinGW64 已移动到目标位置: {MINGW_DIR}")
                
                # 验证安装
                if os.path.exists(os.path.join(MINGW_DIR, 'bin', 'gcc.exe')):
                    print(f"MinGW64 安装验证成功: gcc.exe 存在")
                    # 清理临时目录
                    try:
                        shutil.rmtree(temp_extract_dir)
                        print(f"临时目录已清理: {temp_extract_dir}")
                    except Exception as e:
                        print(f"警告: 无法清理临时目录: {e}")
                    return True
                else:
                    print("错误: MinGW64 安装验证失败，未找到gcc.exe")
            except Exception as e:
                print(f"错误: 无法移动mingw64目录: {e}")
        else:
            print("错误: 在解压目录中未找到mingw64文件夹")
    else:
        print("错误: MinGW64 解压失败")
    
    # 清理失败的安装
    if os.path.exists(temp_extract_dir):
        try:
            shutil.rmtree(temp_extract_dir)
        except:
            pass
    
    print("MinGW64 安装失败")
    return False


"""
安装Rust到本地环境，确保使用相对路径并创建干净的环境

此函数确保：
1. 所有操作都在本地环境目录中进行，不依赖系统PATH
2. 使用相对路径调用程序，避免错误调用系统程序
3. 创建干净的环境变量，仅包含必要的配置

返回:
    bool: 安装成功返回True，失败返回False
"""
def install_rust():
    # 验证必要的目录存在
    if not os.path.isdir(sCRIPT_DIR):
        print(f"错误: 脚本目录不存在: {sCRIPT_DIR}")
        return False
    
    if not os.path.isdir(LOCAL_ENV_DIR):
        try:
            os.makedirs(LOCAL_ENV_DIR, exist_ok=True)
            print(f"已创建本地环境目录: {LOCAL_ENV_DIR}")
        except Exception as e:
            print(f"错误: 无法创建本地环境目录: {e}")
            return False
    
    # 检查Rust是否已安装
    if os.path.exists(CARGO_HOME) and os.path.exists(RUSTUP_HOME):
        print("Rust 已安装在本地环境中")
        return True
    
    print("=== 步骤 2: 安装Rust到本地环境 ===")
    
    # 创建干净的环境变量字典，不继承系统PATH，仅设置必要的环境变量
    # 这样可以避免调用到系统中已安装的Rust工具
    env = {
        'CARGO_HOME': CARGO_HOME,
        'RUSTUP_HOME': RUSTUP_HOME,
        # 保留一些必要的系统变量以确保基本功能
        'SYSTEMROOT': os.environ.get('SYSTEMROOT', ''),
        'WINDIR': os.environ.get('WINDIR', ''),
        # 设置临时目录
        'TEMP': os.environ.get('TEMP', os.path.join(LOCAL_ENV_DIR, 'temp')),
        'TMP': os.environ.get('TMP', os.path.join(LOCAL_ENV_DIR, 'temp'))
    }
    
    # 创建临时目录
    temp_dir = env['TEMP']
    os.makedirs(temp_dir, exist_ok=True)
    
    # 确保目标安装目录存在
    os.makedirs(RUST_DIR, exist_ok=True)
    
    if platform.system() == 'Windows':
        # Windows安装 - 使用相对路径调用rustup-init.exe
        rustup_rel_path = os.path.relpath(RUSTUP_EXE, sCRIPT_DIR)
        print(f"准备使用相对路径安装Rust: {rustup_rel_path}")
        
        if not os.path.exists(RUSTUP_EXE):
            print(f"下载rustup-init.exe到: {RUSTUP_EXE}")
            download_file(RUSTUP_URL, RUSTUP_EXE)
        
        # 静默安装，强制使用GNU工具链，不安装MSVC工具链
        # 使用绝对路径确保在任何工作目录下都能正确执行
        # --default-host参数强制使用GNU目标架构，避免安装MSVC工具链
        cmd = [RUSTUP_EXE, '-y', '--default-toolchain', 'stable-x86_64-pc-windows-gnu', '--default-host', 'x86_64-pc-windows-gnu', '--profile', 'minimal']
        print(f"执行安装命令: {' '.join(cmd)}")
        
        # 使用指定的环境变量运行命令，不继承系统PATH
        code, stdout, stderr = run_command(cmd, env=env, cwd=sCRIPT_DIR)
        
        if code != 0:
            print(f"Rust安装失败: {stderr}")
            # 清理失败的安装
            if os.path.exists(RUST_DIR):
                try:
                    shutil.rmtree(RUST_DIR)
                    print("已清理失败的安装目录")
                except Exception as e:
                    print(f"警告: 无法清理失败的安装目录: {e}")
            return False
    else:
        # Linux/macOS安装 - 使用相对路径
        rustup_rel_path = os.path.relpath(RUSTUP_SCRIPT, sCRIPT_DIR)
        print(f"准备使用相对路径安装Rust: {rustup_rel_path}")
        
        if not os.path.exists(RUSTUP_SCRIPT):
            print(f"下载rustup-init.sh到: {RUSTUP_SCRIPT}")
            download_file(RUSTUP_URL, RUSTUP_SCRIPT)
            # 给脚本添加执行权限
            try:
                st = os.stat(RUSTUP_SCRIPT)
                os.chmod(RUSTUP_SCRIPT, st.st_mode | stat.S_IEXEC)
                print("已添加执行权限")
            except Exception as e:
                print(f"错误: 无法添加执行权限: {e}")
                return False
        
        # 静默安装
        # 使用绝对路径确保在任何工作目录下都能正确执行
        cmd = ['sh', RUSTUP_SCRIPT, '-y', '--default-toolchain', 'stable', '--profile', 'minimal']
        print(f"执行安装命令: {' '.join(cmd)}")
        
        # 使用指定的环境变量运行命令，不继承系统PATH
        code, stdout, stderr = run_command(cmd, env=env, cwd=sCRIPT_DIR)
        
        if code != 0:
            print(f"Rust安装失败: {stderr}")
            # 清理失败的安装
            if os.path.exists(RUST_DIR):
                try:
                    shutil.rmtree(RUST_DIR)
                    print("已清理失败的安装目录")
                except Exception as e:
                    print(f"警告: 无法清理失败的安装目录: {e}")
            return False
    
    # 验证安装是否成功
    if os.path.exists(CARGO_HOME) and os.path.exists(RUSTUP_HOME):
        print("Rust 已成功安装到本地环境")
        # 输出安装信息，确认使用的是本地环境
        print(f"安装位置: {RUST_DIR}")
        print(f"Cargo home: {CARGO_HOME}")
        print(f"Rustup home: {RUSTUP_HOME}")
        return True
    else:
        print("错误: Rust安装似乎已完成，但必要的目录不存在")
        return False


def setup_gnu_toolchain():
    """
    配置GNU工具链，确保完全使用本地环境
    
    返回:
        tuple: (target_triple, env)
    """
    print("=== 步骤 3: 配置GNU工具链 ===")
    
    # 创建一个几乎空的环境变量字典，只保留必要的系统变量
    env = {}
    # 保留一些必要的系统环境变量
    for var in ['SYSTEMROOT', 'TEMP', 'TMP', 'USERPROFILE']:
        if var in os.environ:
            env[var] = os.environ[var]
    
    # 设置本地环境变量
    env['CARGO_HOME'] = CARGO_HOME
    env['RUSTUP_HOME'] = RUSTUP_HOME
    env['RUST_BACKTRACE'] = '1'  # 启用详细的错误回溯
    
    # 构建新的PATH，优先使用本地工具
    new_path = []
    cargo_bin = os.path.join(CARGO_HOME, 'bin')
    if os.path.exists(cargo_bin):
        new_path.append(cargo_bin)
    
    # 根据操作系统确定目标三元组和添加MinGW
    if platform.system() == 'Windows':
        target_triple = 'x86_64-pc-windows-gnu'
        mingw_bin = os.path.join(MINGW_DIR, 'bin')
        if os.path.exists(mingw_bin):
            new_path.append(mingw_bin)
        # 添加Windows系统目录
        if 'SYSTEMROOT' in env:
            new_path.append(os.path.join(env['SYSTEMROOT'], 'System32'))
    elif platform.system() == 'Darwin':
        target_triple = 'x86_64-apple-darwin'  # 或 aarch64-apple-darwin
        # macOS的系统路径
        new_path.extend(['/usr/local/bin', '/usr/bin', '/bin'])
    else:  # Linux
        target_triple = 'x86_64-unknown-linux-gnu'
        # Linux的系统路径
        new_path.extend(['/usr/local/bin', '/usr/bin', '/bin'])
    
    # 设置PATH
    path_separator = ';' if platform.system() == 'Windows' else ':'
    env['PATH'] = path_separator.join(new_path)
    
    print(f"目标三元组: {target_triple}")
    print(f"使用本地PATH: {env['PATH']}")
    
    # 检查并安装目标工具链
    if os.path.exists(os.path.join(cargo_bin, 'rustup')):
        # 检查是否已安装gnu工具链
        cmd = ['rustup', 'show']
        code, stdout, stderr = run_command(cmd, env=env, capture_output=True)
        
        if target_triple not in stdout:
            print(f"安装 {target_triple} 工具链...")
            cmd = ['rustup', 'target', 'add', target_triple]
            code, stdout, stderr = run_command(cmd, env=env)
            
            if code != 0:
                print(f"工具链安装失败: {stderr}")
                # 即使失败也继续，后面可以通过cargo配置文件指定目标
    else:
        print("警告: 未找到本地rustup，将尝试使用Cargo配置文件指定目标")
    
    return target_triple, env


def create_cargo_config(target_triple):
    """
    创建Cargo配置文件，确保路径引用正确
    
    参数:
        target_triple (str): 目标三元组
    """
    print("=== 步骤 4: 创建Cargo配置文件 ===")
    
    try:
        # 在项目根目录创建.cargo目录
        cargo_config_dir = get_normalized_path(os.path.join(PROJECT_ROOT, '.cargo'))
        print(f"创建Cargo配置目录: {cargo_config_dir}")
        os.makedirs(cargo_config_dir, exist_ok=True)
        
        # 创建配置文件
        config_content = f"""
[build]
target = "{target_triple}"
"""
        
        # 配置目标特定设置
        if platform.system() == 'Windows' and target_triple == 'x86_64-pc-windows-gnu':
            # Windows平台且目标为x86_64-pc-windows-gnu时，创建一个包含所有设置的配置块
            mingw_gcc = get_normalized_path(os.path.join(MINGW_DIR, 'bin', 'gcc.exe'))
            # 在配置文件中使用正斜杠，Rust/Cargo能正确处理
            mingw_gcc_config = mingw_gcc.replace('\\', '/')
            config_content += f"""

# 静态链接CRT，避免依赖系统DLL
[target.x86_64-pc-windows-gnu]
linker = "gcc"
rustflags = [
    "-C", "target-feature=+crt-static",
    "-C", "linker={mingw_gcc_config}"
]
""".format(mingw_gcc_config=mingw_gcc_config)
        else:
            # 其他平台或目标，使用通用配置
            config_content += f"""

[target.{target_triple}]
linker = "gcc"
"""
            # 如果是Windows但目标不是x86_64-pc-windows-gnu，添加mingw路径
            if platform.system() == 'Windows':
                mingw_gcc = get_normalized_path(os.path.join(MINGW_DIR, 'bin', 'gcc.exe'))
                mingw_gcc_config = mingw_gcc.replace('\\', '/')
                config_content += f"\nrustflags = ['-C', 'linker={mingw_gcc_config}']\n"
        
        config_path = get_normalized_path(os.path.join(cargo_config_dir, 'config'))
        print(f"写入Cargo配置文件: {config_path}")
        
        # 确保目录存在并有权限写入
        if not os.access(cargo_config_dir, os.W_OK):
            print(f"警告: 没有权限写入目录: {cargo_config_dir}")
            print("尝试以管理员权限运行脚本")
        
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content.strip())
        
        print(f"Cargo配置文件已创建: {config_path}")
        print(f"配置内容:\n{config_content.strip()}")
        
        return True
    except Exception as e:
        print(f"创建Cargo配置文件失败: {e}")
        # 尝试创建简化版本的配置文件
        try:
            simple_config = f"""
[build]
target = "{target_triple}"
"""
            config_path = get_normalized_path(os.path.join(cargo_config_dir, 'config'))
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(simple_config.strip())
            print(f"已创建简化版Cargo配置文件: {config_path}")
            return True
        except:
            print("创建简化版配置文件也失败")
            return False


def copy_external_components(build_dir):
    """
    复制外部组件到构建输出目录的sqfs_for_win子目录
    特别确保包含LZMA压缩支持的squashfs工具被正确复制
    
    参数:
        build_dir (str): 构建输出目录路径
    
    返回:
        bool: 复制是否成功
    """
    print("=== 复制外部组件 ===")
    
    # 定义外部组件源目录
    sqfs_source_dir = get_normalized_path(os.path.join(PROJECT_ROOT, 'dependencies', 'sqfs_for_win'))
    
    # 定义目标目录为build_dir下的sqfs_for_win子目录
    sqfs_target_dir = get_normalized_path(os.path.join(build_dir, 'sqfs_for_win'))
    
    # 关键工具列表，确保这些工具被复制（尤其是支持LZMA的squashfs工具）
    critical_tools = ['unsquashfs.exe', 'mksquashfs.exe']
    tools_found = 0
    
    if not os.path.exists(sqfs_source_dir):
        print(f"警告: 未找到外部组件目录: {sqfs_source_dir}")
        return False
    
    try:
        # 复制sqfs_for_win目录下的所有文件到构建输出目录的sqfs_for_win子目录
        print(f"正在从 {sqfs_source_dir} 复制文件到 {sqfs_target_dir}")
        
        # 确保目标目录存在
        os.makedirs(sqfs_target_dir, exist_ok=True)
        
        # 遍历源目录中的所有文件
        for item in os.listdir(sqfs_source_dir):
            source_path = os.path.join(sqfs_source_dir, item)
            target_path = os.path.join(sqfs_target_dir, item)
            
            # 复制文件
            if os.path.isfile(source_path):
                shutil.copy2(source_path, target_path)
                print(f"✅ 已复制: sqfs_for_win\\{item}")
                
                # 检查关键工具是否已复制
                if item.lower() in [tool.lower() for tool in critical_tools]:
                    tools_found += 1
            elif os.path.isdir(source_path):
                # 如果是子目录，也复制
                if os.path.exists(target_path):
                    shutil.rmtree(target_path)
                shutil.copytree(source_path, target_path)
                print(f"✅ 已复制目录: sqfs_for_win\\{item}")
        
        # 检查是否所有关键工具都已复制
        if tools_found < len(critical_tools):
            print(f"⚠️  警告: 未找到所有关键squashfs工具。期望的工具: {', '.join(critical_tools)}")
            print(f"已找到的工具数量: {tools_found}")
            print("请确保使用的squashfs工具支持LZMA压缩格式")
        else:
            print(f"✅ 所有关键squashfs工具已成功复制，确保支持LZMA压缩格式")
            
        print("外部组件复制完成！")
        return True
    except Exception as e:
        print(f"❌ 复制外部组件时出错: {e}")
        return False

def build_project(env):
    """
    构建项目，确保使用本地环境
    
    参数:
        env (dict): 环境变量
    """
    print("=== 步骤 5: 构建项目 ===")
    print(f"项目根目录: {PROJECT_ROOT}")
    
    # 确保cargo存在于本地环境
    cargo_path = os.path.join(CARGO_HOME, 'bin', 'cargo')
    if platform.system() == 'Windows':
        cargo_path += '.exe'
    
    if not os.path.exists(cargo_path):
        print(f"错误: 未找到本地cargo: {cargo_path}")
        print("请确保Rust安装成功")
        return False
    
    print(f"使用本地cargo: {cargo_path}")
    
    # 清理之前的构建
    print("清理之前的构建...")
    build_dir = os.path.join(PROJECT_ROOT, 'target')
    if os.path.exists(build_dir):
        try:
            shutil.rmtree(build_dir)
            print("手动清理构建目录成功")
        except Exception as e:
            print(f"手动清理失败: {e}")
    
    # 构建项目
    print("开始构建项目...")
    cmd = [cargo_path, 'build', '--verbose']
    
    try:
        # 再次确保环境变量正确设置
        local_env = env.copy()
        # 确保不使用系统的.cargo目录
        if 'HOME' in local_env:
            del local_env['HOME']
        if 'USERPROFILE' in local_env:
            del local_env['USERPROFILE']
        # 明确设置CARGO_HOME和RUSTUP_HOME为本地环境路径
        local_env['CARGO_HOME'] = CARGO_HOME
        local_env['RUSTUP_HOME'] = RUSTUP_HOME
        
        # 设置工作目录为项目根目录
        os.chdir(PROJECT_ROOT)
        
        # 添加encoding参数解决编码错误
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            env=local_env
        )
        
        # 实时输出构建进度
        print("\n构建输出:")
        print("----------------------------------------")
        for line in process.stdout:
            try:
                # 过滤掉可能暴露系统路径的信息
                home_path = os.environ.get('HOME', '')
                userprofile_path = os.environ.get('USERPROFILE', '')
                if home_path and home_path in line or userprofile_path and userprofile_path in line:
                    line = "[系统路径已过滤]"
                print(line.strip())
            except UnicodeDecodeError:
                # 如果遇到编码错误，尝试用替换模式解码
                print("[编码错误: 无法显示此行输出]")
        
        process.wait()
        
        # 恢复工作目录
        os.chdir(sCRIPT_DIR)
        
        if process.returncode == 0:
            print("----------------------------------------")
            print("\n构建成功！")
            
            # 获取目标三元组以确定构建输出目录
            target_triple = setup_gnu_toolchain()[0]  # 调用函数获取目标三元组
            build_dir = os.path.join(PROJECT_ROOT, 'target', target_triple, 'debug')
            
            # 复制外部组件到构建输出目录
            copy_external_components(build_dir)
            
            return True
        else:
            print("----------------------------------------")
            print("\n构建失败！")
            return False
    except Exception as e:
        print(f"构建过程出错: {e}")
        # 恢复工作目录
        os.chdir(sCRIPT_DIR)
        return False


def main():
    """
    主函数，确保完全使用本地构建环境
    """
    print("========================================")
    print("Binwalk 本地环境构建脚本")
    print("========================================")
    print(f"当前系统: {platform.system()}")
    print(f"脚本目录: {sCRIPT_DIR}")
    print(f"本地环境目录: {LOCAL_ENV_DIR}")
    print(f"项目根目录: {PROJECT_ROOT}")
    print("========================================")
    print("注意: 此脚本将在builder目录下创建隔离的构建环境")
    print("完全不依赖系统中已安装的MinGW64、7-Zip和Rust环境")
    print("========================================")
    
    # 创建本地环境目录
    os.makedirs(LOCAL_ENV_DIR, exist_ok=True)
    
    # 安装本地7-Zip工具（用于解压其他组件）
    seven_zip_success = install_seven_zip()
    if not seven_zip_success:
        print("⚠️  7-Zip工具安装失败，将使用Python库作为备选")
    
    # 安装本地MinGW64（仅Windows需要）
    mingw_success = True
    if platform.system() == 'Windows':
        mingw_success = install_mingw()
        if not mingw_success:
            print("⚠️  MinGW64 安装失败，将使用Cargo配置强制指定链接器")
            # 尝试使用系统7z解压
            if os.path.exists(MINGW_ARCHIVE):
                print(f"请手动解压 mingw64.7z 到 {os.path.join(LOCAL_ENV_DIR, 'mingw64')}")
    
    # 安装本地Rust
    rust_success = install_rust()
    if not rust_success:
        print("⚠️  Rust 安装失败，这会导致构建失败")
        print("请检查网络连接和权限")
    
    # 配置GNU工具链
    target_triple, env = setup_gnu_toolchain()
    
    # 检查是否存在config.toml文件
    cargo_config_dir = get_normalized_path(os.path.join(PROJECT_ROOT, '.cargo'))
    config_toml_path = get_normalized_path(os.path.join(cargo_config_dir, 'config.toml'))
    config_path = get_normalized_path(os.path.join(cargo_config_dir, 'config'))
    
    if os.path.exists(config_toml_path):
        # 如果config.toml已存在，则跳过创建config文件，避免冲突
        print(f"⚠️  检测到.cargo/config.toml已存在，将跳过创建.cargo/config文件以避免冲突")
        # 如果config文件已存在，则删除它
        if os.path.exists(config_path):
            try:
                os.remove(config_path)
                print(f"✅ 已删除冲突的.cargo/config文件")
            except Exception as e:
                print(f"❌ 无法删除冲突的.cargo/config文件: {e}")
    else:
        # 如果config.toml不存在，则创建config文件
        print("创建Cargo配置，即使MinGW安装失败也要强制设置")
        create_cargo_config(target_triple)
    
    # 如果所有依赖都安装成功，执行构建
    if rust_success:
        success = build_project(env)
    else:
        success = False
        print("❌ 跳过构建，因为Rust安装失败")
    
    # 显示构建结果
    print("========================================")
    if success:
        print("🎉 构建成功！")
        # 显示构建输出路径
        build_dir = os.path.join(PROJECT_ROOT, 'target', target_triple, 'debug')
        print(f"构建输出目录: {build_dir}")
        print("\n使用说明:")
        print(f"1. 构建的可执行文件位于: {build_dir}")
        print(f"2. 外部组件（unsquashfs.exe等）已复制到构建输出目录")
        print("3. 所有构建依赖都隔离在 builder/local_env 目录中")
        print("4. 要清理构建环境，删除 builder/local_env 目录即可")
    else:
        print("❌ 构建失败！")
        # 提供详细的排查建议
        print("\n排查建议:")
        print("1. 检查网络连接，确保能下载依赖")
        print("2. 确保磁盘有足够空间（至少需要2GB）")
        if not seven_zip_success:
            print("3. 手动安装py7zr库:")
            print("   - 运行: pip install py7zr")
        if platform.system() == 'Windows' and not mingw_success:
            print("4. 手动下载并解压MinGW64:")
            print(f"   - 下载链接: {MINGW_URL}")
            print(f"   - 解压到: {os.path.join(LOCAL_ENV_DIR, 'mingw64')}")
        if not rust_success:
            print("5. 手动安装Rust到本地环境:")
            print(f"   - 设置环境变量 CARGO_HOME={CARGO_HOME}")
            print(f"   - 设置环境变量 RUSTUP_HOME={RUSTUP_HOME}")
            print("   - 运行 rustup-init 安装")
        print("6. 检查是否有足够权限写入 builder/local_env 目录")
    print("========================================")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n构建被用户中断")
    finally:
        # 在Windows上，让命令窗口保持打开状态
        if platform.system() == 'Windows':
            print("\n按Enter键退出...")
            input()