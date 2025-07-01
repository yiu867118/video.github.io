#!/usr/bin/env python3
"""
B站手机端/平板端下载问题诊断和测试脚本
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

import yt_dlp
import tempfile
import time
from video_downloader import get_downloader, download_video

def test_bilibili_mobile_strategies():
    """测试不同的B站移动端策略"""
    
    # 使用一个确定可用的B站视频进行测试
    test_urls = [
        "https://www.bilibili.com/video/BV1xx411c7mu",  # 经典视频
        "https://www.bilibili.com/video/BV1GJ411x7h7",  # 另一个经典视频
    ]
    
    print("🎯 开始B站手机端/平板端下载策略测试")
    print("=" * 60)
    
    # 模拟不同的移动端User-Agent
    mobile_strategies = [
        {
            'name': '最简化B站策略',
            'format': 'best',
            'options': {
                'merge_output_format': 'mp4',
                'geo_bypass': True,
                'nocheckcertificate': True,
                'ignoreerrors': False,
                'socket_timeout': 60,
                'retries': 2,
                'prefer_insecure': True,
            }
        },
        {
            'name': 'B站手机端模拟(简化)',
            'format': 'best[acodec!=none]/best',
            'options': {
                'merge_output_format': 'mp4',
                'geo_bypass': True,
                'nocheckcertificate': True,
                'ignoreerrors': False,
                'socket_timeout': 90,
                'retries': 2,
                'prefer_insecure': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36',
                    'Referer': 'https://www.bilibili.com/',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                }
            }
        },
        {
            'name': 'B站iPad模拟(简化)',
            'format': 'best[height<=720]/best',
            'options': {
                'merge_output_format': 'mp4',
                'geo_bypass': True,
                'nocheckcertificate': True,
                'ignoreerrors': False,
                'socket_timeout': 90,
                'retries': 2,
                'prefer_insecure': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
                    'Referer': 'https://www.bilibili.com/',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                }
            }
        }
    ]
    
    for test_url in test_urls:
        print(f"\n🔗 测试视频: {test_url}")
        print("-" * 40)
        
        for i, strategy in enumerate(mobile_strategies, 1):
            print(f"\n📱 策略 {i}: {strategy['name']}")
            
            try:
                # 创建临时下载目录
                with tempfile.TemporaryDirectory() as temp_dir:
                    output_template = os.path.join(temp_dir, "%(title)s.%(ext)s")
                    
                    # 配置yt-dlp
                    ydl_opts = {
                        'format': strategy['format'],
                        'outtmpl': output_template,
                        'quiet': True,
                        'no_warnings': True,
                        'extract_flat': False,
                    }
                    ydl_opts.update(strategy['options'])
                    
                    start_time = time.time()
                    
                    # 尝试下载
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        # 先获取信息
                        info = ydl.extract_info(test_url, download=False)
                        title = info.get('title', 'Unknown')
                        duration = info.get('duration', 0)
                        
                        print(f"   ✅ 视频信息获取成功")
                        print(f"   📝 标题: {title[:50]}...")
                        print(f"   ⏱️ 时长: {duration}秒")
                        
                        # 实际下载测试（小文件）
                        ydl_opts['format'] = 'worst'  # 测试时使用最小质量
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl_download:
                            ydl_download.download([test_url])
                        
                        # 检查下载结果
                        files = os.listdir(temp_dir)
                        if files:
                            file_path = os.path.join(temp_dir, files[0])
                            file_size = os.path.getsize(file_path)
                            
                            elapsed = time.time() - start_time
                            print(f"   🎉 下载成功！")
                            print(f"   📁 文件: {files[0][:30]}...")
                            print(f"   📊 大小: {file_size/1024:.1f} KB")
                            print(f"   ⏱️ 耗时: {elapsed:.1f}秒")
                        else:
                            print(f"   ❌ 下载失败: 无文件生成")
                            
            except Exception as e:
                error_msg = str(e)
                print(f"   ❌ 策略失败: {error_msg[:100]}...")
                
                # 分析错误类型
                if 'unsupported url' in error_msg.lower():
                    print(f"      🔍 错误类型: URL不支持")
                elif 'geo' in error_msg.lower() or 'region' in error_msg.lower():
                    print(f"      🔍 错误类型: 地区限制")
                elif 'json' in error_msg.lower():
                    print(f"      🔍 错误类型: JSON解析失败")
                elif 'timeout' in error_msg.lower():
                    print(f"      🔍 错误类型: 连接超时")
                else:
                    print(f"      🔍 错误类型: 其他")
    
    print("\n" + "=" * 60)
    print("🎯 测试完成！")

if __name__ == "__main__":
    test_bilibili_mobile_strategies()
