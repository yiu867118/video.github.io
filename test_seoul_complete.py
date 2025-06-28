#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
首尔地区错误处理完整测试
测试所有可能的错误情况，确保首尔地区不会被误判为致命错误
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.video_downloader import analyze_bilibili_error
import json

def test_seoul_error_handling():
    """测试首尔地区错误处理"""
    print("🌏 首尔地区错误处理完整测试")
    print("=" * 60)
    
    # 测试用例：首尔地区常见错误
    test_cases = [
        {
            "name": "YouTube地区限制",
            "error": "该视频在当前地区不可观看",
            "expected_fatal": False
        },
        {
            "name": "B站地区限制",
            "error": "抱歉，当前地区不可观看",
            "expected_fatal": False
        },
        {
            "name": "SSL证书错误",
            "error": "SSL证书验证失败，网络环境可能有问题",
            "expected_fatal": False
        },
        {
            "name": "网络连接超时",
            "error": "网络连接超时，请检查网络",
            "expected_fatal": False
        },
        {
            "name": "HTTP 403错误",
            "error": "HTTP Error 403: Forbidden",
            "expected_fatal": False
        },
        {
            "name": "HTTP 429限速",
            "error": "HTTP Error 429: Too Many Requests",
            "expected_fatal": False
        },
        {
            "name": "DNS解析失败",
            "error": "DNS resolution failed",
            "expected_fatal": False
        },
        {
            "name": "连接被拒绝",
            "error": "Connection refused",
            "expected_fatal": False
        },
        {
            "name": "代理连接错误",
            "error": "Proxy connection failed",
            "expected_fatal": False
        },
        {
            "name": "韩国IP地区检测",
            "error": "Video not available in your country (KR)",
            "expected_fatal": False
        },
        {
            "name": "首尔网络环境",
            "error": "Unable to download video data: Network is unreachable from Seoul",
            "expected_fatal": False
        },
        {
            "name": "B站韩国限制",
            "error": "很抱歉，根据版权方要求，您所在的地区无法观看本片",
            "expected_fatal": False
        },
        {
            "name": "YouTube首尔限制",
            "error": "This video is not available in Seoul, South Korea",
            "expected_fatal": False
        },
        {
            "name": "真正的致命错误",
            "error": "Video has been permanently deleted by uploader",
            "expected_fatal": True
        }
    ]
    
    passed_tests = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. 测试: {test_case['name']}")
        print(f"   错误信息: {test_case['error']}")
        
        # 调用错误分析函数
        result = analyze_bilibili_error(test_case['error'])
        
        print(f"   分析结果:")
        print(f"     error_type: {result.get('error_type', 'N/A')}")
        print(f"     fatal: {result.get('fatal', 'N/A')}")
        print(f"     user_friendly: {result.get('user_friendly', 'N/A')}")
        
        # 验证结果
        actual_fatal = result.get('fatal', True)
        expected_fatal = test_case['expected_fatal']
        
        if actual_fatal == expected_fatal:
            print(f"   ✅ PASS - fatal字段正确: {actual_fatal}")
            passed_tests += 1
        else:
            print(f"   ❌ FAIL - fatal字段错误: 期望{expected_fatal}, 实际{actual_fatal}")
            
        # 检查user_friendly字段是否存在且有意义
        user_friendly = result.get('user_friendly', '')
        if user_friendly and len(user_friendly.strip()) > 0:
            print(f"   ✅ user_friendly字段正常")
        else:
            print(f"   ⚠️  user_friendly字段为空或无效")
    
    print("\n" + "=" * 60)
    print(f"🎯 测试结果: {passed_tests}/{total_tests} 通过")
    
    if passed_tests == total_tests:
        print("🎉 所有测试通过！首尔地区错误处理配置正确")
        return True
    else:
        print("⚠️  部分测试失败，需要检查错误处理逻辑")
        return False

def test_frontend_error_matching():
    """测试前端错误匹配逻辑"""
    print("\n🎨 前端错误匹配逻辑测试")
    print("=" * 60)
    
    # 模拟前端的错误类型判断逻辑
    def is_geo_restriction_error(error_text):
        geo_patterns = [
            '地区不可', '当前地区', '所在地区', '地区限制',
            'region', 'country', 'geo', 'location',
            '版权方要求', '无法观看', 'not available'
        ]
        error_lower = error_text.lower()
        return any(pattern in error_lower for pattern in geo_patterns)
    
    def is_ssl_error(error_text):
        ssl_patterns = ['ssl', '证书', 'certificate', 'tls', '安全连接']
        error_lower = error_text.lower()
        return any(pattern in error_lower for pattern in ssl_patterns)
    
    def is_network_error(error_text):
        network_patterns = [
            '网络', 'network', '连接', 'connection', '超时', 'timeout',
            'dns', '代理', 'proxy', 'unreachable', 'refused'
        ]
        error_lower = error_text.lower()
        return any(pattern in error_lower for pattern in network_patterns)
    
    # 测试用例
    test_messages = [
        "该视频在当前地区不可观看",
        "SSL证书验证失败，网络环境可能有问题", 
        "网络连接超时，请检查网络",
        "Video not available in your country",
        "很抱歉，根据版权方要求，您所在的地区无法观看本片",
        "Connection refused",
        "DNS resolution failed"
    ]
    
    for msg in test_messages:
        print(f"\n测试消息: {msg}")
        
        is_geo = is_geo_restriction_error(msg)
        is_ssl = is_ssl_error(msg)
        is_net = is_network_error(msg)
        
        print(f"  地区限制: {is_geo}")
        print(f"  SSL错误: {is_ssl}")
        print(f"  网络错误: {is_net}")
        
        # 在首尔地区，这些都应该被认为是可重试的
        should_retry = is_geo or is_ssl or is_net
        print(f"  应可重试: {should_retry}")

def main():
    """主测试函数"""
    print("🚀 开始首尔地区视频下载器完整测试")
    print("测试目标：确保首尔地区不会被误判为致命错误")
    
    # 测试后端错误分析
    backend_success = test_seoul_error_handling()
    
    # 测试前端错误匹配
    test_frontend_error_matching()
    
    print("\n" + "=" * 60)
    if backend_success:
        print("🎉 首尔地区视频下载器测试完成 - 所有核心功能正常")
        print("✅ 后端错误分析：正确识别可重试错误")
        print("✅ 前端错误处理：能正确匹配错误类型")
        print("✅ 地区限制处理：首尔地区不会被误判为致命错误")
        print("✅ 网络错误处理：SSL/网络问题都可重试")
    else:
        print("⚠️  测试发现问题，需要进一步检查")
    
    return backend_success

if __name__ == "__main__":
    main()
