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
            # 🔥关键：处理文件名中的特殊字符，但保留原始标题
            'restrictfilenames': False,  # 不限制文件名，保留中文等字符
            'windowsfilenames': True,   # Windows文件名兼容
            # 文件名模板配置
            'outtmpl': '%(title)s.%(ext)s',  # 使用视频原始标题作为文件名
        }
    
    def download_video(self, url: str, output_template: str, progress_callback: Optional[Callable] = None) -> str:
        """主下载函数 - 使用视频真实标题作为文件名"""
        logger.info(f"🎯 开始下载: {url}")
        
        try:
            # 🔥修复：确保URL格式正确
            if 'bilibili.com' in url:
                url = url.replace('m.bilibili.com', 'www.bilibili.com')
                url = url.replace('//bilibili.com', '//www.bilibili.com')
                logger.info(f"🔧 URL格式化: {url}")
            
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
        
        # 🔥创建专用的下载子目录，避免与现有文件冲突
        download_subdir = os.path.join(temp_dir, f"video_download_{int(time.time())}")
        os.makedirs(download_subdir, exist_ok=True)
        
        logger.info(f"📁 使用专用下载目录: {download_subdir}")
        
        # 修改output_template到子目录
        original_template = output_template
        output_template = os.path.join(download_subdir, "%(title)s.%(ext)s")
        
        # 🔥先暂时简化，不列出格式，直接开始下载
        # 🔥新增：先列出可用格式，帮助优化策略选择
        # logger.info("📋 正在分析可用视频格式...")
        # available_formats = self._list_available_formats(url, platform)
        
        # 🔥彻底修复的下载策略 - 专注最高画质+音频
        # B站和其他平台使用不同的策略
        if platform == 'bilibili':
            strategies = [
                {
                    'name': 'B站最佳1080p合并',
                    'format': '100050+30232/100050+30280/100050+30216',  # 1080p视频 + 音频
                    'options': {
                        'merge_output_format': 'mp4',
                        'geo_bypass': True,
                        'nocheckcertificate': True,
                    }
                },
                {
                    'name': 'B站最佳720p合并',
                    'format': '100048+30232/100048+30280/100048+30216',  # 720p视频 + 音频
                    'options': {
                        'merge_output_format': 'mp4',
                        'geo_bypass': True,
                        'nocheckcertificate': True,
                    }
                },
                {
                    'name': 'B站最佳480p合并',
                    'format': '100047+30232/100047+30280/100047+30216',  # 480p视频 + 音频
                    'options': {
                        'merge_output_format': 'mp4',
                        'geo_bypass': True,
                        'nocheckcertificate': True,
                    }
                },
                {
                    'name': 'B站智能合并(H264)',
                    'format': 'bestvideo[vcodec^=avc1]+bestaudio/bestvideo+bestaudio',
                    'options': {
                        'merge_output_format': 'mp4',
                        'geo_bypass': True,
                        'nocheckcertificate': True,
                    }
                },
                {
                    'name': 'B站通用合并',
                    'format': 'bestvideo+bestaudio/best',
                    'options': {
                        'merge_output_format': 'mp4',
                        'geo_bypass': True,
                        'nocheckcertificate': True,
                    }
                },
                {
                    'name': 'B站兜底策略',
                    'format': 'best/worst',
                    'options': {
                        'merge_output_format': 'mp4',
                        'geo_bypass': True,
                        'nocheckcertificate': True,
                        'ignoreerrors': True,
                    }
                }
            ]
        else:
            # YouTube等其他平台的策略
            strategies = [
                {
                    'name': '最佳质量(自动音视频合并)',
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    'options': {
                        'merge_output_format': 'mp4',
                        'geo_bypass': True,
                        'nocheckcertificate': True,
                    }
                },
                {
                    'name': '最佳质量(任何格式音视频合并)', 
                    'format': 'bestvideo+bestaudio/best',
                    'options': {
                        'merge_output_format': 'mp4',
                        'geo_bypass': True,
                        'nocheckcertificate': True,
                        'prefer_insecure': True,
                    }
                },
                {
                    'name': '最佳MP4(含音频)',
                    'format': 'best[ext=mp4][acodec!=none]/best[ext=mp4]/best',
                    'options': {
                        'merge_output_format': 'mp4',
                        'geo_bypass': True,
                        'nocheckcertificate': True,
                        'prefer_insecure': True,
                    }
                },
                {
                    'name': '通用兼容策略',
                    'format': 'best',
                    'options': {
                        'merge_output_format': 'mp4',
                        'geo_bypass': True,
                        'nocheckcertificate': True,
                        'prefer_insecure': True,
                        'ignoreerrors': True,
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
                
                # 🔥修复：确保使用视频原始标题作为文件名
                ydl_opts['outtmpl'] = output_template
                
                # 平台特定配置 - 增强移动端支持
                if platform == 'youtube':
                    ydl_opts['youtube_include_dash_manifest'] = False
                elif platform == 'bilibili':
                    # 🔥修复B站下载 - 简化但有效的配置
                    if strategy['name'] == 'B站移动端兼容':
                        # 移动端User-Agent
                        ydl_opts['http_headers'] = {
                            'Referer': 'https://www.bilibili.com/',
                            'User-Agent': 'Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
                            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                        }
                    else:
                        # 桌面端User-Agent
                        ydl_opts['http_headers'] = {
                            'Referer': 'https://www.bilibili.com/',
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                        }
                    
                    # 🔥关键：简化B站配置，避免复杂的extractor参数
                    # 让yt-dlp自动处理格式选择
                
                # 进度回调
                progress_tracker = ProgressTracker()
                if progress_callback:
                    progress_tracker.set_callback(progress_callback)
                    ydl_opts['progress_hooks'] = [progress_tracker.update]
                
                # 执行下载
                files_before = set(os.listdir(download_subdir)) if os.path.exists(download_subdir) else set()
                download_start_time = time.time()
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                
                # 🔥简化的文件检测逻辑：检查下载目录中的所有文件
                files_after = set(os.listdir(download_subdir)) if os.path.exists(download_subdir) else set()
                all_files = list(files_after)
                
                logger.info(f"📁 下载目录文件数: {len(all_files)}")
                
                if all_files:
                    # 找到最大的视频文件
                    video_files = []
                    for filename in all_files:
                        file_path = os.path.join(download_subdir, filename)
                        if os.path.isfile(file_path):
                            size = os.path.getsize(file_path)
                            # 检查是否是视频文件
                            if filename.lower().endswith(('.mp4', '.webm', '.mkv', '.avi', '.mov', '.flv', '.m4v')):
                                logger.info(f"📦 发现视频文件: {filename} ({size/1024:.1f} KB)")
                                video_files.append((filename, size, file_path))
                            else:
                                logger.info(f"� 发现其他文件: {filename} ({size/1024:.1f} KB)")
                    
                    if video_files:
                        # 按文件大小排序，选择最大的
                        video_files.sort(key=lambda x: x[1], reverse=True)
                        largest_file, largest_size, file_path = video_files[0]
                        
                        # 🔥支持各种大小的视频文件
                        if largest_size > 10 * 1024:  # 至少10KB
                            # 🔥保持原始文件名（yt-dlp已经按照我们的模板命名了）
                            final_path = os.path.join(temp_dir, largest_file)
                            try:
                                # 如果目标文件已存在，删除它
                                if os.path.exists(final_path):
                                    os.remove(final_path)
                                # 移动文件并保持原名
                                import shutil
                                shutil.move(file_path, final_path)
                                
                                logger.info(f"🎉 下载成功！文件: {largest_file} ({largest_size/1024/1024:.2f} MB)")
                                logger.info(f"📁 文件位置: {final_path}")
                                logger.info(f"📝 文件名来源: yt-dlp自动命名（基于视频标题）")
                                
                                if progress_callback:
                                    progress_callback({
                                        'status': 'completed',
                                        'percent': 100,
                                        'filename': largest_file,
                                        'file_size_mb': largest_size / 1024 / 1024,
                                        'strategy': strategy['name'],
                                        'final': True
                                    })
                                
                                # 清理下载目录
                                try:
                                    shutil.rmtree(download_subdir)
                                except:
                                    pass
                                
                                return final_path
                            except Exception as e:
                                logger.error(f"移动文件失败: {e}")
                        else:
                            logger.warning(f"⚠️ 文件太小: {largest_file} ({largest_size} bytes)")
                    else:
                        logger.warning(f"⚠️ 未发现视频文件，只有: {[f for f in all_files]}")
                else:
                    logger.warning(f"⚠️ 下载目录为空: {download_subdir}")
                
                # 清理空的下载目录
                try:
                    if os.path.exists(download_subdir):
                        import shutil
                        shutil.rmtree(download_subdir)
                except:
                    pass
                
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
        """获取视频信息，包括标题 - 增强移动端支持"""
        try:
            # 🔥修复：确保URL格式正确，不要让yt-dlp自动转换为移动版
            original_url = url
            if 'bilibili.com' in url:
                # 确保使用桌面版URL
                url = url.replace('m.bilibili.com', 'www.bilibili.com')
                url = url.replace('//bilibili.com', '//www.bilibili.com')
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'geo_bypass': True,
                'nocheckcertificate': True,
                'skip_download': True,  # 只获取信息，不下载
                'socket_timeout': 120,
            }
            
            # 检测平台并添加特定配置
            if 'bilibili.com' in url or 'b23.tv' in url:
                # B站特殊配置 - 简化版
                ydl_opts['http_headers'] = {
                    'Referer': 'https://www.bilibili.com/',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                }
                # 🔥关键：让yt-dlp自动处理，避免复杂配置
            
            logger.info(f"📱 正在获取视频信息: {url}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # 清理标题，但保留原始中文字符
                raw_title = info.get('title', 'Unknown_Video')
                clean_title = self._clean_filename(raw_title)
                
                logger.info(f"📝 获取视频信息成功")
                logger.info(f"   原始标题: {raw_title}")
                logger.info(f"   清理标题: {clean_title}")
                
                return {
                    'title': clean_title,
                    'raw_title': raw_title,  # 保留原始标题
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', ''),
                    'upload_date': info.get('upload_date', ''),
                }
        except Exception as e:
            logger.warning(f"获取视频信息失败: {e}")
            return {'title': 'Unknown_Video', 'raw_title': 'Unknown_Video'}
    
    def _clean_filename(self, title: str) -> str:
        """高级文件名清理 - 保留更多原始信息但确保Windows兼容"""
        import re
        
        if not title or not title.strip():
            return 'Unknown_Video'
        
        # 移除或替换不安全的字符，但尽量保留原意
        replacements = {
            # Windows文件系统不允许的字符 - 用相似字符替换
            '<': '＜',  # 用全角字符替换
            '>': '＞',
            ':': '：',  # 用中文冒号替换
            '"': "'",   # 用单引号替换双引号
            '/': '／',  # 用全角斜杠替换
            '\\': '＼',
            '|': '｜',
            '?': '？',  # 用中文问号替换
            '*': '＊',
            
            # 其他标点符号优化
            '【': '[',
            '】': ']',
            '（': '(',
            '）': ')',
        }
        
        # 应用替换
        for old, new in replacements.items():
            title = title.replace(old, new)
        
        # 移除首尾的空格和点
        title = title.strip(' ._-')
        
        # 智能长度限制，尽量保留完整单词
        max_length = 120  # Windows路径限制考虑
        if len(title) > max_length:
            # 尝试在合适的位置截断
            title = title[:max_length]
            # 如果截断位置不是空格，尝试找到最近的空格或标点
            if title[-1] not in ' -_.,，。':
                last_good_pos = max(
                    title.rfind(' '),
                    title.rfind('-'),
                    title.rfind('_'),
                    title.rfind('，'),
                    title.rfind('。'),
                    title.rfind(','),
                    title.rfind('.')
                )
                if last_good_pos > max_length * 0.8:  # 如果截断点不会丢失太多内容
                    title = title[:last_good_pos]
        
        # 再次清理首尾
        title = title.strip(' ._-')
        
        # 如果清理后为空，使用默认名称
        if not title:
            title = 'Unknown_Video'
        
        return title

    def _list_available_formats(self, url: str, platform: str) -> list:
        """列出可用的视频格式 - 用于调试和优化格式选择"""
        try:
            ydl_opts = self._get_base_config()
            ydl_opts['listformats'] = True
            ydl_opts['quiet'] = False  # 显示格式信息
            ydl_opts['skip_download'] = True
            
            # 平台特定配置
            if platform == 'bilibili':
                ydl_opts['http_headers'] = {
                    'Referer': 'https://www.bilibili.com/',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = info.get('formats', [])
                logger.info(f"📋 可用格式数量: {len(formats)}")
                
                # 记录前几个格式用于调试
                for i, fmt in enumerate(formats[:5]):
                    logger.info(f"  格式{i+1}: {fmt.get('format_id', 'N/A')} - {fmt.get('ext', 'N/A')} - {fmt.get('resolution', 'N/A')} - {fmt.get('acodec', 'N/A')}")
                
                return formats
        except Exception as e:
            logger.warning(f"列出格式失败: {e}")
            return []

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
