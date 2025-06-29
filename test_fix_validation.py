#!/usr/bin/env python3
"""
视频下载器修复验证测试
测试文件名命名和移动端B站下载功能
"""

import os
import sys
import tempfile
import logging
from app.video_downloader import get_downloader, get_video_info

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_video_info_extraction():
    """测试视频信息提取功能"""
    print("🧪 测试 1: 视频信息提取")
    
    test_urls = [
        "https://www.bilibili.com/video/BV1GJ411x7h7",  # B站测试视频
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",   # YouTube测试视频
    ]
    
    for url in test_urls:
        try:
            print(f"\n📺 测试链接: {url}")
            info = get_video_info(url)
            print(f"✅ 标题: {info.get('title', 'N/A')}")
            print(f"✅ 平台: {info.get('platform', 'N/A')}")
            print(f"✅ 时长: {info.get('duration', 'N/A')} 秒")
            print(f"✅ 上传者: {info.get('uploader', 'N/A')}")
        except Exception as e:
            print(f"❌ 提取失败: {str(e)}")

def test_filename_cleaning():
    """测试文件名清理功能"""
    print("\n🧪 测试 2: 文件名清理")
    
    downloader = get_downloader()
    
    test_titles = [
        "【测试视频】这是一个<测试>标题：包含特殊字符？！",
        "Test Video with English & Chinese 中文标题",
        "很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长的标题",
        "普通标题",
        "",
        "Title/with\\illegal|chars*and:more?",
    ]
    
    for title in test_titles:
        cleaned = downloader._clean_filename(title)
        print(f"原标题: '{title}'")
        print(f"清理后: '{cleaned}'")
        print(f"长度: {len(cleaned)}")
        print("---")

def test_mobile_headers():
    """测试移动端请求头配置"""
    print("\n🧪 测试 3: 移动端请求头配置")
    
    downloader = get_downloader()
    
    # 测试B站配置
    test_url = "https://www.bilibili.com/video/BV1GJ411x7h7"
    
    try:
        # 直接测试_get_video_info方法，它包含了我们的移动端增强配置
        info = downloader._get_video_info(test_url)
        print(f"✅ B站信息获取成功")
        print(f"   标题: {info.get('title', 'N/A')}")
        print(f"   原始标题: {info.get('raw_title', 'N/A')}")
    except Exception as e:
        print(f"❌ B站信息获取失败: {str(e)}")

def test_output_template_handling():
    """测试输出模板处理"""
    print("\n🧪 测试 4: 输出模板处理")
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    print(f"📁 临时目录: {temp_dir}")
    
    # 测试各种模板格式
    templates = [
        os.path.join(temp_dir, "%(title)s.%(ext)s"),
        os.path.join(temp_dir, "测试视频.%(ext)s"),
        os.path.join(temp_dir, "Test Video.%(ext)s"),
    ]
    
    for template in templates:
        print(f"模板: {template}")
        try:
            # 测试文件名是否合法
            test_path = template.replace("%(title)s", "测试标题").replace("%(ext)s", "mp4")
            print(f"测试路径: {test_path}")
            
            # 尝试创建测试文件
            with open(test_path, 'w', encoding='utf-8') as f:
                f.write("test")
            
            if os.path.exists(test_path):
                print("✅ 文件创建成功")
                os.remove(test_path)
            else:
                print("❌ 文件创建失败")
                
        except Exception as e:
            print(f"❌ 模板测试失败: {str(e)}")
    
    # 清理临时目录
    import shutil
    try:
        shutil.rmtree(temp_dir)
    except:
        pass

def main():
    """主测试函数"""
    print("🚀 === 视频下载器修复验证测试 ===\n")
    
    try:
        test_video_info_extraction()
        test_filename_cleaning()
        test_mobile_headers()
        test_output_template_handling()
        
        print("\n✅ === 所有测试完成 ===")
        
    except Exception as e:
        print(f"\n❌ 测试过程出错: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
