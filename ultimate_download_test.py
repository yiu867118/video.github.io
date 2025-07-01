#!/usr/bin/env python3
"""
终极下载测试脚本 - 彻底验证三端下载功能
测试所有设备的下载兼容性、速度和稳定性
"""

import time
import requests
import json
import sys
import os
from typing import Dict, Any
import threading
from concurrent.futures import ThreadPoolExecutor

# 测试配置
TEST_CONFIG = {
    'base_url': 'http://127.0.0.1:5000',
    'test_videos': [
        {
            'name': 'B站测试视频1',
            'url': 'https://www.bilibili.com/video/BV1GJ411x7h7',  # 一个常见的测试视频
            'expected_platform': 'bilibili'
        }
    ],
    'user_agents': {
        'pc': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'android': 'Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
        'ios': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
        'ipad': 'Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
        'wechat': 'Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/120.0.0.0 Mobile Safari/537.36 MicroMessenger/8.0.40.2420'
    }
}

class DownloadTester:
    def __init__(self):
        self.base_url = TEST_CONFIG['base_url']
        self.results = {}
        
    def test_device_download(self, device_name: str, user_agent: str, video_info: Dict[str, Any]) -> Dict[str, Any]:
        """测试特定设备的下载功能"""
        print(f"\n🔄 测试 {device_name} 设备下载...")
        
        headers = {
            'User-Agent': user_agent,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        try:
            # 步骤1: 开始下载
            download_data = {'url': video_info['url']}
            print(f"📤 发送下载请求到: {self.base_url}/download")
            
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/download",
                json=download_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f"下载请求失败: {response.status_code} - {response.text}",
                    'stage': 'download_request'
                }
            
            download_result = response.json()
            download_id = download_result.get('download_id')
            
            if not download_id:
                return {
                    'success': False,
                    'error': "未获取到下载ID",
                    'stage': 'download_id'
                }
            
            print(f"✅ 获取下载ID: {download_id}")
            
            # 步骤2: 监控进度
            progress_url = f"{self.base_url}/progress/{download_id}"
            max_wait_time = 300  # 5分钟超时
            check_interval = 2   # 2秒检查一次
            checks_count = 0
            max_checks = max_wait_time // check_interval
            
            last_percent = 0
            stalled_count = 0
            max_stalled = 10  # 最多允许10次进度停滞
            
            print(f"📊 开始监控进度 (最大等待时间: {max_wait_time}秒)...")
            
            while checks_count < max_checks:
                try:
                    progress_response = requests.get(progress_url, headers=headers, timeout=10)
                    
                    if progress_response.status_code != 200:
                        print(f"⚠️ 进度查询失败: {progress_response.status_code}")
                        time.sleep(check_interval)
                        checks_count += 1
                        continue
                    
                    progress = progress_response.json()
                    status = progress.get('status', 'unknown')
                    percent = progress.get('percent', 0)
                    message = progress.get('message', '')
                    speed = progress.get('speed', '')
                    
                    print(f"📈 [{device_name}] {status}: {percent:.1f}% - {message} - {speed}")
                    
                    # 检查进度是否停滞
                    if abs(percent - last_percent) < 1:
                        stalled_count += 1
                        if stalled_count >= max_stalled:
                            return {
                                'success': False,
                                'error': f"进度停滞超过 {max_stalled * check_interval} 秒",
                                'stage': 'progress_stalled',
                                'last_progress': progress
                            }
                    else:
                        stalled_count = 0
                        last_percent = percent
                    
                    # 检查是否完成
                    if status == 'completed':
                        total_time = time.time() - start_time
                        
                        # 验证下载链接
                        download_url = progress.get('download_url')
                        filename = progress.get('filename', 'unknown.mp4')
                        
                        if not download_url:
                            return {
                                'success': False,
                                'error': "下载完成但未获取到下载链接",
                                'stage': 'download_url_missing',
                                'progress': progress
                            }
                        
                        # 测试下载链接可访问性
                        try:
                            file_response = requests.head(
                                f"{self.base_url}{download_url}",
                                headers=headers,
                                timeout=10
                            )
                            
                            if file_response.status_code not in [200, 206]:
                                return {
                                    'success': False,
                                    'error': f"下载链接不可访问: {file_response.status_code}",
                                    'stage': 'file_access',
                                    'download_url': download_url
                                }
                            
                            file_size = file_response.headers.get('Content-Length', 'unknown')
                            content_type = file_response.headers.get('Content-Type', 'unknown')
                            
                            return {
                                'success': True,
                                'download_id': download_id,
                                'filename': filename,
                                'file_size': file_size,
                                'content_type': content_type,
                                'total_time': total_time,
                                'download_url': download_url,
                                'final_progress': progress,
                                'avg_speed': f"{int(file_size)/1024/1024/total_time:.2f} MB/s" if file_size.isdigit() else 'unknown'
                            }
                            
                        except Exception as e:
                            return {
                                'success': False,
                                'error': f"验证下载链接失败: {str(e)}",
                                'stage': 'file_verification',
                                'download_url': download_url
                            }
                    
                    # 检查是否失败
                    elif status == 'failed':
                        error_msg = progress.get('error', '未知错误')
                        return {
                            'success': False,
                            'error': f"下载失败: {error_msg}",
                            'stage': 'download_failed',
                            'progress': progress
                        }
                    
                except Exception as e:
                    print(f"⚠️ 进度检查异常: {str(e)}")
                
                time.sleep(check_interval)
                checks_count += 1
            
            # 超时
            return {
                'success': False,
                'error': f"下载超时 (超过 {max_wait_time} 秒)",
                'stage': 'timeout',
                'checks_count': checks_count
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"测试异常: {str(e)}",
                'stage': 'exception'
            }
    
    def run_comprehensive_test(self):
        """运行全面的三端兼容性测试"""
        print("🚀 开始终极下载测试...")
        print("=" * 60)
        
        test_video = TEST_CONFIG['test_videos'][0]
        
        # 并行测试所有设备
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {}
            
            for device_name, user_agent in TEST_CONFIG['user_agents'].items():
                future = executor.submit(
                    self.test_device_download,
                    device_name,
                    user_agent,
                    test_video
                )
                futures[device_name] = future
            
            # 收集结果
            for device_name, future in futures.items():
                try:
                    result = future.result(timeout=400)  # 每个设备最大等待400秒
                    self.results[device_name] = result
                except Exception as e:
                    self.results[device_name] = {
                        'success': False,
                        'error': f"测试执行异常: {str(e)}",
                        'stage': 'execution_error'
                    }
        
        # 输出测试报告
        self.print_test_report()
    
    def print_test_report(self):
        """打印详细的测试报告"""
        print("\n" + "=" * 60)
        print("🎯 终极下载测试报告")
        print("=" * 60)
        
        success_count = 0
        total_count = len(self.results)
        
        for device_name, result in self.results.items():
            print(f"\n📱 {device_name.upper()} 设备测试:")
            print("-" * 40)
            
            if result['success']:
                success_count += 1
                print(f"✅ 测试成功!")
                print(f"   📁 文件名: {result.get('filename', 'N/A')}")
                print(f"   📊 文件大小: {result.get('file_size', 'N/A')} bytes")
                print(f"   ⏱️  总耗时: {result.get('total_time', 'N/A'):.2f} 秒")
                print(f"   🚀 平均速度: {result.get('avg_speed', 'N/A')}")
                print(f"   🔗 下载链接: {result.get('download_url', 'N/A')}")
                print(f"   📋 内容类型: {result.get('content_type', 'N/A')}")
            else:
                print(f"❌ 测试失败!")
                print(f"   🚫 错误阶段: {result.get('stage', 'N/A')}")
                print(f"   💬 错误信息: {result.get('error', 'N/A')}")
                
                if 'progress' in result:
                    progress = result['progress']
                    print(f"   📊 最后进度: {progress.get('percent', 0):.1f}%")
                    print(f"   📝 最后状态: {progress.get('status', 'N/A')}")
        
        print("\n" + "=" * 60)
        print(f"🎉 测试总结: {success_count}/{total_count} 设备测试成功")
        
        success_rate = (success_count / total_count) * 100
        if success_rate == 100:
            print("🏆 完美！所有设备都能正常下载!")
        elif success_rate >= 80:
            print(f"✅ 良好！成功率: {success_rate:.1f}%")
        elif success_rate >= 60:
            print(f"⚠️ 一般！成功率: {success_rate:.1f}% - 需要优化")
        else:
            print(f"❌ 较差！成功率: {success_rate:.1f}% - 需要大幅改进")
        
        print("=" * 60)
        
        # 保存详细结果到文件
        self.save_results_to_file()
    
    def save_results_to_file(self):
        """保存测试结果到文件"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"download_test_results_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': timestamp,
                    'test_config': TEST_CONFIG,
                    'results': self.results
                }, f, indent=2, ensure_ascii=False)
            
            print(f"📄 详细测试结果已保存到: {filename}")
        except Exception as e:
            print(f"⚠️ 保存测试结果失败: {e}")

def main():
    """主函数"""
    print("🎯 终极下载测试启动中...")
    
    # 检查服务器是否运行
    try:
        response = requests.get(f"{TEST_CONFIG['base_url']}/test", timeout=5)
        if response.status_code != 200:
            print(f"❌ 服务器未正常运行，状态码: {response.status_code}")
            sys.exit(1)
        print("✅ 服务器连接正常")
    except Exception as e:
        print(f"❌ 无法连接到服务器: {e}")
        print("请确保Flask应用正在运行在 http://127.0.0.1:5000")
        sys.exit(1)
    
    # 运行测试
    tester = DownloadTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()
