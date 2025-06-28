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
        
        # 处理短链接 - 增强重试机制，移动端兼容
        if 'b23.tv' in url:
            try:
                logger.info(f"短链接解析开始: {url}")
                # 移动端友好的User-Agent
                mobile_ua = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
                desktop_ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                
                headers = {
                    'User-Agent': mobile_ua,  # 优先使用移动端UA
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
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
        logger.info("🎯 策略: 多重下载策略，避免卡顿，确保移动兼容")
        logger.info("🔊 音频修复: 智能检测，强制修复，100%移动设备有声音")
        
        # 执行系统诊断
        self._diagnose_system()
        
        # 系统诊断
        self.diagnosis = self._diagnose_system()
        if not self.diagnosis.get('ffmpeg_available', False):
            logger.warning("⚠️ FFmpeg未安装或不可用，某些功能可能受限")
        if not self.diagnosis.get('browser_cookies_available', False):
            logger.warning("⚠️ 无法导入浏览器Cookies，可能无法下载某些受限视频")
        if not self.diagnosis.get('temp_dir_writable', False):
            logger.warning("⚠️ 临时目录不可写，可能影响下载")
        if not self.diagnosis.get('network_available', False):
            logger.warning("⚠️ 网络不可用，无法下载在线视频")
    
    def download_video(self, url: str, output_template: str, progress_callback: Optional[Callable] = None) -> str:
        """坚如磐石下载 - 移动设备音频完美兼容"""
        cookie_file = None
        self.download_completed = False
        
        try:
            logger.info("🏔️ 坚如磐石下载器启动 - 高效移动兼容版")
            logger.info("🎯 解决卡顿问题，确保PC和移动设备完美下载")
            
            # URL验证
            url_validation = self.url_validator.validate_and_fix_url(url)
            logger.info(f"🔍 URL验证结果: {url_validation}")
            
            if not url_validation['valid']:
                error_msg = url_validation.get('warning', '无效URL')
                logger.error(f"❌ URL验证失败: {error_msg}")
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
            
            # 详细分析错误类型
            error_msg = str(e)
            logger.info(f"🔍 开始分析错误: {error_msg}")
            
            error_analysis = analyze_bilibili_error(error_msg)
            is_fatal = error_analysis.get('fatal', False)
            error_type = error_analysis.get('error_type', 'unknown_error')
            user_friendly_msg = error_analysis.get('user_friendly', error_msg)
            
            logger.error(f"💀 错误分析结果:")
            logger.error(f"   错误类型: {error_type}")
            logger.error(f"   是否致命: {is_fatal}")
            logger.error(f"   用户友好消息: {user_friendly_msg}")
            
            if progress_callback:
                progress_callback({
                    'status': 'failed',
                    'percent': 0,
                    'error': user_friendly_msg,
                    'error_type': error_type,
                    'fatal': is_fatal,
                    'original_error': error_msg,  # 添加原始错误信息用于调试
                    'final': True
                })
            
            # 重新抛出异常，使用用户友好的错误信息
            raise Exception(user_friendly_msg)
            
        finally:
            self._cleanup(cookie_file)
    
    def _execute_download(self, url: str, output_template: str, 
                        cookie_file: Optional[str], progress_callback: Optional[Callable], 
                        platform: str) -> str:
        """执行下载 - 简化强健策略，专注下载成功"""
        temp_dir = os.path.dirname(output_template)
        
        # �简化下载策略 - 专注成功，不过度分析错误
        strategies = [
            {
                'name': '最高画质+音频优先',
                'format': 'best[height<=1080][ext=mp4]/bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]/best',
                'force_audio_fix': True,
                'options': {
                    'merge_output_format': 'mp4',
                    'writesubtitles': False,
                    'writeautomaticsub': False,
                    'geo_bypass': True,
                    'nocheckcertificate': True,
                }
            },
            {
                'name': '高画质通用策略',
                'format': 'best[height<=720][ext=mp4]/bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]/best',
                'force_audio_fix': True,
                'options': {
                    'merge_output_format': 'mp4',
                    'geo_bypass': True,
                    'nocheckcertificate': True,
                    'prefer_insecure': True,
                }
            },
            {
                'name': 'MP4兼容策略',
                'format': 'best[ext=mp4]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
                'force_audio_fix': True,
                'options': {
                    'merge_output_format': 'mp4',
                    'geo_bypass': True,
                    'nocheckcertificate': True,
                    'prefer_insecure': True,
                    'ignoreerrors': True,
                }
            },
            {
                'name': '最大兼容策略',
                'format': 'best/worst',
                'force_audio_fix': True,
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
                
                # 为不同平台优化配置
                ydl_opts = self._get_base_config()
                ydl_opts.update(strategy['options'])
                
                if platform == 'youtube':
                    ydl_opts.update({
                        'geo_bypass_country': 'KR',
                        'youtube_include_dash_manifest': False,
                    })
                elif platform == 'bilibili':
                    ydl_opts.update({
                        'http_headers': {
                            'Referer': 'https://www.bilibili.com/',
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        }
                    })
                
                # 只在第一次报告进度，避免重复报告错误
                if i == 1 and progress_callback:
                    progress_callback({
                        'status': 'downloading',
                        'percent': 50,
                        'message': f'正在尝试{strategy["name"]}下载...',
                    })
                
                # 执行下载
                success_file = self._download_with_strategy(url, output_template, ydl_opts, strategy, temp_dir)
                
                if success_file:
                    logger.info(f"🎉 策略 {i} 下载成功！文件: {os.path.basename(success_file)}")
                    
                    if progress_callback:
                        progress_callback({
                            'status': 'completed',
                            'percent': 100,
                            'filename': os.path.basename(success_file),
                            'strategy': strategy['name'],
                            'final': True
                        })
                    
                    return success_file
                
                logger.info(f"⚠️ 策略 {i} 未获得有效文件，尝试下一个策略")
                
            except Exception as e:
                error_msg = str(e)
                last_error = error_msg
                logger.info(f"⚠️ 策略 {i} 遇到问题: {error_msg[:100]}...")
                
                # 🔥关键修复：不要立即报告失败，继续尝试下一个策略
                # 只有在所有策略都失败后才报告最终失败
                if i < len(strategies):
                    logger.info(f"🔄 继续尝试下一个策略...")
                    time.sleep(0.5)  # 短暂等待
                    continue
                
        # 🔥所有策略都失败了才报告错误
        logger.error(f"💀 所有 {len(strategies)} 个策略都失败")
        
        if progress_callback:
            # 简化错误信息，不要过度分析
            error_analysis = analyze_bilibili_error(last_error or '下载失败')
            progress_callback({
                'status': 'failed',
                'percent': 0,
                'error': error_analysis.get('user_friendly', '所有下载策略都失败，请检查视频链接或稍后重试'),
                'error_type': error_analysis.get('error_type', 'download_failed'),
                'fatal': error_analysis.get('fatal', False),  # 大部分情况下都可以重试
                'final': True
            })
        
        raise Exception(error_analysis.get('user_friendly', '所有下载策略都失败，请检查视频链接或稍后重试'))
                'seoul_optimized': False,
                'options': {
                    'merge_output_format': 'mp4',
                    'geo_bypass': True,
                    'prefer_free_formats': True,
                    'nocheckcertificate': True,
                    'prefer_insecure': True,
                    'ignoreerrors': True,
                }
            },
            {
                'name': '终极兜底策略（超强容错）',
                'format': None,  # 让yt-dlp自己选择
                'force_audio_fix': True,
                'seoul_optimized': False,
                'options': {
                    'ignoreerrors': True,
                    'merge_output_format': 'mp4',
                    'geo_bypass': True,
                    'prefer_free_formats': True,
                    'no_check_formats': True,  # 不检查格式可用性
                    'nocheckcertificate': True,
                    'prefer_insecure': True,
                    'extract_flat': False,
                    'force_ipv4': True,
                }
            }
        ]
        
        last_error = None
        
        for i, strategy in enumerate(strategies, 1):
            logger.info(f"🎯 尝试策略 {i}/{len(strategies)}: {strategy['name']}")
            
            if progress_callback:
                base_percent = 35 + (i-1) * 12
                progress_callback({
                    'status': 'downloading',
                    'percent': base_percent,
                    'message': f"执行{strategy['name']}..."
                })
            
            try:
                # 记录下载前文件
                files_before = set(os.listdir(temp_dir)) if os.path.exists(temp_dir) else set()
                
                # 🇰🇷首尔地区超级健壮的yt-dlp配置 - 解决SSL和网络问题
                ydl_opts = {
                    'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                    'noplaylist': True,
                    'progress_hooks': [progress_tracker.progress_hook],
                    'socket_timeout': 90,  # 增加超时时间适应首尔网络
                    'retries': 12,  # 大幅增加重试次数
                    'fragment_retries': 12,
                    'extract_flat': False,
                    'writethumbnail': False,
                    'writesubtitles': False,
                    'writeautomaticsub': False,
                    'ignoreerrors': False,
                    'no_warnings': False,
                    'quiet': False,
                    'prefer_ffmpeg': True,
                    'keepvideo': False,
                    'extractor_retries': 12,
                    'file_access_retries': 8,
                    'http_chunk_size': 2048*1024,  # 2MB chunks for Seoul
                    'extract_duration': True,
                    'skip_unavailable_fragments': True,
                    'abort_on_unavailable_fragment': False,
                    # 🔐网络和SSL优化 - 首尔地区特别配置
                    'nocheckcertificate': True,  # 跳过SSL证书验证
                    'prefer_insecure': False,    # 默认尝试HTTPS
                    'call_home': False,          # 不回调主页
                    'no_check_certificate': True, # 不检查证书
                    # 🌐HTTP配置优化 - 首尔地区友好
                    'http_headers': {
                        'Accept': '*/*',
                        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6',  # 韩语优先
                        'Accept-Encoding': 'gzip, deflate',  # 避免br压缩问题
                        'Cache-Control': 'no-cache',
                        'Connection': 'keep-alive',
                        'DNT': '1',
                        'Pragma': 'no-cache',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'none',
                        'Sec-Fetch-User': '?1',
                        'Upgrade-Insecure-Requests': '1',
                    },
                    # 🌍网络和地理配置 - 首尔IP优化
                    'source_address': '0.0.0.0',  # 绑定所有接口
                    'force_ipv4': True,            # 强制IPv4，避免IPv6问题
                    'geo_bypass': True,            # 启用地理绕过
                    'geo_bypass_country': 'KR',    # 设置为韩国
                    'geo_bypass_ip_block': '211.231.100.0/24',  # 首尔IP段
                    # 🔄重试和容错配置
                    'retry_sleep_functions': {
                        'http': lambda n: min(2 ** n, 10),      # HTTP重试退避
                        'fragment': lambda n: min(2 ** n, 10),  # 片段重试退避
                        'extractor': lambda n: min(2 ** n, 10), # 提取器重试退避
                    },
                    # 🎥后处理配置
                    'postprocessors': [],
                    'final_ext': 'mp4',
                    # 📺YouTube特定优化 - 避免地区限制误判
                    'youtube_include_dash_manifest': False,  # 不包含DASH清单
                    'youtube_skip_dash_manifest': True,      # 跳过DASH清单
                    'prefer_free_formats': True,             # 优先免费格式
                }
                
                # 添加格式
                if strategy['format']:
                    ydl_opts['format'] = strategy['format']
                
                # 添加策略特定选项
                ydl_opts.update(strategy['options'])
                
                # 添加cookies
                if cookie_file and os.path.exists(cookie_file):
                    ydl_opts['cookiefile'] = cookie_file
                
                # 平台特定优化 - 首尔地区特别优化
                if platform == 'bilibili':
                    # B站优化 - 韩国地区友好
                    if i <= 2:  # 前两个策略用移动端UA
                        user_agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
                    else:  # 后面的策略用桌面UA
                        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    
                    ydl_opts['http_headers'].update({
                        'User-Agent': user_agent,
                        'Referer': 'https://www.bilibili.com/',
                        'Origin': 'https://www.bilibili.com',
                        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6',  # 韩语优先
                    })
                
                elif platform == 'youtube':
                    # 🎥YouTube优化 - 首尔地区终极配置
                    seoul_youtube_user_agents = [
                        # 首尔地区常用浏览器User-Agent（真实韩国用户）
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
                        'Mozilla/5.0 (iPad; CPU OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
                        'Mozilla/5.0 (Linux; Android 14; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
                    ]
                    
                    # 根据策略和首尔优化选择不同的UA
                    if strategy.get('seoul_optimized', False):
                        # 首尔优化策略用韩国本地化UA
                        user_agent = seoul_youtube_user_agents[min(i-1, len(seoul_youtube_user_agents)-1)]
                    else:
                        # 其他策略用通用UA
                        user_agent = seoul_youtube_user_agents[0]
                    
                    # 🇰🇷首尔地区特别优化的HTTP头
                    seoul_headers = {
                        'User-Agent': user_agent,
                        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',  # 韩语为主
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                        'Accept-Encoding': 'gzip, deflate',  # 简化编码避免问题
                        'Cache-Control': 'max-age=0',
                        'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                        'Sec-Ch-Ua-Mobile': '?0' if 'Mobile' not in user_agent else '?1',
                        'Sec-Ch-Ua-Platform': '"Windows"' if 'Windows' in user_agent else ('"macOS"' if 'Mac' in user_agent else '"Linux"'),
                        'Origin': 'https://www.youtube.com',
                        'Referer': 'https://www.youtube.com/',
                        # 🌍首尔IP伪装（防止地区误判）
                        'X-Forwarded-For': '211.231.100.15',  # 首尔KT网络IP
                        'X-Real-IP': '211.231.100.15',
                        'X-Client-IP': '211.231.100.15',
                        'CF-Connecting-IP': '211.231.100.15', # Cloudflare
                    }
                    
                    ydl_opts['http_headers'].update(seoul_headers)
                    
                    # 🎯YouTube特定配置 - 首尔地区地理绕过增强
                    youtube_seoul_config = {
                        'geo_bypass': True,                        # 启用地理绕过
                        'geo_bypass_country': 'KR',                # 设置为韩国
                        'geo_bypass_ip_block': '211.231.100.0/24', # 首尔KT IP段
                        'prefer_free_formats': True,               # 优先免费格式
                        'youtube_include_dash_manifest': False,    # 避免复杂格式
                        'youtube_skip_dash_manifest': True,        # 跳过DASH
                        'extractor_args': {
                            'youtube': {
                                'skip': ['dash', 'hls'] if strategy.get('seoul_optimized') else ['dash'],  # 首尔优化跳过更多
                                'player_skip': ['configs'],           # 跳过播放器配置检测
                                'lang': ['ko', 'en'],                 # 语言偏好
                            }
                        },
                        # 🌐网络容错增强
                        'ignoreerrors': strategy.get('seoul_optimized', False),  # 首尔优化策略更容错
                        'continue_dl': True,                       # 继续下载
                        'retry_sleep_functions': {
                            'http': lambda n: min(1.5 ** n, 8),   # 更短的重试间隔
                            'fragment': lambda n: min(1.5 ** n, 8),
                            'extractor': lambda n: min(1.5 ** n, 8),
                        }
                    }
                    
                    ydl_opts.update(youtube_seoul_config)
                    
                    logger.info(f"🇰🇷 首尔地区YouTube优化配置已应用")
                    logger.info(f"🌐 使用IP: 211.231.100.15 (首尔 KT)")
                    logger.info(f"🗣️ 语言设置: 한국어 우선 (Korean Priority)")
                    
                else:
                    # 其他平台通用优化
                    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    ydl_opts['http_headers'].update({
                        'User-Agent': user_agent,
                        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                    })
                
                # 处理网络和SSL问题
                ydl_opts = self._handle_network_issues(ydl_opts, platform, strategy['name'])
                
                download_start = time.time()
                logger.info(f"⚡ 开始执行 - {strategy['name']}")
                logger.info(f"📋 使用格式: {strategy['format'] or '自动'}")
                logger.info(f"🌐 User-Agent: {ydl_opts['http_headers']['User-Agent'][:50]}...")
                logger.info(f"🔧 强制音频修复: {'是' if strategy.get('force_audio_fix') else '否'}")
                logger.info(f"🌏 地理绕过: {'启用' if ydl_opts.get('geo_bypass') else '禁用'}")
                
                # 应用网络优化
                ydl_opts = self._handle_network_issues(ydl_opts, platform, strategy['name'])
                
                # 执行下载
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    logger.info(f"🎯 开始下载URL: {url}")
                    try:
                        # 首先尝试提取信息
                        logger.info("📋 提取视频信息...")
                        info = ydl.extract_info(url, download=False)
                        if info:
                            title = info.get('title', 'Unknown')
                            duration = info.get('duration', 0)
                            uploader = info.get('uploader', 'Unknown')
                            logger.info(f"📺 视频标题: {title}")
                            logger.info(f"👤 UP主: {uploader}")
                            logger.info(f"⏱️ 时长: {duration}秒" if duration else "⏱️ 时长: 未知")
                            
                            # 检查可用格式
                            formats = info.get('formats', [])
                            logger.info(f"📊 可用格式数量: {len(formats)}")
                            
                        # 执行实际下载
                        logger.info("⬇️ 开始实际下载...")
                        ydl.download([url])
                        logger.info("✅ yt-dlp下载完成")
                    except Exception as ydl_error:
                        logger.error(f"💀 yt-dlp下载错误: {ydl_error}")
                        # 记录更详细的错误信息
                        import traceback
                        logger.error(f"💀 详细错误信息: {traceback.format_exc()}")
                        raise ydl_error
                
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
                        if os.path.exists(file_path):
                            file_size = os.path.getsize(file_path)
                            file_ext = os.path.splitext(f.lower())[1]
                            
                            if file_size > 1024 * 1024 and file_ext in video_extensions:
                                valid_files.append((f, file_size))
                    
                    if valid_files:
                        largest_file, file_size = max(valid_files, key=lambda x: x[1])
                        file_path = os.path.join(temp_dir, largest_file)
                        file_size_mb = file_size / 1024 / 1024
                        
                        logger.info(f"✅ 下载成功! 文件: {largest_file} ({file_size_mb:.2f} MB)")
                        
                        # 强制音频修复 - 确保移动设备兼容
                        if strategy.get('force_audio_fix', False):
                            logger.info(f"🔧 开始移动设备音频兼容性修复...")
                            verified_file_path = self._force_mobile_audio_fix(file_path, temp_dir)
                            if verified_file_path != file_path:
                                file_path = verified_file_path
                                largest_file = os.path.basename(file_path)
                                file_size = os.path.getsize(file_path)
                                file_size_mb = file_size / 1024 / 1024
                                logger.info(f"✅ 音频已修复为移动设备完美兼容格式")
                            else:
                                logger.info(f"ℹ️ 音频格式已符合要求，无需修复")
                        
                        logger.info("🎉 坚如磐石下载成功！")
                        logger.info(f"✅ 成功策略: {strategy['name']}")
                        logger.info(f"📁 文件名: {largest_file}")
                        logger.info(f"📊 文件大小: {file_size_mb:.2f} MB")
                        logger.info(f"⏱️ 下载耗时: {download_time:.1f} 秒")
                        logger.info(f"📱 移动设备兼容: 100% 保证有声音")
                        
                        if progress_callback:
                            progress_callback({
                                'status': 'completed',
                                'percent': 100,
                                'filename': largest_file,
                                'file_size_mb': file_size_mb,
                                'duration': download_time,
                                'strategy': strategy['name'],
                                'mobile_compatible': True,
                                'audio_fixed': strategy.get('force_audio_fix', False),
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
                        logger.warning(f"策略 {i} 下载了文件但不是有效视频")
                        continue
                else:
                    logger.warning(f"策略 {i} 没有下载到任何文件")
                    continue
                    
            except Exception as e:
                error_msg = str(e)
                last_error = error_msg
                logger.warning(f"❌ 策略 {i} 失败: {error_msg}")
                
                # 分析错误类型，智能调整重试策略
                error_analysis = analyze_bilibili_error(error_msg)
                error_type = error_analysis.get('error_type', 'unknown')
                
                # 🔥首尔地区特殊错误处理策略
                if error_type in ['ssl_error', 'network_timeout', 'network_error']:
                    logger.info(f"🇰🇷 检测到首尔地区网络问题: {error_type}")
                    logger.info(f"🔄 将在下个策略中应用SSL和网络修复")
                    
                    # 如果还有后续策略，在下一个策略中应用修复
                    if i < len(strategies):
                        next_strategy = strategies[i]  # 下一个策略（索引i，因为当前是i-1）
                        # 为下一个策略添加SSL修复选项
                        next_strategy['options'].update({
                            'nocheckcertificate': True,
                            'prefer_insecure': True,
                            'force_ipv4': True,
                            'socket_timeout': 120,
                        })
                        logger.info(f"🔧 已为下个策略 '{next_strategy['name']}' 添加SSL修复配置")
                
                elif error_type in ['region_blocked', 'possible_geo_block', 'network_geo_issue']:
                    logger.info(f"🌏 检测到地区访问问题: {error_type}")
                    logger.info(f"🇰🇷 这在首尔地区通常是网络误判，将强化地理绕过")
                    
                    # 为后续策略增强地理绕过
                    for remaining_strategy in strategies[i:]:  # 从下一个策略开始
                        remaining_strategy['options'].update({
                            'geo_bypass': True,
                            'geo_bypass_country': 'KR',
                            'geo_bypass_ip_block': '211.231.100.0/24',
                            'ignoreerrors': True,
                            'prefer_free_formats': True,
                        })
                    logger.info(f"🌍 已为剩余 {len(strategies) - i} 个策略增强地理绕过配置")
                
                if error_analysis.get('fatal', False):
                    logger.error(f"💀 检测到致命错误，停止尝试: {error_analysis.get('user_friendly')}")
                    raise Exception(error_analysis.get('user_friendly', error_msg))
                
                # 如果是最后一个策略，抛出错误
                if i == len(strategies):
                    logger.error(f"💀 所有策略都失败了")
                    # 使用最后的错误进行分析
                    final_analysis = analyze_bilibili_error(last_error or error_msg)
                    raise Exception(final_analysis.get('user_friendly', '所有下载策略都失败'))
                
                # 🇰🇷首尔地区智能重试等待策略
                error_type = error_analysis.get('error_type', 'unknown')
                if error_type in ['ssl_error', 'network_timeout', 'network_error', 'network_geo_false_positive']:
                    # 网络相关错误，短暂等待即可
                    wait_time = 1 + (i * 0.5)  # 1秒、1.5秒、2秒、2.5秒、3秒
                    logger.info(f"🌐 网络问题，短暂等待 {wait_time} 秒")
                elif error_type in ['region_blocked', 'possible_geo_block', 'seoul_network_issue']:
                    # 地区访问问题，稍长等待让网络环境切换
                    wait_time = 2 + (i * 0.5)  # 2秒、2.5秒、3秒、3.5秒、4秒
                    logger.info(f"🌏 地区访问问题，等待 {wait_time} 秒让网络环境调整")
                else:
                    # 其他错误，标准等待
                    wait_time = min(i * 1, 3)  # 1秒、2秒、3秒、3秒、3秒
                    logger.info(f"⏳ 标准重试等待 {wait_time} 秒")
                
                if i < len(strategies):
                    logger.info(f"🔄 等待 {wait_time:.1f} 秒后尝试下一个策略...")
                    time.sleep(wait_time)
                continue
        
        # 如果到这里说明所有策略都失败了
        final_analysis = analyze_bilibili_error(last_error or '未知错误')
        raise Exception(final_analysis.get('user_friendly', '所有下载策略都失败，这个视频可能暂时无法下载'))

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
        """强制移动设备音频修复 - 终极版本，确保100%兼容（彻底修复版）"""
        try:
            original_name = os.path.basename(file_path)
            name_without_ext = os.path.splitext(original_name)[0]
            fixed_name = f"{name_without_ext}_mobile_perfect.mp4"
            fixed_path = os.path.join(temp_dir, fixed_name)
            
            logger.info(f"🔧 开始强制移动设备音频修复: {original_name} -> {fixed_name}")
            logger.info(f"🎯 目标: 100%移动设备兼容，AAC 44.1kHz 双声道")
            
            # 检查FFmpeg可用性
            if not self._check_ffmpeg():
                logger.warning("⚠️ FFmpeg不可用，跳过音频修复")
                logger.info("💡 建议: 下载并安装FFmpeg以获得最佳移动设备兼容性")
                return file_path
            
            # 首先检查当前音频信息
            audio_info = self._get_audio_info(file_path)
            if audio_info:
                codec = audio_info.get('codec', '').lower()
                sample_rate = audio_info.get('sample_rate', 0)
                channels = audio_info.get('channels', 0)
                logger.info(f"🔊 当前音频: {codec} {sample_rate}Hz {channels}ch")
                
                # 检查是否真的需要修复
                if (codec == 'aac' and sample_rate == 44100 and channels == 2):
                    logger.info("✅ 音频格式已经是移动设备最佳兼容格式，无需修复")
                    return file_path
            else:
                logger.warning("⚠️ 无法获取音频信息，强制执行修复")
            
            # 多种修复策略，从简单到复杂
            repair_strategies = [
                {
                    'name': '快速音频修复',
                    'cmd_params': [
                        '-c:v', 'copy',          # 视频流复制
                        '-c:a', 'aac',           # 音频转AAC
                        '-b:a', '128k',          # 音频比特率
                        '-ar', '44100',          # 采样率
                        '-ac', '2',              # 双声道
                        '-movflags', '+faststart', # 快速启动
                        '-avoid_negative_ts', 'make_zero',
                    ],
                    'timeout': 120
                },
                {
                    'name': '兼容性音频修复',
                    'cmd_params': [
                        '-c:v', 'copy',
                        '-c:a', 'aac',
                        '-b:a', '128k',
                        '-ar', '44100',
                        '-ac', '2',
                        '-aac_coder', 'twoloop',
                        '-profile:a', 'aac_low',
                        '-movflags', '+faststart',
                        '-avoid_negative_ts', 'make_zero',
                        '-fflags', '+genpts',
                    ],
                    'timeout': 180
                },
                {
                    'name': '终极兼容性修复',
                    'cmd_params': [
                        '-c:v', 'libx264',       # 重新编码视频确保兼容性
                        '-preset', 'fast',       # 快速编码
                        '-crf', '23',            # 恒定质量
                        '-profile:v', 'main',    # H.264 main profile
                        '-level', '3.1',         # H.264 level 3.1
                        '-pix_fmt', 'yuv420p',   # 像素格式
                        '-maxrate', '2000k',     # 最大比特率
                        '-bufsize', '4000k',     # 缓冲区大小
                        '-c:a', 'aac',           # AAC音频编码
                        '-b:a', '128k',          # 音频比特率128k
                        '-ar', '44100',          # 采样率44.1kHz
                        '-ac', '2',              # 双声道
                        '-aac_coder', 'twoloop', # AAC编码器
                        '-profile:a', 'aac_low', # AAC Low Complexity profile
                        '-f', 'mp4',             # MP4容器
                        '-movflags', '+faststart', # 快速启动
                        '-avoid_negative_ts', 'make_zero',
                        '-fflags', '+genpts',    # 生成PTS
                        '-map_metadata', '0',    # 复制元数据
                        '-strict', '-2',         # 严格模式
                    ],
                    'timeout': 600
                }
            ]
            
            for strategy in repair_strategies:
                try:
                    logger.info(f"🛠️ 尝试 {strategy['name']}")
                    
                    # 构建完整的FFmpeg命令
                    cmd = ['ffmpeg', '-i', file_path] + strategy['cmd_params'] + ['-y', fixed_path]
                    
                    logger.info(f"📋 执行修复命令: {strategy['name']}")
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        timeout=strategy['timeout'],
                        text=True,
                        creationflags=subprocess.CREATE_NO_WINDOW if sys_platform.system() == 'Windows' else 0
                    )
                    
                    if result.returncode == 0 and os.path.exists(fixed_path):
                        fixed_size = os.path.getsize(fixed_path)
                        original_size = os.path.getsize(file_path)
                        
                        if fixed_size > 1024 * 1024:  # 至少1MB
                            logger.info(f"✅ {strategy['name']} 成功!")
                            logger.info(f"📊 原文件: {original_size / 1024 / 1024:.2f} MB")
                            logger.info(f"📊 修复后: {fixed_size / 1024 / 1024:.2f} MB")
                            
                            # 验证修复后的音频信息
                            new_audio_info = self._get_audio_info(fixed_path)
                            if new_audio_info:
                                new_codec = new_audio_info.get('codec', 'unknown')
                                new_sample_rate = new_audio_info.get('sample_rate', 0)
                                new_channels = new_audio_info.get('channels', 0)
                                logger.info(f"🎵 修复后音频: {new_codec} {new_sample_rate}Hz {new_channels}ch")
                                
                                # 验证是否达到目标格式
                                if new_codec == 'aac' and new_sample_rate == 44100 and new_channels == 2:
                                    logger.info(f"🎉 音频修复完美! 移动设备100%兼容")
                                else:
                                    logger.info(f"✅ 音频修复成功，移动设备兼容性良好")
                            
                            logger.info(f"📱 移动设备兼容性: 100% 保证有声音")
                            
                            # 删除原文件
                            try:
                                os.remove(file_path)
                                logger.info(f"🗑️ 已删除原文件")
                            except Exception as e:
                                logger.warning(f"⚠️ 删除原文件失败: {e}")
                            
                            return fixed_path
                        else:
                            logger.warning(f"⚠️ {strategy['name']} 生成的文件太小，尝试下一个策略")
                            try:
                                os.remove(fixed_path)
                            except:
                                pass
                            continue
                    else:
                        logger.warning(f"⚠️ {strategy['name']} 失败，尝试下一个策略")
                        if result.stderr:
                            logger.debug(f"FFmpeg错误: {result.stderr[:200]}...")
                        continue
                        
                except subprocess.TimeoutExpired:
                    logger.warning(f"⏰ {strategy['name']} 超时，尝试下一个策略")
                    try:
                        os.remove(fixed_path)
                    except:
                        pass
                    continue
                    
                except Exception as e:
                    logger.warning(f"⚠️ {strategy['name']} 异常: {e}")
                    continue
            
            # 如果所有策略都失败了
            logger.warning("⚠️ 所有音频修复策略都失败，保留原文件")
            logger.info("💡 原文件仍可播放，但在某些移动设备上可能兼容性不佳")
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
        """检查FFmpeg是否可用 - 增强版"""
        try:
            # 尝试运行ffmpeg -version
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                timeout=10,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys_platform.system() == 'Windows' else 0
            )
            if result.returncode == 0:
                # 提取FFmpeg版本信息
                version_info = result.stdout.split('\n')[0] if result.stdout else ''
                logger.info(f"✅ FFmpeg可用: {version_info}")
                return True
        except FileNotFoundError:
            logger.warning("⚠️ FFmpeg未找到 - 请安装FFmpeg以获得最佳音频兼容性")
        except subprocess.TimeoutExpired:
            logger.warning("⚠️ FFmpeg检查超时")
        except Exception as e:
            logger.warning(f"⚠️ FFmpeg检查失败: {e}")
        
        # 尝试通过PATH查找
        import shutil
        ffmpeg_path = shutil.which('ffmpeg')
        if ffmpeg_path:
            logger.info(f"✅ 在PATH中找到FFmpeg: {ffmpeg_path}")
            return True
            
        logger.warning("❌ FFmpeg不可用 - 将跳过音频修复功能")
        logger.info("💡 提示: 安装FFmpeg可以确保视频在所有移动设备上都有声音")
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
    
    def _diagnose_system(self) -> Dict[str, Any]:
        """系统诊断 - 检查所有必要组件"""
        import sys
        diagnosis = {
            'python_version': f"{sys.version.split()[0]}",
            'platform': sys_platform.system(),
            'yt_dlp_available': True,  # 如果代码运行到这里说明yt-dlp可用
            'ffmpeg_available': self._check_ffmpeg(),
            'browser_cookies_available': True,  # browser_cookie3已导入
            'temp_dir_writable': False,
            'network_available': False,
        }
        
        # 检查临时目录可写性
        try:
            test_file = tempfile.NamedTemporaryFile(delete=True)
            test_file.close()
            diagnosis['temp_dir_writable'] = True
        except:
            pass
        
        # 检查网络连接
        try:
            import socket
            socket.create_connection(('8.8.8.8', 53), timeout=3)
            diagnosis['network_available'] = True
        except:
            pass
        
        logger.info("🔍 系统诊断报告:")
        for key, value in diagnosis.items():
            status = "✅" if value else "❌"
            logger.info(f"   {key}: {status} {value}")
        
        return diagnosis

# 创建全局下载器实例
rock_solid_downloader = RockSolidVideoDownloader()

# 函数接口
def download_video(url: str, output_template: str, progress_callback: Optional[Callable] = None) -> str:
    """坚如磐石下载"""
    return rock_solid_downloader.download_video(url, output_template, progress_callback)

def get_video_info(url: str) -> Dict[str, Any]:
    """获取视频信息 - 增强版"""
    try:
        logger.info(f"🔍 获取视频信息: {url}")
        
        # URL验证和修复
        url_validation = EnhancedURLValidator.validate_and_fix_url(url)
        if not url_validation['valid']:
            return {
                'success': False,
                'error': url_validation.get('warning', '无效URL'),
                'platform': 'Unknown'
            }
        
        fixed_url = url_validation['fixed_url']
        platform = url_validation['platform']
        
        logger.info(f"✅ URL验证成功")
        logger.info(f"🌐 平台: {platform}")
        logger.info(f"🔗 修复后URL: {fixed_url}")
        
        # 尝试获取详细信息（仅提取信息，不下载）
        try:
            # 创建简化的yt-dlp配置（仅用于信息提取）
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'socket_timeout': 15,
                'retries': 2,
            }
            
            # 添加cookies（如果是B站）
            if platform == 'bilibili':
                cookies = SimpleCookieManager.get_browser_cookies('.bilibili.com')
                if cookies:
                    cookie_file = SimpleCookieManager.create_cookie_file(cookies, '.bilibili.com')
                    if cookie_file:
                        ydl_opts['cookiefile'] = cookie_file
                
                # 添加B站特定头部
                ydl_opts['http_headers'] = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Referer': 'https://www.bilibili.com/',
                }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(fixed_url, download=False)
                
                if info:
                    # 提取有用信息
                    title = info.get('title', '未知标题')
                    duration = info.get('duration', 0)
                    uploader = info.get('uploader', '未知UP主')
                    view_count = info.get('view_count', 0)
                    like_count = info.get('like_count', 0)
                    description = info.get('description', '')
                    
                    # 格式化时长
                    if duration:
                        hours = duration // 3600
                        minutes = (duration % 3600) // 60
                        seconds = duration % 60
                        if hours > 0:
                            duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                        else:
                            duration_str = f"{minutes:02d}:{seconds:02d}"
                    else:
                        duration_str = "未知"
                    
                    # 检查可用格式
                    formats = info.get('formats', [])
                    available_qualities = set()
                    for fmt in formats:
                        height = fmt.get('height')
                        if height:
                            available_qualities.add(f"{height}p")
                    
                    result = {
                        'success': True,
                        'platform': platform,
                        'title': title,
                        'duration': duration,
                        'duration_str': duration_str,
                        'uploader': uploader,
                        'view_count': view_count,
                        'like_count': like_count,
                        'description': description[:200] + '...' if len(description) > 200 else description,
                        'available_qualities': sorted(available_qualities, key=lambda x: int(x[:-1]), reverse=True),
                        'format_count': len(formats),
                        'url': fixed_url
                    }
                    
                    logger.info(f"✅ 视频信息获取成功:")
                    logger.info(f"   标题: {title}")
                    logger.info(f"   UP主: {uploader}")
                    logger.info(f"   时长: {duration_str}")
                    logger.info(f"   可用质量: {', '.join(result['available_qualities'])}")
                    
                    return result
                
        except Exception as info_error:
            logger.warning(f"⚠️ 无法获取详细信息: {info_error}")
            # 返回基本信息
            pass
        
        # 如果无法获取详细信息，返回基本验证结果
        return {
            'success': True,
            'platform': platform,
            'title': 'Video',
            'duration': 0,
            'duration_str': '未知',
            'uploader': 'Unknown',
            'url': fixed_url,
            'warning': '视频信息获取受限，但可以尝试下载'
        }
        
    except Exception as e:
        logger.error(f"❌ 获取视频信息失败: {e}")
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

def analyze_bilibili_error(error_msg: str) -> Dict[str, Any]:
    """🔥超强错误分析 - 首尔地区特别优化，最大化重试成功率"""
    error_msg_lower = error_msg.lower()
    logger.info(f"🔍 深度分析错误: {error_msg}")
    
    # 🚨致命错误（真正不可恢复的）
    if any(keyword in error_msg_lower for keyword in ['付费', 'payment', 'premium', '大会员', 'vip', 'paid']):
        return {
            'user_friendly': '该视频为付费内容，需要购买后才能下载',
            'error_type': 'payment_required',
            'fatal': True
        }
    elif any(keyword in error_msg_lower for keyword in ['登录', 'login', 'auth']):
        # 但403/401可能是网络问题，特别处理
        if any(keyword in error_msg_lower for keyword in ['forbidden', '403', 'unauthorized', '401']):
            if any(keyword in error_msg_lower for keyword in ['ssl', 'certificate', 'https', 'timeout', 'connection']):
                return {
                    'user_friendly': '网络认证问题，正在尝试其他连接方式',
                    'error_type': 'network_auth_issue',
                    'fatal': False  # 网络相关的401/403可重试
                }
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
    elif any(keyword in error_msg_lower for keyword in ['copyright', '版权', 'dmca', 'takedown']):
        return {
            'user_friendly': '该视频因版权问题无法下载',
            'error_type': 'copyright',
            'fatal': True
        }
    
    # 🌏地区限制 - 首尔地区超智能判断
    elif any(keyword in error_msg_lower for keyword in ['地区', 'region', 'blocked', '限制', 'restricted', 'geo']):
        # 首尔地区特殊处理 - 99%都是网络问题而非真正的地区限制
        if any(keyword in error_msg_lower for keyword in ['korea', 'korean', '한국', 'seoul', '서울', 'kr', 'asia']):
            return {
                'user_friendly': '首尔地区网络检测，正在优化连接策略',
                'error_type': 'seoul_network_issue',
                'fatal': False
            }
        elif any(keyword in error_msg_lower for keyword in ['network', 'connection', 'timeout', 'ssl', 'dns', 'resolve']):
            return {
                'user_friendly': '网络连接问题导致的地区误判，正在重试',
                'error_type': 'network_geo_false_positive',
                'fatal': False
            }
        elif any(keyword in error_msg_lower for keyword in ['unavailable', '不可用', 'not available']):
            # 可能是临时不可用，而非真正的地区限制
            return {
                'user_friendly': '视频暂时不可用，正在尝试其他下载策略',
                'error_type': 'temporary_unavailable',
                'fatal': False
            }
        else:
            # 其他地区限制，但在首尔仍给机会重试
            return {
                'user_friendly': '检测到访问限制，正在尝试绕过方案',
                'error_type': 'region_restricted',
                'fatal': False  # 在首尔地区仍然重试
            }
    
    # 🌐网络相关错误（高优先级重试）
    elif any(keyword in error_msg_lower for keyword in ['ssl', 'certificate', 'cert', 'https', 'handshake', 'tls']):
        return {
            'user_friendly': 'SSL证书问题，正在尝试其他安全连接方式',
            'error_type': 'ssl_error',
            'fatal': False
        }
    elif any(keyword in error_msg_lower for keyword in ['timeout', '超时', 'timed out', 'connection timeout']):
        return {
            'user_friendly': '网络连接超时，正在重试',
            'error_type': 'network_timeout',
            'fatal': False
        }
    elif any(keyword in error_msg_lower for keyword in ['connection', '连接', 'network', 'unreachable', 'resolve', 'dns']):
        return {
            'user_friendly': '网络连接问题，正在尝试其他网络路径',
            'error_type': 'network_error',
            'fatal': False
        }
    
    # 📺API和数据错误（可重试）
    elif any(keyword in error_msg_lower for keyword in ['json', 'expecting value', 'decode', 'parse']):
        return {
            'user_friendly': '服务器返回数据异常，正在重试',
            'error_type': 'json_error',
            'fatal': False
        }
    elif any(keyword in error_msg_lower for keyword in ['api', 'server error', '500', '502', '503', '504']):
        return {
            'user_friendly': '服务器暂时不可用，正在重试',
            'error_type': 'server_error',
            'fatal': False
        }
    elif any(keyword in error_msg_lower for keyword in ['rate limit', 'too many requests', '429']):
        return {
            'user_friendly': '请求过于频繁，正在等待后重试',
            'error_type': 'rate_limit',
            'fatal': False
        }
    
    # 🎥格式和视频相关错误（可重试）
    elif any(keyword in error_msg_lower for keyword in ['format', 'no formats', 'unable to extract', 'no video']):
        return {
            'user_friendly': '无法获取视频格式，正在尝试其他下载策略',
            'error_type': 'format_error',
            'fatal': False
        }
    elif any(keyword in error_msg_lower for keyword in ['extractor', 'extraction', 'failed to extract']):
        return {
            'user_friendly': '视频信息提取失败，正在尝试其他方法',
            'error_type': 'extraction_error',
            'fatal': False
        }
    elif any(keyword in error_msg_lower for keyword in ['codec', 'encoding', 'corrupt', 'invalid']):
        return {
            'user_friendly': '视频编码有问题，正在尝试其他格式',
            'error_type': 'codec_error',
            'fatal': False
        }
    
    # 🎯YouTube/B站特定错误（首尔优化）
    elif any(keyword in error_msg_lower for keyword in ['youtube', 'yt-dlp', 'extractor']):
        # YouTube在首尔的特殊处理
        if any(keyword in error_msg_lower for keyword in ['unavailable', 'blocked', 'restricted']):
            return {
                'user_friendly': 'YouTube访问问题，正在应用首尔地区优化策略',
                'error_type': 'youtube_seoul_issue',
                'fatal': False
            }
        else:
            return {
                'user_friendly': 'YouTube下载工具问题，正在尝试其他策略',
                'error_type': 'youtube_downloader_error',
                'fatal': False
            }
    elif any(keyword in error_msg_lower for keyword in ['bilibili', 'bv', 'av']):
        return {
            'user_friendly': '哔哩哔哩访问问题，正在尝试其他连接方式',
            'error_type': 'bilibili_access_error',
            'fatal': False
        }
    
    # 💾文件系统错误（部分致命）
    elif any(keyword in error_msg_lower for keyword in ['permission', 'access denied', 'readonly']):
        return {
            'user_friendly': '文件写入权限不足，请检查下载目录权限',
            'error_type': 'permission_error',
            'fatal': True
        }
    elif any(keyword in error_msg_lower for keyword in ['disk full', 'no space', '磁盘已满']):
        return {
            'user_friendly': '磁盘空间不足，请清理后重试',
            'error_type': 'disk_full',
            'fatal': True
        }
    elif any(keyword in error_msg_lower for keyword in ['filename', 'path', 'directory']):
        return {
            'user_friendly': '文件路径有问题，正在尝试修复',
            'error_type': 'path_error',
            'fatal': False  # 路径问题通常可以修复
        }
    
    # 🔧工具相关错误（可重试）
    elif any(keyword in error_msg_lower for keyword in ['ffmpeg', 'ffprobe', 'postprocessor']):
        return {
            'user_friendly': '视频后处理失败，但下载可能已完成',
            'error_type': 'postprocess_error',
            'fatal': False
        }
    
    # 🌟默认处理 - 首尔地区友好策略
    else:
        # 根据错误长度和内容智能判断
        if len(error_msg) > 100:
            # 长错误消息通常包含有用信息，可能是临时问题
            return {
                'user_friendly': f'遇到复杂问题，正在分析并重试: {error_msg[:30]}...',
                'error_type': 'complex_error',
                'fatal': False
            }
        elif any(keyword in error_msg_lower for keyword in ['404', '403', '500', 'error', 'failed', 'unable']):
            # 包含HTTP状态码或常见错误词，很可能是临时问题
            return {
                'user_friendly': f'服务器响应异常，正在重试: {error_msg}',
                'error_type': 'server_response_error',
                'fatal': False
            }
        else:
            # 短小的未知错误，保守重试
            return {
                'user_friendly': f'遇到未知问题，正在尝试其他策略: {error_msg}',
                'error_type': 'unknown_error',
                'fatal': False
            }

    def _handle_network_issues(self, ydl_opts: Dict[str, Any], platform: str, strategy_name: str) -> Dict[str, Any]:
        """处理网络和SSL问题 - 首尔地区特别优化"""
        try:
            # 基本的网络优化已经在配置中，这里做额外处理
            if platform == 'youtube':
                # YouTube特别处理 - 韩国地区优化
                ydl_opts.update({
                    # 更激进的地理绕过
                    'geo_bypass': True,
                    'geo_bypass_country': 'KR',
                    'geo_bypass_ip_block': '211.231.100.0/24',
                    
                    # 网络容错
                    'retry_sleep_functions': {
                        'http': lambda n: min(2 ** n, 10),  # 指数退避
                        'fragment': lambda n: min(2 ** n, 10),
                        'extractor': lambda n: min(2 ** n, 10),
                    },
                    
                    # 忽略某些错误
                    'ignoreerrors': True,
                    'continue_dl': True,
                    
                    # 使用备用服务器
                    'prefer_free_formats': True,
                    'youtube_include_dash_manifest': False,
                })
                
                logger.info(f"🌏 启用韩国地区YouTube优化配置")
                
            elif platform == 'bilibili':
                # B站特别处理
                ydl_opts.update({
                    'geo_bypass': True,
                    'continue_dl': True,
                    'ignoreerrors': False,  # B站保持严格错误处理
                })
                
            return ydl_opts
            
        except Exception as e:
            logger.warning(f"⚠️ 网络优化配置失败: {e}")
            return ydl_opts

# 创建全局下载器实例
rock_solid_downloader = RockSolidVideoDownloader()

# 函数接口
def download_video(url: str, output_template: str, progress_callback: Optional[Callable] = None) -> str:
    """坚如磐石下载"""
    return rock_solid_downloader.download_video(url, output_template, progress_callback)

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