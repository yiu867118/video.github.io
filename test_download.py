#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的下载器测试脚本
用于快速验证下载功能是否正常
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.video_downloader import download_video
import tempfile
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_download():
    """测试下载功能"""
    # 测试URL（哔哩哔哩官方测试视频）
    test_url = "https://www.bilibili.com/video/BV1Ps4y1r7yV"
    
    try:
        logger.info("🧪 开始测试下载功能")
        logger.info(f"📋 测试URL: {test_url}")
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        output_template = os.path.join(temp_dir, "test_video.%(ext)s")
        
        # 进度回调
        def progress_callback(progress):
            status = progress.get('status', 'unknown')
            percent = progress.get('percent', 0)
            message = progress.get('message', '')
            logger.info(f"📊 进度: {status} {percent}% - {message}")
        
        # 执行下载
        result = download_video(test_url, output_template, progress_callback)
        
        if result and os.path.exists(result):
            file_size = os.path.getsize(result) / 1024 / 1024
            logger.info(f"✅ 下载成功!")
            logger.info(f"📁 文件路径: {result}")
            logger.info(f"📊 文件大小: {file_size:.2f} MB")
            return True
        else:
            logger.error("❌ 下载失败: 文件不存在")
            return False
            
    except Exception as e:
        logger.error(f"❌ 下载测试失败: {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🚀 视频下载器功能测试")
    print("=" * 50)
    
    success = test_download()
    
    print("=" * 50)
    if success:
        print("🎉 测试成功! 下载功能正常")
    else:
        print("💥 测试失败! 请检查错误信息")
    
    input("\n按回车键退出...")
