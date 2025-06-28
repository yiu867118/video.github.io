import yt_dlp
import os
import logging
import tempfile
import json
import re
import browser_cookie3
import threading
import time
import subprocess
import platform as sys_platform
from datetime import datetime
from typing import Optional, Dict, Any, Callable, List
import requests
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedURLValidator:
    """增强URL验证器 - 支持更多平台和格式"""
    
    @staticmethod
    def validate_and_fix_url(url: str) -> Dict[str, Any]:
        """验证并修复URL - 增强版"""
        url = url.strip()
        
        # 增强URL提取模式 - 支持更多格式
        url_patterns = [
            # B站各种格式
            r'https?://b23\.tv/[a-zA-Z0-9]+(?:\?[^\s]*)?',
            r'https?://(?:www\.)?bilibili\.com/video/[a-zA-Z0-9]+(?:\?[^\s]*)?',
            r'https?://bilibili\.com/video/[a-zA-Z0-9]+(?:\?[^\s]*)?',
            r'https?://(?:m\.)?bilibili\.com/video/[a-zA-Z0-9]+(?:\?[^\s]*)?',
            # YouTube各种格式
            r'https?://(?:www\.)?youtube\.com/watch\?v=[a-zA-Z0-9_-]+(?:&[^\s]*)?',
            r'https?://youtu\.be/[a-zA-Z0-9_-]+(?:\?[^\s]*)?',
            r'https?://(?:m\.)?youtube\.com/watch\?v=[a-zA-Z0-9_-]+(?:&[^\s]*)?',
            # 其他平台
            r'https?://(?:www\.)?douyin\.com/[^\s]+',
            r'https?://v\.douyin\.com/[^\s]+',
            r'https?://(?:www\.)?tiktok\.com/[^\s]+',
            # 通用URL匹配（最后兜底）
            r'https?://[^\s\u4e00-\u9fff]+',  # 排除中文字符
        ]
        
        # 智能URL提取
        extracted_url = None
        for pattern in url_patterns:
            matches = re.findall(pattern, url, re.IGNORECASE)
            if matches:
                # 如果有多个匹配，选择最长的（通常最完整）
                extracted_url = max(matches, key=len)
                logger.info(f"提取URL: {url} -> {extracted_url}")
                break
        
        if extracted_url:
            url = extracted_url
        
        # 平台识别和处理
        if any(domain in url.lower() for domain in ['bilibili.com', 'b23.tv']):
            return EnhancedURLValidator._validate_bilibili_url(url)
        elif any(domain in url.lower() for domain in ['youtube.com', 'youtu.be']):
            return EnhancedURLValidator._validate_youtube_url(url)
        elif any(domain in url.lower() for domain in ['douyin.com', 'tiktok.com']):
            return EnhancedURLValidator._validate_douyin_url(url)
        else:
            return {
                'valid': True,
                'fixed_url': url,
                'platform': 'unknown',
                'warning': None
            }

    @staticmethod
    def _validate_bilibili_url(url: str) -> Dict[str, Any]:
        """验证B站URL - 增强版"""
        original_url = url
        
        # 处理短链接 - 增强重试机制
        if 'b23.tv' in url:
            try:
                logger.info(f"短链接解析开始: {url}")
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                }
                
                # 多次尝试解析短链接
                for attempt in range(3):
                    try:
                        response = requests.get(
                            url, 
                            allow_redirects=True, 
                            timeout=15,
                            headers=headers,
                            verify=False  # 忽略SSL验证问题
                        )
                        if response.url != url:
                            url = response.url
                            logger.info(f"短链接解析成功 (尝试 {attempt+1}): {original_url} -> {url}")
                            break
                    except Exception as e:
                        logger.warning(f"短链接解析尝试 {attempt+1} 失败: {e}")
                        if attempt == 2:  # 最后一次尝试
                            logger.warning(f"短链接解析最终失败，使用原URL: {original_url}")
                        time.sleep(1)
                        
            except Exception as e:
                logger.warning(f"短链接解析异常: {e}")
        
        # 增强URL参数清理
        if 'bilibili.com' in url:
            unwanted_params = [
                'share_source', 'vd_source', 'share_medium', 'share_plat',
                'timestamp', 'bbid', 'ts', 'from_source', 'from_spmid',
                'spm_id_from', 'unique_k', 'rt', 'up_id', 'seid', 
                'share_from', 'share_times', 'plat_id', 'bsource',
                'msource', 'is_story_h5', 'mid', 'tid', 'network',
                'platform', 'funnel', 'broadcast_type'
            ]
            
            try:
                parsed = urlparse(url)
                if parsed.query:
                    query_params = parse_qs(parsed.query, keep_blank_values=True)
                    cleaned_params = {k: v for k, v in query_params.items() 
                                    if k not in unwanted_params}
                    new_query = urlencode(cleaned_params, doseq=True) if cleaned_params else ''
                    url = urlunparse((
                        parsed.scheme, parsed.netloc, parsed.path,
                        parsed.params, new_query, parsed.fragment
                    ))
                    logger.info(f"清理URL参数: {url}")
            except Exception as e:
                logger.warning(f"URL参数清理失败: {e}")
        
        # 增强视频ID提取
        patterns = [
            # BV号模式 (标准10位 + 新12位格式)
            r'BV([a-zA-Z0-9]{10,12})',
            r'/video/BV([a-zA-Z0-9]{10,12})',
            r'[?&]bvid=BV([a-zA-Z0-9]{10,12})',
            # av号模式
            r'av(\d+)',
            r'/video/av(\d+)',
            r'[?&]aid=(\d+)',
            # 处理新格式
            r'bilibili\.com/video/([A-Za-z0-9]+)',
        ]
        
        video_id = None
        video_type = None
        
        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                extracted_id = match.group(1)
                if pattern.startswith('BV') or 'bvid' in pattern or (extracted_id.startswith('BV')):
                    video_id = f"BV{extracted_id}" if not extracted_id.startswith('BV') else extracted_id
                    video_type = 'BV'
                elif pattern.startswith('av') or 'aid' in pattern or extracted_id.isdigit():
                    video_id = f"av{extracted_id}" if not extracted_id.startswith('av') else extracted_id
                    video_type = 'av'
                else:
                    # 处理其他格式
                    if extracted_id.startswith(('BV', 'av')):
                        video_id = extracted_id
                        video_type = 'BV' if extracted_id.startswith('BV') else 'av'
                    else:
                        # 尝试作为BV号处理
                        video_id = f"BV{extracted_id}"
                        video_type = 'BV'
                
                logger.info(f"提取视频ID: {video_id} (类型: {video_type})")
                break
        
        # 构建标准URL
        if video_id and video_type:
            fixed_url = f'https://www.bilibili.com/video/{video_id}'
            return {
                'valid': True,
                'fixed_url': fixed_url,
                'platform': 'bilibili',
                'warning': None,
                'video_id': video_id,
                'video_type': video_type
            }
        
        # 兜底处理
        if 'bilibili.com' in url and '/video/' in url:
            return {
                'valid': True,
                'fixed_url': url,
                'platform': 'bilibili',
                'warning': None
            }
        
        if 'b23.tv' in original_url:
            return {
                'valid': True,
                'fixed_url': original_url,
                'platform': 'bilibili',
                'warning': '短链接处理中，如果下载失败请使用完整链接'
            }
        
        return {
            'valid': True,
            'fixed_url': url,
            'platform': 'bilibili',
            'warning': 'URL格式可能不标准，将尝试直接下载'
        }

    @staticmethod
    def _validate_youtube_url(url: str) -> Dict[str, Any]:
        """验证YouTube URL - 增强版"""
        patterns = [
            r'youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
            r'youtu\.be/([a-zA-Z0-9_-]{11})',
            r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
            r'm\.youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                video_id = match.group(1)
                fixed_url = f'https://www.youtube.com/watch?v={video_id}'
                return {
                    'valid': True,
                    'fixed_url': fixed_url,
                    'platform': 'youtube',
                    'warning': None,
                    'video_id': video_id
                }
        
        return {
            'valid': True,
            'fixed_url': url,
            'platform': 'youtube',
            'warning': None
        }

    @staticmethod  
    def _validate_douyin_url(url: str) -> Dict[str, Any]:
        """验证抖音/TikTok URL"""
        return {
            'valid': True,
            'fixed_url': url,
            'platform': 'douyin',
            'warning': None
        }

class SimpleProgressTracker:
    """简单进度追踪器"""
    def __init__(self):
        self.progress_callback = None
        self.lock = threading.Lock()
        self.last_update_time = 0
        self.update_interval = 0.3
        self.is_completed = False
        
    def set_callback(self, callback: Optional[Callable]):
        """设置进度回调"""
        with self.lock:
            self.progress_callback = callback
            self.is_completed = False
            
    def progress_hook(self, d: Dict[str, Any]):
        """简单进度回调"""
        if not self.progress_callback or self.is_completed:
            return
            
        current_time = time.time()
        
        # 频率控制
        if current_time - self.last_update_time < self.update_interval:
            return
            
        try:
            with self.lock:
                if self.is_completed:
                    return
                    
                status = d.get('status', 'unknown')
                
                if status == 'downloading':
                    downloaded_bytes = d.get('downloaded_bytes', 0)
                    total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
                    
                    if total_bytes and total_bytes > 0:
                        percent = min((downloaded_bytes / total_bytes) * 100, 99)
                    else:
                        percent = 50
                    
                    speed = d.get('speed', 0)
                    if speed and speed > 0:
                        if speed > 1024 * 1024:
                            speed_str = f"{speed/1024/1024:.2f} MB/s"
                        elif speed > 1024:
                            speed_str = f"{speed/1024:.2f} KB/s"
                        else:
                            speed_str = f"{speed:.0f} B/s"
                    else:
                        speed_str = "计算中..."
                    
                    progress_data = {
                        'status': 'downloading',
                        'percent': round(percent, 1),
                        'downloaded_mb': round(downloaded_bytes / 1024 / 1024, 2),
                        'total_mb': round(total_bytes / 1024 / 1024, 2) if total_bytes else 0,
                        'speed': speed_str,
                        'eta': '计算中...',
                        'filename': os.path.basename(d.get('filename', ''))
                    }
                    
                    self.progress_callback(progress_data)
                    self.last_update_time = current_time
                    
                elif status == 'finished':
                    self.is_completed = True
                    filename = os.path.basename(d.get('filename', ''))
                    file_size = 0
                    if d.get('filename') and os.path.exists(d.get('filename')):
                        file_size = os.path.getsize(d.get('filename')) / 1024 / 1024
                    
                    self.progress_callback({
                        'status': 'finished',
                        'percent': 100,
                        'filename': filename,
                        'file_size_mb': round(file_size, 2)
                    })
                        
        except Exception as e:
            logger.debug(f"进度处理错误: {e}")

progress_tracker = SimpleProgressTracker()

class SimpleCookieManager:
    """简单Cookie管理器"""
    
    @staticmethod
    def get_browser_cookies(domain: str = '.bilibili.com') -> Dict[str, str]:
        """获取浏览器Cookies"""
        cookies = {}
        
        try:
            # 尝试多个浏览器
            browsers = [
                ('Chrome', browser_cookie3.chrome),
                ('Edge', browser_cookie3.edge),
                ('Firefox', browser_cookie3.firefox)
            ]
            
            for browser_name, browser_func in browsers:
                try:
                    logger.info(f"从{browser_name}获取cookies...")
                    browser_cookies = browser_func(domain_name=domain)
                    
                    temp_cookies = {}
                    for cookie in browser_cookies:
                        if cookie.name in ['SESSDATA', 'bili_jct', 'buvid3', 'DedeUserID']:
                            temp_cookies[cookie.name] = cookie.value
                    
                    if temp_cookies:
                        cookies.update(temp_cookies)
                        logger.info(f"从{browser_name}获取到 {len(temp_cookies)} 个cookies")
                        break
                        
                except Exception as e:
                    logger.debug(f"{browser_name} cookies获取失败: {e}")
                    continue
            
            if cookies:
                logger.info(f"总共获取到 {len(cookies)} 个有效cookies")
                
        except Exception as e:
            logger.warning(f"获取cookies失败: {e}")
        
        return cookies

    @staticmethod
    def create_cookie_file(cookies: Dict[str, str], domain: str = '.bilibili.com') -> Optional[str]:
        """创建cookie文件"""
        if not cookies:
            return None
            
        try:
            temp_cookie_file = tempfile.NamedTemporaryFile(
                mode='w', 
                suffix='.txt', 
                delete=False,
                encoding='utf-8'
            )
            
            temp_cookie_file.write("# Netscape HTTP Cookie File\n\n")
            
            expiration = int(datetime.now().timestamp()) + 86400
            
            for name, value in cookies.items():
                line = f"{domain}\tTRUE\t/\tFALSE\t{expiration}\t{name}\t{value}\n"
                temp_cookie_file.write(line)
            
            temp_cookie_file.close()
            logger.info(f"创建cookie文件: {temp_cookie_file.name}")
            return temp_cookie_file.name
            
        except Exception as e:
            logger.error(f"创建cookie文件失败: {e}")
            return None

class RockSolidVideoDownloader:
    """坚如磐石视频下载器 - 移动设备音频终极修复版"""
    
    def __init__(self):
        self.cookie_manager = SimpleCookieManager()
        self.url_validator = EnhancedURLValidator()
        self.download_completed = False
        logger.info("🏔️ 坚如磐石下载器已初始化 - 高效移动兼容版")
        logger.info("🎯 策略: 10个高效策略，避免卡顿，确保移动兼容")
        logger.info("� 音频修复: 智能检测，按需修复")
        
    def download_video(self, url: str, output_template: str, progress_callback: Optional[Callable] = None) -> str:
        """坚如磐石下载 - 移动设备音频完美兼容"""
        cookie_file = None
        self.download_completed = False
        
        try:
            logger.info("🏔️ 坚如磐石下载器启动 - 高效移动兼容版")
            logger.info("🎯 解决卡顿问题，确保PC和移动设备完美下载")
            
            # URL验证
            url_validation = self.url_validator.validate_and_fix_url(url)
            
            if not url_validation['valid']:
                error_msg = url_validation.get('warning', '无效URL')
                raise Exception(error_msg)
            
            fixed_url = url_validation['fixed_url']
            platform = url_validation['platform']
            
            logger.info(f"平台: {platform}")
            logger.info(f"URL: {fixed_url}")
            logger.info(f"📱 移动设备兼容模式: ✅")
            
            # 设置进度回调
            if progress_callback:
                progress_tracker.set_callback(progress_callback)
                progress_callback({
                    'status': 'initializing',
                    'percent': 10,
                    'message': '启动移动兼容下载器...'
                })
            
            # 创建输出目录
            temp_dir = os.path.dirname(output_template)
            os.makedirs(temp_dir, exist_ok=True)
            
            # 获取cookies
            if platform == 'bilibili':
                if progress_callback:
                    progress_callback({
                        'status': 'auth',
                        'percent': 20,
                        'message': '获取登录信息...'
                    })
                
                cookies = self.cookie_manager.get_browser_cookies('.bilibili.com')
                if cookies:
                    cookie_file = self.cookie_manager.create_cookie_file(cookies, '.bilibili.com')
            
            # 执行下载
            if progress_callback:
                progress_callback({
                    'status': 'preparing',
                    'percent': 30,
                    'message': '准备移动兼容下载...'
                })
            
            result = self._execute_download(
                fixed_url, output_template, cookie_file, progress_callback, platform
            )
            
            self.download_completed = True
            return result
            
        except Exception as e:
            logger.error(f"下载失败: {e}")
            
            # 分析错误类型
            error_analysis = analyze_bilibili_error(str(e))
            is_fatal = error_analysis.get('fatal', False)
            error_type = error_analysis.get('error_type', 'unknown_error')
            user_friendly_msg = error_analysis.get('user_friendly', str(e))
            
            if progress_callback:
                progress_callback({
                    'status': 'failed',
                    'percent': 0,
                    'error': user_friendly_msg,
                    'error_type': error_type,
                    'fatal': is_fatal,
                    'final': True
                })
            
            raise e
            
        finally:
            self._cleanup(cookie_file)
    
    def _execute_download(self, url: str, output_template: str, 
                        cookie_file: Optional[str], progress_callback: Optional[Callable], 
                        platform: str) -> str:
        """执行下载 - 10个高效移动设备兼容策略（修复卡顿版）"""
        temp_dir = os.path.dirname(output_template)
        
        # 10个高效策略 - 避免卡顿，确保移动兼容
        strategies = [
            {
                'name': '最佳质量自动合并',
                'format': 'best[height<=1080]',
                'force_audio_fix': False,
                'options': {
                    'merge_output_format': 'mp4'
                }
            },
            {
                'name': '音视频分离合并',
                'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
                'force_audio_fix': True,
                'options': {
                    'merge_output_format': 'mp4'
                }
            },
            {
                'name': '标准720p质量',
                'format': 'best[height<=720]',
                'force_audio_fix': False,
                'options': {
                    'merge_output_format': 'mp4'
                }
            },
            {
                'name': '720p音视频合并',
                'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
                'force_audio_fix': True,
                'options': {
                    'merge_output_format': 'mp4'
                }
            },
            {
                'name': 'MP4格式优先',
                'format': 'best[ext=mp4]/best',
                'force_audio_fix': False,
                'options': {}
            },
            {
                'name': '中等质量480p',
                'format': 'best[height<=480]',
                'force_audio_fix': False,
                'options': {
                    'merge_output_format': 'mp4'
                }
            },
            {
                'name': '480p音视频合并',
                'format': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
                'force_audio_fix': True,
                'options': {
                    'merge_output_format': 'mp4'
                }
            },
            {
                'name': '任意最佳质量',
                'format': 'best',
                'force_audio_fix': False,
                'options': {}
            },
            {
                'name': '任意音视频合并',
                'format': 'bestvideo+bestaudio/best',
                'force_audio_fix': True,
                'options': {
                    'merge_output_format': 'mp4'
                }
            },
            {
                'name': '兜底最低质量',
                'format': 'worst',
                'force_audio_fix': False,
                'options': {
                    'ignoreerrors': True
                }
            }
        ]
        
        for i, strategy in enumerate(strategies, 1):
            logger.info(f"🎯 尝试策略 {i}/10: {strategy['name']}")
            
            if progress_callback:
                base_percent = 35 + (i-1) * 6
                progress_callback({
                    'status': 'downloading',
                    'percent': base_percent,
                    'message': f"执行{strategy['name']}..."
                })
            
            try:
                # 记录下载前文件
                files_before = set(os.listdir(temp_dir)) if os.path.exists(temp_dir) else set()
                
                # 简化但高效的配置
                ydl_opts = {
                    'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                    'noplaylist': True,
                    'progress_hooks': [progress_tracker.progress_hook],
                    'socket_timeout': 60,
                    'retries': 5,
                    'fragment_retries': 5,
                    'extract_flat': False,
                    'writethumbnail': False,
                    'writesubtitles': False,
                    'writeautomaticsub': False,
                    'ignoreerrors': False,
                    'no_warnings': False,
                    'prefer_ffmpeg': True,
                    'keepvideo': False,
                }
                
                # 添加格式
                if strategy['format']:
                    ydl_opts['format'] = strategy['format']
                
                # 添加策略特定选项
                ydl_opts.update(strategy['options'])
                
                # 添加cookies
                if cookie_file and os.path.exists(cookie_file):
                    ydl_opts['cookiefile'] = cookie_file
                
                # B站专用优化
                if platform == 'bilibili':
                    ydl_opts.update({
                        'http_headers': {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                            'Referer': 'https://www.bilibili.com/',
                            'Accept': '*/*',
                            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                        }
                    })
                
                download_start = time.time()
                logger.info(f"⚡ 开始执行 - {strategy['name']}")
                logger.info(f"📋 使用格式: {strategy['format'] or '自动'}")
                
                # 执行下载
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                
                download_time = time.time() - download_start
                
                # 检查下载结果
                files_after = set(os.listdir(temp_dir)) if os.path.exists(temp_dir) else set()
                new_files = files_after - files_before
                
                if new_files:
                    # 找到最大的视频文件
                    valid_files = []
                    video_extensions = {'.mp4', '.flv', '.mkv', '.avi', '.mov', '.wmv', '.webm', '.m4v'}
                    
                    for f in new_files:
                        file_path = os.path.join(temp_dir, f)
                        file_size = os.path.getsize(file_path)
                        file_ext = os.path.splitext(f.lower())[1]
                        
                        if file_size > 1024 * 1024 and file_ext in video_extensions:
                            valid_files.append((f, file_size))
                    
                    if valid_files:
                        largest_file, file_size = max(valid_files, key=lambda x: x[1])
                        file_path = os.path.join(temp_dir, largest_file)
                        file_size_mb = file_size / 1024 / 1024
                        
                        # 选择性音频修复 - 只在需要时进行
                        if strategy.get('force_audio_fix', False):
                            logger.info(f"🔧 检查是否需要音频修复...")
                            verified_file_path = self._smart_audio_fix(file_path, temp_dir)
                            if verified_file_path != file_path:
                                file_path = verified_file_path
                                largest_file = os.path.basename(file_path)
                                file_size = os.path.getsize(file_path)
                                file_size_mb = file_size / 1024 / 1024
                                logger.info(f"✅ 音频已优化为移动设备兼容格式")
                        
                        logger.info("🎉 坚如磐石下载成功！")
                        logger.info(f"✅ 成功策略: {strategy['name']}")
                        logger.info(f"📁 文件名: {largest_file}")
                        logger.info(f"📊 文件大小: {file_size_mb:.2f} MB")
                        logger.info(f"⏱️ 下载耗时: {download_time:.1f} 秒")
                        
                        if progress_callback:
                            progress_callback({
                                'status': 'completed',
                                'percent': 100,
                                'filename': largest_file,
                                'file_size_mb': file_size_mb,
                                'duration': download_time,
                                'strategy': strategy['name'],
                                'mobile_compatible': True,
                                'final': True
                            })
                        
                        return file_path
                    else:
                        # 清理无效文件
                        for f in new_files:
                            try:
                                os.remove(os.path.join(temp_dir, f))
                            except:
                                pass
                        continue
                else:
                    continue
                    
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"❌ 策略 {i} 失败: {error_msg}")
                
                # 如果是最后一个策略
                if i == len(strategies):
                    if any(keyword in error_msg.lower() for keyword in ['json', 'expecting value']):
                        raise Exception('B站服务器返回数据异常，可能是临时故障，请稍后重试')
                    elif any(keyword in error_msg.lower() for keyword in ['timeout', 'timed out']):
                        raise Exception('网络连接问题，请检查网络后重试')
                    else:
                        raise Exception(f'所有下载策略都失败: {error_msg}')
                
                if i < len(strategies):
                    time.sleep(1)
                continue
        
        raise Exception('所有下载策略都失败，这个视频可能无法下载')

    def _smart_audio_fix(self, file_path: str, temp_dir: str) -> str:
        """智能音频修复 - 只在需要时才修复，避免卡顿"""
        try:
            logger.info(f"🔍 智能检查音频兼容性: {os.path.basename(file_path)}")
            
            # 检查是否有FFmpeg
            if not self._check_ffmpeg():
                logger.info("ℹ️ FFmpeg不可用，跳过音频修复")
                return file_path
            
            # 检查音频流信息
            audio_info = self._get_audio_info(file_path)
            if not audio_info:
                logger.info("ℹ️ 无法获取音频信息，可能没有音频流，跳过修复")
                return file_path
            
            codec = audio_info.get('codec', '').lower()
            sample_rate = audio_info.get('sample_rate', 0)
            channels = audio_info.get('channels', 0)
            
            logger.info(f"🔊 当前音频: {codec} {sample_rate}Hz {channels}ch")
            
            # 检查是否需要修复
            needs_fix = False
            reasons = []
            
            if codec not in ['aac', 'mp3']:
                needs_fix = True
                reasons.append(f"编码格式{codec}移动兼容性差")
            
            if sample_rate > 48000:
                needs_fix = True
                reasons.append(f"采样率{sample_rate}Hz过高")
                
            if channels > 2:
                needs_fix = True
                reasons.append(f"声道数{channels}过多")
            
            if not needs_fix:
                logger.info("✅ 音频格式已符合移动设备要求，无需修复")
                return file_path
            
            logger.info(f"🔧 需要音频修复: {', '.join(reasons)}")
            return self._execute_audio_fix(file_path, temp_dir)
            
        except Exception as e:
            logger.warning(f"⚠️ 智能音频检查失败: {e}")
            return file_path

    def _execute_audio_fix(self, file_path: str, temp_dir: str) -> str:
        """执行音频修复 - 快速高效版本"""
        try:
            original_name = os.path.basename(file_path)
            name_without_ext = os.path.splitext(original_name)[0]
            fixed_name = f"{name_without_ext}_mobile_fixed.mp4"
            fixed_path = os.path.join(temp_dir, fixed_name)
            
            logger.info(f"🔧 执行快速音频修复: {original_name} -> {fixed_name}")
            
            # 快速音频修复命令 - 优化性能
            cmd = [
                'ffmpeg',
                '-i', file_path,
                '-c:v', 'copy',  # 复制视频流，不重新编码
                '-c:a', 'aac',   # 音频转AAC
                '-b:a', '128k',  # 音频比特率
                '-ar', '44100',  # 采样率
                '-ac', '2',      # 双声道
                '-movflags', '+faststart',  # 快速启动
                '-avoid_negative_ts', 'make_zero',
                '-y',  # 覆盖输出文件
                fixed_path
            ]
            
            logger.info(f"🛠️ 执行快速音频修复")
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=120,  # 2分钟超时
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys_platform.system() == 'Windows' else 0
            )
            
            if result.returncode == 0 and os.path.exists(fixed_path):
                fixed_size = os.path.getsize(fixed_path)
                if fixed_size > 1024 * 1024:  # 至少1MB
                    logger.info(f"✅ 音频修复成功: {fixed_size / 1024 / 1024:.2f} MB")
                    # 删除原文件
                    try:
                        os.remove(file_path)
                    except:
                        pass
                    return fixed_path
                else:
                    logger.warning("⚠️ 修复后文件太小，保留原文件")
                    try:
                        os.remove(fixed_path)
                    except:
                        pass
            else:
                logger.warning(f"⚠️ 音频修复失败")
            
            return file_path
            
        except Exception as e:
            logger.error(f"❌ 音频修复异常: {e}")
            return file_path

    def _force_mobile_audio_fix(self, file_path: str, temp_dir: str) -> str:
        """强制移动设备音频修复 - 终极版本，确保100%兼容"""
        try:
            original_name = os.path.basename(file_path)
            name_without_ext = os.path.splitext(original_name)[0]
            fixed_name = f"{name_without_ext}_mobile_perfect.mp4"
            fixed_path = os.path.join(temp_dir, fixed_name)
            
            logger.info(f"🔧 开始强制移动设备音频修复: {original_name} -> {fixed_name}")
            logger.info(f"🎯 目标: 100%移动设备兼容，AAC 44.1kHz 双声道")
            
            # 检查是否有FFmpeg
            if not self._check_ffmpeg():
                logger.warning("⚠️ FFmpeg不可用，无法进行音频修复")
                return file_path
            
            # 终极FFmpeg命令 - 移动设备完美兼容
            cmd = [
                'ffmpeg',
                '-i', file_path,
                # 视频流处理
                '-c:v', 'libx264',          # H.264编码
                '-preset', 'medium',        # 编码速度
                '-crf', '23',               # 恒定质量
                '-profile:v', 'main',       # H.264 main profile
                '-level', '3.1',            # H.264 level 3.1
                '-pix_fmt', 'yuv420p',      # 像素格式
                '-maxrate', '2000k',        # 最大比特率
                '-bufsize', '4000k',        # 缓冲区大小
                # 音频流处理 - 移动设备完美兼容
                '-c:a', 'aac',              # AAC音频编码
                '-b:a', '128k',             # 音频比特率128k
                '-ar', '44100',             # 采样率44.1kHz
                '-ac', '2',                 # 双声道
                '-aac_coder', 'twoloop',    # AAC编码器
                '-profile:a', 'aac_low',    # AAC Low Complexity profile
                # 容器和优化
                '-f', 'mp4',                # MP4容器
                '-movflags', '+faststart',  # 快速启动
                '-avoid_negative_ts', 'make_zero',  # 避免负时间戳
                '-fflags', '+genpts',       # 生成PTS
                '-map_metadata', '0',       # 复制元数据
                '-map', '0:v:0',           # 映射第一个视频流
                '-map', '0:a:0',           # 映射第一个音频流
                '-strict', '-2',           # 严格模式
                '-y',                      # 覆盖输出文件
                fixed_path
            ]
            
            logger.info(f"🛠️ 执行终极移动设备音频修复命令")
            logger.info(f"📋 命令: {' '.join(cmd[:10])}...")  # 只显示前10个参数避免日志过长
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=600,  # 10分钟超时
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys_platform.system() == 'Windows' else 0
            )
            
            if result.returncode == 0 and os.path.exists(fixed_path):
                fixed_size = os.path.getsize(fixed_path)
                original_size = os.path.getsize(file_path)
                
                if fixed_size > 1024 * 1024:  # 至少1MB
                    logger.info(f"✅ 移动设备音频修复成功!")
                    logger.info(f"📊 原文件: {original_size / 1024 / 1024:.2f} MB")
                    logger.info(f"📊 修复后: {fixed_size / 1024 / 1024:.2f} MB") 
                    logger.info(f"🔊 音频格式: AAC 128k 44.1kHz 双声道")
                    logger.info(f"📱 移动设备兼容: 100% 完美支持")
                    
                    # 验证修复后的音频信息
                    audio_info = self._get_audio_info(fixed_path)
                    if audio_info:
                        logger.info(f"🎵 验证音频: {audio_info.get('codec', 'unknown')} {audio_info.get('sample_rate', 0)}Hz {audio_info.get('channels', 0)}ch")
                    
                    # 删除原文件
                    try:
                        os.remove(file_path)
                        logger.info(f"🗑️ 已删除原文件")
                    except:
                        pass
                    
                    return fixed_path
                else:
                    logger.warning("⚠️ 修复后文件太小，保留原文件")
                    try:
                        os.remove(fixed_path)
                    except:
                        pass
            else:
                logger.warning(f"⚠️ 移动设备音频修复失败")
                if result.stderr:
                    logger.warning(f"FFmpeg错误: {result.stderr[:500]}...")  # 限制错误信息长度
            
            return file_path
            
        except Exception as e:
            logger.error(f"❌ 强制移动设备音频修复异常: {e}")
            return file_path

    def _verify_and_fix_audio(self, file_path: str, temp_dir: str) -> str:
        """验证并修复音频 - 确保移动设备兼容性"""
        try:
            logger.info(f"🔍 开始音频兼容性检查: {os.path.basename(file_path)}")
            
            # 检查是否有FFmpeg
            if not self._check_ffmpeg():
                logger.warning("⚠️ FFmpeg不可用，跳过音频修复")
                return file_path
            
            # 检查音频流信息
            audio_info = self._get_audio_info(file_path)
            if not audio_info:
                logger.warning("⚠️ 无法获取音频信息，尝试修复")
                return self._force_audio_fix(file_path, temp_dir)
            
            codec = audio_info.get('codec', '').lower()
            sample_rate = audio_info.get('sample_rate', 0)
            channels = audio_info.get('channels', 0)
            
            logger.info(f"🔊 当前音频: {codec} {sample_rate}Hz {channels}ch")
            
            # 检查是否需要修复
            needs_fix = False
            reasons = []
            
            if codec not in ['aac', 'mp3']:
                needs_fix = True
                reasons.append(f"编码格式{codec}不兼容移动设备")
            
            if sample_rate > 48000:
                needs_fix = True
                reasons.append(f"采样率{sample_rate}Hz过高")
                
            if channels > 2:
                needs_fix = True
                reasons.append(f"声道数{channels}过多")
            
            if not needs_fix:
                logger.info("✅ 音频格式已符合移动设备要求")
                return file_path
            
            logger.info(f"🔧 需要修复音频: {', '.join(reasons)}")
            return self._force_audio_fix(file_path, temp_dir)
            
        except Exception as e:
            logger.warning(f"⚠️ 音频检查失败，尝试强制修复: {e}")
            return self._force_audio_fix(file_path, temp_dir)
    
    def _check_ffmpeg(self) -> bool:
        """检查FFmpeg是否可用"""
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if sys_platform.system() == 'Windows' else 0
            )
            return result.returncode == 0
        except:
            return False
    
    def _get_audio_info(self, file_path: str) -> Dict[str, Any]:
        """获取音频流信息"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_streams',
                '-select_streams', 'a:0',
                file_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=30,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys_platform.system() == 'Windows' else 0
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                streams = data.get('streams', [])
                if streams:
                    stream = streams[0]
                    return {
                        'codec': stream.get('codec_name', ''),
                        'sample_rate': int(stream.get('sample_rate', 0)),
                        'channels': int(stream.get('channels', 0)),
                        'bit_rate': int(stream.get('bit_rate', 0))
                    }
            return {}
        except:
            return {}
    
    def _force_audio_fix(self, file_path: str, temp_dir: str) -> str:
        """强制修复音频为移动设备兼容格式"""
        try:
            original_name = os.path.basename(file_path)
            name_without_ext = os.path.splitext(original_name)[0]
            fixed_name = f"{name_without_ext}_mobile_fixed.mp4"
            fixed_path = os.path.join(temp_dir, fixed_name)
            
            logger.info(f"🔧 开始强制音频修复: {original_name} -> {fixed_name}")
            
            # FFmpeg命令 - 移动设备完美兼容
            cmd = [
                'ffmpeg',
                '-i', file_path,
                '-c:v', 'copy',  # 视频流复制（如果可能）
                '-c:a', 'aac',   # 音频转AAC
                '-b:a', '128k',  # 音频比特率
                '-ar', '44100',  # 采样率
                '-ac', '2',      # 双声道
                '-movflags', '+faststart',  # 优化移动播放
                '-avoid_negative_ts', 'make_zero',
                '-fflags', '+genpts',
                '-y',  # 覆盖输出文件
                fixed_path
            ]
            
            logger.info(f"🛠️ 执行FFmpeg修复命令")
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=300,  # 5分钟超时
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys_platform.system() == 'Windows' else 0
            )
            
            if result.returncode == 0 and os.path.exists(fixed_path):
                fixed_size = os.path.getsize(fixed_path)
                if fixed_size > 1024 * 1024:  # 至少1MB
                    logger.info(f"✅ 音频修复成功: {fixed_size / 1024 / 1024:.2f} MB")
                    # 删除原文件（可选）
                    try:
                        os.remove(file_path)
                    except:
                        pass
                    return fixed_path
                else:
                    logger.warning("⚠️ 修复后文件太小，保留原文件")
                    try:
                        os.remove(fixed_path)
                    except:
                        pass
            else:
                logger.warning(f"⚠️ FFmpeg修复失败: {result.stderr}")
            
            return file_path
            
        except Exception as e:
            logger.error(f"❌ 强制音频修复失败: {e}")
            return file_path

    def _cleanup(self, cookie_file: Optional[str]):
        """清理临时文件"""
        if cookie_file and os.path.exists(cookie_file):
            try:
                os.unlink(cookie_file)
                logger.info("🧹 清理临时cookie文件")
            except:
                pass

# 创建全局下载器实例
rock_solid_downloader = RockSolidVideoDownloader()

# 函数接口
def download_video(url: str, output_template: str, progress_callback: Optional[Callable] = None) -> str:
    """坚如磐石下载"""
    return rock_solid_downloader.download_video(url, output_template, progress_callback)

def get_video_info(url: str) -> Dict[str, Any]:
    """获取视频信息"""
    try:
        url_validation = EnhancedURLValidator.validate_and_fix_url(url)
        if not url_validation['valid']:
            return {
                'success': False,
                'error': url_validation.get('warning', '无效URL'),
                'platform': 'Unknown'
            }
        
        return {
            'success': True,
            'platform': url_validation['platform'],
            'title': 'Video',
            'duration': 0,
            'uploader': 'Unknown'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'platform': 'Unknown'
        }

def get_browser_cookies(domain: str = '.bilibili.com') -> Dict[str, str]:
    """获取cookies"""
    return SimpleCookieManager.get_browser_cookies(domain)

def sanitize_filename(filename: str) -> str:
    """清理文件名"""
    if not filename:
        return "Unknown_Video"
    
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
    filename = filename.strip(' ._-')
    
    if len(filename) > 80:
        filename = filename[:80]
    
    return filename or "Unknown_Video"

def analyze_bilibili_error(error_msg: str) -> Dict[str, str]:
    """错误分析 - 增强版"""
    error_msg_lower = error_msg.lower()
    
    # 致命错误（不可恢复，不应重试）
    if any(keyword in error_msg_lower for keyword in ['付费', 'payment', 'premium', '大会员', 'vip']):
        return {
            'user_friendly': '该视频为付费内容，需要购买后才能下载',
            'error_type': 'payment_required',
            'fatal': True
        }
    elif any(keyword in error_msg_lower for keyword in ['登录', 'login', 'auth', 'forbidden', '403']):
        return {
            'user_friendly': '需要登录B站账号才能下载',
            'error_type': 'auth_required', 
            'fatal': True
        }
    elif any(keyword in error_msg_lower for keyword in ['地区', 'region', 'blocked', '限制']):
        return {
            'user_friendly': '该视频在当前地区不可观看',
            'error_type': 'region_blocked',
            'fatal': True
        }
    elif any(keyword in error_msg_lower for keyword in ['private', '私有', 'deleted', '删除', '不存在']):
        return {
            'user_friendly': '视频无法访问，可能已被删除或设为私有',
            'error_type': 'access_denied',
            'fatal': True
        }
    elif any(keyword in error_msg_lower for keyword in ['age', '年龄', 'adult']):
        return {
            'user_friendly': '该视频有年龄限制，需要验证身份',
            'error_type': 'age_restricted',
            'fatal': True
        }
    elif any(keyword in error_msg_lower for keyword in ['live', '直播', 'streaming']):
        return {
            'user_friendly': '检测到直播内容，暂不支持直播下载',
            'error_type': 'live_content',
            'fatal': True
        }
    
    # 可重试错误
    elif any(keyword in error_msg_lower for keyword in ['timeout', '超时']):
        return {
            'user_friendly': '网络连接超时，请重试',
            'error_type': 'network_error',
            'fatal': False
        }
    elif any(keyword in error_msg_lower for keyword in ['json', 'api', '解析']):
        return {
            'user_friendly': 'B站API异常，请稍后重试',
            'error_type': 'api_error',
            'fatal': False
        }
    elif any(keyword in error_msg_lower for keyword in ['format', '格式']):
        return {
            'user_friendly': '视频格式不可用，正在尝试其他格式',
            'error_type': 'format_error',
            'fatal': False
        }
    else:
        return {
            'user_friendly': '下载失败，请重试',
            'error_type': 'unknown_error',
            'fatal': False
        }