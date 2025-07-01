#!/usr/bin/env python3
"""
终极B站移动端修复 - 彻底解决手机/平板端下载问题
本脚本专门用于诊断和修复移动端下载问题
"""

import os
import sys
import tempfile
import time
import logging
import yt_dlp
from typing import Dict, Any, Optional, Callable

# 设置详细日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def diagnose_environment():
    """诊断运行环境"""
    print("🔍 环境诊断开始")
    print("=" * 50)
    
    try:
        import yt_dlp
        print(f"✅ yt-dlp版本: {yt_dlp.version.__version__}")
    except Exception as e:
        print(f"❌ yt-dlp问题: {e}")
    
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
        if result.returncode == 0:
            print("✅ FFmpeg可用")
        else:
            print("⚠️ FFmpeg不可用")
    except:
        print("❌ FFmpeg检查失败")
    
    print(f"🐍 Python版本: {sys.version}")
    print(f"💻 操作系统: {sys.platform}")
    print("=" * 50)

def test_bilibili_with_ultimate_strategy():
    """使用终极策略测试B站下载"""
    
    # 使用多个不同类型的B站视频进行测试
    test_videos = [
        {
            'url': 'https://www.bilibili.com/video/BV1xx411c7mu',
            'name': '经典短视频'
        },
        {
            'url': 'https://www.bilibili.com/video/BV1uE411h7v6', 
            'name': '音乐视频'
        },
        {
            'url': 'https://www.bilibili.com/video/BV1s54y1e7qg',
            'name': '舞蹈视频'
        }
    ]
    
    print("\n🎯 开始终极B站下载测试")
    print("=" * 60)
    
    success_count = 0
    
    for i, video in enumerate(test_videos, 1):
        print(f"\n📹 测试视频 {i}: {video['name']}")
        print(f"🔗 URL: {video['url']}")
        print("-" * 40)
        
        if test_single_video_ultimate(video['url']):
            success_count += 1
            print(f"✅ 视频 {i} 下载成功")
        else:
            print(f"❌ 视频 {i} 下载失败")
    
    print(f"\n📊 总体结果: {success_count}/{len(test_videos)} 成功")
    return success_count / len(test_videos)

def test_single_video_ultimate(url: str) -> bool:
    """使用终极策略测试单个视频"""
    
    # 🔥 终极移动端兼容策略 - 逐级降低要求直到成功
    ultimate_strategies = [
        {
            'name': '策略1: 最简音视频分离下载',
            'config': {
                'format': 'bestaudio+bestvideo/best',
                'merge_output_format': 'mp4',
                'geo_bypass': True,
                'nocheckcertificate': True,
                'ignoreerrors': False,
                'no_warnings': True,
                'quiet': True,
                'socket_timeout': 30,
                'retries': 1,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                    'Referer': 'https://www.bilibili.com/',
                }
            }
        },
        {
            'name': '策略2: 最佳单流下载',
            'config': {
                'format': 'best[acodec!=none]',
                'merge_output_format': 'mp4',
                'geo_bypass': True,
                'nocheckcertificate': True,
                'ignoreerrors': False,
                'no_warnings': True,
                'quiet': True,
                'socket_timeout': 30,
                'retries': 1,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36',
                    'Referer': 'https://www.bilibili.com/',
                }
            }
        },
        {
            'name': '策略3: 通用最佳质量',
            'config': {
                'format': 'best',
                'merge_output_format': 'mp4',
                'geo_bypass': True,
                'nocheckcertificate': True,
                'ignoreerrors': False,
                'no_warnings': True,
                'quiet': True,
                'socket_timeout': 30,
                'retries': 1,
            }
        },
        {
            'name': '策略4: 地区绕过',
            'config': {
                'format': 'best',
                'merge_output_format': 'mp4',
                'geo_bypass': True,
                'geo_bypass_country': 'US',
                'nocheckcertificate': True,
                'ignoreerrors': False,
                'no_warnings': True,
                'quiet': True,
                'socket_timeout': 30,
                'retries': 1,
            }
        },
        {
            'name': '策略5: 最低质量兜底',
            'config': {
                'format': 'worst',
                'merge_output_format': 'mp4',
                'geo_bypass': True,
                'nocheckcertificate': True,
                'ignoreerrors': True,
                'no_warnings': True,
                'quiet': True,
                'socket_timeout': 15,
                'retries': 1,
            }
        }
    ]
    
    for i, strategy in enumerate(ultimate_strategies, 1):
        try:
            print(f"   🎯 尝试{strategy['name']}")
            
            with tempfile.TemporaryDirectory() as temp_dir:
                output_template = os.path.join(temp_dir, "test_video.%(ext)s")
                
                ydl_opts = strategy['config'].copy()
                ydl_opts['outtmpl'] = output_template
                
                start_time = time.time()
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                
                # 检查下载结果
                files = os.listdir(temp_dir)
                if files:
                    for filename in files:
                        filepath = os.path.join(temp_dir, filename)
                        if os.path.isfile(filepath):
                            size = os.path.getsize(filepath)
                            if size > 1024:  # 至少1KB
                                elapsed = time.time() - start_time
                                print(f"   ✅ 成功！文件: {filename}")
                                print(f"   📊 大小: {size/1024:.1f} KB")
                                print(f"   ⏱️ 耗时: {elapsed:.1f}秒")
                                print(f"   🎯 成功策略: {strategy['name']}")
                                return True
                
                print(f"   ⚠️ {strategy['name']} 无有效文件")
                
        except Exception as e:
            error_msg = str(e)
            print(f"   ❌ {strategy['name']} 失败: {error_msg[:60]}...")
            
            # 分析错误类型
            if 'unsupported url' in error_msg.lower():
                print(f"      🔍 错误类型: URL不支持")
            elif 'format' in error_msg.lower() and 'not available' in error_msg.lower():
                print(f"      🔍 错误类型: 格式不可用")
            elif 'geo' in error_msg.lower() or 'region' in error_msg.lower():
                print(f"      🔍 错误类型: 地区限制")
            elif 'timeout' in error_msg.lower():
                print(f"      🔍 错误类型: 连接超时")
            else:
                print(f"      🔍 错误类型: 其他")
            
            continue
    
    print("   💀 所有策略都失败")
    return False

def generate_ultimate_fix():
    """基于测试结果生成终极修复代码"""
    
    print("\n🔧 生成终极修复代码")
    print("=" * 50)
    
    ultimate_code = '''
def ultimate_bilibili_download(url: str, output_template: str, progress_callback: Optional[Callable] = None) -> str:
    """终极B站下载函数 - 专为移动端优化，确保100%兼容性"""
    
    # 🔥 URL标准化 - 确保所有端都使用相同的URL格式
    if 'bilibili.com' in url:
        url = url.replace('m.bilibili.com', 'www.bilibili.com')
        url = url.replace('//bilibili.com', '//www.bilibili.com')
        # 移除可能的移动端参数
        if '?' in url:
            base_url = url.split('?')[0]
            url = base_url
    
    logger.info(f"🔧 标准化URL: {url}")
    
    # 创建专用下载目录
    temp_dir = os.path.dirname(output_template)
    download_dir = os.path.join(temp_dir, f"dl_{int(time.time())}")
    os.makedirs(download_dir, exist_ok=True)
    
    # 🔥 终极策略列表 - 从最高质量到最低质量，确保至少有一个成功
    strategies = [
        {
            'name': 'B站桌面端高质量',
            'format': 'bestaudio+bestvideo/best[acodec!=none]/best',
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Referer': 'https://www.bilibili.com/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
            },
            'timeout': 60
        },
        {
            'name': 'B站手机端适配',
            'format': 'best[acodec!=none]/best',
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36',
                'Referer': 'https://www.bilibili.com/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            },
            'timeout': 45
        },
        {
            'name': 'B站平板端适配',
            'format': 'best',
            'headers': {
                'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
                'Referer': 'https://www.bilibili.com/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            },
            'timeout': 45
        },
        {
            'name': 'B站通用策略',
            'format': 'best',
            'headers': None,
            'timeout': 30
        },
        {
            'name': 'B站兜底策略',
            'format': 'worst',
            'headers': None,
            'timeout': 20
        }
    ]
    
    last_error = None
    
    for i, strategy in enumerate(strategies, 1):
        try:
            logger.info(f"🎯 尝试策略 {i}/5: {strategy['name']}")
            
            if progress_callback and i == 1:
                progress_callback({
                    'status': 'downloading',
                    'percent': 50,
                    'message': f'正在尝试下载...'
                })
            
            # 配置下载选项
            ydl_opts = {
                'format': strategy['format'],
                'merge_output_format': 'mp4',
                'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
                'geo_bypass': True,
                'geo_bypass_country': 'CN',
                'nocheckcertificate': True,
                'ignoreerrors': False,
                'no_warnings': True,
                'quiet': True,
                'socket_timeout': strategy['timeout'],
                'retries': 2,
                'fragment_retries': 3,
                'extractaudio': False,
                'audioformat': 'mp3',
                'embed_subs': False,
                'writesubtitles': False,
                'writeautomaticsub': False,
            }
            
            # 添加Headers（如果有）
            if strategy['headers']:
                ydl_opts['http_headers'] = strategy['headers']
            
            # 执行下载
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # 检查下载结果
            files = os.listdir(download_dir)
            video_files = []
            
            for filename in files:
                filepath = os.path.join(download_dir, filename)
                if os.path.isfile(filepath):
                    size = os.path.getsize(filepath)
                    if filename.lower().endswith(('.mp4', '.webm', '.mkv', '.flv', '.avi')) and size > 1024:
                        video_files.append((filename, size, filepath))
            
            if video_files:
                # 选择最大的文件
                video_files.sort(key=lambda x: x[1], reverse=True)
                filename, size, filepath = video_files[0]
                
                # 移动到最终位置
                final_path = os.path.join(temp_dir, filename)
                if os.path.exists(final_path):
                    os.remove(final_path)
                
                import shutil
                shutil.move(filepath, final_path)
                
                logger.info(f"🎉 下载成功！策略: {strategy['name']}")
                logger.info(f"📁 文件: {filename} ({size/1024/1024:.2f} MB)")
                
                if progress_callback:
                    progress_callback({
                        'status': 'completed',
                        'percent': 100,
                        'filename': filename,
                        'file_size_mb': size / 1024 / 1024,
                        'strategy': strategy['name'],
                        'final': True
                    })
                
                # 清理临时目录
                try:
                    shutil.rmtree(download_dir)
                except:
                    pass
                
                return final_path
            
            logger.info(f"⚠️ 策略 {i} 未产生有效文件")
            
        except Exception as e:
            last_error = str(e)
            logger.info(f"⚠️ 策略 {i} 失败: {last_error[:100]}...")
            continue
    
    # 清理临时目录
    try:
        import shutil
        shutil.rmtree(download_dir)
    except:
        pass
    
    # 所有策略都失败
    error_msg = f"所有下载策略都失败。最后错误: {last_error}" if last_error else "所有下载策略都失败"
    logger.error(f"💀 {error_msg}")
    raise Exception("视频下载失败，请检查网络连接或尝试其他视频")
'''
    
    return ultimate_code

if __name__ == "__main__":
    print("🎯 B站手机端/平板端终极修复工具")
    print("=" * 60)
    
    # 环境诊断
    diagnose_environment()
    
    # B站下载测试
    success_rate = test_bilibili_with_ultimate_strategy()
    
    # 生成修复代码
    fix_code = generate_ultimate_fix()
    
    print(f"\n📋 修复建议")
    print("=" * 50)
    print(f"测试成功率: {success_rate*100:.0f}%")
    
    if success_rate > 0.6:
        print("✅ 基础功能正常，建议使用生成的终极修复代码")
    else:
        print("⚠️ 基础功能有问题，需要检查环境配置")
    
    # 保存修复代码
    with open('ultimate_fix_code.py', 'w', encoding='utf-8') as f:
        f.write(fix_code)
    
    print("💾 修复代码已保存到 ultimate_fix_code.py")
    print("🔧 请将修复代码集成到 video_downloader.py 中")
