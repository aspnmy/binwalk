#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Binwalk 构建清理脚本

此脚本用于清理target目录中的中间文件，只保留可执行文件和必要资源，
便于上传发布。
"""

import os
import shutil
import sys

def get_normalized_path(path):
    """获取规范化的路径"""
    return os.path.normpath(path)

def main():
    # 获取脚本所在目录
    script_dir = get_normalized_path(os.path.dirname(os.path.abspath(__file__)))
    target_dir = get_normalized_path(os.path.join(script_dir, 'target', 'x86_64-pc-windows-gnu', 'debug'))
    
    print(f"开始清理构建目录: {target_dir}")
    
    # 检查目标目录是否存在
    if not os.path.exists(target_dir):
        print(f"错误: 目标目录不存在: {target_dir}")
        sys.exit(1)
    
    # 要保留的文件类型和目录
    keep_extensions = ['.exe', '.dll', '.pdb']  # .pdb是调试符号文件，可选保留
    keep_directories = ['sqfs_for_win']
    
    # 要删除的中间文件目录
    delete_dirs = ['build', 'deps', 'examples', 'incremental', 'native']
    
    # 要删除的文件类型
    delete_extensions = ['.rlib', '.rmeta', '.rs', '.d', '.o', '.exp', '.lib']
    
    files_cleaned = 0
    dirs_cleaned = 0
    
    try:
        # 删除已知的中间文件目录
        for dir_name in delete_dirs:
            dir_path = os.path.join(target_dir, dir_name)
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                print(f"删除中间目录: {dir_path}")
                shutil.rmtree(dir_path)
                dirs_cleaned += 1
        
        # 遍历target目录下的所有文件和目录
        for item in os.listdir(target_dir):
            item_path = os.path.join(target_dir, item)
            
            # 检查是否为需要保留的目录
            if os.path.isdir(item_path):
                if item not in keep_directories:
                    print(f"删除不需要的目录: {item_path}")
                    shutil.rmtree(item_path)
                    dirs_cleaned += 1
                else:
                    print(f"保留目录: {item_path}")
            
            # 检查是否为需要保留的文件
            elif os.path.isfile(item_path):
                # 获取文件扩展名
                _, ext = os.path.splitext(item.lower())
                
                # 如果扩展名不在保留列表中，则删除
                if ext not in keep_extensions:
                    # 检查是否为要删除的扩展名
                    if ext in delete_extensions or not ext:  # 也删除没有扩展名的临时文件
                        print(f"删除中间文件: {item_path}")
                        os.remove(item_path)
                        files_cleaned += 1
                else:
                    print(f"保留文件: {item_path}")
        
        print(f"\n清理完成!")
        print(f"- 删除的中间文件: {files_cleaned}")
        print(f"- 删除的中间目录: {dirs_cleaned}")
        print(f"\n发布目录已准备就绪: {target_dir}")
        
    except Exception as e:
        print(f"清理过程中出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()