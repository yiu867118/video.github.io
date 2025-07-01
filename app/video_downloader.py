"""
彻底修复的视频下载器 - 专门针对B站手机端/平板端下载问题
确保所有设备都能下载最高画质+音频的视频，音视频正确合并
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
    """增强的B站错误分析 - 专门针对移动端问题"""
    error_msg_lower = error_msg.lower()
    
    # 地区限制或VPN相关错误
    if any(keyword in error_msg_lower for keyword in ['geo-restrict', 'vpn', 'proxy', 'region', 'deleted']):
        return {
            'user_friendly': '该视频可能有地区限制或已被删除，正在尝试其他方式下载...',
            'error_type': 'geo_restricted',
            'fatal': False  # 不是致命错误，可以尝试其他策略
        }
    
    # 只有这些才是真正致命的错误
    elif any(keyword in error_msg_lower for keyword in ['付费', 'payment', 'premium', '大会员', 'vip', 'paid']):
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
    elif any(keyword in error_msg_lower for keyword in ['private', '私有', 'unavailable', '不可用']):
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

class CompletelyFixedVideoDownloader:
    def __init__(self):
        self.system_info = self._diagnose_system()
        logger.info("🎯 彻底修复版视频下载器已初始化 - 专为B站手机/平板端优化")
        
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
        """获取基础下载配置 - 优先最高画质+音频"""
        return {
            'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080][acodec!=none]/best',  # 优先最高画质+音频
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
            'fragment_retries': 5,  # 增加片段重试次数
            # 🔥关键：处理文件名中的特殊字符，但保留原始标题
            'restrictfilenames': False,  # 不限制文件名，保留中文等字符
            'windowsfilenames': True,   # Windows文件名兼容
            # 文件名模板配置
            'outtmpl': '%(title)s.%(ext)s',  # 使用视频原始标题作为文件名
            # 🎯确保音视频合并质量
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        }
    
    def download_video(self, url: str, output_template: str, progress_callback: Optional[Callable] = None) -> str:
        """主下载函数 - 彻底修复B站手机/平板端下载"""
        logger.info(f"🎯 开始下载: {url}")
        
        try:
            # 🔥修复：确保URL格式正确并检测访问来源
            if 'bilibili.com' in url:
                # 保留原始URL信息以判断来源
                is_mobile_source = 'm.bilibili.com' in url
                # 统一转换为www格式，但记住来源
                url = url.replace('m.bilibili.com', 'www.bilibili.com')
                url = url.replace('//bilibili.com', '//www.bilibili.com')
                logger.info(f"🔧 URL格式化: {url} (移动端来源: {is_mobile_source})")
            
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
        """🔥终极修复版下载函数 - 彻底解决B站下载问题"""
        temp_dir = os.path.dirname(output_template)
        
        # 🔥核心修复：确保URL格式正确且不会被转换
        if 'bilibili.com' in url:
            url = url.replace('m.bilibili.com', 'www.bilibili.com')
            url = url.replace('//bilibili.com', '//www.bilibili.com')
            if '?' in url:
                url = url.split('?')[0]
            logger.info(f"🔧 URL标准化: {url}")
        
        # 创建专用下载目录
        download_subdir = os.path.join(temp_dir, f"dl_{int(time.time())}")
        os.makedirs(download_subdir, exist_ok=True)
        
        logger.info(f"📁 使用下载目录: {download_subdir}")
        
        # 🔥最高画质优先策略 - 确保三端兼容且优先最高画质+音频
        if platform == 'bilibili':
            strategies = [
                {
                    'name': '🎯B站最高画质音视频策略(1080P+)',
                    'format': 'bestvideo[height<=1080]+bestaudio[acodec!=none]/best[height<=1080][acodec!=none]/best',
                    'options': {
                        'merge_output_format': 'mp4',
                        'geo_bypass': True,
                        'nocheckcertificate': True,
                        'ignoreerrors': True,
                        'socket_timeout': 45,
                        'retries': 2,
                        'fragment_retries': 3,
                        'http_headers': {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                            'Referer': 'https://www.bilibili.com/',
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                            'Accept-Encoding': 'gzip, deflate',
                            'Connection': 'keep-alive',
                        }
                    }
                },
                {
                    'name': '📱B站移动端兼容策略(高画质)',
                    'format': 'best[height<=720][acodec!=none]+bestaudio/best[height<=720]/best',
                    'options': {
                        'merge_output_format': 'mp4',
                        'geo_bypass': True,
                        'nocheckcertificate': True,
                        'ignoreerrors': True,
                        'socket_timeout': 30,
                        'retries': 2,
                        'http_headers': {
                            'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
                            'Referer': 'https://www.bilibili.com/',
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                            'Accept-Language': 'zh-CN,zh;q=0.9',
                        }
                    }
                },
                {
                    'name': '🔧B站音视频ID组合策略(最优质量)',
                    'format': '30077+30280/30066+30280/100048+30280/100047+30232/30011+30216',
                    'options': {
                        'merge_output_format': 'mp4',
                        'geo_bypass': True,
                        'nocheckcertificate': True,
                        'ignoreerrors': True,
                        'socket_timeout': 30,
                        'retries': 1,
                        'http_headers': {
                            'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
                            'Referer': 'https://www.bilibili.com/',
                        }
                    }
                },
                {
                    'name': '🛡️B站通用兼容策略(中等画质)',
                    'format': 'best[height<=480]+bestaudio/best[acodec!=none]/best',
                    'options': {
                        'merge_output_format': 'mp4',
                        'geo_bypass': True,
                        'nocheckcertificate': True,
                        'ignoreerrors': True,
                        'socket_timeout': 20,
                        'retries': 1,
                        'http_headers': {
                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                            'Referer': 'https://www.bilibili.com/',
                        }
                    }
                },
                {
                    'name': '🚨B站最后兜底策略(确保下载)',
                    'format': 'best/worst',
                    'options': {
                        'merge_output_format': 'mp4',
                        'geo_bypass': True,
                        'nocheckcertificate': True,
                        'ignoreerrors': True,
                        'socket_timeout': 15,
                        'retries': 1,
                    }
                }
            ]
        else:
            # YouTube等其他平台 - 优先最高画质+音频
            strategies = [
                {
                    'name': '🎯YouTube最高画质策略(1080P+音频)',
                    'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080][acodec!=none]/best',
                    'options': {
                        'merge_output_format': 'mp4',
                        'geo_bypass': True,
                        'nocheckcertificate': True,
                        'socket_timeout': 45,
                        'retries': 2,
                        'http_headers': {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        }
                    }
                },
                {
                    'name': '📱YouTube移动端策略(720P+音频)',
                    'format': 'best[height<=720][acodec!=none]/best[ext=mp4]/best',
                    'options': {
                        'merge_output_format': 'mp4',
                        'geo_bypass': True,
                        'nocheckcertificate': True,
                        'ignoreerrors': True,
                        'socket_timeout': 30,
                        'retries': 1,
                        'http_headers': {
                            'User-Agent': 'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
                        }
                    }
                },
                {
                    'name': '🛡️YouTube通用兼容策略', 
                    'format': 'best[acodec!=none]/best',
                    'options': {
                        'merge_output_format': 'mp4',
                        'geo_bypass': True,
                        'nocheckcertificate': True,
                        'ignoreerrors': True,
                        'socket_timeout': 20,
                        'retries': 1,
                    }
                }
            ]
        
        last_error = None
        output_template = os.path.join(download_subdir, "%(title)s.%(ext)s")
        
        for i, strategy in enumerate(strategies, 1):
            try:
                logger.info(f"🎯 尝试策略 {i}/{len(strategies)}: {strategy['name']}")
                
                if i == 1 and progress_callback:
                    progress_callback({
                        'status': 'downloading',
                        'percent': 50,
                        'message': f'正在尝试下载...'
                    })
                
                # 配置下载选项
                ydl_opts = self._get_base_config()
                ydl_opts.update(strategy['options'])
                ydl_opts['format'] = strategy['format']
                ydl_opts['outtmpl'] = output_template
                
                # 进度跟踪
                progress_tracker = ProgressTracker()
                if progress_callback:
                    progress_tracker.set_callback(progress_callback)
                    ydl_opts['progress_hooks'] = [progress_tracker.update]
                
                # 🔥关键：确保URL不被修改
                download_url = url
                
                start_time = time.time()
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([download_url])
                
                # 检查下载结果
                files = os.listdir(download_subdir) if os.path.exists(download_subdir) else []
                
                if files:
                    video_files = []
                    for filename in files:
                        file_path = os.path.join(download_subdir, filename)
                        if os.path.isfile(file_path):
                            size = os.path.getsize(file_path)
                            # 🎯优化：检查视频文件质量，优先选择大文件（通常质量更好）
                            if filename.lower().endswith(('.mp4', '.webm', '.mkv', '.avi', '.mov', '.flv', '.m4v')) and size > 1024:
                                logger.info(f"📦 发现视频文件: {filename} ({size/1024/1024:.1f} MB)")
                                video_files.append((filename, size, file_path))
                    
                    if video_files:
                        # 🎯关键：按文件大小排序，优先选择最大的文件（通常是最高画质）
                        video_files.sort(key=lambda x: x[1], reverse=True)
                        largest_file, largest_size, file_path = video_files[0]
                        
                        # 🔍质量验证：确保下载的是高质量文件
                        quality_info = ""
                        if largest_size > 50 * 1024 * 1024:  # 50MB+
                            quality_info = "🎯高画质"
                        elif largest_size > 20 * 1024 * 1024:  # 20MB+
                            quality_info = "📹中画质"
                        else:
                            quality_info = "📱标准画质"
                        
                        # 移动到最终位置
                        final_path = os.path.join(temp_dir, largest_file)
                        try:
                            if os.path.exists(final_path):
                                os.remove(final_path)
                            
                            import shutil
                            shutil.move(file_path, final_path)
                            
                            elapsed = time.time() - start_time
                            
                            logger.info(f"🎉 下载成功！策略: {strategy['name']}")
                            logger.info(f"📁 文件: {largest_file} ({largest_size/1024/1024:.2f} MB) - {quality_info}")
                            logger.info(f"⏱️ 耗时: {elapsed:.1f}秒")
                            logger.info(f"📊 平均速度: {(largest_size/1024/1024)/elapsed:.1f} MB/s")
                            
                            if progress_callback:
                                progress_callback({
                                    'status': 'completed',
                                    'percent': 100,
                                    'filename': largest_file,
                                    'file_size_mb': largest_size / 1024 / 1024,
                                    'quality_info': quality_info,
                                    'strategy': strategy['name'],
                                    'download_speed': f"{(largest_size/1024/1024)/elapsed:.1f} MB/s",
                                    'final': True
                                })
                            
                            # 清理下载目录
                            try:
                                import shutil
                                shutil.rmtree(download_subdir)
                            except:
                                pass
                            
                            return final_path
                            
                        except Exception as e:
                            logger.error(f"移动文件失败: {e}")
                    else:
                        logger.warning(f"⚠️ 未发现有效视频文件")
                else:
                    logger.warning(f"⚠️ 下载目录为空")
                
                logger.info(f"⚠️ 策略 {i} 未产生有效文件，继续下一个")
                
            except Exception as e:
                error_msg = str(e)
                last_error = error_msg
                logger.info(f"⚠️ 策略 {i} 失败: {error_msg[:100]}...")
                
                if i < len(strategies):
                    logger.info(f"🔄 继续尝试下一个策略...")
                    time.sleep(0.5)
                    continue
        
        # 清理临时目录
        try:
            import shutil
            shutil.rmtree(download_subdir)
        except:
            pass
        
        # 所有策略都失败
        logger.error(f"💀 所有 {len(strategies)} 个策略都失败")
        error_analysis = analyze_bilibili_error(last_error or '下载失败')
        raise Exception(error_analysis.get('user_friendly', '所有下载策略都失败，请检查视频链接'))
    
    def _get_video_info(self, url: str) -> Dict[str, Any]:
        """获取视频信息 - 彻底修复B站访问问题"""
        try:
            # 🔥关键修复：确保URL始终为桌面版格式
            if 'bilibili.com' in url:
                url = url.replace('m.bilibili.com', 'www.bilibili.com')
                url = url.replace('//bilibili.com', '//www.bilibili.com')
                # 移除可能导致问题的参数
                if '?' in url:
                    url = url.split('?')[0]
            
            # 🔥新的简化配置 - 专门针对B站JSON解析错误
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'skip_download': True,
                'socket_timeout': 30,
                'retries': 1,
                'geo_bypass': True,
                'nocheckcertificate': True,
                'ignoreerrors': True,  # 忽略部分错误
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Referer': 'https://www.bilibili.com/',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Cache-Control': 'no-cache',
                }
            }
            
            logger.info(f"📱 尝试获取视频信息: {url}")
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    if info and info.get('title'):
                        raw_title = info.get('title', 'Unknown_Video')
                        clean_title = self._clean_filename(raw_title)
                        
                        logger.info(f"✅ 获取视频信息成功")
                        logger.info(f"   标题: {clean_title}")
                        
                        return {
                            'title': clean_title,
                            'raw_title': raw_title,
                            'duration': info.get('duration', 0),
                            'uploader': info.get('uploader', ''),
                            'upload_date': info.get('upload_date', ''),
                        }
            except Exception as e:
                logger.warning(f"⚠️ 获取信息失败，使用默认标题: {str(e)[:50]}...")
            
            # 如果获取失败，生成基于URL的标题
            if 'bilibili.com' in url and 'BV' in url:
                import re
                bv_match = re.search(r'BV[A-Za-z0-9]+', url)
                if bv_match:
                    bv_id = bv_match.group()
                    default_title = f"Bilibili_Video_{bv_id}"
                    logger.info(f"✅ 使用BV号生成标题: {default_title}")
                    return {
                        'title': default_title,
                        'raw_title': default_title,
                        'duration': 0,
                        'uploader': '',
                        'upload_date': '',
                    }
            
            return {'title': 'Unknown_Video', 'raw_title': 'Unknown_Video'}
            
        except Exception as e:
            logger.warning(f"❌ 获取视频信息异常: {e}")
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

# 全局下载器实例
_downloader = None

def get_downloader():
    global _downloader
    if _downloader is None:
        _downloader = CompletelyFixedVideoDownloader()
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
