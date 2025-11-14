#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
网关域名管理模块

用于统一管理下载网关和Docker镜像网关域名，支持从配置文件读取和默认值设置。
"""

import os
import sys

def get_gateway_from_file(gateway_file, default_gateway):
    """
    从文件读取网关域名
    
    参数:
        gateway_file: str, 网关文件路径
        default_gateway: str, 默认网关域名
    
    返回:
        str: 网关域名
    """
    try:
        if os.path.exists(gateway_file):
            with open(gateway_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    # 取第一行非空内容
                    lines = content.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            return line
        return default_gateway
    except Exception as e:
        print(f"读取网关文件失败 {gateway_file}: {e}")
        return default_gateway

def get_download_gateway():
    """
    获取下载网关域名
    
    返回:
        str: 下载网关域名
    """
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 构建网关文件路径
    download_gateway_file = os.path.join(script_dir, '..', '..', '.trae', 'rules', 'download-gateway')
    
    # 默认下载网关
    default_download_gateway = "gateway.cf.shdrr.org"
    
    return get_gateway_from_file(download_gateway_file, default_download_gateway)

def get_dockerimage_gateway():
    """
    获取Docker镜像网关域名
    
    返回:
        str: Docker镜像网关域名
    """
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 构建网关文件路径
    dockerimage_gateway_file = os.path.join(script_dir, '..', '..', '.trae', 'rules', 'dockerimage-gateway')
    
    # 默认Docker镜像网关
    default_dockerimage_gateway = "drrpull.shdrr.org"
    
    return get_gateway_from_file(dockerimage_gateway_file, default_dockerimage_gateway)

def test_gateway_domains():
    """
    测试网关域名功能
    
    返回:
        bool: 测试是否成功
    """
    print("测试网关域名管理模块...")
    
    try:
        # 测试下载网关
        download_gateway = get_download_gateway()
        print(f"下载网关: {download_gateway}")
        
        # 测试Docker镜像网关
        dockerimage_gateway = get_dockerimage_gateway()
        print(f"Docker镜像网关: {dockerimage_gateway}")
        
        # 测试URL构建
        test_download_url = f"https://{download_gateway}/files/test.zip"
        test_docker_url = f"{dockerimage_gateway}/library/ubuntu:latest"
        
        print(f"测试下载URL: {test_download_url}")
        print(f"测试Docker镜像URL: {test_docker_url}")
        
        # 检查环境变量
        env_download = os.environ.get('DOWNLOAD_GATEWAY')
        env_dockerimage = os.environ.get('DOCKERIMAGE_GATEWAY')
        
        if env_download:
            print(f"环境变量 DOWNLOAD_GATEWAY: {env_download}")
        if env_dockerimage:
            print(f"环境变量 DOCKERIMAGE_GATEWAY: {env_dockerimage}")
        
        print("网关域名管理模块测试完成")
        return True
        
    except Exception as e:
        print(f"网关域名管理模块测试失败: {e}")
        return False

if __name__ == "__main__":
    success = test_gateway_domains()
    sys.exit(0 if success else 1)