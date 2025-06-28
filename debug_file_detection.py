#!/usr/bin/env python3
"""
调试文件检测问题
"""

import os
import tempfile
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.video_downloader import SimpleVideoDownloader
import yt_dlp

def debug_file_detection():
    temp_dir = tempfile.gettempdir()
    
    # 先清理可能存在的文件
    existing_files = os.listdir(temp_dir)
    target_files = [f for f in existing_files if 'Me at the zoo' in f]
    
    print(f"🧹 清理现有的测试文件...")
    for f in target_files:
        try:
            os.remove(os.path.join(temp_dir, f))
            print(f"   删除: {f}")
        except:
            pass
    
    print(f"\n📁 临时目录: {temp_dir}")
    files_initial = os.listdir(temp_dir)
    print(f"📊 初始文件数: {len(files_initial)}")
    
    # 使用我们的下载器
    downloader = SimpleVideoDownloader()
    test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
    output_template = os.path.join(temp_dir, "%(title)s.%(ext)s")
    
    print(f"\n🎯 使用我们的下载器测试")
    print(f"🔗 URL: {test_url}")
    print(f"📝 输出模板: {output_template}")
    
    def progress_callback(data):
        status = data.get('status', 'unknown')
        percent = data.get('percent', 0)
        message = data.get('message', '')
        print(f"   📊 {status}: {percent:.1f}% - {message}")
    
    try:
        # 记录下载前的文件
        files_before = set(os.listdir(temp_dir))
        print(f"📦 下载前文件数: {len(files_before)}")
        
        # 执行单个策略测试
        ydl_opts = downloader._get_base_config()
        ydl_opts.update({
            'format': 'best[height<=720]/best',
            'merge_output_format': 'mp4',
            'geo_bypass': True,
            'nocheckcertificate': True,
            'outtmpl': output_template,
            'progress_hooks': [lambda d: print(f"      Hook: {d.get('status', 'unknown')} - {d.get('downloaded_bytes', 0)} bytes")]
        })
        
        print(f"\n🚀 开始下载...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([test_url])
        
        # 检查下载后的文件
        files_after = set(os.listdir(temp_dir))
        new_files = files_after - files_before
        
        print(f"\n📊 结果分析:")
        print(f"   下载前: {len(files_before)} 个文件")
        print(f"   下载后: {len(files_after)} 个文件")
        print(f"   新增: {len(new_files)} 个文件")
        
        if new_files:
            print(f"   新文件列表:")
            for filename in new_files:
                file_path = os.path.join(temp_dir, filename)
                if os.path.isfile(file_path):
                    size = os.path.getsize(file_path)
                    print(f"     - {filename} ({size/1024:.1f} KB)")
        else:
            print(f"   ❌ 没有发现新文件")
            
            # 检查是否有相关文件
            related_files = [f for f in files_after if 'zoo' in f.lower() or 'me at' in f.lower()]
            if related_files:
                print(f"   🔍 发现相关文件:")
                for f in related_files:
                    print(f"     - {f}")
        
    except Exception as e:
        print(f"💀 下载失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_file_detection()
