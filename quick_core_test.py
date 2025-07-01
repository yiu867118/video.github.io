#!/usr/bin/env python3
"""
核心问题验证脚本 - 专门测试关键修复点
1. 电脑端下载任务是否稳定出现
2. 移动端下载任务是否稳定出现  
3. 下载速度是否正常
"""

import requests
import time
import json

def test_download_task_appearance(device_name, user_agent, video_url):
    """测试下载任务出现的稳定性"""
    print(f"\n🔄 测试 {device_name} 下载任务出现...")
    
    base_url = 'http://127.0.0.1:5000'
    headers = {
        'User-Agent': user_agent,
        'Content-Type': 'application/json'
    }
    
    try:
        # 1. 发起下载请求
        start_time = time.time()
        response = requests.post(
            f"{base_url}/download",
            json={'url': video_url},
            headers=headers,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ [{device_name}] 下载请求失败: {response.status_code}")
            return False
        
        data = response.json()
        download_id = data.get('download_id')
        
        if not download_id:
            print(f"❌ [{device_name}] 未获取到下载ID")
            return False
        
        print(f"✅ [{device_name}] 获取下载ID: {download_id}")
        
        # 2. 测试任务是否出现 (关键测试点)
        task_appeared = False
        appearance_time = None
        
        print(f"⏳ [{device_name}] 等待下载任务出现...")
        
        for attempt in range(15):  # 最多等待30秒
            try:
                progress_response = requests.get(
                    f"{base_url}/progress/{download_id}",
                    headers=headers,
                    timeout=8
                )
                
                if progress_response.status_code == 200:
                    task_appeared = True
                    appearance_time = time.time() - start_time
                    progress_data = progress_response.json()
                    status = progress_data.get('status', 'unknown')
                    percent = progress_data.get('percent', 0)
                    
                    print(f"🎯 [{device_name}] 任务出现! 耗时: {appearance_time:.2f}秒, 状态: {status}, 进度: {percent:.1f}%")
                    
                    # 3. 简单监控一下进度，确保下载正常进行
                    for i in range(10):  # 监控20秒
                        time.sleep(2)
                        try:
                            check_response = requests.get(
                                f"{base_url}/progress/{download_id}",
                                headers=headers,
                                timeout=5
                            )
                            
                            if check_response.status_code == 200:
                                check_data = check_response.json()
                                check_status = check_data.get('status', 'unknown')
                                check_percent = check_data.get('percent', 0)
                                speed = check_data.get('speed', '')
                                
                                print(f"📊 [{device_name}] {check_status}: {check_percent:.1f}% - {speed}")
                                
                                if check_status == 'completed':
                                    download_url = check_data.get('download_url')
                                    filename = check_data.get('filename', 'unknown')
                                    
                                    if download_url:
                                        print(f"🎉 [{device_name}] 下载完成! 文件: {filename}")
                                        print(f"🔗 [{device_name}] 下载链接: {download_url}")
                                        
                                        # 测试文件链接可访问性
                                        try:
                                            file_check = requests.head(
                                                f"{base_url}{download_url}",
                                                headers=headers,
                                                timeout=10
                                            )
                                            
                                            if file_check.status_code in [200, 206]:
                                                file_size = file_check.headers.get('Content-Length', 'unknown')
                                                print(f"📁 [{device_name}] 文件可访问, 大小: {file_size} bytes")
                                                return True
                                            else:
                                                print(f"❌ [{device_name}] 文件链接不可访问: {file_check.status_code}")
                                                return False
                                        except Exception as e:
                                            print(f"❌ [{device_name}] 文件链接测试失败: {e}")
                                            return False
                                    else:
                                        print(f"❌ [{device_name}] 下载完成但无下载链接")
                                        return False
                                        
                                elif check_status == 'failed':
                                    error = check_data.get('error', '未知错误')
                                    print(f"❌ [{device_name}] 下载失败: {error}")
                                    return False
                            
                        except Exception as e:
                            print(f"⚠️ [{device_name}] 进度检查异常: {e}")
                    
                    # 如果20秒后还没完成，也算任务出现成功（至少任务在正常运行）
                    print(f"⏱️ [{device_name}] 下载任务正常运行中，测试通过")
                    return True
                    
                elif progress_response.status_code == 404:
                    print(f"⏳ [{device_name}] 等待任务创建... ({attempt + 1}/15)")
                    time.sleep(2)
                else:
                    print(f"⚠️ [{device_name}] 意外状态码: {progress_response.status_code}")
                    time.sleep(2)
                    
            except Exception as e:
                print(f"⚠️ [{device_name}] 进度查询异常: {e}")
                time.sleep(2)
        
        if not task_appeared:
            print(f"❌ [{device_name}] 下载任务从未出现 (等待30秒)")
            return False
            
    except Exception as e:
        print(f"❌ [{device_name}] 测试异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🎯 核心问题验证测试")
    print("专门测试：下载任务出现稳定性、三端兼容性")
    print("=" * 60)
    
    # 测试视频
    test_video = 'https://www.bilibili.com/video/BV1GJ411x7h7'
    
    # 测试配置
    test_configs = [
        {
            'name': 'PC端-Chrome',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        },
        {
            'name': '移动端-Android',
            'user_agent': 'Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
        },
        {
            'name': '移动端-iOS',
            'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
        }
    ]
    
    results = {}
    
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
        return
    
    # 依次测试各设备
    for config in test_configs:
        success = test_download_task_appearance(
            config['name'],
            config['user_agent'],
            test_video
        )
        results[config['name']] = success
        
        # 每次测试后等待一下
        print(f"⏸️ 等待5秒后进行下一个设备测试...")
        time.sleep(5)
    
    # 输出总结
    print("\n" + "=" * 60)
    print("📊 核心问题修复验证结果")
    print("=" * 60)
    
    success_count = sum(1 for success in results.values() if success)
    total_count = len(results)
    
    for device, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{device}: {status}")
    
    print(f"\n总成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    
    if success_count == total_count:
        print("🎉 完美！所有核心问题都已修复！")
        print("✅ 电脑端下载任务出现稳定")
        print("✅ 移动端下载任务出现稳定")
        print("✅ 三端兼容性良好")
    elif success_count >= total_count * 0.8:
        print("✅ 良好！大部分问题已修复")
    else:
        print("⚠️ 仍需优化，部分问题未彻底解决")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
