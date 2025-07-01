#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站视频下载 - 移动端兼容性测试（最新视频）
"""

import os
import sys
import tempfile
import time
import json
from typing import Dict, Any, Optional, Callable

# 添加app目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from video_downloader import get_downloader, get_video_info

def progress_callback(info: Dict[str, Any]) -> None:
    """进度回调函数"""
    status = info.get('status', 'unknown')
    percent = info.get('percent', 0)
    message = info.get('message', '')
    
    if status == 'completed':
        print(f"✅ 下载完成！文件：{info.get('filename', 'N/A')}")
        print(f"   大小：{info.get('file_size_mb', 0):.2f} MB")
        print(f"   策略：{info.get('strategy', 'N/A')}")
    elif status == 'failed':
        print(f"❌ 下载失败：{info.get('error', 'N/A')}")
    else:
        print(f"📱 {message} ({percent:.1f}%)")

def test_single_video(url: str, test_name: str) -> bool:
    """测试单个视频，返回是否成功"""
    print(f"\n{'='*50}")
    print(f"🎯 {test_name}")
    print(f"🔗 {url}")
    print(f"{'='*50}")
    
    temp_dir = tempfile.mkdtemp(prefix=f"bilibili_mobile_test_")
    output_template = os.path.join(temp_dir, "%(title)s.%(ext)s")
    
    try:
        # 获取视频信息
        print("📋 获取视频信息...")
        try:
            video_info = get_video_info(url)
            print(f"   ✅ 标题：{video_info.get('title', 'N/A')}")
            print(f"   ⏱️ 时长：{video_info.get('duration', 0)}秒")
        except Exception as e:
            print(f"   ⚠️ 信息获取失败：{e}")
        
        # 开始下载
        print("📥 开始下载...")
        downloader = get_downloader()
        file_path = downloader.download_video(url, output_template, progress_callback)
        
        if file_path and os.path.exists(file_path):
            file_size_mb = os.path.getsize(file_path) / 1024 / 1024
            print(f"✅ 下载成功！大小：{file_size_mb:.2f} MB")
            
            # 清理文件
            try:
                os.remove(file_path)
                os.rmdir(temp_dir)
            except:
                pass
            return True
        else:
            print("❌ 下载失败：未生成有效文件")
            return False
            
    except Exception as e:
        print(f"❌ 下载异常：{e}")
        # 清理临时目录
        try:
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except:
            pass
        return False

def run_mobile_compatibility_test():
    """专门测试移动端兼容性"""
    print("📱 B站移动端兼容性测试")
    print(f"⏰ 测试时间：{time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_cases = [
        {
            'name': '桌面版链接',
            'url': 'https://www.bilibili.com/video/BV1xx411c7mD'  # 之前成功的视频
        },
        {
            'name': '移动版链接(同一视频)',
            'url': 'https://m.bilibili.com/video/BV1xx411c7mD'  # 相同视频的移动版
        },
        {
            'name': 'B站热门视频1',
            'url': 'https://www.bilibili.com/video/BV1uv411q7Mv'  # 之前成功的视频
        },
        {
            'name': 'B站热门视频1(移动版)',
            'url': 'https://m.bilibili.com/video/BV1uv411q7Mv'  # 相同视频的移动版
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📲 测试 {i}/{len(test_cases)}")
        if test_single_video(test_case['url'], test_case['name']):
            success_count += 1
        
        # 测试间隔
        if i < len(test_cases):
            print("⏳ 等待2秒...")
            time.sleep(2)
    
    # 结果总结
    print(f"\n{'='*60}")
    print(f"📊 移动端兼容性测试结果")
    print(f"{'='*60}")
    print(f"✅ 总测试：{len(test_cases)}")
    print(f"✅ 成功：{success_count}")
    print(f"❌ 失败：{len(test_cases) - success_count}")
    print(f"📈 成功率：{success_count/len(test_cases)*100:.1f}%")
    
    if success_count >= len(test_cases) * 0.75:  # 75%以上成功率
        print(f"\n🎉 移动端兼容性良好！")
        return True
    else:
        print(f"\n⚠️ 移动端兼容性需要改进")
        return False

if __name__ == '__main__':
    try:
        success = run_mobile_compatibility_test()
        if success:
            print(f"\n✅ 移动端兼容性测试通过")
            sys.exit(0)
        else:
            print(f"\n⚠️ 移动端兼容性测试需要优化")
            sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n⏹️ 测试中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n💀 测试异常：{e}")
        sys.exit(1)
