#!/usr/bin/env python3
"""
简单的B站下载测试
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.video_downloader import get_video_info

def simple_test():
    """简单测试B站视频信息获取"""
    # 使用一个更简单的B站视频URL进行测试
    test_urls = [
        "https://www.bilibili.com/video/BV1GJ411x7h7",  # 著名的视频
        "https://www.bilibili.com/video/BV1xx411c7mD",  # 另一个公开视频
        "https://b23.tv/av2",  # 经典视频
    ]
    
    for test_url in test_urls:
        print(f"\n测试URL: {test_url}")
        
        try:
            info = get_video_info(test_url)
            print("✅ 视频信息获取成功:")
            print(f"  标题: {info.get('title', 'N/A')}")
            print(f"  平台: {info.get('platform', 'N/A')}")
            return True
        except Exception as e:
            print(f"❌ 失败: {e}")
            continue
    
    print("⚠️ 所有测试URL都失败，可能是网络或地区限制问题")
    return False

if __name__ == "__main__":
    print("🧪 简单B站测试")
    simple_test()
