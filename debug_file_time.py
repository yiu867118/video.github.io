#!/usr/bin/env python3
"""
调试文件修改时间检测
"""

import os
import tempfile
import time

def debug_file_modification():
    temp_dir = tempfile.gettempdir()
    
    print(f"📁 临时目录: {temp_dir}")
    print(f"⏰ 当前时间: {time.time()}")
    
    # 查找相关文件
    all_files = os.listdir(temp_dir)
    video_files = [f for f in all_files if f.lower().endswith(('.mp4', '.webm', '.mkv', '.avi', '.mov', '.flv'))]
    zoo_files = [f for f in all_files if 'zoo' in f.lower()]
    
    print(f"\n📊 文件统计:")
    print(f"   总文件数: {len(all_files)}")
    print(f"   视频文件数: {len(video_files)}")
    print(f"   包含'zoo'的文件: {len(zoo_files)}")
    
    if zoo_files:
        print(f"\n🔍 'zoo'相关文件详情:")
        for filename in zoo_files:
            file_path = os.path.join(temp_dir, filename)
            try:
                mtime = os.path.getmtime(file_path)
                size = os.path.getsize(file_path)
                time_diff = time.time() - mtime
                print(f"   📦 {filename}")
                print(f"      大小: {size/1024:.1f} KB")
                print(f"      修改时间: {mtime} (距今 {time_diff:.1f} 秒)")
                print(f"      最近5分钟内修改: {'是' if time_diff < 300 else '否'}")
            except Exception as e:
                print(f"   ❌ 无法获取 {filename} 的信息: {e}")
    
    # 找最近修改的视频文件
    print(f"\n🎯 最近修改的视频文件 (5分钟内):")
    recent_videos = []
    current_time = time.time()
    
    for filename in video_files:
        file_path = os.path.join(temp_dir, filename)
        try:
            mtime = os.path.getmtime(file_path)
            if current_time - mtime < 300:  # 5分钟内
                size = os.path.getsize(file_path)
                recent_videos.append((filename, size, mtime))
        except:
            continue
    
    if recent_videos:
        recent_videos.sort(key=lambda x: x[2], reverse=True)  # 按修改时间排序
        for filename, size, mtime in recent_videos[:10]:  # 显示前10个
            time_diff = current_time - mtime
            print(f"   📦 {filename} ({size/1024:.1f} KB, {time_diff:.1f}秒前)")
    else:
        print(f"   ❌ 没有找到最近修改的视频文件")

if __name__ == "__main__":
    debug_file_modification()
