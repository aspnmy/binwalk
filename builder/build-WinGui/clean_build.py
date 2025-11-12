#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
构建清理脚本
用于清理builder/build-WinGui目录下的构建中间文件
保留源代码文件和必要的配置文件
"""

import os
import shutil
import argparse

def clean_build_files(dry_run=False):
    """
    清理构建中间文件
    
    参数:
        dry_run: 布尔值，如果为True则只显示要删除的文件，不实际删除
    
    返回值:
        整数，表示删除的文件和目录数量
    """
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 定义要删除的文件和目录模式
    # 这些是构建过程中生成的中间文件
    to_delete = {
        'directories': [
            'build',          # PyInstaller构建目录
            'dist',           # PyInstaller输出目录
            'extractions',    # 提取的文件目录
            'sqfs_for_win',   # SquashFS相关临时目录
            'Tests',          # 测试目录
        ],
        'files': [
            'binwalk_gui.spec',  # PyInstaller规格文件
            'devROM.jpg',        # 开发用ROM文件
            '.cargo-lock',       # Cargo锁文件
        ],
        'extensions': [
            '.pyc',          # Python编译文件
            '.pyo',          # 优化的Python编译文件
            '.bak',          # 备份文件
            '.tmp',          # 临时文件
            '.log',          # 日志文件
        ]
    }
    
    # 定义要保留的重要文件
    to_keep = [
        'clean_build.py',     # 当前清理脚本
        'binwalk_gui.py',     # 主程序源文件
        'build_gui.py',       # 构建脚本
        '如何更新最新组件及基础教程.txt',  # 教程文件
    ]
    
    deleted_count = 0
    
    # 删除指定的目录
    for dir_name in to_delete['directories']:
        dir_path = os.path.join(current_dir, dir_name)
        if os.path.exists(dir_path):
            if dry_run:
                print(f"[模拟删除] 目录: {dir_path}")
            else:
                try:
                    # 尝试使用更强健的方式删除目录，处理文件锁定情况
                    if os.path.isdir(dir_path):
                        # 先尝试删除目录中的文件
                        for root, _, files in os.walk(dir_path, topdown=False):
                            for file in files:
                                try:
                                    os.remove(os.path.join(root, file))
                                except:
                                    pass  # 忽略单个文件删除失败
                        # 然后尝试删除目录结构
                        shutil.rmtree(dir_path, ignore_errors=True)
                        if not os.path.exists(dir_path):
                            print(f"[已删除] 目录: {dir_path}")
                            deleted_count += 1
                        else:
                            print(f"[部分删除] 目录: {dir_path} (可能有文件被锁定)")
                except Exception as e:
                    print(f"[删除失败] 目录: {dir_path}, 错误: {str(e)}")
    
    # 删除指定的文件
    for file_name in to_delete['files']:
        file_path = os.path.join(current_dir, file_name)
        if os.path.exists(file_path):
            if dry_run:
                print(f"[模拟删除] 文件: {file_path}")
            else:
                try:
                    os.remove(file_path)
                    print(f"[已删除] 文件: {file_path}")
                    deleted_count += 1
                except Exception as e:
                    print(f"[删除失败] 文件: {file_path}, 错误: {str(e)}")
    
    # 删除指定扩展名的文件
    for root, dirs, files in os.walk(current_dir):
        # 排除不在当前目录的子目录处理
        if root != current_dir:
            continue
        
        for file_name in files:
            # 检查是否是要保留的文件
            if file_name in to_keep:
                continue
            
            # 检查文件扩展名 - 保留所有.py文件，因为它们是构建脚本
            _, ext = os.path.splitext(file_name)
            if ext.lower() in to_delete['extensions'] and ext.lower() != '.py':
                file_path = os.path.join(root, file_name)
                if dry_run:
                    print(f"[模拟删除] 文件: {file_path}")
                else:
                    try:
                        os.remove(file_path)
                        print(f"[已删除] 文件: {file_path}")
                        deleted_count += 1
                    except Exception as e:
                        print(f"[删除失败] 文件: {file_path}, 错误: {str(e)}")
            elif ext.lower() == '.py':
                # 记录但不删除Python文件
                if dry_run:
                    print(f"[保留] Python脚本: {os.path.join(root, file_name)}")
    
    return deleted_count


def main():
    """
    主函数，处理命令行参数并执行清理操作
    """
    parser = argparse.ArgumentParser(description='清理构建中间文件')
    parser.add_argument('--dry-run', action='store_true', help='只显示将要删除的文件，不实际删除')
    args = parser.parse_args()
    
    print("开始清理构建中间文件...")
    print(f"清理目录: {os.path.dirname(os.path.abspath(__file__))}")
    
    if args.dry_run:
        print("\n[模拟模式] 以下是将要删除的文件和目录:")
    
    deleted_count = clean_build_files(args.dry_run)
    
    if args.dry_run:
        print(f"\n[模拟模式] 总共将删除 {deleted_count} 个文件或目录")
        print("要执行实际删除，请移除 --dry-run 参数")
    else:
        print(f"\n清理完成！总共删除了 {deleted_count} 个文件或目录")


if __name__ == "__main__":
    main()