#!/usr/bin/env python3
"""
检查B站视频的可用格式
"""

import yt_dlp

def check_bilibili_formats():
    """检查B站视频的可用格式"""
    
    test_url = "https://www.bilibili.com/video/BV1xx411c7mu"
    
    print(f"🔍 检查B站视频格式: {test_url}")
    print("=" * 60)
    
    try:
        ydl_opts = {
            'quiet': False,
            'no_warnings': False,
            'listformats': True,  # 列出所有格式
            'geo_bypass': True,
            'nocheckcertificate': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([test_url])
            
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    check_bilibili_formats()
