from flask import Blueprint, render_template, request, jsonify, send_file
import os
import tempfile
from .video_downloader import download_video, get_video_info
import logging
import threading
import time

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bp = Blueprint('main', __name__)

# 存储下载进度的全局字典
download_progress = {}

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/background-test')
def background_test():
    """背景显示测试页面"""
    return render_template('background_test.html')

@bp.route('/video-info', methods=['POST'])
def video_info():
    """视频信息预检测接口"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': '缺少视频URL'}), 400
        
        url = data['url']
        logger.info(f"收到视频信息请求: {url}")
        
        # 调用视频信息获取函数
        try:
            info = get_video_info(url)
            return jsonify({
                'title': info.get('title', ''),
                'duration': info.get('duration', ''),
                'platform': info.get('platform', ''),
                'available': True
            })
        except Exception as e:
            logger.error(f"获取视频信息失败: {str(e)}")
            
            # 分析错误类型
            from .video_downloader import analyze_bilibili_error
            error_analysis = analyze_bilibili_error(str(e))
            
            return jsonify({
                'error': error_analysis.get('user_friendly', str(e)),
                'error_type': error_analysis.get('error_type', 'unknown_error'),
                'fatal': error_analysis.get('fatal', False),
                'available': False
            }), 400
            
    except Exception as e:
        logger.error(f"视频信息接口出错: {str(e)}")
        return jsonify({
            'error': str(e),
            'error_type': 'unknown_error',
            'fatal': False,
            'available': False
        }), 500

@bp.route('/download', methods=['POST'])
def download():
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': '缺少视频URL'}), 400
        
        url = data['url']
        
        # 检测移动端请求 - 增强检测
        user_agent = request.headers.get('User-Agent', '').lower()
        is_mobile = any(mobile in user_agent for mobile in [
            'mobile', 'android', 'iphone', 'ipad', 'ipod', 
            'phone', 'tablet', 'touch', 'mini'
        ])
        
        # 检测设备类型
        device_type = 'mobile' if is_mobile else 'desktop'
        
        logger.info(f"收到下载请求: {url} (设备类型: {device_type}, UA: {user_agent[:50]}...)")
        
        # 生成下载ID
        download_id = str(int(time.time() * 1000))
        
        # 初始化进度
        download_progress[download_id] = {
            'status': 'starting',
            'percent': 0,
            'message': '正在准备下载...',
            'device_type': device_type
        }
        
        # 创建进度回调函数
        def progress_callback(progress_info):
            download_progress[download_id] = {
                'status': progress_info['status'],
                'percent': progress_info.get('percent', 0),
                'message': get_progress_message(progress_info),
                'filename': progress_info.get('filename', ''),
                'speed': progress_info.get('speed', ''),
                'downloaded_mb': progress_info.get('downloaded_mb', 0),
                'error': progress_info.get('error', ''),
                'error_type': progress_info.get('error_type', ''),
                'fatal': progress_info.get('fatal', False)
            }
        
        # 在后台线程中执行下载
        def download_thread():
            try:
                # 创建临时目录
                temp_dir = tempfile.mkdtemp()
                
                # 🔥修复：首先获取视频信息以使用原始标题
                try:
                    logger.info("📝 正在获取视频标题信息...")
                    video_info = get_video_info(url)
                    video_title = video_info.get('title', 'Unknown_Video')
                    logger.info(f"✅ 获取到视频标题: {video_title}")
                    
                    # 创建基于视频标题的输出模板
                    # 直接使用清理后的标题，避免yt-dlp重新处理
                    safe_filename = video_title.replace('/', '_').replace('\\', '_')
                    output_template = os.path.join(temp_dir, f"{safe_filename}.%(ext)s")
                    
                    # 测试文件名是否可以创建
                    test_path = os.path.join(temp_dir, f"{safe_filename}.mp4")
                    try:
                        with open(test_path, 'w', encoding='utf-8') as f:
                            f.write('')
                        os.remove(test_path)
                        logger.info(f"✅ 文件名测试通过: {safe_filename}")
                    except Exception as e:
                        logger.warning(f"⚠️ 文件名测试失败，使用默认模板: {e}")
                        output_template = os.path.join(temp_dir, "%(title)s.%(ext)s")
                        
                except Exception as e:
                    logger.warning(f"⚠️ 获取视频信息失败，使用默认模板: {e}")
                    output_template = os.path.join(temp_dir, "%(title)s.%(ext)s")
                    video_title = 'Unknown_Video'
                
                logger.info(f"📁 使用输出模板: {output_template}")
                
                # 调用下载函数
                file_path = download_video(url, output_template, progress_callback)
                
                # 🔥修复：确保返回的文件使用正确的名称
                if file_path and os.path.exists(file_path):
                    original_filename = os.path.basename(file_path)
                    
                    # 如果下载的文件名不符合预期，重命名它
                    if video_title != 'Unknown_Video' and not original_filename.startswith(video_title):
                        desired_filename = f"{video_title}.mp4"
                        new_file_path = os.path.join(os.path.dirname(file_path), desired_filename)
                        
                        try:
                            if os.path.exists(new_file_path):
                                os.remove(new_file_path)
                            os.rename(file_path, new_file_path)
                            file_path = new_file_path
                            logger.info(f"🔄 文件重命名: {original_filename} -> {desired_filename}")
                        except Exception as e:
                            logger.warning(f"⚠️ 文件重命名失败: {e}")
                
                # 下载完成
                download_progress[download_id]['file_path'] = file_path
                download_progress[download_id]['status'] = 'completed'
                download_progress[download_id]['percent'] = 100
                download_progress[download_id]['message'] = '下载完成'
                
            except Exception as e:
                logger.error(f"下载线程出错: {str(e)}")
                
                # 导入错误分析函数
                from .video_downloader import analyze_bilibili_error
                error_analysis = analyze_bilibili_error(str(e))
                
                download_progress[download_id]['status'] = 'failed'
                download_progress[download_id]['error'] = error_analysis.get('user_friendly', str(e))
                download_progress[download_id]['error_type'] = error_analysis.get('error_type', 'unknown_error')
                download_progress[download_id]['fatal'] = error_analysis.get('fatal', False)
                download_progress[download_id]['message'] = f'下载失败: {error_analysis.get("user_friendly", str(e))}'
        
        # 启动下载线程
        thread = threading.Thread(target=download_thread)
        thread.daemon = True
        thread.start()
        
        # 返回下载ID
        return jsonify({
            'download_id': download_id,
            'message': '下载已开始，请等待...'
        })
        
    except Exception as e:
        logger.error(f"启动下载时出错: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/progress/<download_id>')
def get_progress(download_id):
    """获取下载进度"""
    if download_id in download_progress:
        progress = download_progress[download_id]
        
        # 如果下载完成，提供下载链接
        if progress['status'] == 'completed' and 'file_path' in progress:
            file_path = progress['file_path']
            if os.path.exists(file_path):
                filename = os.path.basename(file_path)
                progress['download_url'] = f'/download-file/{download_id}'
                progress['filename'] = filename
        
        return jsonify(progress)
    else:
        return jsonify({'error': '下载ID不存在'}), 404

@bp.route('/download-file/<download_id>')
def download_file(download_id):
    """三端兼容的文件下载接口 - 彻底修复版"""
    try:
        if download_id not in download_progress:
            logger.warning(f"下载ID不存在: {download_id}")
            return jsonify({'error': '下载ID不存在或已过期'}), 404
            
        progress = download_progress[download_id]
        if 'file_path' not in progress or not os.path.exists(progress['file_path']):
            logger.warning(f"文件不存在: {download_id}")
            return jsonify({'error': '文件不存在或已被清理'}), 404
            
        file_path = progress['file_path']
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        # 获取用户代理，进行详细的设备检测
        user_agent = request.headers.get('User-Agent', '').lower()
        is_mobile = any(mobile in user_agent for mobile in ['mobile', 'android', 'iphone', 'ipad', 'ipod'])
        is_ios = any(ios in user_agent for ios in ['iphone', 'ipad', 'ipod'])
        is_android = 'android' in user_agent
        is_safari = 'safari' in user_agent and 'chrome' not in user_agent
        is_chrome = 'chrome' in user_agent
        is_wechat = 'micromessenger' in user_agent
        
        device_info = f"Mobile={is_mobile}, iOS={is_ios}, Android={is_android}, Safari={is_safari}, WeChat={is_wechat}"
        logger.info(f"📱 文件下载请求: {filename} ({file_size / 1024 / 1024:.2f} MB) - {device_info}")
        
        try:
            # 🔥核心修复：根据设备类型采用不同的文件传输策略
            if is_mobile:
                # 移动端优化传输
                response = send_file(
                    file_path,
                    as_attachment=True,
                    download_name=filename,
                    mimetype='application/octet-stream'  # 通用二进制类型，确保下载而不是播放
                )
                
                # 🔥移动端关键响应头 - 确保浏览器正确处理下载
                response.headers['Content-Type'] = 'application/octet-stream'
                response.headers['Content-Disposition'] = f'attachment; filename="{filename}"; filename*=UTF-8\'\'{filename}'
                response.headers['Content-Length'] = str(file_size)
                response.headers['Accept-Ranges'] = 'bytes'
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response.headers['Pragma'] = 'no-cache'
                response.headers['Expires'] = '0'
                
                # iOS Safari 特殊处理
                if is_ios:
                    response.headers['Content-Type'] = 'video/mp4'  # iOS Safari 可能需要正确的视频类型
                    # 移除强制下载，让Safari以播放方式打开，用户可以选择下载
                    response.headers['Content-Disposition'] = f'inline; filename="{filename}"'
                
                # 微信浏览器特殊处理
                elif is_wechat:
                    response.headers['Content-Type'] = 'video/mp4'
                    response.headers['Content-Disposition'] = f'inline; filename="{filename}"'
                
                # Android Chrome 优化
                elif is_android and is_chrome:
                    response.headers['Content-Type'] = 'application/octet-stream'
                    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
                    # Android Chrome 需要正确的文件大小
                    response.headers['Content-Length'] = str(file_size)
                
                logger.info(f"✅ 移动端({device_info})文件传输开始: {filename}")
                
            else:
                # PC端标准传输
                response = send_file(
                    file_path,
                    as_attachment=True,
                    download_name=filename,
                    mimetype='video/mp4'
                )
                
                # PC端优化响应头
                response.headers['Content-Type'] = 'video/mp4'
                response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
                response.headers['Content-Length'] = str(file_size)
                response.headers['Accept-Ranges'] = 'bytes'
                response.headers['Cache-Control'] = 'public, max-age=0'
                
                logger.info(f"✅ PC端文件传输开始: {filename}")
            
            # 🔥优化：延迟清理，给不同设备足够的下载时间
            def delayed_cleanup():
                # 移动端需要更长的清理延迟
                delay_time = 60 if is_mobile else 30  # 移动端60秒，PC端30秒
                time.sleep(delay_time)
                
                if download_id in download_progress:
                    try:
                        # 清理临时文件
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            logger.info(f"🗑️ 临时文件已删除: {filename}")
                            
                        # 尝试清理临时目录
                        temp_dir = os.path.dirname(file_path)
                        if os.path.exists(temp_dir) and temp_dir != tempfile.gettempdir():
                            try:
                                os.rmdir(temp_dir)
                                logger.info(f"🗑️ 临时目录已删除: {temp_dir}")
                            except OSError:
                                logger.info(f"⚠️ 临时目录非空，跳过删除: {temp_dir}")
                                
                        # 清理进度记录
                        del download_progress[download_id]
                        logger.info(f"🧹 延迟清理完成: {download_id} (延迟{delay_time}秒)")
                        
                    except Exception as e:
                        logger.warning(f"清理文件时出错: {e}")
            
            # 启动延迟清理线程
            cleanup_thread = threading.Thread(target=delayed_cleanup)
            cleanup_thread.daemon = True
            cleanup_thread.start()
            
            # 🔥新增：文件传输完成后的回调日志
            def log_transfer_complete():
                try:
                    logger.info(f"📤 文件传输完成: {filename} -> {device_info}")
                except:
                    pass
            
            # 为响应添加完成回调
            response.call_on_close(log_transfer_complete)
            
            return response
            
        except Exception as file_error:
            logger.error(f"文件传输出错: {file_error}")
            # 🔥备用方案：如果send_file失败，尝试流式传输
            try:
                def generate_file_stream():
                    with open(file_path, 'rb') as f:
                        chunk_size = 8192 if is_mobile else 65536  # 移动端使用较小的块大小
                        while True:
                            chunk = f.read(chunk_size)
                            if not chunk:
                                break
                            yield chunk
                
                from flask import Response
                response = Response(
                    generate_file_stream(),
                    headers={
                        'Content-Type': 'application/octet-stream' if is_mobile else 'video/mp4',
                        'Content-Disposition': f'attachment; filename="{filename}"',
                        'Content-Length': str(file_size),
                        'Accept-Ranges': 'bytes',
                        'Cache-Control': 'no-cache' if is_mobile else 'public, max-age=0'
                    }
                )
                
                logger.info(f"🔄 使用流式传输备用方案: {filename}")
                return response
                
            except Exception as stream_error:
                logger.error(f"流式传输也失败: {stream_error}")
                return jsonify({'error': f'文件传输失败: {str(stream_error)}'}), 500
        
    except Exception as e:
        logger.error(f"下载文件接口出错: {e}")
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500

def get_progress_message(progress_info):
    """根据进度信息生成消息"""
    status = progress_info['status']
    
    if status == 'downloading':
        percent = progress_info.get('percent', 0)
        speed = progress_info.get('speed', '')
        downloaded_mb = progress_info.get('downloaded_mb', 0)
        return f'正在下载... {percent:.1f}% (已下载 {downloaded_mb:.1f}MB) - {speed}'
    elif status == 'finished':
        return '下载完成，正在处理...'
    elif status == 'completed':
        return '下载完成'
    elif status == 'failed':
        return f'下载失败: {progress_info.get("error", "未知错误")}'
    else:
        return '正在准备下载...'

@bp.route('/test')
def test():
    return "Flask 应用运行正常！"