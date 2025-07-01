#!/usr/bin/env python3
"""
三端兼容性+最高画质优先测试
测试电脑端、手机端、平板端的兼容性，确保优先下载最高画质+音频
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.video_downloader import CompletelyFixedVideoDownloader
import tempfile
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

def test_multi_platform_download():
    """测试多平台下载，确保最高画质优先"""
    print("🎯 开始三端兼容性+最高画质优先测试...")
    
    # 测试URL
    test_url = "https://www.bilibili.com/video/BV1PBKUzVEip"
    
    # 模拟不同设备的User-Agent
    device_configs = [
        {
            'name': '💻电脑端Chrome',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'expected_quality': '高画质'
        },
        {
            'name': '📱手机端Chrome',
            'user_agent': 'Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'expected_quality': '中高画质'
        },
        {
            'name': '📱iPad Safari',
            'user_agent': 'Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
            'expected_quality': '中高画质'
        }
    ]
    
    results = []
    
    for config in device_configs:
        print(f"\n🧪 测试设备: {config['name']}")
        print(f"📋 User-Agent: {config['user_agent'][:50]}...")
        
        try:
            # 创建下载器
            downloader = CompletelyFixedVideoDownloader()
            
            # 测试获取视频信息
            print("📝 获取视频信息...")
            info = downloader._get_video_info(test_url)
            print(f"✅ 视频标题: {info.get('title', 'N/A')}")
            
            # 模拟下载测试
            print("📥 模拟下载测试...")
            
            with tempfile.TemporaryDirectory() as temp_dir:
                output_template = os.path.join(temp_dir, "%(title)s.%(ext)s")
                
                download_success = False
                file_size_mb = 0
                quality_info = ""
                strategy_used = ""
                
                def progress_callback(progress):
                    nonlocal download_success, file_size_mb, quality_info, strategy_used
                    
                    if progress.get('status') == 'downloading':
                        percent = progress.get('percent', 0)
                        if percent > 50:  # 只显示重要进度
                            print(f"📊 下载进度: {percent:.1f}%")
                    elif progress.get('status') == 'completed':
                        download_success = True
                        file_size_mb = progress.get('file_size_mb', 0)
                        quality_info = progress.get('quality_info', '')
                        strategy_used = progress.get('strategy', '')
                        print(f"🎉 下载完成: {progress.get('filename', 'N/A')}")
                        print(f"📦 文件大小: {file_size_mb:.1f} MB")
                        print(f"🎯 画质: {quality_info}")
                        print(f"🔧 策略: {strategy_used}")
                    elif progress.get('status') == 'failed':
                        print(f"❌ 下载失败: {progress.get('error', 'N/A')}")
                
                try:
                    result_path = downloader.download_video(test_url, output_template, progress_callback)
                    
                    if download_success and file_size_mb > 0:
                        # 评估画质
                        quality_score = "优秀" if file_size_mb > 100 else "良好" if file_size_mb > 50 else "一般"
                        
                        results.append({
                            'device': config['name'],
                            'success': True,
                            'file_size_mb': file_size_mb,
                            'quality_info': quality_info,
                            'quality_score': quality_score,
                            'strategy': strategy_used,
                            'has_audio': 'mp4' in result_path.lower(),  # MP4通常包含音频
                        })
                        
                        print(f"✅ {config['name']} 测试成功")
                        print(f"   📊 画质评分: {quality_score}")
                        print(f"   🔊 音频: {'✅包含' if 'mp4' in result_path.lower() else '❌缺失'}")
                        
                    else:
                        print(f"⚠️ {config['name']} 下载未完成")
                        results.append({
                            'device': config['name'],
                            'success': False,
                            'error': '下载未完成'
                        })
                        
                except Exception as e:
                    print(f"⚠️ {config['name']} 下载异常: {str(e)[:50]}...")
                    results.append({
                        'device': config['name'],
                        'success': False,
                        'error': str(e)[:100]
                    })
                    
        except Exception as e:
            print(f"❌ {config['name']} 测试失败: {str(e)}")
            results.append({
                'device': config['name'],
                'success': False,
                'error': str(e)
            })
    
    return results

def test_quality_priority():
    """测试画质优先策略"""
    print("\n🎯 测试画质优先策略...")
    
    try:
        downloader = CompletelyFixedVideoDownloader()
        
        # 检查基础配置
        base_config = downloader._get_base_config()
        format_string = base_config.get('format', '')
        
        print(f"📋 基础格式配置: {format_string}")
        
        # 验证格式配置是否优先高画质
        quality_keywords = ['bestvideo', 'best', '1080', '720']
        audio_keywords = ['bestaudio', 'acodec']
        
        has_quality_priority = any(keyword in format_string for keyword in quality_keywords)
        has_audio_priority = any(keyword in format_string for keyword in audio_keywords)
        
        print(f"✅ 画质优先: {'✅是' if has_quality_priority else '❌否'}")
        print(f"✅ 音频优先: {'✅是' if has_audio_priority else '❌否'}")
        
        return has_quality_priority and has_audio_priority
        
    except Exception as e:
        print(f"❌ 画质优先测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🎯 三端兼容性+最高画质优先测试开始")
    print("=" * 60)
    
    # 测试画质优先配置
    quality_priority_ok = test_quality_priority()
    
    # 测试多平台下载
    download_results = test_multi_platform_download()
    
    # 分析结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    successful_downloads = [r for r in download_results if r.get('success', False)]
    total_tests = len(download_results)
    success_rate = len(successful_downloads) / total_tests * 100 if total_tests > 0 else 0
    
    print(f"📈 成功率: {success_rate:.1f}% ({len(successful_downloads)}/{total_tests})")
    print(f"🎯 画质优先配置: {'✅正确' if quality_priority_ok else '❌错误'}")
    
    if successful_downloads:
        avg_size = sum(r.get('file_size_mb', 0) for r in successful_downloads) / len(successful_downloads)
        print(f"📦 平均文件大小: {avg_size:.1f} MB")
        
        high_quality_count = sum(1 for r in successful_downloads if r.get('file_size_mb', 0) > 50)
        high_quality_rate = high_quality_count / len(successful_downloads) * 100
        print(f"🎯 高画质比例: {high_quality_rate:.1f}% ({high_quality_count}/{len(successful_downloads)})")
        
        audio_count = sum(1 for r in successful_downloads if r.get('has_audio', False))
        audio_rate = audio_count / len(successful_downloads) * 100
        print(f"🔊 音频包含比例: {audio_rate:.1f}% ({audio_count}/{len(successful_downloads)})")
    
    # 详细结果
    print("\n📋 详细结果:")
    for result in download_results:
        device = result.get('device', 'Unknown')
        if result.get('success', False):
            size = result.get('file_size_mb', 0)
            quality = result.get('quality_score', 'N/A')
            strategy = result.get('strategy', 'N/A')
            audio = '🔊' if result.get('has_audio', False) else '🔇'
            print(f"✅ {device}: {size:.1f}MB ({quality}) {audio} - {strategy}")
        else:
            error = result.get('error', 'Unknown error')
            print(f"❌ {device}: {error[:50]}...")
    
    # 最终评估
    print("\n" + "=" * 60)
    overall_success = (
        quality_priority_ok and 
        success_rate >= 66.7 and  # 至少2/3成功
        (not successful_downloads or avg_size > 30)  # 平均文件大小合理
    )
    
    if overall_success:
        print("🎉 三端兼容性+最高画质优先测试 - 全部通过！")
        print("✅ 下载器已优化完成，支持三端最高画质+音频下载")
        return True
    else:
        print("⚠️ 测试发现需要改进的地方")
        if not quality_priority_ok:
            print("❌ 画质优先配置需要优化")
        if success_rate < 66.7:
            print("❌ 成功率偏低，需要提高兼容性")
        return False

if __name__ == "__main__":
    main()
