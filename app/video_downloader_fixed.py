# 这个文件需要替换原来的video_downloader.py
# 为了避免破坏原文件，这里先创建一个新版本，测试无误后再替换

# 保留所有import和类定义，只修复错误分析函数

def analyze_bilibili_error(error_msg: str) -> Dict[str, str]:
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

# 这是修复后的函数，可以直接替换原文件中的同名函数
