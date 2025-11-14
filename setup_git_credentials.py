#!/usr/bin/env python3
"""
Git凭据设置脚本
用于解决Windows环境下Git凭据管理器问题
"""

import os
import subprocess
import sys

def run_command(cmd):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def setup_git_credentials():
    """设置Git凭据"""
    print("正在设置Git凭据...")
    
    # 检查Git是否已安装
    success, stdout, stderr = run_command("git --version")
    if not success:
        print("错误: Git未安装或不在PATH中")
        return False
    
    print(f"Git版本: {stdout.strip()}")
    
    # 设置凭据助手为store模式
    print("设置凭据助手为store模式...")
    run_command("git config --global credential.helper store")
    
    # 禁用凭据管理器
    print("禁用Git凭据管理器...")
    run_command("git config --global --unset credential.helper")
    run_command("git config --global credential.helper store")
    
    # 设置其他有用的配置
    print("设置其他Git配置...")
    run_command("git config --global core.autocrlf true")
    run_command("git config --global core.safecrlf false")
    
    print("Git凭据设置完成!")
    print("\n下次执行git push时，系统会提示输入用户名和密码")
    print("输入的凭据将被保存，后续操作不再需要输入")
    return True

def test_git_push():
    """测试git push"""
    print("\n测试git push...")
    success, stdout, stderr = run_command("git push origin devWinWsl2:devWinWsl2")
    if success:
        print("git push成功!")
        return True
    else:
        print(f"git push失败: {stderr}")
        return False

if __name__ == "__main__":
    print("=== Git凭据设置工具 ===\n")
    
    # 设置凭据
    if setup_git_credentials():
        print("\n设置完成! 现在可以尝试git push了")
        print("如果仍然有问题，请手动输入用户名和密码")
    else:
        print("\n设置失败，请检查Git安装和权限")
        sys.exit(1)