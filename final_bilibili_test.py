#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终B站移动端兼容性测试
测试在不同用户代理下B站视频下载情况
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

def test_bilibili_video(url: str, test_name: str) -> Dict[str, Any]:
    """测试单个B站视频"""
    print(f"\n{'='*60}")
    print(f"🎯 测试：{test_name}")
    print(f"🔗 视频：{url}")
    print(f"{'='*60}")
    
    # 创建临时下载目录
    temp_dir = tempfile.mkdtemp(prefix=f"bilibili_test_{int(time.time())}_")
    output_template = os.path.join(temp_dir, "%(title)s.%(ext)s")
    
    start_time = time.time()
    result = {
        'test_name': test_name,
        'url': url,
        'success': False,
        'error': None,
        'file_path': None,
        'file_size_mb': 0,
        'duration': 0,
        'strategy': None
    }
    
    try:
        # 1. 先获取视频信息
        print("📋 获取视频信息...")
        try:
            video_info = get_video_info(url)
            print(f"   标题：{video_info.get('title', 'N/A')}")
            print(f"   时长：{video_info.get('duration', 0)}秒")
            print(f"   上传者：{video_info.get('uploader', 'N/A')}")
            print(f"   平台：{video_info.get('platform', 'N/A')}")
        except Exception as e:
            print(f"⚠️ 获取视频信息失败：{e}")
        
        # 2. 开始下载
        print("📥 开始下载...")
        downloader = get_downloader()
        file_path = downloader.download_video(url, output_template, progress_callback)
        
        # 3. 检查结果
        if file_path and os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / 1024 / 1024
            
            print(f"✅ 下载成功！")
            print(f"   文件位置：{file_path}")
            print(f"   文件大小：{file_size_mb:.2f} MB")
            print(f"   耗时：{time.time() - start_time:.1f}秒")
            
            result.update({
                'success': True,
                'file_path': file_path,
                'file_size_mb': file_size_mb,
                'duration': time.time() - start_time
            })
            
            # 清理文件
            try:
                os.remove(file_path)
                os.rmdir(temp_dir)
            except:
                pass
                
        else:
            print("❌ 下载失败：未生成有效文件")
            result['error'] = '未生成有效文件'
    
    except Exception as e:
        error_msg = str(e)
        print(f"❌ 下载异常：{error_msg}")
        result['error'] = error_msg
        
        # 清理临时目录
        try:
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except:
            pass
    
    return result

def run_comprehensive_test():
    """运行全面的B站下载测试"""
    print("🚀 开始B站移动端下载兼容性测试")
    print(f"⏰ 开始时间：{time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试用例：不同类型的B站视频
    test_cases = [
        {
            'name': 'B站短视频(桌面)',
            'url': 'https://www.bilibili.com/video/BV1GJ411x7h7'  # 经典测试视频
        },
        {
            'name': 'B站短视频(移动)',
            'url': 'https://m.bilibili.com/video/BV1GJ411x7h7'  # 相同视频的移动版链接
        },
        {
            'name': 'B站普通视频',
            'url': 'https://www.bilibili.com/video/BV1xx411c7mD'  # 另一个测试视频
        },
        {
            'name': 'B站UP主视频',
            'url': 'https://www.bilibili.com/video/BV1uv411q7Mv'  # UP主视频
        }
    ]
    
    results = []
    success_count = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📱 执行测试 {i}/{len(test_cases)}")
        result = test_bilibili_video(test_case['url'], test_case['name'])
        results.append(result)
        
        if result['success']:
            success_count += 1
        
        # 测试间隔，避免请求过快
        if i < len(test_cases):
            print("⏳ 等待3秒后继续下一个测试...")
            time.sleep(3)
    
    # 输出总结报告
    print(f"\n{'='*80}")
    print(f"📊 测试总结报告")
    print(f"{'='*80}")
    print(f"✅ 总测试数：{len(test_cases)}")
    print(f"✅ 成功数量：{success_count}")
    print(f"❌ 失败数量：{len(test_cases) - success_count}")
    print(f"📈 成功率：{success_count/len(test_cases)*100:.1f}%")
    
    print(f"\n📋 详细结果：")
    for result in results:
        status = "✅ 成功" if result['success'] else "❌ 失败"
        size_info = f" ({result['file_size_mb']:.1f}MB)" if result['success'] else ""
        error_info = f" - {result['error']}" if result['error'] else ""
        print(f"   {status} {result['test_name']}{size_info}{error_info}")
    
    # 保存详细结果到文件
    report_path = os.path.join(os.path.dirname(__file__), 'bilibili_test_report.json')
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                'test_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_tests': len(test_cases),
                'success_count': success_count,
                'success_rate': success_count/len(test_cases)*100,
                'results': results
            }, f, ensure_ascii=False, indent=2)
        print(f"📄 详细报告已保存：{report_path}")
    except Exception as e:
        print(f"⚠️ 保存报告失败：{e}")
    
    return success_count == len(test_cases)

if __name__ == '__main__':
    try:
        success = run_comprehensive_test()
        if success:
            print(f"\n🎉 所有测试通过！B站下载功能正常")
            sys.exit(0)
        else:
            print(f"\n⚠️ 部分测试失败，需要进一步调试")
            sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n\n⏹️ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n💀 测试过程异常：{e}")
        sys.exit(1)
