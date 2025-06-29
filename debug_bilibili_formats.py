#!/usr/bin/env python3
"""诊断B站视频格式问题"""

import yt_dlp
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def list_bilibili_formats(url):
    """列出B站视频的所有可用格式"""
    
    ydl_opts = {
        'quiet': False,
        'listformats': True,  # 列出所有格式
        'geo_bypass': True,
        'nocheckcertificate': True,
        'http_headers': {
            'Referer': 'https://www.bilibili.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"🔍 分析URL: {url}")
            info = ydl.extract_info(url, download=False)
            
            print("\n" + "="*80)
            print(f"📹 视频标题: {info.get('title', '未知')}")
            print(f"👤 上传者: {info.get('uploader', '未知')}")
            print(f"⏱️ 时长: {info.get('duration', 0)}秒")
            print("="*80)
            
            formats = info.get('formats', [])
            if formats:
                print(f"\n🎞️ 发现 {len(formats)} 个可用格式:")
                print("-"*100)
                print(f"{'ID':<10} {'扩展名':<8} {'分辨率':<12} {'文件大小':<12} {'音频':<8} {'视频编码':<15} {'音频编码':<10}")
                print("-"*100)
                
                for fmt in formats:
                    format_id = fmt.get('format_id', 'N/A')
                    ext = fmt.get('ext', 'N/A')
                    resolution = fmt.get('resolution', 'N/A')
                    filesize = fmt.get('filesize') or fmt.get('filesize_approx', 0)
                    filesize_str = f"{filesize // 1024 // 1024}MB" if filesize else "未知"
                    acodec = fmt.get('acodec', 'N/A')
                    vcodec = fmt.get('vcodec', 'N/A')
                    has_audio = "有" if acodec != 'none' and acodec != 'N/A' else "无"
                    
                    print(f"{format_id:<10} {ext:<8} {resolution:<12} {filesize_str:<12} {has_audio:<8} {vcodec:<15} {acodec:<10}")
                
                # 测试常用格式选择器
                print("\n🧪 测试格式选择器:")
                test_selectors = [
                    'best',
                    'best[ext=mp4]',
                    'bestvideo+bestaudio',
                    'bestvideo[ext=mp4]+bestaudio[ext=m4a]',
                    'best[height<=720]',
                    'worst'
                ]
                
                for selector in test_selectors:
                    try:
                        # 使用yt-dlp内部方法测试格式选择
                        selected = ydl._default_format_spec(selector, info.copy())
                        print(f"  ✅ '{selector}' -> 可用")
                    except Exception as e:
                        print(f"  ❌ '{selector}' -> 失败: {str(e)[:50]}...")
                        
            else:
                print("❌ 未找到任何可用格式！")
                
    except Exception as e:
        logger.error(f"❌ 分析失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    # 测试URL
    test_url = "https://www.bilibili.com/video/BV1fT421a71N"
    
    print("🚀 B站格式诊断工具")
    print(f"🎯 测试URL: {test_url}")
    
    success = list_bilibili_formats(test_url)
    
    if success:
        print("\n✅ 格式分析完成")
    else:
        print("\n❌ 格式分析失败")
