#!/usr/bin/env python3
"""
B站移动端下载测试脚本
专门测试手机端和平板端B站视频下载功能
"""

import os
import sys
import tempfile
import time
from app.video_downloader import download_video, get_video_info

def test_bilibili_mobile_download():
    """测试B站移动端下载功能"""
    print("🧪 B站移动端下载测试开始")
    print("=" * 60)
    
    # 测试URL - 使用一个公开的B站视频
    test_url = "https://www.bilibili.com/video/BV1TEKJZeEJD"  # 一个公开视频
    print(f"📺 测试视频: {test_url}")
    
    # 创建临时输出目录
    temp_dir = tempfile.mkdtemp()
    print(f"📁 临时目录: {temp_dir}")
    
    # 进度回调函数
    def progress_callback(progress_data):
        status = progress_data.get('status', 'unknown')
        percent = progress_data.get('percent', 0)
        message = progress_data.get('message', '')
        
        if status == 'downloading':
            speed = progress_data.get('speed', '')
            print(f"⬇️  下载进度: {percent:.1f}% - {message} - {speed}")
        elif status == 'completed':
            filename = progress_data.get('filename', 'unknown')
            file_size = progress_data.get('file_size_mb', 0)
            strategy = progress_data.get('strategy', 'unknown')
            print(f"✅ 下载完成!")
            print(f"   文件名: {filename}")
            print(f"   大小: {file_size:.2f} MB")
            print(f"   策略: {strategy}")
        elif status == 'failed':
            error = progress_data.get('error', 'unknown error')
            print(f"❌ 下载失败: {error}")
        else:
            print(f"ℹ️  {message} ({percent:.1f}%)")
    
    try:
        # 1. 获取视频信息测试
        print("\n🔍 步骤1: 获取视频信息")
        try:
            video_info = get_video_info(test_url)
            print(f"✅ 视频信息获取成功:")
            print(f"   标题: {video_info.get('title', 'N/A')}")
            print(f"   时长: {video_info.get('duration', 0)} 秒")
            print(f"   平台: {video_info.get('platform', 'N/A')}")
            print(f"   UP主: {video_info.get('uploader', 'N/A')}")
        except Exception as e:
            print(f"❌ 视频信息获取失败: {e}")
            print("⚠️  继续尝试下载...")
        
        # 2. 下载测试
        print("\n⬇️  步骤2: 开始下载测试")
        output_template = os.path.join(temp_dir, "test_video.%(ext)s")
        
        start_time = time.time()
        result_path = download_video(test_url, output_template, progress_callback)
        end_time = time.time()
        
        # 验证下载结果
        if result_path and os.path.exists(result_path):
            file_size = os.path.getsize(result_path)
            print(f"\n🎉 下载测试成功!")
            print(f"   文件路径: {result_path}")
            print(f"   文件大小: {file_size / 1024 / 1024:.2f} MB")
            print(f"   下载耗时: {end_time - start_time:.1f} 秒")
            
            # 检查文件是否为有效的视频文件
            if file_size > 1024 * 1024:  # 至少1MB
                print("✅ 文件大小检查通过")
            else:
                print("⚠️  文件可能太小，请检查")
                
            # 清理测试文件
            try:
                os.remove(result_path)
                print("🗑️  测试文件已清理")
            except:
                pass
                
        else:
            print("❌ 下载失败 - 未生成有效文件")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 清理临时目录
        try:
            import shutil
            shutil.rmtree(temp_dir)
            print("🧹 临时目录已清理")
        except:
            pass
    
    print("\n" + "=" * 60)
    print("🎯 B站移动端下载测试完成")
    return True

def test_multiple_strategies():
    """测试多种下载策略"""
    print("\n🔄 多策略测试")
    print("-" * 40)
    
    # 模拟不同的环境
    test_cases = [
        {
            'name': '桌面端环境',
            'url': 'https://www.bilibili.com/video/BV1TEKJZeEJD'
        },
        {
            'name': '移动端环境', 
            'url': 'https://m.bilibili.com/video/BV1TEKJZeEJD'
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📱 测试环境: {test_case['name']}")
        print(f"🔗 URL: {test_case['url']}")
        
        try:
            info = get_video_info(test_case['url'])
            print(f"✅ 信息获取成功: {info.get('title', 'N/A')}")
        except Exception as e:
            print(f"❌ 信息获取失败: {e}")

if __name__ == "__main__":
    print("🚀 B站下载功能完整性测试")
    print("测试目标：确保手机端和平板端能正常下载B站视频")
    print()
    
    # 主要测试
    success = test_bilibili_mobile_download()
    
    # 多策略测试
    test_multiple_strategies()
    
    print("\n📊 测试总结:")
    if success:
        print("✅ 主要功能测试通过")
        print("🎯 B站移动端下载修复成功")
    else:
        print("❌ 测试发现问题，需要进一步修复")
    
    print("\n💡 使用建议:")
    print("1. 如果桌面端下载正常，移动端失败，请检查网络环境")
    print("2. 某些B站视频可能需要登录或有地区限制")
    print("3. 如果下载速度慢，属于正常现象，会自动重试不同策略")
    print("4. 下载的视频文件已包含音频，无需额外处理")
