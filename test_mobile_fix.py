#!/usr/bin/env python3
"""
B站手机端/平板端下载修复验证测试
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

import tempfile
import time
from video_downloader import download_video

def simulate_mobile_download():
    """模拟手机端下载过程"""
    
    # 使用一个确认可用的B站视频
    test_url = "https://www.bilibili.com/video/BV1xx411c7mu"
    
    print("🎯 B站手机端下载修复验证")
    print("=" * 50)
    print(f"🔗 测试视频: {test_url}")
    print("-" * 50)
    
    # 模拟进度回调函数
    def progress_callback(progress_info):
        status = progress_info.get('status', 'unknown')
        percent = progress_info.get('percent', 0)
        message = progress_info.get('message', '')
        
        if status == 'starting':
            print(f"🚀 开始: {message}")
        elif status == 'downloading':
            print(f"📥 进度: {percent:.1f}% - {message}")
        elif status == 'completed':
            filename = progress_info.get('filename', 'unknown')
            file_size = progress_info.get('file_size_mb', 0)
            strategy = progress_info.get('strategy', 'unknown')
            print(f"✅ 完成: {filename}")
            print(f"📊 大小: {file_size:.2f} MB")
            print(f"🎯 成功策略: {strategy}")
        elif status == 'failed':
            error = progress_info.get('error', 'unknown error')
            print(f"❌ 失败: {error}")
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_template = os.path.join(temp_dir, "test_video.%(ext)s")
            
            print("🔄 开始下载...")
            start_time = time.time()
            
            # 执行下载
            result_path = download_video(test_url, output_template, progress_callback)
            
            elapsed = time.time() - start_time
            
            if result_path and os.path.exists(result_path):
                file_size = os.path.getsize(result_path)
                filename = os.path.basename(result_path)
                
                print("\n" + "=" * 50)
                print("🎉 下载成功！")
                print(f"📁 文件: {filename}")
                print(f"📊 大小: {file_size/1024/1024:.2f} MB")
                print(f"⏱️ 耗时: {elapsed:.1f}秒")
                print(f"📍 路径: {result_path}")
                print("✅ B站手机端下载修复验证通过！")
                return True
            else:
                print("\n❌ 下载失败：未找到输出文件")
                return False
                
    except Exception as e:
        print(f"\n❌ 下载异常: {str(e)}")
        return False

def test_multiple_bilibili_videos():
    """测试多个B站视频"""
    
    test_videos = [
        "https://www.bilibili.com/video/BV1xx411c7mu",  # 经典视频1
        "https://www.bilibili.com/video/BV1GJ411x7h7",  # 经典视频2
    ]
    
    print("\n" + "=" * 60)
    print("🎯 多视频测试开始")
    print("=" * 60)
    
    success_count = 0
    total_count = len(test_videos)
    
    for i, video_url in enumerate(test_videos, 1):
        print(f"\n📹 测试视频 {i}/{total_count}: {video_url}")
        print("-" * 40)
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                output_template = os.path.join(temp_dir, f"video_{i}.%(ext)s")
                
                def simple_callback(info):
                    if info.get('status') == 'completed':
                        print(f"✅ 视频 {i} 下载成功")
                    elif info.get('status') == 'failed':
                        print(f"❌ 视频 {i} 下载失败")
                
                result = download_video(video_url, output_template, simple_callback)
                
                if result and os.path.exists(result):
                    success_count += 1
                    file_size = os.path.getsize(result) / 1024 / 1024
                    print(f"📊 文件大小: {file_size:.2f} MB")
                else:
                    print(f"❌ 视频 {i} 下载失败")
                    
        except Exception as e:
            print(f"❌ 视频 {i} 异常: {str(e)[:100]}...")
    
    print(f"\n" + "=" * 60)
    print(f"📊 测试结果: {success_count}/{total_count} 成功")
    
    if success_count == total_count:
        print("🎉 所有测试通过！B站手机端下载完全修复！")
    elif success_count > 0:
        print("⚠️ 部分测试通过，仍有改进空间")
    else:
        print("❌ 所有测试失败，需要进一步修复")
    
    return success_count / total_count

if __name__ == "__main__":
    print("🔧 B站手机端/平板端下载修复验证")
    print("=" * 60)
    
    # 单视频详细测试
    single_success = simulate_mobile_download()
    
    # 多视频测试
    multi_success_rate = test_multiple_bilibili_videos()
    
    print(f"\n" + "=" * 60)
    print("📋 最终总结")
    print("=" * 60)
    print(f"单视频测试: {'✅ 通过' if single_success else '❌ 失败'}")
    print(f"多视频测试: {multi_success_rate*100:.0f}% 成功率")
    
    if single_success and multi_success_rate > 0.5:
        print("🎉 B站手机端下载修复基本成功！")
    else:
        print("⚠️ 仍需进一步优化修复策略")
