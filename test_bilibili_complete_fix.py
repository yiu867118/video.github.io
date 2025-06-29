#!/usr/bin/env python3
"""
B站手机端/平板端下载测试脚本
测试修复后的下载器是否能正确下载B站视频
"""

import sys
import os
import tempfile
import logging
from pathlib import Path

# 添加应用目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from video_downloader import get_downloader, get_video_info, download_video

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_bilibili_mobile_download():
    """测试B站手机端下载功能"""
    # 测试URL（可以替换为实际的B站视频链接）
    test_urls = [
        "https://www.bilibili.com/video/BV1GJ411x7h7",  # 经典测试视频
        "https://b23.tv/OmaGDGh",  # 短链接
        # 可以添加更多测试URL
    ]
    
    logger.info("🎯 开始测试B站手机端/平板端下载修复")
    logger.info("=" * 50)
    
    for i, url in enumerate(test_urls, 1):
        logger.info(f"\n📱 测试 {i}/{len(test_urls)}: {url}")
        
        try:
            # 测试获取视频信息
            logger.info("🔍 获取视频信息...")
            info = get_video_info(url)
            logger.info(f"✅ 视频标题: {info.get('title', 'N/A')}")
            logger.info(f"✅ 视频时长: {info.get('duration', 0)}秒")
            logger.info(f"✅ 平台: {info.get('platform', 'N/A')}")
            logger.info(f"✅ 上传者: {info.get('uploader', 'N/A')}")
            
            # 创建临时下载目录
            with tempfile.TemporaryDirectory() as temp_dir:
                output_template = os.path.join(temp_dir, "%(title)s.%(ext)s")
                
                # 进度回调函数
                def progress_callback(progress):
                    status = progress.get('status', 'unknown')
                    percent = progress.get('percent', 0)
                    message = progress.get('message', '')
                    
                    if status == 'downloading':
                        logger.info(f"📥 下载进度: {percent:.1f}% - {message}")
                    elif status == 'completed':
                        filename = progress.get('filename', 'N/A')
                        file_size = progress.get('file_size_mb', 0)
                        strategy = progress.get('strategy', 'N/A')
                        logger.info(f"🎉 下载完成！")
                        logger.info(f"   文件名: {filename}")
                        logger.info(f"   大小: {file_size:.2f} MB")
                        logger.info(f"   策略: {strategy}")
                    elif status == 'failed':
                        error = progress.get('error', 'N/A')
                        logger.error(f"❌ 下载失败: {error}")
                
                # 执行下载
                logger.info("🚀 开始下载...")
                result_path = download_video(url, output_template, progress_callback)
                
                if result_path and os.path.exists(result_path):
                    file_size = os.path.getsize(result_path)
                    logger.info(f"✅ 下载成功！")
                    logger.info(f"   文件路径: {result_path}")
                    logger.info(f"   文件大小: {file_size / 1024 / 1024:.2f} MB")
                    
                    # 检查文件是否为有效的视频文件
                    if file_size > 100 * 1024:  # 至少100KB
                        logger.info("✅ 文件大小正常，可能是有效的视频文件")
                    else:
                        logger.warning("⚠️ 文件大小较小，可能不是完整的视频文件")
                else:
                    logger.error("❌ 下载失败，未获得有效文件")
                    
        except Exception as e:
            logger.error(f"❌ 测试失败: {str(e)}")
        
        logger.info("-" * 50)
    
    logger.info("🎯 测试完成！")

def test_get_downloader_info():
    """测试下载器信息"""
    logger.info("🔧 下载器信息:")
    downloader = get_downloader()
    logger.info(f"   系统信息: {downloader.system_info}")
    logger.info(f"   FFmpeg可用: {downloader.system_info.get('ffmpeg_available', False)}")

if __name__ == "__main__":
    print("🎯 B站手机端/平板端下载修复测试")
    print("=" * 60)
    
    # 测试下载器信息
    test_get_downloader_info()
    print()
    
    # 测试B站下载
    test_bilibili_mobile_download()
    
    print("\n🎯 测试完成！如果下载成功，说明修复有效。")
    print("💡 建议：在实际手机端Web界面中测试完整的下载流程。")
