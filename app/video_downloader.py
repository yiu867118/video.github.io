"""
简化强健的视频下载器
专注：下载成功，最高画质，有音频，不过度分析错误
"""

import os
import tempfile
import logging
import time
import yt_dlp
import subprocess
import sys
import platform as sys_platform
from typing import Dict, Any, Optional, Callable
import requests

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_bilibili_error(error_msg: str) -> Dict[str, Any]:
    """简化错误分析 - 只标记真正致命的错误"""
    error_msg_lower = error_msg.lower()
    
    # 只有这些才是真正致命的错误
    if any(keyword in error_msg_lower for keyword in ['付费', 'payment', 'premium', '大会员', 'vip', 'paid']):
        return {
            'user_friendly': '该视频为付费内容，需要购买后才能下载',
            'error_type': 'payment_required',
            'fatal': True
        }
    elif any(keyword in error_msg_lower for keyword in ['登录', 'login', 'auth']) and not any(keyword in error_msg_lower for keyword in ['timeout', 'connection', 'network']):
        return {
            'user_friendly': '需要登录账号才能下载此视频',
            'error_type': 'auth_required', 
            'fatal': True
        }
    elif any(keyword in error_msg_lower for keyword in ['private', '私有', 'deleted', '删除', '不存在', 'removed']):
        return {
            'user_friendly': '视频无法访问，可能已被删除或设为私有',
            'error_type': 'access_denied',
            'fatal': True
        }
    else:
        # 其他所有错误都可以重试 - 包括网络、SSL、地区等
        return {
            'user_friendly': '下载遇到问题，正在尝试其他方式...',
            'error_type': 'retryable_error',
            'fatal': False
        }

class ProgressTracker:
    def __init__(self):
        self.start_time = time.time()
        self.last_percent = 0
        self.progress_callback = None
        self.is_completed = False
        
    def set_callback(self, callback: Optional[Callable]):
        if callback:
            self.progress_callback = callback
    
    def update(self, d):
        if not self.progress_callback or self.is_completed:
            return
            
        try:
            status = d.get('status', 'downloading')
            
            if status == 'downloading':
                downloaded_bytes = d.get('downloaded_bytes', 0)
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                
                if total_bytes > 0:
                    percent = (downloaded_bytes / total_bytes) * 100
                    percent = max(40, min(95, percent))
                    
                    if abs(percent - self.last_percent) >= 5:
                        speed = d.get('speed', 0)
                        speed_str = f"{speed/1024/1024:.1f} MB/s" if speed else ""
                        
                        self.progress_callback({
                            'status': 'downloading',
                            'percent': percent,
                            'speed': speed_str,
                            'downloaded_mb': downloaded_bytes / 1024 / 1024,
                            'message': f'正在下载... {percent:.1f}%'
                        })
                        self.last_percent = percent
                        
            elif status == 'finished':
                self.progress_callback({
                    'status': 'finished',
                    'percent': 95,
                    'message': '下载完成，正在处理文件...'
                })
                self.is_completed = True
                
        except Exception as e:
            logger.warning(f"进度更新异常: {e}")

class SimpleVideoDownloader:
    def __init__(self):
        self.system_info = self._diagnose_system()
        logger.info("🎯 简化视频下载器已初始化 - 专注下载成功")
        
    def _diagnose_system(self) -> Dict[str, Any]:
        """简单系统检查"""
        try:
            return {
                'python_version': sys.version.split()[0],
                'platform': sys_platform.system(),
                'yt_dlp_available': True,
                'ffmpeg_available': self._check_ffmpeg(),
            }
        except Exception as e:
            logger.warning(f"系统检查异常: {e}")
            return {}
    
    def _check_ffmpeg(self) -> bool:
        """检查FFmpeg可用性"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, timeout=5,
                                  creationflags=subprocess.CREATE_NO_WINDOW if sys_platform.system() == 'Windows' else 0)
            return result.returncode == 0
        except:
            return False
    
    def _get_base_config(self) -> Dict[str, Any]:
        """获取基础下载配置"""
        return {
            'format': 'best[height<=1080]/best',
            'merge_output_format': 'mp4',
            'writesubtitles': False,
            'writeautomaticsub': False,
            'geo_bypass': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'no_warnings': True,
            'quiet': True,
            'extract_flat': False,
            'socket_timeout': 60,
            'retries': 3,
            # 🔥关键：处理文件名中的特殊字符
            'restrictfilenames': True,  # 限制文件名为ASCII字符
            'windowsfilenames': True,   # Windows文件名兼容
        }
    
    def download_video(self, url: str, output_template: str, progress_callback: Optional[Callable] = None) -> str:
        """主下载函数 - 使用视频真实标题作为文件名"""
        logger.info(f"🎯 开始下载: {url}")
        
        try:
            # 设置进度跟踪
            progress_tracker = ProgressTracker()
            if progress_callback:
                progress_tracker.set_callback(progress_callback)
                progress_callback({
                    'status': 'starting',
                    'percent': 5,
                    'message': '正在获取视频信息...'
                })
            
            # 检测平台
            platform = 'unknown'
            if 'youtube.com' in url or 'youtu.be' in url:
                platform = 'youtube'
            elif 'bilibili.com' in url or 'b23.tv' in url:
                platform = 'bilibili'
            
            logger.info(f"📱 检测到平台: {platform}")
            
            if progress_callback:
                progress_callback({
                    'status': 'downloading',
                    'percent': 30,
                    'message': '正在连接服务器...'
                })
            
            # 执行下载
            return self._execute_download(url, output_template, progress_callback, platform)
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"💀 所有下载策略失败: {error_msg}")
            
            # 🔥关键：只在真正所有策略都失败后才向前端报告失败
            if progress_callback:
                # 这里的异常已经是_execute_download经过所有策略后抛出的
                # 错误分析已经在_execute_download中完成，这里直接传递
                progress_callback({
                    'status': 'failed',
                    'percent': 0,
                    'error': error_msg,
                    'error_type': 'download_failed',
                    'fatal': True,
                    'final': True
                })
            
            raise
    
    def _execute_download(self, url: str, output_template: str, progress_callback: Optional[Callable], platform: str) -> str:
        """执行下载 - 多策略，不轻易报告失败"""
        temp_dir = os.path.dirname(output_template)
        
        # 简化而强健的下载策略
        strategies = [
            {
                'name': '最高画质+音频',
                'format': 'best[height<=1080][ext=mp4]/bestvideo[height<=1080]+bestaudio/best[height<=1080]/best',
                'options': {
                    'merge_output_format': 'mp4',
                    'geo_bypass': True,
                    'nocheckcertificate': True,
                }
            },
            {
                'name': '通用高画质',
                'format': 'best[height<=720][ext=mp4]/bestvideo[height<=720]+bestaudio/best[height<=720]/best',
                'options': {
                    'merge_output_format': 'mp4',
                    'geo_bypass': True,
                    'nocheckcertificate': True,
                    'prefer_insecure': True,
                }
            },
            {
                'name': '兼容策略',
                'format': 'best[ext=mp4]/best',
                'options': {
                    'merge_output_format': 'mp4',
                    'geo_bypass': True,
                    'nocheckcertificate': True,
                    'prefer_insecure': True,
                    'ignoreerrors': True,
                }
            },
            {
                'name': '最大兼容',
                'format': 'best/worst',
                'options': {
                    'merge_output_format': 'mp4',
                    'geo_bypass': True,
                    'nocheckcertificate': True,
                    'prefer_insecure': True,
                    'ignoreerrors': True,
                    'force_ipv4': True,
                }
            }
        ]
        
        last_error = None
        
        for i, strategy in enumerate(strategies, 1):
            try:
                logger.info(f"🎯 尝试策略 {i}/{len(strategies)}: {strategy['name']}")
                
                # 🔥关键：不要在中间策略失败时报告给前端
                # 只在第一个策略开始时报告进度
                if i == 1 and progress_callback:
                    progress_callback({
                        'status': 'downloading',
                        'percent': 50,
                        'message': f'正在尝试下载...'
                    })
                
                # 获取配置
                ydl_opts = self._get_base_config()
                ydl_opts.update(strategy['options'])
                ydl_opts['format'] = strategy['format']
                
                # 🔥修复：直接使用传入的output_template
                ydl_opts['outtmpl'] = output_template
                
                # 平台特定配置
                if platform == 'youtube':
                    ydl_opts['youtube_include_dash_manifest'] = False
                elif platform == 'bilibili':
                    ydl_opts['http_headers'] = {
                        'Referer': 'https://www.bilibili.com/',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                
                # 进度回调
                progress_tracker = ProgressTracker()
                if progress_callback:
                    progress_tracker.set_callback(progress_callback)
                    ydl_opts['progress_hooks'] = [progress_tracker.update]
                
                # 执行下载
                files_before = set(os.listdir(temp_dir)) if os.path.exists(temp_dir) else set()
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                
                # 检查下载的文件
                files_after = set(os.listdir(temp_dir)) if os.path.exists(temp_dir) else set()
                new_files = files_after - files_before
                
                if new_files:
                    # 找到最大的文件
                    largest_file = None
                    largest_size = 0
                    
                    for filename in new_files:
                        file_path = os.path.join(temp_dir, filename)
                        if os.path.isfile(file_path):
                            size = os.path.getsize(file_path)
                            if size > largest_size:
                                largest_size = size
                                largest_file = filename
                    
                    if largest_file and largest_size > 1024 * 1024:  # 至少1MB
                        file_path = os.path.join(temp_dir, largest_file)
                        logger.info(f"🎉 下载成功！文件: {largest_file} ({largest_size/1024/1024:.2f} MB)")
                        
                        if progress_callback:
                            progress_callback({
                                'status': 'completed',
                                'percent': 100,
                                'filename': largest_file,
                                'file_size_mb': largest_size / 1024 / 1024,
                                'strategy': strategy['name'],
                                'final': True
                            })
                        
                        return file_path
                
                logger.info(f"⚠️ 策略 {i} 未获得有效文件，继续尝试下一个")
                
            except Exception as e:
                error_msg = str(e)
                last_error = error_msg
                logger.info(f"⚠️ 策略 {i} 失败: {error_msg[:100]}...")
                
                # 🔥关键：不要向前端报告中间策略的失败
                # 只记录错误，继续尝试下一个策略
                if i < len(strategies):
                    logger.info(f"🔄 继续尝试下一个策略...")
                    time.sleep(0.5)
                    continue
        
        # 🔥只有所有策略都失败了才报告错误
        logger.error(f"💀 所有 {len(strategies)} 个策略都失败")
        error_analysis = analyze_bilibili_error(last_error or '下载失败')
        raise Exception(error_analysis.get('user_friendly', '所有下载策略都失败，请检查视频链接'))
    
    def _get_video_info(self, url: str) -> Dict[str, Any]:
        """获取视频信息，包括标题"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'geo_bypass': True,
                'nocheckcertificate': True,
                'skip_download': True,  # 只获取信息，不下载
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    'title': info.get('title', 'Unknown_Video'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', ''),
                    'upload_date': info.get('upload_date', ''),
                }
        except Exception as e:
            logger.warning(f"获取视频信息失败: {e}")
            return {'title': 'Unknown_Video'}
    
    def _clean_filename(self, title: str) -> str:
        """清理文件名，移除不合法字符"""
        import re
        
        # 移除不合法的文件名字符
        illegal_chars = r'[<>:"/\\|?*]'
        title = re.sub(illegal_chars, '', title)
        
        # 替换一些特殊字符为合法字符
        replacements = {
            '【': '[',
            '】': ']',
            '（': '(',
            '）': ')',
            '：': '-',
            '？': '',
            '！': '',
            '，': ',',
            '。': '.',
        }
        
        for old, new in replacements.items():
            title = title.replace(old, new)
        
        # 移除首尾空格和点
        title = title.strip(' ._-')
        
        # 限制长度，避免文件名过长
        if len(title) > 100:
            title = title[:100]
        
        # 如果清理后为空，使用默认名称
        if not title:
            title = 'Unknown_Video'
        
        return title

# 全局下载器实例
_downloader = None

def get_downloader():
    global _downloader
    if _downloader is None:
        _downloader = SimpleVideoDownloader()
    return _downloader

def download_video(url: str, output_template: str, progress_callback: Optional[Callable] = None) -> str:
    """公共下载接口"""
    downloader = get_downloader()
    return downloader.download_video(url, output_template, progress_callback)

def get_video_info(url: str) -> Dict[str, Any]:
    """获取视频信息用于预检测"""
    try:
        downloader = get_downloader()
        info = downloader._get_video_info(url)
        
        platform = 'unknown'
        if 'youtube.com' in url or 'youtu.be' in url:
            platform = 'youtube'
        elif 'bilibili.com' in url or 'b23.tv' in url:
            platform = 'bilibili'
        
        return {
            'title': info.get('title', '未知标题'),
            'duration': info.get('duration', 0),
            'platform': platform,
            'uploader': info.get('uploader', ''),
            'available': True
        }
    except Exception as e:
        logger.warning(f"获取视频信息失败: {str(e)}")
        raise Exception("无法获取视频信息，请检查链接是否有效")
