#!/usr/bin/env python3
"""测试修复后的B站下载功能"""

import sys
import os
import logging

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.video_downloader import SimpleVideoDownloader

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_bilibili_download():
    """测试B站视频下载"""
    downloader = SimpleVideoDownloader()
    
    test_url = "https://www.bilibili.com/video/BV1fT421a71N"
    
    print("🚀 测试B站视频下载")
    print(f"🎯 测试URL: {test_url}")
    print("-" * 60)
    
    def progress_callback(data):
        status = data.get('status', '')
        percent = data.get('percent', 0)
        message = data.get('message', '')
        
        if status == 'downloading':
            print(f"⬇️ 下载中: {percent}% - {message}")
        elif status == 'completed':
            filename = data.get('filename', '未知')
            file_size = data.get('file_size_mb', 0)
            strategy = data.get('strategy', '未知')
            print(f"✅ 下载完成: {filename}")
            print(f"   文件大小: {file_size:.2f}MB")
            print(f"   使用策略: {strategy}")
        elif status == 'error':
            error = data.get('error', '未知错误')
            print(f"❌ 下载失败: {error}")
        else:
            print(f"ℹ️ {status}: {message}")
    
    try:
        # 创建输出模板
        import tempfile
        temp_dir = tempfile.gettempdir()
        output_template = os.path.join(temp_dir, "%(title)s.%(ext)s")
        
        result = downloader.download_video(test_url, output_template, progress_callback)
        if result:
            print(f"\n🎉 下载成功!")
            print(f"📁 文件路径: {result}")
            
            # 检查文件是否存在
            if os.path.exists(result):
                file_size = os.path.getsize(result) / (1024 * 1024)
                print(f"📊 文件大小: {file_size:.2f}MB")
                print(f"📝 文件名: {os.path.basename(result)}")
            else:
                print("⚠️ 警告: 文件路径不存在")
        else:
            print("❌ 下载失败，返回None")
            
    except Exception as e:
        print(f"💥 下载异常: {e}")

if __name__ == "__main__":
    test_bilibili_download()
