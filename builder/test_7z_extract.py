#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
7-Zip 解压功能测试脚本

此脚本用于测试build.py中的7z解压功能，验证本地7z工具的安装和使用。
"""

import os
import sys
import shutil
import tempfile
import subprocess

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # 导入build.py中的相关函数和变量
    from build import (
        get_normalized_path,
        download_file,
        install_seven_zip,
        extract_7z,
        SEVEN_ZIP_EXE,
        SEVEN_ZIP_DIR,
        LOCAL_ENV_DIR
    )
    
    print("成功导入build.py中的函数和变量")
except ImportError as e:
    print(f"导入失败: {e}")
    print("请确保此脚本位于builder目录中，并且build.py文件存在")
    sys.exit(1)

def create_test_archive():
    """
    创建一个测试用的7z文件（使用Python库）
    """
    try:
        import py7zr
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        test_file_path = os.path.join(temp_dir, 'test_file.txt')
        
        # 创建测试文件
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write("This is a test file for 7z extraction.")
        
        # 创建7z归档文件
        archive_path = os.path.join(temp_dir, 'test_archive.7z')
        with py7zr.SevenZipFile(archive_path, 'w') as z:
            z.write(test_file_path, 'test_file.txt')
        
        print(f"创建测试归档文件: {archive_path}")
        return archive_path, temp_dir
    except Exception as e:
        print(f"创建测试归档失败: {e}")
        return None, None

def test_local_seven_zip_installation():
    """
    测试本地7-Zip工具的安装
    """
    print("\n=== 测试本地7-Zip工具安装 ===")
    
    # 尝试安装7-Zip
    success = install_seven_zip()
    
    if success:
        print(f"✅ 7-Zip工具安装成功: {SEVEN_ZIP_EXE}")
        # 验证文件存在
        if os.path.exists(SEVEN_ZIP_EXE):
            print(f"✅ 7z.exe文件存在: {SEVEN_ZIP_EXE}")
            # 尝试运行版本命令
            try:
                result = subprocess.run([SEVEN_ZIP_EXE, '--help'], 
                                      capture_output=True, text=True)
                if "7-Zip" in result.stdout:
                    print("✅ 7-Zip工具可以正常运行")
                    return True
                else:
                    print("❌ 7-Zip工具运行异常")
            except Exception as e:
                print(f"❌ 运行7-Zip工具出错: {e}")
        else:
            print(f"❌ 7z.exe文件不存在: {SEVEN_ZIP_EXE}")
    else:
        print("❌ 7-Zip工具安装失败")
    
    return False

def test_extraction_with_local_7z(archive_path):
    """
    测试使用本地7-Zip工具解压
    """
    print("\n=== 测试使用本地7-Zip工具解压 ===")
    
    if not os.path.exists(SEVEN_ZIP_EXE):
        print("❌ 本地7-Zip工具不存在，跳过此测试")
        return False
    
    # 创建临时解压目录
    extract_dir = tempfile.mkdtemp()
    
    try:
        # 使用build.py中的extract_7z函数
        success = extract_7z(archive_path, extract_dir)
        
        if success:
            # 验证解压结果
            test_file = os.path.join(extract_dir, 'test_file.txt')
            if os.path.exists(test_file):
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                if "This is a test file for 7z extraction." in content:
                    print("✅ 使用本地7-Zip工具解压成功")
                    return True
                else:
                    print("❌ 解压的文件内容不正确")
            else:
                print(f"❌ 解压的文件不存在: {test_file}")
        else:
            print("❌ 使用本地7-Zip工具解压失败")
    except Exception as e:
        print(f"❌ 解压过程出错: {e}")
    finally:
        # 清理临时目录
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
    
    return False

def test_extraction_with_py7zr(archive_path):
    """
    测试使用py7zr库解压（备选方法）
    """
    print("\n=== 测试使用py7zr库解压 ===")
    
    # 创建临时解压目录
    extract_dir = tempfile.mkdtemp()
    
    try:
        # 强制使用py7zr库（临时重命名SEVEN_ZIP_EXE以模拟失败）
        original_seven_zip_exe = SEVEN_ZIP_EXE
        temp_rename = SEVEN_ZIP_EXE + '.tmp'
        
        if os.path.exists(SEVEN_ZIP_EXE):
            os.rename(SEVEN_ZIP_EXE, temp_rename)
            
        try:
            # 使用build.py中的extract_7z函数
            success = extract_7z(archive_path, extract_dir)
            
            if success:
                # 验证解压结果
                test_file = os.path.join(extract_dir, 'test_file.txt')
                if os.path.exists(test_file):
                    with open(test_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if "This is a test file for 7z extraction." in content:
                        print("✅ 使用py7zr库解压成功（备选方法工作正常）")
                        return True
                    else:
                        print("❌ 解压的文件内容不正确")
                else:
                    print(f"❌ 解压的文件不存在: {test_file}")
            else:
                print("❌ 使用py7zr库解压失败")
        finally:
            # 恢复7z.exe文件名
            if os.path.exists(temp_rename):
                os.rename(temp_rename, original_seven_zip_exe)
                
    except Exception as e:
        print(f"❌ 解压过程出错: {e}")
    finally:
        # 清理临时目录
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
    
    return False

def download_sample_7z():
    """
    下载一个示例7z文件进行测试
    """
    print("\n=== 下载示例7z文件进行测试 ===")
    
    # 使用一个小型的7z示例文件
    sample_url = "https://github.com/itchyny/gojq/releases/download/v0.12.12/gojq_v0.12.12_windows_amd64.zip"
    # 注意：这里使用zip文件作为替代，因为直接找小型7z示例可能有限制
    # 实际测试中，我们可以使用创建的测试归档
    
    sample_path = os.path.join(LOCAL_ENV_DIR, 'sample_archive.zip')
    
    try:
        download_file(sample_url, sample_path)
        print(f"✅ 示例文件下载成功: {sample_path}")
        return sample_path
    except Exception as e:
        print(f"❌ 示例文件下载失败: {e}")
        return None

def main():
    """
    主测试函数
    """
    print("========================================")
    print("Binwalk 7-Zip 功能测试脚本")
    print("========================================")
    print(f"脚本目录: {os.path.dirname(os.path.abspath(__file__))}")
    print(f"本地环境目录: {LOCAL_ENV_DIR}")
    print("========================================")
    
    # 确保LOCAL_ENV_DIR存在
    os.makedirs(LOCAL_ENV_DIR, exist_ok=True)
    
    # 测试1: 本地7-Zip工具安装
    seven_zip_installed = test_local_seven_zip_installation()
    
    # 创建测试归档
    print("\n=== 创建测试归档文件 ===")
    test_archive, temp_dir = create_test_archive()
    
    if not test_archive:
        print("❌ 无法创建测试归档，测试中止")
        sys.exit(1)
    
    try:
        # 测试2: 使用本地7-Zip解压
        if seven_zip_installed:
            local_7z_test = test_extraction_with_local_7z(test_archive)
        else:
            local_7z_test = False
            print("⚠️  跳过本地7-Zip测试，因为7-Zip未安装成功")
        
        # 测试3: 使用py7zr库解压（备选方法）
        py7zr_test = test_extraction_with_py7zr(test_archive)
        
        # 综合测试结果
        print("\n========================================")
        print("测试结果汇总:")
        print(f"1. 本地7-Zip安装: {'✅ 成功' if seven_zip_installed else '❌ 失败'}")
        print(f"2. 本地7-Zip解压: {'✅ 成功' if local_7z_test else '❌ 失败'}")
        print(f"3. py7zr库解压: {'✅ 成功' if py7zr_test else '❌ 失败'}")
        print("========================================")
        
        # 至少有一个解压方法成功即为通过
        if local_7z_test or py7zr_test:
            print("🎉 测试通过！至少有一个解压方法工作正常")
            return 0
        else:
            print("❌ 测试失败！所有解压方法都失败了")
            return 1
            
    finally:
        # 清理临时文件
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"\n清理临时目录: {temp_dir}")

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)