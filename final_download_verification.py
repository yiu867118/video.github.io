#!/usr/bin/env python3
"""
最终修复验证脚本 - 验证三端下载问题是否彻底解决
专门针对"电脑端有时不出下载任务/移动端不出下载任务/下载慢"等问题
"""

import requests
import time
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import statistics

class FinalDownloadVerifier:
    def __init__(self):
        self.base_url = 'http://127.0.0.1:5000'
        self.test_results = []
        
    def test_single_download(self, test_name: str, user_agent: str, video_url: str) -> dict:
        """测试单次下载的完整流程"""
        print(f"\n🔄 开始测试: {test_name}")
        
        headers = {
            'User-Agent': user_agent,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        start_time = time.time()
        result = {
            'test_name': test_name,
            'user_agent': user_agent[:50] + '...',
            'video_url': video_url,
            'start_time': start_time,
            'success': False,
            'error': None,
            'stages': {},
            'download_speed': None,
            'file_size_mb': None,
            'total_time': None
        }
        
        try:
            # 阶段1: 发起下载请求
            stage1_start = time.time()
            response = requests.post(
                f"{self.base_url}/download",
                json={'url': video_url},
                headers=headers,
                timeout=30
            )
            
            if response.status_code != 200:
                result['error'] = f"下载请求失败: {response.status_code}"
                result['stages']['download_request'] = 'failed'
                return result
            
            data = response.json()
            download_id = data.get('download_id')
            
            if not download_id:
                result['error'] = "未获取到下载ID"
                result['stages']['download_request'] = 'failed'
                return result
            
            result['stages']['download_request'] = time.time() - stage1_start
            result['download_id'] = download_id
            print(f"✅ [{test_name}] 获取下载ID: {download_id}")
            
            # 阶段2: 等待任务出现 (关键测试点)
            stage2_start = time.time()
            task_appeared = False
            task_appearance_time = None
            
            for attempt in range(20):  # 最多等待40秒任务出现
                try:
                    progress_response = requests.get(
                        f"{self.base_url}/progress/{download_id}",
                        headers=headers,
                        timeout=10
                    )
                    
                    if progress_response.status_code == 200:
                        task_appeared = True
                        task_appearance_time = time.time() - stage2_start
                        print(f"🎯 [{test_name}] 下载任务出现! 耗时: {task_appearance_time:.2f}秒")
                        break
                    elif progress_response.status_code == 404:
                        print(f"⏳ [{test_name}] 等待任务出现... ({attempt + 1}/20)")
                        time.sleep(2)
                    else:
                        print(f"⚠️ [{test_name}] 意外状态码: {progress_response.status_code}")
                        time.sleep(2)
                        
                except Exception as e:
                    print(f"⚠️ [{test_name}] 进度查询异常: {e}")
                    time.sleep(2)
            
            if not task_appeared:
                result['error'] = "下载任务从未出现"
                result['stages']['task_appearance'] = 'failed'
                return result
            
            result['stages']['task_appearance'] = task_appearance_time
            
            # 阶段3: 监控下载进度
            stage3_start = time.time()
            last_progress = 0
            max_wait = 300  # 5分钟超时
            check_interval = 3
            stalled_count = 0
            
            while time.time() - stage3_start < max_wait:
                try:
                    progress_response = requests.get(
                        f"{self.base_url}/progress/{download_id}",
                        headers=headers,
                        timeout=10
                    )
                    
                    if progress_response.status_code != 200:
                        print(f"⚠️ [{test_name}] 进度查询失败: {progress_response.status_code}")
                        time.sleep(check_interval)
                        continue
                    
                    progress = progress_response.json()
                    status = progress.get('status', 'unknown')
                    percent = progress.get('percent', 0)
                    speed = progress.get('speed', '')
                    
                    print(f"📊 [{test_name}] {status}: {percent:.1f}% - {speed}")
                    
                    # 检查进度是否停滞
                    if abs(percent - last_progress) < 1:
                        stalled_count += 1
                        if stalled_count > 10:  # 30秒无进度变化
                            result['error'] = "下载进度停滞"
                            result['stages']['download_progress'] = 'stalled'
                            return result
                    else:
                        stalled_count = 0
                        last_progress = percent
                    
                    # 检查完成状态
                    if status == 'completed':
                        result['stages']['download_progress'] = time.time() - stage3_start
                        
                        # 阶段4: 验证下载链接
                        stage4_start = time.time()
                        download_url = progress.get('download_url')
                        filename = progress.get('filename', 'unknown.mp4')
                        
                        if not download_url:
                            result['error'] = "下载完成但无下载链接"
                            result['stages']['link_generation'] = 'failed'
                            return result
                        
                        # 测试文件访问性
                        try:
                            file_response = requests.head(
                                f"{self.base_url}{download_url}",
                                headers=headers,
                                timeout=15
                            )
                            
                            if file_response.status_code not in [200, 206]:
                                result['error'] = f"文件链接不可访问: {file_response.status_code}"
                                result['stages']['file_access'] = 'failed'
                                return result
                            
                            file_size = int(file_response.headers.get('Content-Length', 0))
                            result['file_size_mb'] = file_size / 1024 / 1024
                            result['filename'] = filename
                            result['download_url'] = download_url
                            
                            # 计算总耗时和平均速度
                            total_time = time.time() - start_time
                            result['total_time'] = total_time
                            
                            if file_size > 0 and total_time > 0:
                                result['download_speed'] = (file_size / 1024 / 1024) / total_time
                            
                            result['stages']['file_access'] = time.time() - stage4_start
                            result['success'] = True
                            
                            print(f"🎉 [{test_name}] 下载成功!")
                            print(f"   📁 文件: {filename}")
                            print(f"   📊 大小: {result['file_size_mb']:.2f} MB")
                            print(f"   ⏱️  总耗时: {total_time:.2f} 秒")
                            print(f"   🚀 平均速度: {result['download_speed']:.2f} MB/s")
                            
                            return result
                            
                        except Exception as e:
                            result['error'] = f"文件访问测试失败: {str(e)}"
                            result['stages']['file_access'] = 'failed'
                            return result
                    
                    elif status == 'failed':
                        error_msg = progress.get('error', '未知错误')
                        result['error'] = f"下载失败: {error_msg}"
                        result['stages']['download_progress'] = 'failed'
                        return result
                    
                except Exception as e:
                    print(f"⚠️ [{test_name}] 进度监控异常: {e}")
                
                time.sleep(check_interval)
            
            # 超时
            result['error'] = "下载超时"
            result['stages']['download_progress'] = 'timeout'
            return result
            
        except Exception as e:
            result['error'] = f"测试异常: {str(e)}"
            return result
    
    def run_comprehensive_verification(self):
        """运行全面验证测试"""
        print("🎯 开始最终修复验证测试...")
        print("专门测试：电脑端下载任务出现率、移动端下载任务出现率、下载速度")
        print("=" * 80)
        
        # 测试配置
        test_configs = [
            {
                'name': 'PC端-Chrome',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'repeat': 5  # PC端测试5次
            },
            {
                'name': '移动端-Android',
                'user_agent': 'Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
                'repeat': 5  # 移动端测试5次
            },
            {
                'name': '移动端-iOS',
                'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
                'repeat': 3  # iOS测试3次
            },
            {
                'name': '平板端-iPad',
                'user_agent': 'Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
                'repeat': 3  # 平板测试3次
            },
            {
                'name': '微信浏览器',
                'user_agent': 'Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/120.0.0.0 Mobile Safari/537.36 MicroMessenger/8.0.40.2420',
                'repeat': 3  # 微信浏览器测试3次
            }
        ]
        
        # 测试视频 - 使用一个稳定的B站视频
        test_video = 'https://www.bilibili.com/video/BV1GJ411x7h7'
        
        # 执行所有测试
        total_tests = sum(config['repeat'] for config in test_configs)
        completed_tests = 0
        
        for config in test_configs:
            print(f"\n📱 开始测试设备: {config['name']} (重复{config['repeat']}次)")
            print("-" * 50)
            
            for i in range(config['repeat']):
                test_name = f"{config['name']}-第{i+1}次"
                result = self.test_single_download(
                    test_name,
                    config['user_agent'],
                    test_video
                )
                self.test_results.append(result)
                completed_tests += 1
                
                print(f"📊 总进度: {completed_tests}/{total_tests}")
                
                # 每次测试后等待一段时间，避免服务器压力
                if i < config['repeat'] - 1:
                    time.sleep(5)
        
        # 生成详细报告
        self.generate_final_report()
    
    def generate_final_report(self):
        """生成最终验证报告"""
        print("\n" + "=" * 80)
        print("🎉 最终修复验证报告")
        print("=" * 80)
        
        # 按设备类型分组统计
        device_stats = {}
        for result in self.test_results:
            device = result['test_name'].split('-')[0]
            if device not in device_stats:
                device_stats[device] = {
                    'total': 0,
                    'success': 0,
                    'task_appearance_failures': 0,
                    'download_failures': 0,
                    'speeds': [],
                    'sizes': [],
                    'times': []
                }
            
            stats = device_stats[device]
            stats['total'] += 1
            
            if result['success']:
                stats['success'] += 1
                if result['download_speed']:
                    stats['speeds'].append(result['download_speed'])
                if result['file_size_mb']:
                    stats['sizes'].append(result['file_size_mb'])
                if result['total_time']:
                    stats['times'].append(result['total_time'])
            else:
                if 'task_appearance' in result['stages'] and result['stages']['task_appearance'] == 'failed':
                    stats['task_appearance_failures'] += 1
                else:
                    stats['download_failures'] += 1
        
        # 打印各设备详细统计
        overall_success = 0
        overall_total = 0
        
        for device, stats in device_stats.items():
            print(f"\n📱 {device} 设备统计:")
            print("-" * 40)
            
            success_rate = (stats['success'] / stats['total']) * 100
            print(f"✅ 成功率: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")
            
            # 🔥关键指标：下载任务出现率
            task_appearance_rate = ((stats['total'] - stats['task_appearance_failures']) / stats['total']) * 100
            print(f"🎯 下载任务出现率: {task_appearance_rate:.1f}% (关键指标)")
            
            if stats['task_appearance_failures'] > 0:
                print(f"❌ 任务未出现次数: {stats['task_appearance_failures']}")
            
            if stats['download_failures'] > 0:
                print(f"⚠️ 下载过程失败次数: {stats['download_failures']}")
            
            if stats['speeds']:
                avg_speed = statistics.mean(stats['speeds'])
                min_speed = min(stats['speeds'])
                max_speed = max(stats['speeds'])
                print(f"🚀 平均下载速度: {avg_speed:.2f} MB/s (范围: {min_speed:.2f}-{max_speed:.2f})")
            
            if stats['sizes']:
                avg_size = statistics.mean(stats['sizes'])
                print(f"📊 平均文件大小: {avg_size:.2f} MB")
            
            if stats['times']:
                avg_time = statistics.mean(stats['times'])
                print(f"⏱️  平均完成时间: {avg_time:.2f} 秒")
            
            overall_success += stats['success']
            overall_total += stats['total']
        
        # 总体评估
        print(f"\n" + "=" * 80)
        print("🏆 总体评估")
        print("=" * 80)
        
        overall_success_rate = (overall_success / overall_total) * 100
        print(f"📊 总体成功率: {overall_success}/{overall_total} ({overall_success_rate:.1f}%)")
        
        # 关键问题修复验证
        print(f"\n🔍 关键问题修复验证:")
        
        # 1. 电脑端下载任务出现问题
        pc_stats = device_stats.get('PC端', {})
        if pc_stats:
            pc_task_rate = ((pc_stats['total'] - pc_stats['task_appearance_failures']) / pc_stats['total']) * 100
            if pc_task_rate >= 90:
                print(f"✅ 电脑端下载任务出现问题: 已修复 ({pc_task_rate:.1f}%任务正常出现)")
            else:
                print(f"❌ 电脑端下载任务出现问题: 仍需修复 ({pc_task_rate:.1f}%任务出现)")
        
        # 2. 移动端下载任务问题
        mobile_devices = ['移动端', '平板端', '微信浏览器']
        mobile_success = 0
        mobile_total = 0
        mobile_task_failures = 0
        
        for device in mobile_devices:
            if device in device_stats:
                stats = device_stats[device]
                mobile_success += stats['success']
                mobile_total += stats['total']
                mobile_task_failures += stats['task_appearance_failures']
        
        if mobile_total > 0:
            mobile_success_rate = (mobile_success / mobile_total) * 100
            mobile_task_rate = ((mobile_total - mobile_task_failures) / mobile_total) * 100
            
            if mobile_success_rate >= 80 and mobile_task_rate >= 90:
                print(f"✅ 移动端下载问题: 已修复 (成功率{mobile_success_rate:.1f}%, 任务出现率{mobile_task_rate:.1f}%)")
            else:
                print(f"❌ 移动端下载问题: 仍需修复 (成功率{mobile_success_rate:.1f}%, 任务出现率{mobile_task_rate:.1f}%)")
        
        # 3. 下载速度问题
        all_speeds = []
        for stats in device_stats.values():
            all_speeds.extend(stats['speeds'])
        
        if all_speeds:
            avg_overall_speed = statistics.mean(all_speeds)
            slow_downloads = len([s for s in all_speeds if s < 1.0])  # 小于1MB/s视为慢
            
            if avg_overall_speed >= 2.0 and slow_downloads <= len(all_speeds) * 0.2:
                print(f"✅ 下载速度问题: 已修复 (平均速度{avg_overall_speed:.2f}MB/s, {slow_downloads}个慢速下载)")
            else:
                print(f"❌ 下载速度问题: 仍需优化 (平均速度{avg_overall_speed:.2f}MB/s, {slow_downloads}个慢速下载)")
        
        # 最终结论
        print(f"\n" + "=" * 80)
        if overall_success_rate >= 90:
            print("🎉 修复成功！三端下载功能已基本稳定")
        elif overall_success_rate >= 75:
            print("⚠️ 部分修复成功，仍有优化空间")
        else:
            print("❌ 修复效果不理想，需要进一步调试")
        
        print("=" * 80)
        
        # 保存详细结果
        self.save_verification_results()
    
    def save_verification_results(self):
        """保存验证结果"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"final_verification_results_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': timestamp,
                    'total_tests': len(self.test_results),
                    'results': self.test_results
                }, f, indent=2, ensure_ascii=False)
            
            print(f"📄 验证结果已保存到: {filename}")
        except Exception as e:
            print(f"⚠️ 保存结果失败: {e}")

def main():
    """主函数"""
    print("🎯 最终修复验证启动...")
    
    # 检查服务器
    try:
        response = requests.get('http://127.0.0.1:5000/test', timeout=5)
        if response.status_code == 200:
            print("✅ 服务器连接正常")
        else:
            print(f"❌ 服务器响应异常: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 无法连接服务器: {e}")
        print("请确保Flask应用运行在 http://127.0.0.1:5000")
        return
    
    # 运行验证
    verifier = FinalDownloadVerifier()
    verifier.run_comprehensive_verification()

if __name__ == "__main__":
    main()
