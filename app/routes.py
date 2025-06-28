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

@bp.route('/download', methods=['POST'])
def download():
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': '缺少视频URL'}), 400
        
        url = data['url']
        logger.info(f"收到下载请求: {url}")
        
        # 生成下载ID
        download_id = str(int(time.time() * 1000))
        
        # 初始化进度
        download_progress[download_id] = {
            'status': 'starting',
            'percent': 0,
            'message': '正在准备下载...'
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
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                if 'bilibili.com' in url:
                    output_template = os.path.join(temp_dir, f"bilibili_{timestamp}.%(ext)s")
                else:
                    output_template = os.path.join(temp_dir, f"video_{timestamp}.%(ext)s")
                
                # 调用下载函数
                file_path = download_video(url, output_template, progress_callback)
                
                # 下载完成
                download_progress[download_id]['file_path'] = file_path
                download_progress[download_id]['status'] = 'completed'
                download_progress[download_id]['percent'] = 100
                download_progress[download_id]['message'] = '下载完成！'
                
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
    """下载文件"""
    if download_id in download_progress:
        progress = download_progress[download_id]
        if 'file_path' in progress and os.path.exists(progress['file_path']):
            file_path = progress['file_path']
            filename = os.path.basename(file_path)
            
            # 清理进度记录
            del download_progress[download_id]
            
            return send_file(
                file_path,
                as_attachment=True,
                download_name=filename,
                mimetype='video/mp4'
            )
    
    return jsonify({'error': '文件不存在'}), 404

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
        return '下载完成！'
    elif status == 'failed':
        return f'下载失败: {progress_info.get("error", "未知错误")}'
    else:
        return '正在准备下载...'

@bp.route('/test')
def test():
    return "Flask 应用运行正常！"