#!/usr/bin/env python3
"""
快速下载测试脚本
用于验证修复效果
"""

import os
import sys
import tempfile
import logging

# 添加项目路径
sys.path.append('.')

from app.video_downloader import get_downloader

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_quick_download():
    """快速下载测试"""
    print("🧪 === 快速下载测试 ===")
    
    # 测试URL - 使用一个相对简单的B站视频
    test_urls = [
        "https://www.bilibili.com/video/BV1xx411c7mu",  # B站测试视频1
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",   # YouTube测试视频
    ]
    
    downloader = get_downloader()
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n📺 测试 {i}: {url}")
        
        try:
            # 创建临时目录
            temp_dir = tempfile.mkdtemp()
            output_template = os.path.join(temp_dir, "%(title)s.%(ext)s")
            
            print(f"📁 临时目录: {temp_dir}")
            
            # 简单的进度回调
            def progress_callback(progress):
                status = progress.get('status', 'unknown')
                percent = progress.get('percent', 0)
                message = progress.get('message', '')
                print(f"📊 {status}: {percent:.1f}% - {message}")
            
            # 执行下载
            print("🎯 开始下载...")
            result_path = downloader.download_video(url, output_template, progress_callback)
            
            if result_path and os.path.exists(result_path):
                file_size = os.path.getsize(result_path) / (1024 * 1024)  # MB
                filename = os.path.basename(result_path)
                print(f"✅ 下载成功!")
                print(f"   文件名: {filename}")
                print(f"   大小: {file_size:.2f} MB")
                print(f"   路径: {result_path}")
                
                # 清理测试文件
                try:
                    os.remove(result_path)
                    os.rmdir(temp_dir)
                    print("🗑️ 测试文件已清理")
                except:
                    pass
            else:
                print("❌ 下载失败或文件不存在")
                
        except Exception as e:
            print(f"❌ 下载异常: {str(e)}")
            
        print("-" * 50)

def test_format_listing():
    """测试格式列举功能"""
    print("\n🧪 === 格式列举测试 ===")
    
    downloader = get_downloader()
    test_url = "https://www.bilibili.com/video/BV1xx411c7mu"
    
    try:
        print(f"📺 测试URL: {test_url}")
        formats = downloader._list_available_formats(test_url, 'bilibili')
        print(f"📋 发现 {len(formats)} 个可用格式")
    except Exception as e:
        print(f"❌ 格式列举失败: {str(e)}")

if __name__ == "__main__":
    print("🚀 === 视频下载器快速测试 ===")
    
    # 测试格式列举
    test_format_listing()
    
    # 测试实际下载
    test_quick_download()
    
    print("\n✅ === 测试完成 ===")
