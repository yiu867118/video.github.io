
def ultimate_bilibili_download(url: str, output_template: str, progress_callback: Optional[Callable] = None) -> str:
    """终极B站下载函数 - 专为移动端优化，确保100%兼容性"""
    
    # 🔥 URL标准化 - 确保所有端都使用相同的URL格式
    if 'bilibili.com' in url:
        url = url.replace('m.bilibili.com', 'www.bilibili.com')
        url = url.replace('//bilibili.com', '//www.bilibili.com')
        # 移除可能的移动端参数
        if '?' in url:
            base_url = url.split('?')[0]
            url = base_url
    
    logger.info(f"🔧 标准化URL: {url}")
    
    # 创建专用下载目录
    temp_dir = os.path.dirname(output_template)
    download_dir = os.path.join(temp_dir, f"dl_{int(time.time())}")
    os.makedirs(download_dir, exist_ok=True)
    
    # 🔥 终极策略列表 - 从最高质量到最低质量，确保至少有一个成功
    strategies = [
        {
            'name': 'B站桌面端高质量',
            'format': 'bestaudio+bestvideo/best[acodec!=none]/best',
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Referer': 'https://www.bilibili.com/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
            },
            'timeout': 60
        },
        {
            'name': 'B站手机端适配',
            'format': 'best[acodec!=none]/best',
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36',
                'Referer': 'https://www.bilibili.com/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            },
            'timeout': 45
        },
        {
            'name': 'B站平板端适配',
            'format': 'best',
            'headers': {
                'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
                'Referer': 'https://www.bilibili.com/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            },
            'timeout': 45
        },
        {
            'name': 'B站通用策略',
            'format': 'best',
            'headers': None,
            'timeout': 30
        },
        {
            'name': 'B站兜底策略',
            'format': 'worst',
            'headers': None,
            'timeout': 20
        }
    ]
    
    last_error = None
    
    for i, strategy in enumerate(strategies, 1):
        try:
            logger.info(f"🎯 尝试策略 {i}/5: {strategy['name']}")
            
            if progress_callback and i == 1:
                progress_callback({
                    'status': 'downloading',
                    'percent': 50,
                    'message': f'正在尝试下载...'
                })
            
            # 配置下载选项
            ydl_opts = {
                'format': strategy['format'],
                'merge_output_format': 'mp4',
                'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
                'geo_bypass': True,
                'geo_bypass_country': 'CN',
                'nocheckcertificate': True,
                'ignoreerrors': False,
                'no_warnings': True,
                'quiet': True,
                'socket_timeout': strategy['timeout'],
                'retries': 2,
                'fragment_retries': 3,
                'extractaudio': False,
                'audioformat': 'mp3',
                'embed_subs': False,
                'writesubtitles': False,
                'writeautomaticsub': False,
            }
            
            # 添加Headers（如果有）
            if strategy['headers']:
                ydl_opts['http_headers'] = strategy['headers']
            
            # 执行下载
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # 检查下载结果
            files = os.listdir(download_dir)
            video_files = []
            
            for filename in files:
                filepath = os.path.join(download_dir, filename)
                if os.path.isfile(filepath):
                    size = os.path.getsize(filepath)
                    if filename.lower().endswith(('.mp4', '.webm', '.mkv', '.flv', '.avi')) and size > 1024:
                        video_files.append((filename, size, filepath))
            
            if video_files:
                # 选择最大的文件
                video_files.sort(key=lambda x: x[1], reverse=True)
                filename, size, filepath = video_files[0]
                
                # 移动到最终位置
                final_path = os.path.join(temp_dir, filename)
                if os.path.exists(final_path):
                    os.remove(final_path)
                
                import shutil
                shutil.move(filepath, final_path)
                
                logger.info(f"🎉 下载成功！策略: {strategy['name']}")
                logger.info(f"📁 文件: {filename} ({size/1024/1024:.2f} MB)")
                
                if progress_callback:
                    progress_callback({
                        'status': 'completed',
                        'percent': 100,
                        'filename': filename,
                        'file_size_mb': size / 1024 / 1024,
                        'strategy': strategy['name'],
                        'final': True
                    })
                
                # 清理临时目录
                try:
                    shutil.rmtree(download_dir)
                except:
                    pass
                
                return final_path
            
            logger.info(f"⚠️ 策略 {i} 未产生有效文件")
            
        except Exception as e:
            last_error = str(e)
            logger.info(f"⚠️ 策略 {i} 失败: {last_error[:100]}...")
            continue
    
    # 清理临时目录
    try:
        import shutil
        shutil.rmtree(download_dir)
    except:
        pass
    
    # 所有策略都失败
    error_msg = f"所有下载策略都失败。最后错误: {last_error}" if last_error else "所有下载策略都失败"
    logger.error(f"💀 {error_msg}")
    raise Exception("视频下载失败，请检查网络连接或尝试其他视频")
