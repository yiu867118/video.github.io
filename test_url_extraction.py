#!/usr/bin/env python3
"""
测试URL提取和下载功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_url_extraction():
    """测试前端URL提取功能的模拟"""
    
    test_cases = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "youtube.com/watch?v=dQw4w9WgXcQ",
        "【官方MV】Rick Astley - Never Gonna Give You Up https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "Rick Astley - Never Gonna Give You Up youtube.com/watch?v=dQw4w9WgXcQ 超经典歌曲",
        "https://www.bilibili.com/video/BV1xx411c7mD",
        "bilibili.com/video/BV1xx411c7mD",
        "【哔哩哔哩】amazing video https://www.bilibili.com/video/BV1xx411c7mD",
    ]
    
    import re
    
    def extract_url_python(input_str):
        """模拟前端URL提取逻辑"""
        if not input_str:
            return None
            
        input_str = input_str.strip()
        
        # URL正则模式
        url_patterns = [
            r'(?:https?://)?(?:www\.)?(?:youtube\.com/(?:watch\?v=|embed/|v/)|youtu\.be/)([a-zA-Z0-9_-]{11})',
            r'(?:https?://)?(?:www\.)?bilibili\.com/video/([A-Za-z0-9]+)',
            r'https?://[^\s]+',
        ]
        
        for pattern in url_patterns:
            match = re.search(pattern, input_str)
            if match:
                url = match.group(0)
                if not url.startswith('http'):
                    url = 'https://' + url
                return url
                
        # 检查域名
        if '.com' in input_str or '.tv' in input_str:
            words = input_str.split()
            for word in words:
                if '.com' in word or '.tv' in word:
                    clean_word = re.sub(r'[，。！？；：""''「」【】()（）\[\]]', '', word)
                    if not clean_word.startswith('http'):
                        clean_word = 'https://' + clean_word
                    return clean_word
        
        return None
    
    print("🧪 URL提取测试")
    print("=" * 50)
    
    for i, test_input in enumerate(test_cases, 1):
        extracted = extract_url_python(test_input)
        print(f"测试 {i}:")
        print(f"  输入: {test_input}")
        print(f"  提取: {extracted}")
        print(f"  结果: {'✅ 成功' if extracted else '❌ 失败'}")
        print()

def test_simple_download():
    """测试简单下载功能"""
    print("🎯 下载测试")
    print("=" * 50)
    
    # 导入下载器
    from app.video_downloader import get_downloader
    
    # 测试YouTube短视频
    test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
    
    def progress_callback(data):
        status = data.get('status', 'unknown')
        percent = data.get('percent', 0)
        message = data.get('message', '')
        print(f"📊 {status}: {percent:.1f}% - {message}")
        
        if data.get('error'):
            print(f"❌ 错误: {data['error']}")
            print(f"   类型: {data.get('error_type', 'unknown')}")
            print(f"   致命: {data.get('fatal', False)}")
    
    try:
        downloader = get_downloader()
        
        # 输出模板
        import tempfile
        temp_dir = tempfile.gettempdir()
        output_template = os.path.join(temp_dir, "%(title)s.%(ext)s")
        
        print(f"🚀 开始下载: {test_url}")
        print(f"📁 输出目录: {temp_dir}")
        
        result = downloader.download_video(test_url, output_template, progress_callback)
        
        print(f"🎉 下载成功: {result}")
        if os.path.exists(result):
            size_mb = os.path.getsize(result) / 1024 / 1024
            print(f"📦 文件大小: {size_mb:.2f} MB")
        
    except Exception as e:
        print(f"💀 下载失败: {e}")

if __name__ == "__main__":
    print("🧪 视频下载器修复验证")
    print("=" * 60)
    
    test_url_extraction()
    print("\n")
    test_simple_download()
