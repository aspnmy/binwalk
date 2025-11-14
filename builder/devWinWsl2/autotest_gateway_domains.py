#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
网关域名管理自动测试脚本

用于测试网关域名管理模块的功能，包括域名读取、URL构建、错误处理等。
"""

import os
import sys
import tempfile
import time

def test_gateway_domain_reading():
    """
    测试网关域名读取功能
    
    返回:
        bool: 测试是否通过
    """
    print("=" * 60)
    print("测试网关域名读取功能")
    print("=" * 60)
    
    try:
        # 导入网关管理模块
        from gateway_manager import get_download_gateway, get_dockerimage_gateway
        
        # 测试默认域名读取
        download_gateway = get_download_gateway()
        dockerimage_gateway = get_dockerimage_gateway()
        
        print(f"[+] 下载网关域名: {download_gateway}")
        print(f"[+] Docker镜像网关域名: {dockerimage_gateway}")
        
        # 验证默认域名
        if download_gateway != "gateway.cf.shdrr.org":
            print(f"[-] 下载网关域名错误，期望: gateway.cf.shdrr.org，实际: {download_gateway}")
            return False
            
        if dockerimage_gateway != "drrpull.shdrr.org":
            print(f"[-] Docker镜像网关域名错误，期望: drrpull.shdrr.org，实际: {dockerimage_gateway}")
            return False
        
        print("[+] 默认域名读取测试通过")
        return True
        
    except Exception as e:
        print(f"[-] 网关域名读取测试失败: {e}")
        return False

def test_gateway_file_reading():
    """
    测试网关文件读取功能
    
    返回:
        bool: 测试是否通过
    """
    print("\n" + "=" * 60)
    print("测试网关文件读取功能")
    print("=" * 60)
    
    try:
        from gateway_manager import get_gateway_from_file
        
        # 创建临时测试文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("test-gateway.example.com\n")
            f.write("# 这是注释行\n")
            f.write("another-gateway.example.com\n")
            test_file = f.name
        
        try:
            # 测试文件读取
            result = get_gateway_from_file(test_file, "default.gateway.com")
            
            if result != "test-gateway.example.com":
                print(f"[-] 文件读取错误，期望: test-gateway.example.com，实际: {result}")
                return False
            
            print("[+] 网关文件读取测试通过")
            return True
            
        finally:
            # 清理临时文件
            os.unlink(test_file)
            
    except Exception as e:
        print(f"[-] 网关文件读取测试失败: {e}")
        return False

def test_url_building():
    """
    测试URL构建功能
    
    返回:
        bool: 测试是否通过
    """
    print("\n" + "=" * 60)
    print("测试URL构建功能")
    print("=" * 60)
    
    try:
        from gateway_manager import get_download_gateway, get_dockerimage_gateway
        
        # 获取网关域名
        download_gateway = get_download_gateway()
        dockerimage_gateway = get_dockerimage_gateway()
        
        # 测试下载URL构建
        test_file = "files/tool.zip"
        download_url = f"https://{download_gateway}/{test_file}"
        expected_download_url = f"https://gateway.cf.shdrr.org/{test_file}"
        
        if download_url != expected_download_url:
            print(f"[-] 下载URL构建错误，期望: {expected_download_url}，实际: {download_url}")
            return False
        
        # 测试Docker镜像URL构建
        test_image = "library/ubuntu:latest"
        docker_url = f"{dockerimage_gateway}/{test_image}"
        expected_docker_url = f"drrpull.shdrr.org/{test_image}"
        
        if docker_url != expected_docker_url:
            print(f"[-] Docker镜像URL构建错误，期望: {expected_docker_url}，实际: {docker_url}")
            return False
        
        print(f"[+] 下载URL: {download_url}")
        print(f"[+] Docker镜像URL: {docker_url}")
        print("[+] URL构建测试通过")
        return True
        
    except Exception as e:
        print(f"[-] URL构建测试失败: {e}")
        return False

def test_error_handling():
    """
    测试错误处理功能
    
    返回:
        bool: 测试是否通过
    """
    print("\n" + "=" * 60)
    print("测试错误处理功能")
    print("=" * 60)
    
    try:
        from gateway_manager import get_gateway_from_file
        
        # 测试不存在的文件
        result = get_gateway_from_file("/non/existent/file.txt", "default.gateway.com")
        if result != "default.gateway.com":
            print(f"[-] 不存在文件处理错误，期望: default.gateway.com，实际: {result}")
            return False
        
        # 测试空文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("")
            empty_file = f.name
        
        try:
            result = get_gateway_from_file(empty_file, "default.gateway.com")
            if result != "default.gateway.com":
                print(f"[-] 空文件处理错误，期望: default.gateway.com，实际: {result}")
                return False
        finally:
            os.unlink(empty_file)
        
        # 测试只有注释的文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("# 这是注释\n")
            f.write("# 另一行注释\n")
            comment_file = f.name
        
        try:
            result = get_gateway_from_file(comment_file, "default.gateway.com")
            if result != "default.gateway.com":
                print(f"[-] 注释文件处理错误，期望: default.gateway.com，实际: {result}")
                return False
        finally:
            os.unlink(comment_file)
        
        print("[+] 错误处理测试通过")
        return True
        
    except Exception as e:
        print(f"[-] 错误处理测试失败: {e}")
        return False

def test_integration_with_ip_detection():
    """
    测试与IP检测模块的集成功能
    
    返回:
        bool: 测试是否通过
    """
    print("\n" + "=" * 60)
    print("测试与IP检测模块集成")
    print("=" * 60)
    
    try:
        # 测试IP检测模块中的网关使用
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        try:
            from true_check_ip_location import check_network_environment
            
            # 执行网络环境检测
            network_info = check_network_environment()
            
            if not network_info:
                print("[-] 网络环境检测返回None")
                return False
            
            gateway_url = network_info.get('gateway_url')
            if not gateway_url:
                print("[-] 网络信息中没有gateway_url")
                return False
            
            # 验证网关URL格式
            if not gateway_url.startswith('https://'):
                print(f"[-] 网关URL格式错误: {gateway_url}")
                return False
            
            print(f"[+] 检测到的网关URL: {gateway_url}")
            print("[+] IP检测模块集成测试通过")
            return True
            
        except ImportError:
            print("[!] IP检测模块不可用，跳过集成测试")
            return True
        
    except Exception as e:
        print(f"[-] IP检测模块集成测试失败: {e}")
        return False

def main():
    """
    主测试函数
    
    返回:
        int: 退出码，0表示成功，非0表示失败
    """
    print("网关域名管理自动测试脚本")
    print("测试时间:", time.strftime("%Y-%m-%d %H:%M:%S"))
    print()
    
    # 运行所有测试
    test_functions = [
        ("网关域名读取", test_gateway_domain_reading),
        ("网关文件读取", test_gateway_file_reading),
        ("URL构建", test_url_building),
        ("错误处理", test_error_handling),
        ("IP检测集成", test_integration_with_ip_detection)
    ]
    
    test_results = []
    
    for test_name, test_func in test_functions:
        try:
            result = test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"[-] 测试 {test_name} 执行失败: {e}")
            test_results.append((test_name, False))
    
    # 输出测试结果汇总
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "通过" if result else "失败"
        print(f"[{'+' if result else '-'}] {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n测试完成: {passed}/{total} 通过")
    
    if passed == total:
        print("[+] 所有测试通过！")
        return 0
    else:
        print("[-] 部分测试失败！")
        return 1

if __name__ == "__main__":
    # 配置日志
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    sys.exit(main())