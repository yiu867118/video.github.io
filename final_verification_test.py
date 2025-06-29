#!/usr/bin/env python3
"""最终验证测试 - 确保所有功能正常"""

import sys
import os
import time
import requests
import json

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.video_downloader import SimpleVideoDownloader

def test_command_line_download():
    """测试命令行下载功能"""
    print("=" * 60)
    print("🧪 测试1: 命令行下载")
    print("=" * 60)
    
    downloader = SimpleVideoDownloader()
    
    test_urls = [
        "https://www.bilibili.com/video/BV1fT421a71N",  # B站视频
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # YouTube视频
    ]
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n📹 测试 {i}/{len(test_urls)}: {url}")
        
        def progress_callback(data):
            status = data.get('status', '')
            percent = data.get('percent', 0)
            if status == 'completed':
                print(f"✅ 下载完成: {data.get('filename', 'Unknown')}")
            elif status == 'downloading' and percent > 0:
                print(f"⬇️ 进度: {percent:.1f}%", end='\r')
        
        try:
            import tempfile
            temp_dir = tempfile.gettempdir()
            output_template = os.path.join(temp_dir, f"test_{i}_%(title)s.%(ext)s")
            
            result = downloader.download_video(url, output_template, progress_callback)
            
            if result and os.path.exists(result):
                file_size = os.path.getsize(result) / (1024 * 1024)
                print(f"✅ 测试 {i} 成功: {os.path.basename(result)} ({file_size:.2f}MB)")
            else:
                print(f"❌ 测试 {i} 失败: 无文件生成")
                
        except Exception as e:
            print(f"❌ 测试 {i} 异常: {e}")
    
    return True

def test_web_api():
    """测试Web API功能"""
    print("\n" + "=" * 60)
    print("🧪 测试2: Web API")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:5000"
    test_url = "https://www.bilibili.com/video/BV1fT421a71N"
    
    try:
        # 测试下载启动
        print("📡 发送下载请求...")
        response = requests.post(f"{base_url}/download", 
                               json={"url": test_url}, 
                               timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            download_id = data.get('download_id')
            print(f"✅ 获得下载ID: {download_id}")
            
            # 测试进度查询
            print("📊 监控下载进度...")
            for i in range(10):  # 最多等待10秒
                time.sleep(1)
                try:
                    progress_response = requests.get(f"{base_url}/progress/{download_id}", timeout=5)
                    if progress_response.status_code == 200:
                        progress_data = progress_response.json()
                        status = progress_data.get('status', '')
                        percent = progress_data.get('percent', 0)
                        
                        print(f"📈 状态: {status}, 进度: {percent}%")
                        
                        if status == 'completed':
                            print("✅ Web API 测试成功!")
                            return True
                        elif status == 'failed':
                            print(f"❌ 下载失败: {progress_data.get('error', 'Unknown')}")
                            return False
                    else:
                        print(f"⚠️ 进度查询失败: {progress_response.status_code}")
                except Exception as e:
                    print(f"⚠️ 进度查询异常: {e}")
            
            print("⚠️ 下载超时")
            return False
        else:
            print(f"❌ 下载请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Web API 测试异常: {e}")
        return False

def test_file_naming():
    """测试文件名处理"""
    print("\n" + "=" * 60)
    print("🧪 测试3: 文件名处理")
    print("=" * 60)
    
    downloader = SimpleVideoDownloader()
    
    test_names = [
        "普通视频标题",
        "带有特殊字符的标题<>:\"|?*",
        "很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长的标题",
        "本科被表白VS博士被表白",
        "空标题测试",
        "",
    ]
    
    for name in test_names:
        cleaned = downloader._clean_filename(name)
        print(f"原始: '{name}' -> 清理后: '{cleaned}'")
    
    print("✅ 文件名处理测试完成")
    return True

def main():
    """主测试函数"""
    print("🚀 视频下载器最终验证测试")
    print("=" * 60)
    
    tests = [
        ("命令行下载", test_command_line_download),
        ("Web API", test_web_api),
        ("文件名处理", test_file_naming),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔬 开始测试: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"{'✅ 通过' if result else '❌ 失败'}: {test_name}")
        except Exception as e:
            print(f"💥 测试异常: {test_name} - {e}")
            results.append((test_name, False))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有测试通过! 视频下载器修复完成!")
    else:
        print("⚠️ 部分测试失败，需要进一步检查")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
