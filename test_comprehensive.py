#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
坚如磐石下载器测试脚本
测试各种场景，确保PC、手机、平板都能完美下载并播放
"""

import sys
import os
import logging
import traceback

# 添加app模块到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    from video_downloader import (
        RockSolidVideoDownloader, 
        get_video_info, 
        analyze_bilibili_error,
        EnhancedURLValidator
    )
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_download.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class DownloadTester:
    """下载测试器"""
    
    def __init__(self):
        self.downloader = RockSolidVideoDownloader()
        self.test_results = []
        
    def test_url_validation(self):
        """测试URL验证功能"""
        print("\n🔍 测试URL验证功能...")
        
        test_urls = [
            "https://www.bilibili.com/video/BV1x4411V7Pg",
            "https://b23.tv/BV1x4411V7Pg",
            "BV1x4411V7Pg",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "invalid_url",
            "",
        ]
        
        for url in test_urls:
            try:
                result = EnhancedURLValidator.validate_and_fix_url(url)
                status = "✅" if result['valid'] else "❌"
                print(f"   {status} {url} -> {result}")
            except Exception as e:
                print(f"   ❌ {url} -> 异常: {e}")
    
    def test_error_analysis(self):
        """测试错误分析功能"""
        print("\n🔍 测试错误分析功能...")
        
        test_errors = [
            "需要登录才能观看",
            "403 Forbidden",
            "该视频为付费内容",
            "Connection timeout",
            "JSON decode error",
            "No formats found",
            "Network unreachable",
            "FFmpeg error",
            "Unknown error message",
        ]
        
        for error_msg in test_errors:
            try:
                analysis = analyze_bilibili_error(error_msg)
                print(f"   📝 '{error_msg}' -> {analysis}")
            except Exception as e:
                print(f"   ❌ 错误分析失败: {e}")
    
    def test_video_info(self, url: str):
        """测试视频信息获取"""
        print(f"\n🔍 测试视频信息获取: {url}")
        
        try:
            info = get_video_info(url)
            print(f"   结果: {info}")
            return info
        except Exception as e:
            print(f"   ❌ 获取视频信息失败: {e}")
            return None
    
    def test_download(self, url: str, output_dir: str = "./downloads"):
        """测试下载功能"""
        print(f"\n⬇️ 测试下载功能: {url}")
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        output_template = os.path.join(output_dir, "%(title)s.%(ext)s")
        
        # 进度回调
        def progress_callback(progress_data):
            status = progress_data.get('status', 'unknown')
            percent = progress_data.get('percent', 0)
            message = progress_data.get('message', '')
            
            if status == 'downloading':
                print(f"   📥 下载中: {percent:.1f}%")
            elif status == 'completed':
                filename = progress_data.get('filename', '')
                file_size = progress_data.get('file_size_mb', 0)
                print(f"   ✅ 下载完成: {filename} ({file_size:.2f} MB)")
            elif status == 'failed':
                error = progress_data.get('error', '')
                print(f"   ❌ 下载失败: {error}")
            else:
                print(f"   📋 {status}: {message}")
        
        try:
            result_file = self.downloader.download_video(
                url, output_template, progress_callback
            )
            
            if result_file and os.path.exists(result_file):
                file_size = os.path.getsize(result_file) / 1024 / 1024
                print(f"   🎉 下载成功!")
                print(f"   📁 文件: {os.path.basename(result_file)}")
                print(f"   📊 大小: {file_size:.2f} MB")
                print(f"   📍 路径: {result_file}")
                
                self.test_results.append({
                    'url': url,
                    'success': True,
                    'file': result_file,
                    'size_mb': file_size
                })
                
                return result_file
            else:
                print(f"   ❌ 下载失败: 文件不存在")
                self.test_results.append({
                    'url': url,
                    'success': False,
                    'error': '文件不存在'
                })
                return None
                
        except Exception as e:
            print(f"   ❌ 下载异常: {e}")
            print(f"   🔍 详细错误: {traceback.format_exc()}")
            
            self.test_results.append({
                'url': url,
                'success': False,
                'error': str(e)
            })
            return None
    
    def test_system_diagnosis(self):
        """测试系统诊断"""
        print("\n🔍 测试系统诊断...")
        try:
            diagnosis = self.downloader._diagnose_system()
            print("   诊断完成!")
            return diagnosis
        except Exception as e:
            print(f"   ❌ 系统诊断失败: {e}")
            return None
    
    def run_comprehensive_test(self):
        """运行综合测试"""
        print("🧪 开始综合测试...")
        print("=" * 60)
        
        # 1. 测试URL验证
        self.test_url_validation()
        
        # 2. 测试错误分析
        self.test_error_analysis()
        
        # 3. 测试系统诊断
        self.test_system_diagnosis()
        
        # 4. 测试视频信息获取
        test_url = "https://www.bilibili.com/video/BV1x4411V7Pg"  # 一个经典测试视频
        self.test_video_info(test_url)
        
        # 5. 测试下载（注释掉避免实际下载）
        # print(f"\n⚠️ 跳过实际下载测试，避免网络流量消耗")
        # self.test_download(test_url)
        
        print("\n" + "=" * 60)
        print("🎉 综合测试完成!")
        
        if self.test_results:
            print(f"\n📊 下载测试结果:")
            for i, result in enumerate(self.test_results, 1):
                status = "✅" if result['success'] else "❌"
                print(f"   {i}. {status} {result['url']}")
                if result['success']:
                    print(f"      📁 {result['file']}")
                    print(f"      📊 {result['size_mb']:.2f} MB")
                else:
                    print(f"      ❌ {result['error']}")

def main():
    """主函数"""
    print("🏔️ 坚如磐石下载器 - 综合测试")
    print("=" * 60)
    
    tester = DownloadTester()
    tester.run_comprehensive_test()
    
    print("\n💡 测试完成! 如需实际下载测试，请手动调用:")
    print("   tester.test_download('YOUR_VIDEO_URL')")

if __name__ == "__main__":
    main()
