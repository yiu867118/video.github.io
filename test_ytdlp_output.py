#!/usr/bin/env python3
"""
测试yt-dlp下载和文件名问题
"""

import os
import tempfile
import yt_dlp
import sys

def test_ytdlp_output():
    """测试yt-dlp的输出模板"""
    
    test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
    temp_dir = tempfile.gettempdir()
    
    print(f"🧪 测试yt-dlp下载和文件名")
    print(f"📁 临时目录: {temp_dir}")
    print(f"📄 目录内容数量: {len(os.listdir(temp_dir))}")
    
    # 测试不同的output_template
    templates = [
        os.path.join(temp_dir, "%(title)s.%(ext)s"),
        os.path.join(temp_dir, "test_video.%(ext)s"),
        "%(title)s.%(ext)s",  # 相对路径
        "./%(title)s.%(ext)s",  # 当前目录
    ]
    
    for i, template in enumerate(templates, 1):
        print(f"\n🎯 测试模板 {i}: {template}")
        
        try:
            files_before = set(os.listdir(temp_dir))
            current_dir_before = set(os.listdir('.'))
            
            ydl_opts = {
                'outtmpl': template,
                'format': 'best[height<=720]/best',
                'quiet': True,
                'no_warnings': True,
                'geo_bypass': True,
                'nocheckcertificate': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(test_url, download=True)
                print(f"   📝 视频标题: {info.get('title', 'Unknown')}")
            
            # 检查文件变化
            files_after = set(os.listdir(temp_dir))
            current_dir_after = set(os.listdir('.'))
            
            new_files_temp = files_after - files_before
            new_files_current = current_dir_after - current_dir_before
            
            print(f"   📊 临时目录新增文件: {len(new_files_temp)}")
            if new_files_temp:
                for f in new_files_temp:
                    size = os.path.getsize(os.path.join(temp_dir, f))
                    print(f"     - {f} ({size/1024:.1f} KB)")
            
            print(f"   📊 当前目录新增文件: {len(new_files_current)}")
            if new_files_current:
                for f in new_files_current:
                    size = os.path.getsize(f)
                    print(f"     - {f} ({size/1024:.1f} KB)")
            
            if new_files_temp or new_files_current:
                print(f"   ✅ 成功！")
                break
            else:
                print(f"   ❌ 没有发现新文件")
                
        except Exception as e:
            print(f"   💀 失败: {e}")

if __name__ == "__main__":
    test_ytdlp_output()
