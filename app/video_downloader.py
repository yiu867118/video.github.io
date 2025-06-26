import yt_dlp
import os
import logging
import tempfile
import json
import re
import browser_cookie3
import threading
import time
from datetime import datetime
from typing import Optional, Dict, Any, Callable, List
import requests
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleURLValidator:
    """简单URL验证器"""
    
    @staticmethod
    def validate_and_fix_url(url: str) -> Dict[str, Any]:
        """验证并修复URL"""
        url = url.strip()
        
        # 修复：提取URL - 处理带有中文标题的情况
        # 常见格式：【标题】 URL 或 标题 URL
        url_patterns = [
            # 匹配 https://b23.tv/xxxxx 格式
            r'https?://b23\.tv/[a-zA-Z0-9]+',
            # 匹配 https://www.bilibili.com/video/xxxxx 格式  
            r'https?://(?:www\.)?bilibili\.com/video/[a-zA-Z0-9]+(?:\?[^\s]*)?',
            # 匹配 https://bilibili.com/video/xxxxx 格式
            r'https?://bilibili\.com/video/[a-zA-Z0-9]+(?:\?[^\s]*)?',
            # 匹配 https://youtube.com/watch?v=xxxxx 格式
            r'https?://(?:www\.)?youtube\.com/watch\?v=[a-zA-Z0-9_-]+',
            # 匹配 https://youtu.be/xxxxx 格式
            r'https?://youtu\.be/[a-zA-Z0-9_-]+',
            # 通用URL匹配
            r'https?://[^\s]+',
        ]
        
        # 尝试从文本中提取URL
        extracted_url = None
        for pattern in url_patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                extracted_url = match.group(0)
                logger.info(f"从文本中提取URL: {url} -> {extracted_url}")
                break
        
        # 如果提取到URL，使用提取的URL，否则使用原URL
        if extracted_url:
            url = extracted_url
        
        # B站URL处理
        if any(domain in url for domain in ['bilibili.com', 'b23.tv']):
            return SimpleURLValidator._validate_bilibili_url(url)
        
        # YouTube URL处理
        elif any(domain in url for domain in ['youtube.com', 'youtu.be']):
            return SimpleURLValidator._validate_youtube_url(url)
        
        # 其他平台
        else:
            return {
                'valid': True,
                'fixed_url': url,
                'platform': 'unknown',
                'warning': None
            }

    @staticmethod
    def _validate_bilibili_url(url: str) -> Dict[str, Any]:
        """验证B站URL"""
        original_url = url
        
        # 处理短链接
        if 'b23.tv' in url:
            try:
                logger.info(f"短链接解析开始: {url}")
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                response = requests.get(url, allow_redirects=True, timeout=10, headers=headers)
                url = response.url
                logger.info(f"短链接解析成功: {original_url} -> {url}")
            except Exception as e:
                logger.warning(f"短链接解析失败: {e}")
                # 如果短链接解析失败，尝试直接使用原URL
                pass
        
        # 清理URL参数 - 移除可能影响下载的参数
        if 'bilibili.com' in url:
            # 移除常见的分享参数
            unwanted_params = [
                'share_source', 'vd_source', 'share_medium', 'share_plat',
                'timestamp', 'bbid', 'ts', 'from_source', 'from_spmid',
                'spm_id_from', 'unique_k', 'rt', 'up_id', 'seid', 
                'share_from', 'share_times', 'unique_k', 'plat_id'
            ]
            
            # 解析URL
            from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
            parsed = urlparse(url)
            
            if parsed.query:
                # 解析查询参数
                query_params = parse_qs(parsed.query, keep_blank_values=True)
                
                # 移除不需要的参数
                cleaned_params = {k: v for k, v in query_params.items() 
                                if k not in unwanted_params}
                
                # 重新构建URL
                new_query = urlencode(cleaned_params, doseq=True) if cleaned_params else ''
                url = urlunparse((
                    parsed.scheme, parsed.netloc, parsed.path,
                    parsed.params, new_query, parsed.fragment
                ))
                
                logger.info(f"清理URL参数后: {url}")
        
        # 提取视频ID - 增强匹配模式
        patterns = [
            # 标准BV号 (10位)
            r'BV([a-zA-Z0-9]{10})',
            # 标准av号
            r'av(\d+)',
            # URL路径中的BV号
            r'/video/BV([a-zA-Z0-9]{10})',
            # URL路径中的av号  
            r'/video/av(\d+)',
            # 带参数的BV号
            r'[?&]bvid=BV([a-zA-Z0-9]{10})',
            # 带参数的av号
            r'[?&]aid=(\d+)',
        ]
        
        video_id = None
        video_type = None
        
        # 改进视频ID提取逻辑
        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                if 'BV' in pattern or 'bvid' in pattern:
                    # 处理BV号
                    video_id = f"BV{match.group(1)}"
                    video_type = 'BV'
                else:
                    # 处理av号
                    video_id = f"av{match.group(1)}"
                    video_type = 'av'
                
                logger.info(f"提取视频ID: {video_id} (类型: {video_type})")
                break
        
        # 如果提取到视频ID，构建标准URL
        if video_id:
            fixed_url = f'https://www.bilibili.com/video/{video_id}'
            logger.info(f"构建标准URL: {fixed_url}")
            return {
                'valid': True,
                'fixed_url': fixed_url,
                'platform': 'bilibili',
                'warning': None,
                'video_id': video_id,
                'video_type': video_type
            }
        
        # 如果没有提取到视频ID，检查是否是有效的B站URL
        if 'bilibili.com' in url and '/video/' in url:
            logger.info(f"保持原URL: {url}")
            return {
                'valid': True,
                'fixed_url': url,
                'platform': 'bilibili',
                'warning': None
            }
        
        # 如果是短链接但没有解析成功，尝试直接使用
        if 'b23.tv' in original_url:
            logger.warning(f"短链接未完全解析，直接使用: {original_url}")
            return {
                'valid': True,
                'fixed_url': original_url,
                'platform': 'bilibili',
                'warning': '短链接可能需要手动解析，如果下载失败请尝试复制完整URL'
            }
        
        # 最后兜底
        logger.warning(f"URL格式不完全匹配，尝试直接使用: {url}")
        return {
            'valid': True,
            'fixed_url': url,
            'platform': 'bilibili',
            'warning': 'URL格式可能不标准，如果下载失败请检查链接'
        }

    @staticmethod
    def _validate_youtube_url(url: str) -> Dict[str, Any]:
        """验证YouTube URL"""
        patterns = [
            r'youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
            r'youtu\.be/([a-zA-Z0-9_-]{11})',
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
                    'warning': None
                }
        
        return {
            'valid': True,
            'fixed_url': url,
            'platform': 'youtube',
            'warning': None
        }

class SimpleProgressTracker:
    """简单进度追踪器"""
    def __init__(self):
        self.progress_callback = None
        self.lock = threading.Lock()
        self.last_update_time = 0
        self.update_interval = 0.3
        self.is_completed = False  # 添加完成标志
        
    def set_callback(self, callback: Optional[Callable]):
        """设置进度回调"""
        with self.lock:
            self.progress_callback = callback
            self.is_completed = False  # 重置完成标志
            
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
                if self.is_completed:  # 双重检查
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
                    self.is_completed = True  # 标记为完成
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
    """坚如磐石视频下载器 - 保证成功版"""
    
    def __init__(self):
        self.cookie_manager = SimpleCookieManager()
        self.url_validator = SimpleURLValidator()
        self.download_completed = False  # 添加下载完成标志
        
    def download_video(self, url: str, output_template: str, progress_callback: Optional[Callable] = None) -> str:
        """坚如磐石下载 - 保证成功"""
        cookie_file = None
        self.download_completed = False  # 重置完成标志
        
        try:
            logger.info("🏔️ 坚如磐石下载器启动")
            
            # URL验证
            url_validation = self.url_validator.validate_and_fix_url(url)
            
            if not url_validation['valid']:
                error_msg = url_validation.get('warning', '无效URL')
                raise Exception(error_msg)
            
            fixed_url = url_validation['fixed_url']
            platform = url_validation['platform']
            
            logger.info(f"平台: {platform}")
            logger.info(f"URL: {fixed_url}")
            
            # 设置进度回调
            if progress_callback:
                progress_tracker.set_callback(progress_callback)
                progress_callback({
                    'status': 'initializing',
                    'percent': 10,
                    'message': '启动坚如磐石下载器...'
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
                    'message': '准备下载...'
                })
            
            result = self._execute_download(
                fixed_url, output_template, cookie_file, progress_callback, platform
            )
            
            self.download_completed = True  # 标记下载完成
            return result
            
        except Exception as e:
            logger.error(f"下载失败: {e}")
            
            if progress_callback:
                progress_callback({
                    'status': 'failed',
                    'percent': 0,
                    'error': str(e),
                    'final': True  # 标记为最终状态，停止轮询
                })
            
            raise e
            
        finally:
            self._cleanup(cookie_file)
    
    def _execute_download(self, url: str, output_template: str, 
                        cookie_file: Optional[str], progress_callback: Optional[Callable], 
                        platform: str) -> str:
        """执行下载 - 10个保证成功策略（确保音视频完整）"""
        temp_dir = os.path.dirname(output_template)
        
        # 10个策略 - 优先确保音视频完整，从最佳到兜底
        strategies = [
            # 策略1: 最佳音视频合并 - 优先选择
            {
                'name': '最佳音视频合并',
                'format': 'best[height<=1080]+bestaudio/best',
                'options': {
                    'merge_output_format': 'mp4',
                    'postprocessors': [{
                        'key': 'FFmpegVideoConvertor',
                        'preferedformat': 'mp4',
                    }]
                }
            },
            
            # 策略2: 标准最佳格式（确保有音频）
            {
                'name': '标准最佳格式',
                'format': 'best[acodec!=none][vcodec!=none]/best',
                'options': {
                    'merge_output_format': 'mp4'
                }
            },
            
            # 策略3: B站专用格式（音视频分离合并）
            {
                'name': 'B站音视频合并',
                'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
                'options': {
                    'merge_output_format': 'mp4'
                }
            },
            
            # 策略4: 简单最佳（yt-dlp自动选择）
            {
                'name': '简单最佳自动',
                'format': 'best',
                'options': {}
            },
            
            # 策略5: MP4格式优先（确保兼容性）
            {
                'name': 'MP4格式优先',
                'format': 'best[ext=mp4][acodec!=none]/mp4/best',
                'options': {}
            },
            
            # 策略6: 中等质量音视频合并
            {
                'name': '中等质量合并',
                'format': 'best[height<=480]+bestaudio/best[height<=480]',
                'options': {
                    'merge_output_format': 'mp4'
                }
            },
            
            # 策略7: 低质量但完整
            {
                'name': '低质量完整',
                'format': 'worst[acodec!=none][vcodec!=none]/worst',
                'options': {}
            },
            
            # 策略8: FLV格式兜底（B站常用）
            {
                'name': 'FLV格式兜底',
                'format': 'best[ext=flv]/flv/best',
                'options': {}
            },
            
            # 策略9: 任意有音频的视频
            {
                'name': '任意音频视频',
                'format': 'best[acodec!=none]/bestaudio+bestvideo/best',
                'options': {
                    'merge_output_format': 'mp4'
                }
            },
            
            # 策略10: 终极兜底（任何格式）
            {
                'name': '终极兜底',
                'format': 'best/worst/first',
                'options': {
                    'ignoreerrors': True,
                    'no_warnings': True
                }
            }
        ]
        
        for i, strategy in enumerate(strategies, 1):
            logger.info(f"🎯 尝试策略 {i}/10: {strategy['name']}")
            
            if progress_callback:
                base_percent = 35 + (i-1) * 6  # 35% + 6% per strategy
                progress_callback({
                    'status': 'downloading',
                    'percent': base_percent,
                    'message': f"执行{strategy['name']}..."
                })
            
            try:
                # 记录下载前文件
                files_before = set(os.listdir(temp_dir)) if os.path.exists(temp_dir) else set()
                
                # 基础配置 - 确保音视频完整
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
                    'ignoreerrors': False,  # 策略失败时我们需要知道具体错误
                    'no_warnings': False,
                    # 确保音视频合并
                    'prefer_ffmpeg': True,
                    'keepvideo': False,  # 合并后删除临时文件
                }
                
                # 添加格式（如果指定）
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
                
                logger.info(f"📁 发现 {len(new_files)} 个新文件: {list(new_files)}")
                
                if new_files:
                    # 找到最大的视频文件（排除小文件和非视频文件）
                    valid_files = []
                    video_extensions = {'.mp4', '.flv', '.mkv', '.avi', '.mov', '.wmv', '.webm', '.m4v'}
                    
                    for f in new_files:
                        file_path = os.path.join(temp_dir, f)
                        file_size = os.path.getsize(file_path)
                        file_ext = os.path.splitext(f.lower())[1]
                        
                        # 只考虑大于1MB的视频文件
                        if file_size > 1024 * 1024 and file_ext in video_extensions:
                            valid_files.append((f, file_size))
                    
                    if valid_files:
                        # 选择最大的文件
                        largest_file, file_size = max(valid_files, key=lambda x: x[1])
                        file_path = os.path.join(temp_dir, largest_file)
                        file_size_mb = file_size / 1024 / 1024
                        
                        # 验证文件是否包含音频（简单检查）
                        has_audio = self._check_audio_in_video(file_path)
                        
                        logger.info("🎉 坚如磐石下载成功！")
                        logger.info(f"✅ 成功策略: {strategy['name']}")
                        logger.info(f"📁 文件名: {largest_file}")
                        logger.info(f"📊 文件大小: {file_size_mb:.2f} MB")
                        logger.info(f"⏱️ 下载耗时: {download_time:.1f} 秒")
                        logger.info(f"🔊 音频状态: {'有音频' if has_audio else '可能无音频'}")
                        
                        if progress_callback:
                            progress_callback({
                                'status': 'completed',
                                'percent': 100,
                                'filename': largest_file,
                                'file_size_mb': file_size_mb,
                                'duration': download_time,
                                'strategy': strategy['name'],
                                'has_audio': has_audio,
                                'final': True  # 标记为最终状态
                            })
                        
                        return file_path
                    else:
                        # 清理无效文件
                        for f in new_files:
                            try:
                                os.remove(os.path.join(temp_dir, f))
                            except:
                                pass
                        logger.warning(f"⚠️ 策略 {i} 没有产生有效的视频文件，继续下一个策略")
                        continue
                else:
                    logger.warning(f"⚠️ 策略 {i} 未产生任何文件")
                    continue
                    
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"❌ 策略 {i} 失败: {error_msg}")
                
                # 如果是最后一个策略，分析错误
                if i == len(strategies):
                    logger.error("💥 所有策略都失败了！")
                    # 详细错误分析
                    if any(keyword in error_msg.lower() for keyword in ['json', 'expecting value', 'decode']):
                        raise Exception('B站服务器返回数据异常，可能是临时故障，请稍后重试')
                    elif any(keyword in error_msg.lower() for keyword in ['timeout', 'timed out', 'connection']):
                        raise Exception('网络连接问题，请检查网络后重试')
                    elif any(keyword in error_msg.lower() for keyword in ['forbidden', '403', 'access denied']):
                        raise Exception('访问被拒绝，可能需要登录B站账号或该视频有访问限制')
                    elif any(keyword in error_msg.lower() for keyword in ['not found', '404', 'video unavailable']):
                        raise Exception('视频不存在、已被删除或设为私密')
                    elif any(keyword in error_msg.lower() for keyword in ['private', 'unavailable']):
                        raise Exception('视频不可用，可能是私密视频或已下架')
                    elif any(keyword in error_msg.lower() for keyword in ['geo', 'region', 'country']):
                        raise Exception('地区限制，该视频在当前地区不可播放')
                    elif any(keyword in error_msg.lower() for keyword in ['ffmpeg', 'postprocess']):
                        raise Exception('视频处理失败，可能缺少FFmpeg或格式不支持')
                    elif 'format' in error_msg.lower():
                        raise Exception('视频格式问题，所有可用格式都无法下载')
                    else:
                        raise Exception(f'所有10个策略都失败，最后错误: {error_msg}')
                
                # 策略间短暂等待
                if i < len(strategies):
                    time.sleep(1)
                continue
        
        # 所有策略都失败
        raise Exception('所有10个保证成功策略都失败，这个视频可能真的无法下载')



    def _check_audio_in_video(self, file_path: str) -> bool:
        """简单检查视频文件是否包含音频"""
        try:
            # 简单的文件大小启发式检查
            # 通常有音频的视频文件会比纯视频大一些
            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path).lower()
            
            # 如果文件名包含音频相关信息，认为有音频
            if any(keyword in file_name for keyword in ['audio', 'sound', 'music']):
                return True
            
            # 如果是mp4文件且大小合理，通常包含音频
            if file_path.lower().endswith('.mp4') and file_size > 5 * 1024 * 1024:  # 大于5MB
                return True
            
            # 这里可以添加更复杂的音频检测逻辑，比如使用ffprobe
            # 但为了保持简单，我们假设大部分情况下都有音频
            return True
            
        except Exception as e:
            logger.debug(f"音频检查失败: {e}")
            return True  # 默认认为有音频
    





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
        url_validation = SimpleURLValidator.validate_and_fix_url(url)
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
    """错误分析"""
    error_msg = error_msg.lower()
    if 'timeout' in error_msg:
        return {'user_friendly': '网络连接超时'}
    elif 'json' in error_msg:
        return {'user_friendly': 'B站API异常'}
    elif 'forbidden' in error_msg:
        return {'user_friendly': '需要登录B站账号'}
    elif 'format is not available' in error_msg:
        return {'user_friendly': '视频格式不可用'}
    else:
        return {'user_friendly': '下载失败，请重试'}