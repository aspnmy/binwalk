#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IP地址检测和地区识别模块

用于检测用户的外网IP地址和所属地区，并根据地区选择合适的安装源
"""

import urllib.request
import urllib.error
import json
import socket
import time
import logging

# 导入网关域名管理模块
try:
    from gateway_manager import get_download_gateway
    GATEWAY_AVAILABLE = True
except ImportError:
    GATEWAY_AVAILABLE = False
    def get_download_gateway():
        return "gateway.cf.shdrr.org"

logger = logging.getLogger(__name__)

def get_external_ip():
    """
    获取外网IP地址
    
    返回:
        str: 外网IP地址，如果获取失败返回None
    """
    try:
        # 使用多个IP检测服务作为备选
        ip_services = [
            "https://checkip.amazonaws.com/",
            "https://api.ipify.org/",
            "https://ipinfo.io/ip",
            "https://ifconfig.me/ip"
        ]
        
        for service in ip_services:
            try:
                with urllib.request.urlopen(service, timeout=5) as response:
                    if response.status == 200:
                        ip = response.read().decode('utf-8').strip()
                        # 验证IP格式
                        if validate_ip_format(ip):
                            logger.info(f"通过 {service} 获取到IP: {ip}")
                            return ip
            except Exception as e:
                logger.warning(f"通过 {service} 获取IP失败: {str(e)}")
                continue
        
        logger.error("所有IP检测服务都失败")
        return None
        
    except Exception as e:
        logger.error(f"获取外网IP时出错: {str(e)}")
        return None

def validate_ip_format(ip):
    """
    验证IP地址格式
    
    参数:
        ip: str, 要验证的IP地址
    
    返回:
        bool: True表示格式正确，False表示格式错误
    """
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False

def get_ip_location_online(ip):
    """
    在线获取IP地址的地理位置信息
    
    参数:
        ip: str, IP地址
    
    返回:
        dict: 包含地区信息的字典，如果获取失败返回None
    """
    try:
        # 使用多个地理位置服务作为备选
        location_services = [
            f"https://api.ipinfo.io/{ip}?token=b8f46943d26f45",
            f"https://ipapi.co/{ip}/json/",
            f"https://freegeoip.app/json/{ip}"
        ]
        
        for service in location_services:
            try:
                with urllib.request.urlopen(service, timeout=5) as response:
                    if response.status == 200:
                        data = json.loads(response.read().decode('utf-8'))
                        
                        # 提取国家代码
                        country_code = None
                        if 'country' in data:
                            country_code = data['country']
                        elif 'country_code' in data:
                            country_code = data['country_code']
                        elif 'region' in data:
                            country_code = data['region']
                        
                        if country_code:
                            logger.info(f"通过 {service} 获取到地区: {country_code}")
                            return {
                                'ip': ip,
                                'country': country_code,
                                'raw_data': data
                            }
                        
            except Exception as e:
                logger.warning(f"通过 {service} 获取地区失败: {str(e)}")
                continue
        
        logger.warning("所有在线地区检测服务都失败")
        return None
        
    except Exception as e:
        logger.error(f"在线获取IP地区时出错: {str(e)}")
        return None

def test_url_accessibility(url, timeout=10):
    """
    测试URL的可访问性
    
    参数:
        url: str, 要测试的URL
        timeout: int, 超时时间（秒）
    
    返回:
        dict: 包含测试结果的字典
            - accessible: bool, 是否可访问
            - status_code: int, HTTP状态码
            - response_time: float, 响应时间（秒）
            - error: str, 错误信息（如果有）
    """
    result = {
        'accessible': False,
        'status_code': None,
        'response_time': None,
        'error': None
    }
    
    try:
        start_time = time.time()
        
        # 创建请求对象，设置超时
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req, timeout=timeout) as response:
            end_time = time.time()
            
            result['status_code'] = response.status
            result['response_time'] = end_time - start_time
            
            if 200 <= response.status < 300:
                result['accessible'] = True
                logger.info(f"URL {url} 可访问，状态码: {response.status}, 响应时间: {result['response_time']:.2f}秒")
            else:
                result['error'] = f"HTTP状态码: {response.status}"
                logger.warning(f"URL {url} 返回异常状态码: {response.status}")
                
    except urllib.error.URLError as e:
        result['error'] = str(e)
        logger.error(f"URL {url} 访问失败: {str(e)}")
    except socket.timeout:
        result['error'] = "连接超时"
        logger.error(f"URL {url} 连接超时")
    except Exception as e:
        result['error'] = str(e)
        logger.error(f"URL {url} 测试时出错: {str(e)}")
    
    return result

def get_ip_location_with_fallback(ip):
    """
    获取IP地区信息，包含离线备选方案
    
    参数:
        ip: str, IP地址
    
    返回:
        dict: 包含地区信息的字典
    """
    # 首先尝试在线获取
    location_info = get_ip_location_online(ip)
    
    if location_info:
        return location_info
    
    # 如果在线获取失败，使用IP地址范围进行粗略判断
    logger.info("使用IP地址范围进行粗略地区判断")
    
    try:
        # 简单的IP地址范围判断（仅作为备选）
        ip_parts = ip.split('.')
        if len(ip_parts) == 4:
            first_octet = int(ip_parts[0])
            
            # 中国大陆常见的IP段（非常粗略的估计）
            if (first_octet == 1 or      # 1.x.x.x
                first_octet == 14 or    # 14.x.x.x
                first_octet == 27 or    # 27.x.x.x
                first_octet == 36 or    # 36.x.x.x
                first_octet == 39 or    # 39.x.x.x
                first_octet == 42 or    # 42.x.x.x
                first_octet == 49 or    # 49.x.x.x
                first_octet == 58 or    # 58.x.x.x
                first_octet == 59 or    # 59.x.x.x
                first_octet == 60 or    # 60.x.x.x
                first_octet == 61 or    # 61.x.x.x
                first_octet == 101 or   # 101.x.x.x
                first_octet == 103 or   # 103.x.x.x
                first_octet == 106 or   # 106.x.x.x
                first_octet == 110 or   # 110.x.x.x
                first_octet == 111 or   # 111.x.x.x
                first_octet == 112 or   # 112.x.x.x
                first_octet == 113 or   # 113.x.x.x
                first_octet == 114 or   # 114.x.x.x
                first_octet == 115 or   # 115.x.x.x
                first_octet == 116 or   # 116.x.x.x
                first_octet == 117 or   # 117.x.x.x
                first_octet == 118 or   # 118.x.x.x
                first_octet == 119 or   # 119.x.x.x
                first_octet == 120 or   # 120.x.x.x
                first_octet == 121 or   # 121.x.x.x
                first_octet == 122 or   # 122.x.x.x
                first_octet == 123 or   # 123.x.x.x
                first_octet == 124 or   # 124.x.x.x
                first_octet == 125 or   # 125.x.x.x
                first_octet == 126 or   # 126.x.x.x
                first_octet == 140 or   # 140.x.x.x
                first_octet == 163 or   # 163.x.x.x
                first_octet == 171 or   # 171.x.x.x
                first_octet == 175 or   # 175.x.x.x
                first_octet == 180 or   # 180.x.x.x
                first_octet == 182 or   # 182.x.x.x
                first_octet == 183 or   # 183.x.x.x
                first_octet == 202 or   # 202.x.x.x
                first_octet == 203 or   # 203.x.x.x
                first_octet == 210 or   # 210.x.x.x
                first_octet == 211 or   # 211.x.x.x
                first_octet == 218 or   # 218.x.x.x
                first_octet == 219 or   # 219.x.x.x
                first_octet == 220 or   # 220.x.x.x
                first_octet == 221 or   # 221.x.x.x
                first_octet == 222 or   # 222.x.x.x
                first_octet == 223):    # 223.x.x.x
                return {
                    'ip': ip,
                    'country': 'CN',
                    'method': 'ip_range_fallback'
                }
            else:
                return {
                    'ip': ip,
                    'country': 'UNKNOWN',
                    'method': 'ip_range_fallback'
                }
    except Exception as e:
        logger.error(f"IP地址范围判断失败: {str(e)}")
    
    return {
        'ip': ip,
        'country': 'UNKNOWN',
        'method': 'fallback'
    }

def check_network_environment():
    """
    检查网络环境，确定是否需要使用镜像源
    
    返回:
        dict: 包含网络环境信息的字典
            - ip: str, 外网IP地址
            - country: str, 国家代码
            - use_mirror: bool, 是否建议使用镜像源
            - gateway_url: str, 建议使用的网关URL
            - test_results: dict, 网络测试结果
    """
    logger.info("开始检测网络环境...")
    
    result = {
        'ip': None,
        'country': 'UNKNOWN',
        'use_mirror': False,
        'gateway_url': f'https://{get_download_gateway()}',
        'test_results': {}
    }
    
    # 获取外网IP
    external_ip = get_external_ip()
    if not external_ip:
        logger.warning("无法获取外网IP，使用默认配置")
        result['use_mirror'] = True  # 无法确定IP时，保守起见使用镜像源
        return result
    
    result['ip'] = external_ip
    logger.info(f"检测到外网IP: {external_ip}")
    
    # 获取IP地区信息
    location_info = get_ip_location_with_fallback(external_ip)
    result['country'] = location_info.get('country', 'UNKNOWN')
    result['location_method'] = location_info.get('method', 'unknown')
    
    logger.info(f"IP地区: {result['country']} (检测方法: {result.get('location_method', 'unknown')})")
    
    # 根据地区决定是否使用镜像源
    if result['country'] == 'CN' or result['country'] == 'UNKNOWN':
        result['use_mirror'] = True
        logger.info("检测到中国大陆或未知地区，建议使用镜像源")
    else:
        # 对于非CN地区，测试网络连通性
        logger.info("检测到非CN地区，测试网络连通性...")
        
        # 测试一些常用的国外服务
        test_urls = [
            'https://github.com',
            'https://raw.githubusercontent.com',
            'https://docker.com',
            'https://registry-1.docker.io'
        ]
        
        accessible_count = 0
        total_response_time = 0
        
        for url in test_urls:
            test_result = test_url_accessibility(url, timeout=10)
            result['test_results'][url] = test_result
            
            if test_result['accessible']:
                accessible_count += 1
                if test_result['response_time']:
                    total_response_time += test_result['response_time']
        
        logger.info(f"网络测试结果: {accessible_count}/{len(test_urls)} 个服务可访问")
        
        # 如果少于一半的服务可访问，或者平均响应时间过长，建议使用镜像源
        if accessible_count < len(test_urls) / 2:
            result['use_mirror'] = True
            logger.info("网络连通性较差，建议使用镜像源")
        elif accessible_count > 0:
            avg_response_time = total_response_time / accessible_count
            if avg_response_time > 5.0:  # 平均响应时间超过5秒
                result['use_mirror'] = True
                logger.info(f"网络延迟较高(平均{avg_response_time:.2f}秒)，建议使用镜像源")
            else:
                logger.info(f"网络状况良好(平均{avg_response_time:.2f}秒)，可直接访问")
    
    logger.info(f"网络环境检测结果: 使用镜像源 = {result['use_mirror']}")
    return result

def get_smart_url(original_url, network_info):
    """
    根据网络环境获取智能URL
    
    参数:
        original_url: str, 原始URL
        network_info: dict, 网络环境信息
    
    返回:
        str: 智能选择后的URL
    """
    # 检查网络信息是否有效
    if not network_info:
        return original_url
    
    if network_info.get('use_mirror', False):
        gateway_url = network_info.get('gateway_url', f'https://{get_download_gateway()}')
        # 构建镜像URL
        mirror_url = f"{gateway_url}/{original_url}"
        logger.info(f"使用镜像源: {mirror_url}")
        return mirror_url
    else:
        logger.info(f"使用原始URL: {original_url}")
        return original_url

if __name__ == "__main__":
    # 测试功能
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("测试IP地址检测和地区识别功能...")
    network_info = check_network_environment()
    
    print(f"\n检测结果:")
    print(f"IP地址: {network_info.get('ip', '未知')}")
    print(f"地区: {network_info.get('country', '未知')}")
    print(f"建议使用镜像源: {network_info.get('use_mirror', False)}")
    print(f"网关URL: {network_info.get('gateway_url', '未知')}")
    
    # 测试URL智能选择
    test_urls = [
        "https://github.com/aspnmy/BestHostsMonitor/refs/heads/devbox/CN/docker.list",
        "https://raw.githubusercontent.com/docker/docker-ce/master/components/engine/daemon.json"
    ]
    
    print(f"\nURL智能选择测试:")
    for url in test_urls:
        smart_url = get_smart_url(url, network_info)
        print(f"原始URL: {url}")
        print(f"智能URL: {smart_url}")
        print("-" * 50)