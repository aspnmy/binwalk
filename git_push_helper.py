#!/usr/bin/env python3
"""
Git推送辅助工具
解决Windows环境下的凭据问题
"""

import os
import subprocess
import getpass

def push_with_credentials():
    """使用用户名和密码进行git push"""
    print("=== Git推送辅助工具 ===\n")
    
    # 获取用户名
    username = input("请输入GitHub用户名: ").strip()
    if not username:
        print("用户名不能为空")
        return False
    
    # 获取访问令牌（推荐使用Personal Access Token）
    print("\n建议使用GitHub Personal Access Token代替密码")
    print("获取地址: https://github.com/settings/tokens")
    token = getpass.getpass("请输入GitHub Personal Access Token或密码: ").strip()
    
    if not token:
        print("Token/密码不能为空")
        return False
    
    # 构建远程URL
    remote_url = f"https://{username}:{token}@github.com/aspnmy/binwalk.git"
    
    print(f"\n正在推送到远程仓库...")
    print(f"用户: {username}")
    print(f"分支: devWinWsl2")
    
    try:
        # 设置临时远程
        subprocess.run(["git", "remote", "add", "temp-push", remote_url], 
                      capture_output=True, text=True)
        
        # 执行推送
        result = subprocess.run(["git", "push", "temp-push", "devWinWsl2:devWinWsl2"], 
                               capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 推送成功!")
            print("输出:", result.stdout)
            
            # 清理临时远程
            subprocess.run(["git", "remote", "remove", "temp-push"], 
                           capture_output=True)
            return True
        else:
            print("❌ 推送失败!")
            print("错误:", result.stderr)
            
            # 清理临时远程
            subprocess.run(["git", "remote", "remove", "temp-push"], 
                           capture_output=True)
            return False
            
    except Exception as e:
        print(f"发生错误: {e}")
        return False

def alternative_push_method():
    """替代推送方法 - 使用SSH"""
    print("\n=== 替代方法：使用SSH推送 ===")
    print("1. 生成SSH密钥: ssh-keygen -t ed25519 -C \"your_email@example.com\"")
    print("2. 添加公钥到GitHub: https://github.com/settings/keys")
    print("3. 修改远程URL为SSH格式")
    print("4. 然后执行: git push origin devWinWsl2:devWinWsl2")
    
    change_to_ssh = input("是否要将远程URL更改为SSH格式? (y/n): ").lower()
    if change_to_ssh == 'y':
        try:
            result = subprocess.run(["git", "remote", "set-url", "origin", 
                                   "git@github.com:aspnmy/binwalk.git"], 
                                   capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ 远程URL已更改为SSH格式")
                print("现在可以执行: git push origin devWinWsl2:devWinWsl2")
            else:
                print("❌ 更改URL失败:", result.stderr)
        except Exception as e:
            print(f"错误: {e}")

if __name__ == "__main__":
    # 尝试第一种方法
    if push_with_credentials():
        print("\n🎉 推送完成!")
    else:
        print("\n尝试替代方法...")
        alternative_push_method()
        
    print("\n如果仍然有问题，请检查:")
    print("1. GitHub账户是否有仓库访问权限")
    print("2. Personal Access Token是否有正确的权限")
    print("3. 网络连接是否正常")