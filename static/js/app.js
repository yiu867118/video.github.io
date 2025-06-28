/**
 * 文萍专属视频下载器 - 多平台增强版 v2.7 (移动设备传输优化版)
 * 支持实时进度显示、多平台下载、智能错误处理、付费内容识别
 * 修复：进度条回退、误导性高进度、致命错误重试、99%卡顿、移动设备传输失败等问题
 * 新增：移动设备文件传输优化，智能重试机制，延迟清理，确保手机平板下载成功
 * 特色：PC端高效下载，移动端优化传输，智能音频修复，完美跨平台兼容
 * Created with ❤️ by 一慧
 */

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 === 🐻🐻专属视频下载器 - 多平台增强版 v2.7 启动 ===');
    
    // 初始化移动设备优化
    initMobileOptimizations();
    
    // 立即初始化主题管理器
    if (typeof themeManager !== 'undefined') {
        themeManager.init();
        console.log('🎨 主题管理器已初始化');
    }
    
    // 核心元素获取
    const elements = {
        downloadButton: document.getElementById('downloadButton'),
        videoUrl: document.getElementById('videoUrl'),
        progressContainer: document.getElementById('progressContainer'),
        statusMessage: document.getElementById('statusMessage'),
        downloadProgress: document.getElementById('downloadProgress'),
        progressPercentage: document.querySelector('.progress-percentage'),
        downloadSpeed: document.getElementById('downloadSpeed'),
        downloadSize: document.getElementById('downloadSize'),
        progressStatusText: document.getElementById('progressStatusText'),
        downloadResult: document.getElementById('downloadResult'),
        downloadFileBtn: document.getElementById('downloadFileBtn'),
        loadingOverlay: document.getElementById('loadingOverlay'),
        successAnimation: document.getElementById('successAnimation'),
        platformIndicator: document.getElementById('platformIndicator'), // 平台指示器
        themeToggle: document.getElementById('themeToggle') // 主题切换按钮
    };
    
    // 元素存在性检查
    console.log('🔍 === 元素检查结果 ===', {
        downloadButton: !!elements.downloadButton,
        videoUrl: !!elements.videoUrl,
        statusMessage: !!elements.statusMessage,
        progressContainer: !!elements.progressContainer,
        downloadProgress: !!elements.downloadProgress,
        progressPercentage: !!elements.progressPercentage,
        downloadSpeed: !!elements.downloadSpeed,
        downloadSize: !!elements.downloadSize,
        progressStatusText: !!elements.progressStatusText,
        themeToggle: !!elements.themeToggle // 
    });
    
    if (!elements.downloadButton || !elements.videoUrl) {
        console.error('❌ 关键元素缺失，页面可能有问题');
        return;
    }

    // 全局状态管理 - 修复版
    const state = {
        isDownloading: false,
        currentDownloadId: null,
        progressInterval: null,
        downloadStartTime: null,
        lastProgressData: null,
        retryCount: 0,
        maxRetries: 3, // 最大重试次数
        maxProgressPolls: 300, // 减少最大轮询次数（5分钟）
        currentPollCount: 0,
        lastProgressTime: null,
        progressStuckThreshold: 30000, // 30秒
        isProgressStuck: false,
        currentPlatform: 'unknown',
        fatalErrorOccurred: false,
        // 新增状态控制
        isRetrying: false, // 是否正在重试
        lastRetryTime: 0, // 最后重试时间
        retryInterval: 5000, // 重试间隔5秒
        abortController: null, // 用于取消请求
        themeMode: localStorage.getItem('theme-preference') || 'system' // 'system', 'light', 'dark'
    };
    
    // 支持的平台配置
    const supportedPlatforms = {
        bilibili: {
            name: 'Bilibili',
            icon: '📺',
            patterns: ['bilibili.com', 'b23.tv', 'acg.tv'],
            color: '#fb7299',
            specialTypes: {
                course: { patterns: ['/cheese/', '课程'], warning: '检测到课程链接，请确保已购买相关内容' },
                bangumi: { patterns: ['/bangumi/'], warning: '检测到番剧链接，部分内容可能需要大会员' },
                live: { patterns: ['/live/'], warning: '检测到直播链接，直播内容可能无法下载' }
            }
        },
        youtube: {
            name: 'YouTube',
            icon: '🎥',
            patterns: ['youtube.com', 'youtu.be'],
            color: '#ff0000',
            specialTypes: {
                shorts: { patterns: ['/shorts/'], warning: '检测到Shorts短视频' },
                live: { patterns: ['/live/', 'live_stream'], warning: '检测到直播内容' }
            }
        },
        douyin: {
            name: '抖音',
            icon: '🎵',
            patterns: ['douyin.com', 'iesdouyin.com'],
            color: '#fe2c55',
            specialTypes: {}
        },
        kuaishou: {
            name: '快手',
            icon: '⚡',
            patterns: ['kuaishou.com', 'gifshow.com'],
            color: '#ff6600',
            specialTypes: {}
        },
        weibo: {
            name: '微博',
            icon: '🐦',
            patterns: ['weibo.com', 'weibo.cn'],
            color: '#e6162d',
            specialTypes: {}
        },
        xiaohongshu: {
            name: '小红书',
            icon: '📖',
            patterns: ['xiaohongshu.com', 'xhslink.com'],
            color: '#ff2442',
            specialTypes: {}
        },
        xigua: {
            name: '西瓜视频',
            icon: '🍉',
            patterns: ['ixigua.com'],
            color: '#20b955',
            specialTypes: {}
        },
        twitter: {
            name: 'Twitter/X',
            icon: '🐦',
            patterns: ['twitter.com', 'x.com'],
            color: '#1da1f2',
            specialTypes: {}
        },
        instagram: {
            name: 'Instagram',
            icon: '📷',
            patterns: ['instagram.com'],
            color: '#e4405f',
            specialTypes: {}
        },
        tiktok: {
            name: 'TikTok',
            icon: '🎭',
            patterns: ['tiktok.com'],
            color: '#ff0050',
            specialTypes: {}
        }
    };

    // 消息类型配置
    const messageTypes = {
        info: {
            icon: 'fas fa-info-circle',
            class: 'status-info',
            color: '#007bff'
        },
        success: {
            icon: 'fas fa-check-circle',
            class: 'status-success',
            color: '#28a745'
        },
        error: {
            icon: 'fas fa-exclamation-triangle',
            class: 'status-error',
            color: '#dc3545'
        },
        warning: {
            icon: 'fas fa-exclamation-triangle',
            class: 'status-warning',
            color: '#ffc107'
        },
        downloading: {
            icon: 'fas fa-download',
            class: 'status-downloading',
            color: '#17a2b8'
        },
        blocked: {
            icon: 'fas fa-lock',
            class: 'status-error',
            color: '#dc3545'
        }
    };

    // 按钮状态配置
    const buttonStates = {
        normal: {
            icon: 'fas fa-download',
            text: '开始下载',
            class: 'btn-normal',
            disabled: false
        },
        loading: {
            icon: 'fas fa-spinner fa-spin',
            text: '准备中...',
            class: 'btn-loading',
            disabled: true
        },
        analyzing: {
            icon: 'fas fa-search fa-spin',
            text: '分析中...',
            class: 'btn-analyzing',
            disabled: true
        },
        downloading: {
            icon: 'fas fa-download fa-spin',
            text: '下载中...',
            class: 'btn-downloading',
            disabled: true
        },
        processing: {
            icon: 'fas fa-cog fa-spin',
            text: '处理中...',
            class: 'btn-processing',
            disabled: true
        },
        completed: {
            icon: 'fas fa-check',
            text: '完成',
            class: 'btn-completed',
            disabled: true
        },
        error: {
            icon: 'fas fa-redo',
            text: '重试',
            class: 'btn-error',
            disabled: false
        },
        blocked: {
            icon: 'fas fa-lock',
            text: '内容受限',
            class: 'btn-error',
            disabled: true
        }
    };

    // 错误类型识别 - 增强版
    const errorPatterns = {
        payment_required: [
            '付费内容', '需要购买', 'purchase', 'payment required',
            '会员专享', '大会员', 'vip only', 'premium content',
            'premium video', '充电专属', 'bp不足', '硬币不足',
            '需要充电', '专栏付费', 'course access'
        ],
        auth_required: [
            '需要登录', 'authentication', 'login required', 
            '未登录', 'not logged in', 'cookies', '登录状态',
            '身份验证', 'authentication failed'
        ],
        region_blocked: [
            '地区限制', 'region', '不可观看', 'geo-blocked',
            'area limit', '当前地区', 'region blocked',
            'not available in your region'
        ],
        access_denied: [
            '私有视频', 'private', '无法访问', 'access denied',
            '已删除', 'deleted', 'unavailable', 'video unavailable',
            'removed', 'not found'
        ],
        network_error: [
            'network', 'timeout', '网络', '超时', 'connection',
            'network error', 'connection failed', 'request timeout'
        ],
        age_restricted: [
            'age restricted', '年龄限制', 'sign in to confirm',
            'age verification', '需要年龄验证'
        ],
        live_content: [
            'live stream', '直播', 'is live', 'currently live',
            'live broadcast', '正在直播'
        ]
    };
    
    // 主题管理功能 - 修复版
    const themeManager = {
        init() {
            this.applyTheme();
            this.setupThemeToggle();
            
            // 监听系统主题变化
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
                if (state.themeMode === 'system') {
                    this.applyTheme();
                }
            });
        },
        
        applyTheme() {
            const root = document.documentElement;
            const body = document.body;
            
            // 移除现有主题类
            root.classList.remove('theme-light', 'theme-dark', 'theme-system');
            body.classList.remove('theme-light', 'theme-dark', 'theme-system');
            
            // 应用新主题
            let actualTheme = state.themeMode;
            
            // 如果是系统模式，检测系统主题
            if (state.themeMode === 'system') {
                actualTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
            }
            
            // 应用主题类
            root.classList.add(`theme-${actualTheme}`);
            body.classList.add(`theme-${actualTheme}`);
            
            // 设置CSS自定义属性
            this.setCSSProperties(actualTheme);
            
            // 设置colorScheme
            root.style.colorScheme = actualTheme;
            
            this.updateToggleButton();
            console.log(`🎨 主题已切换到: ${state.themeMode} (实际: ${actualTheme})`);
        },
        
        setCSSProperties(theme) {
            const root = document.documentElement;
            
            if (theme === 'dark') {
                // 深色模式颜色
                root.style.setProperty('--primary-rgb', '74, 144, 226');
                root.style.setProperty('--secondary-rgb', '108, 117, 125');
                root.style.setProperty('--success-rgb', '40, 167, 69');
                root.style.setProperty('--danger-rgb', '220, 53, 69');
                root.style.setProperty('--warning-rgb', '255, 193, 7');
                root.style.setProperty('--info-rgb', '23, 162, 184');
                root.style.setProperty('--light-rgb', '248, 249, 250');
                root.style.setProperty('--dark-rgb', '52, 58, 64');
                
                // 背景和表面
                root.style.setProperty('--background-rgb', '18, 18, 18');
                root.style.setProperty('--surface-rgb', '33, 37, 41');
                root.style.setProperty('--surface-alt-rgb', '52, 58, 64');
                
                // 文字颜色
                root.style.setProperty('--text-rgb', '248, 249, 250');
                root.style.setProperty('--text-muted-rgb', '173, 181, 189');
                
                // 边框
                root.style.setProperty('--border-rgb', '73, 80, 87');
                
            } else {
                // 浅色模式颜色
                root.style.setProperty('--primary-rgb', '13, 110, 253');
                root.style.setProperty('--secondary-rgb', '108, 117, 125');
                root.style.setProperty('--success-rgb', '25, 135, 84');
                root.style.setProperty('--danger-rgb', '220, 53, 69');
                root.style.setProperty('--warning-rgb', '255, 193, 7');
                root.style.setProperty('--info-rgb', '13, 202, 240');
                root.style.setProperty('--light-rgb', '248, 249, 250');
                root.style.setProperty('--dark-rgb', '33, 37, 41');
                
                // 背景和表面
                root.style.setProperty('--background-rgb', '255, 255, 255');
                root.style.setProperty('--surface-rgb', '248, 249, 250');
                root.style.setProperty('--surface-alt-rgb', '233, 236, 239');
                
                // 文字颜色
                root.style.setProperty('--text-rgb', '33, 37, 41');
                root.style.setProperty('--text-muted-rgb', '108, 117, 125');
                
                // 边框
                root.style.setProperty('--border-rgb', '222, 226, 230');
            }
        },
        
        updateToggleButton() {
            if (!elements.themeToggle) return;
            
            const icons = {
                system: '🌐',
                light: '☀️',
                dark: '🌙'
            };
            
            const texts = {
                system: '跟随系统',
                light: '浅色模式',
                dark: '深色模式'
            };
            
            elements.themeToggle.innerHTML = `
                <span class="theme-icon">${icons[state.themeMode]}</span>
                <span class="theme-text">${texts[state.themeMode]}</span>
            `;
            
            elements.themeToggle.setAttribute('data-theme', state.themeMode);
        },
        
        setupThemeToggle() {
            if (!elements.themeToggle) {
                console.warn('主题切换按钮未找到');
                return;
            }
            
            // 移除所有现有事件监听器
            const newToggle = elements.themeToggle.cloneNode(true);
            elements.themeToggle.parentNode.replaceChild(newToggle, elements.themeToggle);
            elements.themeToggle = newToggle;
            
            // 确保按钮可点击
            elements.themeToggle.style.pointerEvents = 'auto';
            elements.themeToggle.style.cursor = 'pointer';
            elements.themeToggle.style.userSelect = 'none';
            elements.themeToggle.style.zIndex = '10000';
            
            // 添加点击事件 - 多重保障
            const handleThemeClick = (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('🎨 主题切换按钮被点击');
                this.cycleTheme();
            };
            
            // PC端点击
            elements.themeToggle.addEventListener('click', handleThemeClick, { passive: false });
            
            // 移动端触摸支持
            elements.themeToggle.addEventListener('touchstart', (e) => {
                e.preventDefault();
                elements.themeToggle.style.transform = 'scale(0.95)';
            }, { passive: false });
            
            elements.themeToggle.addEventListener('touchend', (e) => {
                e.preventDefault();
                e.stopPropagation();
                elements.themeToggle.style.transform = 'scale(1)';
                console.log('🎨 移动端主题切换按钮被触摸');
                this.cycleTheme();
            }, { passive: false });
            
            // 键盘快捷键
            document.addEventListener('keydown', (e) => {
                if (e.ctrlKey && e.shiftKey && e.key === 'T') {
                    e.preventDefault();
                    this.cycleTheme();
                }
            });
            
            console.log('✅ 主题切换按钮事件已设置');
        },
        
        cycleTheme() {
            const modes = ['system', 'light', 'dark'];
            const currentIndex = modes.indexOf(state.themeMode);
            const nextIndex = (currentIndex + 1) % modes.length;
            
            state.themeMode = modes[nextIndex];
            localStorage.setItem('theme-preference', state.themeMode);
            
            this.applyTheme();
            
            // 显示切换提示 - 短时间显示，避免干扰
            this.showThemeChangeToast();
        },
        
        showThemeChangeToast() {
            // 移除可能存在的旧提示
            const existingToast = document.querySelector('.theme-toast');
            if (existingToast) {
                existingToast.remove();
            }
            
            // 创建新的提示元素
            const toast = document.createElement('div');
            toast.className = 'theme-toast';
            toast.innerHTML = `
                <span class="toast-icon">${this.getThemeIcon()}</span>
                <span class="toast-text">${this.getThemeDisplayName()}</span>
            `;
            
            // 添加样式
            Object.assign(toast.style, {
                position: 'fixed',
                top: '80px',
                right: '20px',
                background: 'rgba(var(--surface-rgb), 0.95)',
                color: 'rgba(var(--text-rgb), 0.9)',
                border: '1px solid rgba(var(--border-rgb), 0.3)',
                borderRadius: '12px',
                padding: '12px 16px',
                fontSize: '14px',
                fontWeight: '500',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                zIndex: '10000',
                backdropFilter: 'blur(12px)',
                boxShadow: '0 4px 16px rgba(0, 0, 0, 0.1)',
                transform: 'translateX(100%)',
                transition: 'transform 0.3s ease',
                pointerEvents: 'none'
            });
            
            document.body.appendChild(toast);
            
            // 动画显示
            requestAnimationFrame(() => {
                toast.style.transform = 'translateX(0)';
            });
            
            // 自动隐藏
            setTimeout(() => {
                toast.style.transform = 'translateX(100%)';
                setTimeout(() => {
                    if (toast.parentNode) {
                        toast.remove();
                    }
                }, 300);
            }, 2000);
        },
        
        getThemeIcon() {
            const icons = {
                system: '🌐',
                light: '☀️',
                dark: '🌙'
            };
            return icons[state.themeMode];
        },
        
        getThemeDisplayName() {
            const names = {
                system: '跟随系统主题',
                light: '浅色模式',
                dark: '深色模式'
            };
            return names[state.themeMode];
        }
    };

    // ========================================
    // 核心工具函数 - 首先定义
    // ========================================

    /**
     * 检测视频平台
     */
    function detectPlatform(url) {
        if (!url) return 'unknown';
        
        const urlLower = url.toLowerCase();
        
        for (const [platformKey, platform] of Object.entries(supportedPlatforms)) {
            if (platform.patterns.some(pattern => urlLower.includes(pattern))) {
                return platformKey;
            }
        }
        
        return 'unknown';
    }

    /**
     * 识别错误类型
     */
    function identifyErrorType(errorMessage) {
        const message = errorMessage.toLowerCase();
        
        for (const [type, patterns] of Object.entries(errorPatterns)) {
            if (patterns.some(pattern => message.includes(pattern.toLowerCase()))) {
                return type;
            }
        }
        
        return 'unknown';
    }

    /**
     * 显示状态消息
     */
    function showMessage(message, type = 'info') {
        if (!elements.statusMessage) {
            console.error('❌ statusMessage 元素不存在');
            return;
        }
        
        const messageConfig = messageTypes[type] || messageTypes.info;
        
        elements.statusMessage.innerHTML = `
            <div class="status-icon">
                <i class="${messageConfig.icon}"></i>
            </div>
            <div class="status-content">
                <div class="status-text">${message}</div>
            </div>
        `;
        
        elements.statusMessage.className = `status-message ${messageConfig.class}`;
        elements.statusMessage.style.display = 'block';
        elements.statusMessage.classList.add('visible');
        
        // 移动端专用处理
        if (type === 'error') {
            showMobileError(message);
        } else if (type === 'success') {
            showMobileStatus(message, 'success', 5000);
        }
        
        console.log(`💬 状态消息: [${type.toUpperCase()}] ${message}`);
    }

    /**
     * 隐藏状态消息
     */
    function hideMessage() {
        if (elements.statusMessage) {
            elements.statusMessage.classList.remove('visible');
            setTimeout(() => {
                if (elements.statusMessage) {
                    elements.statusMessage.style.display = 'none';
                }
            }, 300);
            console.log('💬 状态消息已隐藏');
        }
    }

    /**
     * 设置按钮状态
     */
    function setButtonState(btnState, customText = null) {
        if (!elements.downloadButton) return;
        
        const stateConfig = buttonStates[btnState] || buttonStates.normal;
        
        elements.downloadButton.disabled = stateConfig.disabled;
        elements.downloadButton.className = `download-btn ${stateConfig.class}`;
        
        const btnIcon = elements.downloadButton.querySelector('.btn-icon i');
        const btnText = elements.downloadButton.querySelector('.btn-text');
        
        if (btnIcon) {
            btnIcon.className = stateConfig.icon;
        }
        
        if (btnText) {
            btnText.textContent = customText || stateConfig.text;
        }
        
        console.log(`🔘 按钮状态: ${btnState} - ${customText || stateConfig.text}`);
    }

    /**
     * 更新进度条 - 终极防回退版
     */
    function updateProgress(percent, message, allowReset = false) {
        // 如果是致命错误状态，除非明确允许重置，否则禁止任何进度更新
        if (state.fatalErrorOccurred && !allowReset) {
            console.log('💀 致命错误状态下禁止进度更新，保持当前状态');
            return;
        }
        
        const safePercent = Math.max(0, Math.min(100, percent));
        
        // 获取当前进度，防止回退
        const currentProgress = elements.downloadProgress ? elements.downloadProgress.value : 0;
        
        // 只有在明确允许重置（如非致命错误重试）或进度增加时才更新
        let finalPercent;
        if (allowReset) {
            finalPercent = safePercent;
        } else {
            finalPercent = Math.max(currentProgress, safePercent); // 确保进度只增不减
        }
        
        if (elements.downloadProgress) {
            elements.downloadProgress.value = finalPercent;
        }
        
        if (elements.progressPercentage) {
            elements.progressPercentage.textContent = `${Math.round(finalPercent)}%`;
        }
        
        if (elements.progressStatusText) {
            elements.progressStatusText.textContent = message || '';
        }
        
        // 移动端专用进度显示
        updateMobileProgress(finalPercent, message);
        
        // 只在进度真正变化时记录日志
        if (finalPercent !== currentProgress) {
            console.log(`📊 进度更新: ${currentProgress.toFixed(1)}% → ${finalPercent.toFixed(1)}% - ${message}`);
        }
    }

    /**
     * 更新进度详情
     */
    function updateProgressDetails(speed, size) {
        if (elements.downloadSpeed) {
            elements.downloadSpeed.textContent = speed || '等待中...';
        }
        
        if (elements.downloadSize) {
            elements.downloadSize.textContent = size || '0 MB';
        }
    }

    /**
     * 完全重置所有状态 - 终极修复版
     */
    function completeReset() {
        console.log('🧹 === 执行完全状态重置 ===');
        
        // 取消所有进行中的请求
        if (state.abortController) {
            state.abortController.abort();
            state.abortController = null;
        }
        
        // 停止所有定时器
        stopProgressPolling();
        
        // 记录致命错误状态
        const wasFatalError = state.fatalErrorOccurred;
        
        // 重置所有状态
        Object.assign(state, {
            isDownloading: false,
            currentDownloadId: null,
            downloadStartTime: null,
            lastProgressData: null,
            retryCount: 0,
            currentPollCount: 0,
            lastProgressTime: null,
            isProgressStuck: false,
            fatalErrorOccurred: false,
            isRetrying: false,
            lastRetryTime: 0,
            abortController: null
        });
        
        // 重置UI
        setButtonState('normal');
        hideMessage();
        hideProgressContainer();
        
        // 只在非致命错误时重置进度条
        if (!wasFatalError) {
            updateProgress(0, '', true); // 允许重置
            updateProgressDetails('等待中...', '0 MB');
        } else {
            // 致命错误情况下，保持进度条但清空详情
            updateProgressDetails('已停止', '');
            console.log('💀 致命错误状态下保持进度条显示');
        }
        
        console.log('✅ 完全状态重置完成');
    }

    // ========================================
    // 页面初始化相关函数
    // ========================================
    
    /**
     * 初始化应用程序
     */
    function initializeApp() {
        console.log('🎯 === 初始化应用程序 ===');
        
        // 添加页面加载动画
        document.body.classList.add('page-loaded');

        // 初始化主题管理
        themeManager.init();
        
        // 预加载关键资源
        preloadCriticalElements();
        
        // 设置输入框智能提示
        setupInputValidation();
        
        // 设置性能监控
        setupPerformanceMonitoring();
        
        // 设置用户体验优化
        setupUXEnhancements();
        
        // 初始化平台指示器
        initializePlatformIndicator();
        
        // 移动设备优化初始化
        initMobileOptimizations();
        
        console.log('✅ 应用程序初始化完成');
    }
    
    /**
     * 预加载关键元素
     */
    function preloadCriticalElements() {
        const criticalElements = [
            '#downloadButton',
            '#videoUrl',
            '#progressContainer',
            '#statusMessage'
        ];
        
        criticalElements.forEach(selector => {
            const element = document.querySelector(selector);
            if (element) {
                element.style.willChange = 'transform, opacity';
            }
        });
        
        console.log('🔧 关键元素预加载完成');
    }
    
    /**
     * 初始化平台指示器
     */
    function initializePlatformIndicator() {
        if (elements.platformIndicator) {
            elements.platformIndicator.innerHTML = `
                <div class="platform-info">
                    <span class="platform-icon">🌐</span>
                    <span class="platform-name">支持多平台</span>
                </div>
            `;
        }
    }
    
    /**
     * 设置输入框验证
     */
    function setupInputValidation() {
        const videoUrlInput = document.getElementById('videoUrl');
        if (videoUrlInput) {
            // 粘贴事件监听
            videoUrlInput.addEventListener('paste', function(e) {
                setTimeout(() => {
                    const url = this.value.trim();
                    validateAndHighlightUrl(url, this);
                }, 100);
            });
            
            // 输入事件监听
            videoUrlInput.addEventListener('input', function() {
                const url = this.value.trim();
                validateAndHighlightUrl(url, this);
            });
            
            // 回车键快捷下载
            videoUrlInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter' && this.value.trim() && !state.isDownloading) {
                    e.preventDefault();
                    elements.downloadButton.click();
                }
            });
            
            console.log('🔧 输入框验证设置完成');
        }
    }

    /**
     * 验证并高亮URL
     */
    function validateAndHighlightUrl(url, inputElement) {
        const platform = detectPlatform(url);
        state.currentPlatform = platform;
        
        if (platform !== 'unknown') {
            inputElement.classList.add('valid-url');
            
            const platformConfig = supportedPlatforms[platform];
            console.log(`✅ 检测到有效的${platformConfig.name}链接`);
            
            // 更新平台指示器
            updatePlatformIndicator(platform);
            
            // 检查特殊类型链接
            checkSpecialLinkTypes(url, platform);
        } else {
            inputElement.classList.remove('valid-url');
            resetPlatformIndicator();
            
            if (url) {
                console.log('⚠️ 链接格式可能不正确或不支持该平台');
                showMessage('链接格式可能不正确，请检查是否为支持的平台', 'warning');
            }
        }
    }
    
    /**
     * 更新平台指示器
     */
    function updatePlatformIndicator(platform) {
        if (!elements.platformIndicator) return;
        
        const platformConfig = supportedPlatforms[platform];
        if (platformConfig) {
            elements.platformIndicator.innerHTML = `
                <div class="platform-info active" style="border-color: ${platformConfig.color}">
                    <span class="platform-icon">${platformConfig.icon}</span>
                    <span class="platform-name">${platformConfig.name}</span>
                </div>
            `;
        }
    }
    
    /**
     * 重置平台指示器
     */
    function resetPlatformIndicator() {
        if (elements.platformIndicator) {
            elements.platformIndicator.innerHTML = `
                <div class="platform-info">
                    <span class="platform-icon">🌐</span>
                    <span class="platform-name">支持多平台</span>
                </div>
            `;
        }
    }
    
    /**
     * 检查特殊链接类型
     */
    function checkSpecialLinkTypes(url, platform) {
        const platformConfig = supportedPlatforms[platform];
        if (!platformConfig.specialTypes) return;
        
        for (const [type, config] of Object.entries(platformConfig.specialTypes)) {
            if (config.patterns.some(pattern => url.includes(pattern))) {
                showMessage(config.warning, 'warning');
                break;
            }
        }
    }
    
    /**
     * 设置性能监控
     */
    function setupPerformanceMonitoring() {
        // 页面加载完成监控
        window.addEventListener('load', function() {
            if (window.performance && window.performance.timing) {
                const loadTime = window.performance.timing.loadEventEnd - window.performance.timing.navigationStart;
                console.log(`📊 页面加载时间: ${loadTime}ms`);
                
                if (loadTime > 3000) {
                    console.warn('⚠️ 页面加载时间较长，可能影响用户体验');
                }
            }
        });
        
        // 内存使用监控
        if (window.performance && window.performance.memory) {
            setInterval(() => {
                const memory = window.performance.memory;
                const usedMB = Math.round(memory.usedJSHeapSize / 1048576);
                const totalMB = Math.round(memory.totalJSHeapSize / 1048576);
                
                if (usedMB > 100) {
                    console.warn(`🧠 内存使用较高: ${usedMB}MB / ${totalMB}MB`);
                }
            }, 30000);
        }
        
        console.log('🔧 性能监控设置完成');
    }

    /**
     * 设置用户体验优化
     */
    function setupUXEnhancements() {
        // 添加键盘快捷键
        document.addEventListener('keydown', function(e) {
            // Ctrl+Enter 快速下载
            if (e.ctrlKey && e.key === 'Enter' && !state.isDownloading) {
                const url = elements.videoUrl.value.trim();
                if (url) {
                    elements.downloadButton.click();
                }
            }
            
            // Esc键取消下载
            if (e.key === 'Escape' && state.isDownloading) {
                if (confirm('确定要取消当前下载吗？')) {
                    cancelDownload();
                }
            }
        });

        // 添加拖拽支持 - 支持多平台
        elements.videoUrl.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.classList.add('drag-over');
        });

        elements.videoUrl.addEventListener('dragleave', function(e) {
            e.preventDefault();
            this.classList.remove('drag-over');
        });

        elements.videoUrl.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('drag-over');
            
            const text = e.dataTransfer.getData('text');
            const platform = detectPlatform(text);
            
            if (platform !== 'unknown') {
                this.value = text;
                validateAndHighlightUrl(text, this);
            } else {
                showMessage('拖入的链接不是支持的平台', 'warning');
            }
        });

        console.log('🔧 用户体验优化设置完成');
    }

    // ========================================
    // 主要功能函数 - 修复版
    // ========================================

    /**
     * 重置状态准备新下载 - 修复版
     */
    function resetStateForNewDownload() {
        console.log('🔄 重置状态准备新下载');
        
        // 如果正在下载，先完全停止
        if (state.isDownloading) {
            completeReset();
        }
        
        // 重置关键状态
        state.retryCount = 0;
        state.currentPollCount = 0;
        state.lastProgressTime = null;
        state.isProgressStuck = false;
        state.lastProgressData = null;
        state.fatalErrorOccurred = false;
        state.isRetrying = false;
        state.lastRetryTime = Date.now();
        
        // 创建新的AbortController
        state.abortController = new AbortController();
    }

    /**
     * 带超时的fetch请求 - 修复版
     */
    async function fetchWithTimeout(url, options, timeout = 15000) {
        // 使用全局AbortController
        const controller = state.abortController || new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);
        
        try {
            const response = await fetch(url, {
                ...options,
                signal: controller.signal
            });
            clearTimeout(timeoutId);
            return response;
        } catch (error) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error('请求被取消或超时');
            }
            throw error;
        }
    }

    /**
     * 模拟进度更新 - 防致命错误版
     */
    async function simulateProgress(targetPercent, duration, message) {
        // 如果已经是致命错误状态，不执行任何进度模拟
        if (state.fatalErrorOccurred) {
            console.log('💀 致命错误状态，跳过进度模拟');
            return;
        }
        
        const currentPercent = elements.downloadProgress ? elements.downloadProgress.value : 0;
        const steps = Math.max(1, Math.floor(duration / 50));
        const increment = (targetPercent - currentPercent) / steps;
        
        for (let i = 0; i < steps; i++) {
            // 检查是否已取消下载或发生致命错误
            if (!state.isDownloading || state.fatalErrorOccurred) {
                console.log('💀 下载已停止或发生致命错误，停止进度模拟');
                break;
            }
            
            const newPercent = currentPercent + (increment * (i + 1));
            updateProgress(Math.min(newPercent, targetPercent), message);
            await new Promise(resolve => setTimeout(resolve, 50));
        }
    }

    /**
     * 显示进度容器
     */
    function showProgressContainer() {
        if (elements.progressContainer) {
            elements.progressContainer.style.display = 'block';
            elements.progressContainer.classList.add('visible');
            console.log('📊 进度容器已显示');
        }
    }

    /**
     * 隐藏进度容器
     */
    function hideProgressContainer() {
        if (elements.progressContainer) {
            elements.progressContainer.classList.remove('visible');
            setTimeout(() => {
                if (elements.progressContainer) {
                    elements.progressContainer.style.display = 'none';
                }
            }, 300);
            console.log('📊 进度容器已隐藏');
        }
    }

    /**
     * 停止进度轮询 - 修复版
     */
    function stopProgressPolling() {
        if (state.progressInterval) {
            clearInterval(state.progressInterval);
            state.progressInterval = null;
            console.log('🔄 进度轮询已停止');
        }
    }

    /**
     * 预检测URL可能的问题 - 避免误导性进度
     */
    async function preCheckUrl(url) {
        console.log('🔍 开始预检测URL:', url);
        
        try {
            // 尝试获取视频信息，如果立即失败说明是致命错误
            const response = await fetchWithTimeout('/video-info', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: url })
            }, 10000); // 10秒超时
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ 
                    error: `预检测失败: ${response.status}` 
                }));
                
                // 分析错误类型
                const errorType = identifyErrorType(errorData.error || '');
                const fatalErrors = ['payment_required', 'auth_required', 'region_blocked', 'access_denied', 'age_restricted', 'live_content'];
                
                if (fatalErrors.includes(errorType) || fatalErrors.includes(errorData.error_type) || errorData.fatal) {
                    return {
                        isFatal: true,
                        errorType: errorData.error_type || errorType,
                        errorMessage: errorData.error || '预检测发现问题',
                        fatal: errorData.fatal
                    };
                }
            }
            
            const result = await response.json();
            if (result.error) {
                const errorType = identifyErrorType(result.error);
                const fatalErrors = ['payment_required', 'auth_required', 'region_blocked', 'access_denied', 'age_restricted', 'live_content'];
                
                if (fatalErrors.includes(errorType) || fatalErrors.includes(result.error_type) || result.fatal) {
                    return {
                        isFatal: true,
                        errorType: result.error_type || errorType,
                        errorMessage: result.error,
                        fatal: result.fatal
                    };
                }
            }
            
            console.log('✅ 预检测通过');
            return { isFatal: false };
            
        } catch (error) {
            console.log('⚠️ 预检测异常，继续正常流程:', error.message);
            return { isFatal: false }; // 预检测失败不阻止正常流程
        }
    }

    // 开始下载流程 - 修复版
    async function startDownloadProcess(url) {
        console.log('🚀 === 开始下载流程 ===');
        
        try {
            // 检查是否已在下载中
            if (state.isDownloading) {
                console.log('⚠️ 已有下载任务进行中，跳过新请求');
                return;
            }
            
            // 设置初始状态
            state.isDownloading = true;
            state.downloadStartTime = Date.now();
            
            const platform = detectPlatform(url);
            const platformName = supportedPlatforms[platform]?.name || '未知平台';
            
            console.log(`📋 开始下载: ${platformName} - ${url}`);
            
            // 更新UI状态
            setButtonState('loading');
            showProgressContainer();
            updateProgress(0, '正在初始化下载...');
            showMessage(`正在验证${platformName}视频链接...`, 'info');
            
            // 阶段1：预检测致命错误
            console.log(`🔍 阶段1：预检测${platformName}视频`);
            updateProgress(5, `正在预检测${platformName}视频...`);
            
            const preCheckResult = await preCheckUrl(url);
            if (preCheckResult.isFatal) {
                console.log('💀 预检测发现致命错误，立即停止');
                // 立即处理致命错误，不再继续任何进度
                state.fatalErrorOccurred = true;
                handleSpecificError(preCheckResult.errorType, preCheckResult.errorMessage, preCheckResult.errorType, preCheckResult.fatal);
                return;
            }
            
            // 阶段2：验证链接
            console.log(`📋 阶段2：验证${platformName}视频链接`);
            await simulateProgress(15, 800, `正在验证${platformName}视频链接...`);
            showMessage(`${platformName}链接验证成功，正在连接服务器...`, 'info');
            
            // 阶段3：连接服务器
            console.log('🌐 阶段3：连接服务器');
            await simulateProgress(25, 600, '正在连接下载服务器...');
            showMessage('服务器连接成功，正在发送下载请求...', 'info');
            
            // 阶段4：发送下载请求
            console.log('📤 阶段4：发送下载请求');
            setButtonState('analyzing');
            updateProgress(30, '正在发送下载请求...');
            
            const response = await fetchWithTimeout('/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: url })
            }, 30000); // 30秒超时
            
            console.log('📥 收到服务器响应:', response.status, response.statusText);
            
            await simulateProgress(35, 400, '正在处理服务器响应...');
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ 
                    error: `服务器响应错误: ${response.status}` 
                }));
                throw new Error(errorData.error || `服务器错误: ${response.status}`);
            }
            
            const result = await response.json();
            console.log('📊 解析响应数据:', result);
            
            // 检查是否立即失败（如付费内容）
            if (result.error) {
                const errorType = identifyErrorType(result.error);
                const fatalErrors = ['payment_required', 'auth_required', 'region_blocked', 'access_denied', 'age_restricted', 'live_content'];
                
                if (fatalErrors.includes(errorType) || fatalErrors.includes(result.error_type) || result.fatal) {
                    console.log('💀 服务器返回致命错误，立即停止');
                    state.fatalErrorOccurred = true;
                    handleSpecificError(errorType, result.error, result.error_type, result.fatal);
                    return;
                }
                
                // 非致命错误，抛出异常进入重试流程
                throw new Error(result.error);
            }
            
            if (result.download_id) {
                // 阶段5：开始实际下载
                console.log('🎬 阶段5：开始下载任务');
                state.currentDownloadId = result.download_id;
                
                await simulateProgress(40, 300, '下载任务已创建...');
                showMessage(`${platformName}下载任务已创建，正在开始下载...`, 'downloading');
                setButtonState('downloading');
                
                // 开始进度轮询
                startProgressPolling();
                
            } else {
                throw new Error(result.error || '未能创建下载任务');
            }
            
        } catch (error) {
            console.error('❌ 下载流程出错:', error);
            
            // 分析错误类型
            const errorType = identifyErrorType(error.message);
            const fatalErrors = ['payment_required', 'auth_required', 'region_blocked', 'access_denied', 'age_restricted', 'live_content'];
            
            if (fatalErrors.includes(errorType)) {
                state.fatalErrorOccurred = true;
                handleSpecificError(errorType, error.message);
            } else {
                handleDownloadError(error);
            }
        }
    }

    /**
     * 处理特定错误类型 - 终极修复版（禁用重试和进度回退）
     */
    function handleSpecificError(errorType, errorMessage, backendErrorType = null, isFatal = null) {
        console.log(`🔍 错误类型: ${errorType}, 后端类型: ${backendErrorType}, 致命: ${isFatal}, 消息: ${errorMessage}`);
        
        // 立即停止所有轮询和操作
        stopProgressPolling();
        
        // 取消所有请求
        if (state.abortController) {
            state.abortController.abort();
        }
        
        // 使用后端提供的错误类型（如果有）
        const finalErrorType = backendErrorType || errorType;
        const finalIsFatal = isFatal !== null ? isFatal : ['payment_required', 'auth_required', 'region_blocked', 'access_denied', 'age_restricted', 'live_content'].includes(finalErrorType);
        
        if (finalIsFatal) {
            state.fatalErrorOccurred = true;
            state.isDownloading = false; // 立即停止下载状态
            console.log('💀 检测到致命错误，完全禁用重试机制');
        }
        
        switch (finalErrorType) {
            case 'payment_required':
                setButtonState('blocked', '付费内容');
                showMessage('该视频为付费内容，需要购买后才能下载', 'blocked');
                // 致命错误：保持当前进度并显示错误信息，不允许任何进度更新
                if (elements.progressStatusText) {
                    elements.progressStatusText.textContent = '付费内容无法下载';
                }
                updateProgressDetails('付费限制', '需要购买');
                
                // 显示详细说明
                setTimeout(() => {
                    const platformName = supportedPlatforms[state.currentPlatform]?.name || '该平台';
                    showMessage(`💡 解决方案：1. 在${platformName}购买相关内容 2. 尝试其他免费视频`, 'info');
                }, 3000);
                
                // 不进行重试，直接结束
                setTimeout(() => {
                    completeReset();
                }, 8000);
                break;
                
            case 'auth_required':
                setButtonState('error', '需要登录');
                const platformName = supportedPlatforms[state.currentPlatform]?.name || '相应平台';
                showMessage(`需要登录${platformName}账号才能下载该视频`, 'error');
                if (elements.progressStatusText) {
                    elements.progressStatusText.textContent = '需要登录认证';
                }
                
                setTimeout(() => {
                    showMessage(`💡 请在浏览器中登录${platformName}账号后重试`, 'info');
                }, 3000);
                
                setTimeout(() => {
                    completeReset();
                }, 6000);
                break;
                
            case 'region_blocked':
                setButtonState('blocked', '地区限制');
                showMessage('该视频在当前地区不可观看', 'blocked');
                if (elements.progressStatusText) {
                    elements.progressStatusText.textContent = '地区限制';
                }
                
                setTimeout(() => {
                    completeReset();
                }, 5000);
                break;
                
            case 'access_denied':
                setButtonState('error', '无法访问');
                showMessage('视频无法访问，可能已被删除或设为私有', 'error');
                if (elements.progressStatusText) {
                    elements.progressStatusText.textContent = '访问被拒绝';
                }
                
                setTimeout(() => {
                    completeReset();
                }, 5000);
                break;
                
            case 'age_restricted':
                setButtonState('blocked', '年龄限制');
                showMessage('该视频有年龄限制，需要验证身份', 'blocked');
                if (elements.progressStatusText) {
                    elements.progressStatusText.textContent = '年龄限制';
                }
                
                setTimeout(() => {
                    showMessage('💡 请在原平台完成年龄验证后重试', 'info');
                }, 3000);
                
                setTimeout(() => {
                    completeReset();
                }, 6000);
                break;
                
            case 'live_content':
                setButtonState('blocked', '直播内容');
                showMessage('检测到直播内容，暂不支持直播下载', 'blocked');
                if (elements.progressStatusText) {
                    elements.progressStatusText.textContent = '直播内容';
                }
                
                setTimeout(() => {
                    showMessage('💡 请等待直播结束后尝试下载回放', 'info');
                }, 3000);
                
                setTimeout(() => {
                    completeReset();
                }, 6000);
                break;
                
            case 'network_error':
                // 只有非致命的网络错误才进入重试流程
                if (!finalIsFatal) {
                    handleDownloadError(new Error(errorMessage));
                } else {
                    setButtonState('error', '网络错误');
                    showMessage('网络连接失败，请检查网络后重试', 'error');
                    setTimeout(() => completeReset(), 5000);
                }
                break;
                
            default:
                // 未知错误，根据是否致命决定处理方式
                if (finalIsFatal) {
                    setButtonState('error', '无法下载');
                    showMessage(`该视频无法下载: ${errorMessage}`, 'error');
                    if (elements.progressStatusText) {
                        elements.progressStatusText.textContent = '无法下载';
                    }
                    setTimeout(() => completeReset(), 5000);
                } else {
                    handleDownloadError(new Error(errorMessage));
                }
                break;
        }
    }

    // 开始进度轮询 - 修复版
    function startProgressPolling() {
        if (!state.currentDownloadId) {
            console.error('❌ 没有下载ID，无法开始轮询');
            handleDownloadError(new Error('下载ID丢失'));
            return;
        }
        
        console.log('🔄 开始进度轮询:', state.currentDownloadId);
        
        state.currentPollCount = 0;
        state.lastProgressTime = Date.now();
        
        // 清除已有的轮询
        stopProgressPolling();
        
        state.progressInterval = setInterval(async () => {
            // 检查下载状态
            if (!state.isDownloading || !state.currentDownloadId) {
                console.log('❌ 下载已停止或ID丢失，停止轮询');
                stopProgressPolling();
                return;
            }
            
            state.currentPollCount++;
            
            try {
                console.log(`📊 第${state.currentPollCount}次进度查询`);
                
                // 检查轮询次数限制
                if (state.currentPollCount >= state.maxProgressPolls) {
                    throw new Error('下载超时，请重试');
                }

                // 检查进度是否卡住
                checkProgressStuck();
                
                const response = await fetchWithTimeout(`/progress/${state.currentDownloadId}`, {}, 8000);
                
                if (!response.ok) {
                    if (response.status === 404) {
                        throw new Error('下载任务不存在或已过期');
                    }
                    throw new Error(`无法获取进度: ${response.status}`);
                }
                
                const progressData = await response.json();
                console.log('📈 进度数据:', progressData);
                
                // 检查是否是致命错误（如付费内容）- 增强版
                if (progressData.error) {
                    const errorType = identifyErrorType(progressData.error);
                    const fatalErrors = ['payment_required', 'auth_required', 'region_blocked', 'access_denied', 'age_restricted', 'live_content'];
                    
                    // 检查是否为致命错误
                    const isFatalError = fatalErrors.includes(errorType) || 
                                       fatalErrors.includes(progressData.error_type) || 
                                       progressData.fatal === true;
                    
                    if (isFatalError) {
                        console.log('💀 检测到致命错误，立即停止轮询:', {
                            errorType,
                            backendErrorType: progressData.error_type,
                            fatal: progressData.fatal,
                            error: progressData.error
                        });
                        
                        stopProgressPolling();
                        handleSpecificError(errorType, progressData.error, progressData.error_type, progressData.fatal);
                        return; // 立即退出，不再处理任何进度更新
                    }
                }
                
                state.lastProgressData = progressData;
                state.lastProgressTime = Date.now();
                handleProgressUpdate(progressData, state.currentPollCount);
                
                // 检查是否需要停止轮询
                if (['completed', 'failed'].includes(progressData.status)) {
                    stopProgressPolling();
                    return;
                }
                
            } catch (error) {
                console.error('❌ 进度查询失败:', error);
                stopProgressPolling();
                handleDownloadError(error);
            }
        }, 2000); // 每2秒查询一次，减少频率
    }

    /**
     * 检查进度卡住情况
     */
    function checkProgressStuck() {
        if (!state.lastProgressTime) return;
        
        const timeSinceLastProgress = Date.now() - state.lastProgressTime;
        
        if (timeSinceLastProgress > state.progressStuckThreshold && !state.isProgressStuck) {
            state.isProgressStuck = true;
            console.warn('⚠️ 进度可能卡住，尝试处理...');
            
            showMessage('下载进度似乎卡住了，正在尝试恢复...', 'warning');
            
            // 如果卡住时间超过1分钟，强制重试
            if (timeSinceLastProgress > 60000) {
                console.error('❌ 进度长时间卡住，强制重试');
                stopProgressPolling();
                handleDownloadError(new Error('下载进度卡住，请重试'));
            }
        }
    }

    // 处理进度更新
    function handleProgressUpdate(progressData, pollCount) {
        const { status, percent, message, filename, speed, downloaded_mb, download_url, error } = progressData;
        
        console.log(`📊 处理进度更新 (第${pollCount}次):`, status, `${percent || 0}%`);
        
        // 重置卡住状态
        if (state.isProgressStuck) {
            state.isProgressStuck = false;
            console.log('✅ 进度恢复正常');
        }
        
        switch (status) {
            case 'starting':
                // 检查starting状态中是否包含致命错误信息
                if (error) {
                    const errorType = identifyErrorType(error);
                    const fatalErrors = ['payment_required', 'auth_required', 'region_blocked', 'access_denied', 'age_restricted', 'live_content'];
                    
                    if (fatalErrors.includes(errorType) || fatalErrors.includes(progressData.error_type) || progressData.fatal) {
                        console.log('💀 Starting状态下检测到致命错误，立即停止');
                        stopProgressPolling();
                        handleSpecificError(errorType, error, progressData.error_type, progressData.fatal);
                        return;
                    }
                }
                
                const startPercent = Math.max(40, percent || 0); // 起始进度不低于40%
                updateProgress(startPercent, '正在分析视频格式...');
                updateProgressDetails('分析中...', `${downloaded_mb || 0} MB`);
                showMessage('正在分析视频信息和可用格式...', 'downloading');
                setButtonState('analyzing');
                break;
                
            case 'downloading':
                const realPercent = Math.min(Math.max(40, percent || 0), 99); // 下载进度不低于40%
                let progressMsg = '正在下载视频文件...';
                let statusMsg = '正在下载视频...';
                
                if (speed && downloaded_mb !== undefined) {
                    progressMsg = `下载中... (${speed})`;
                    statusMsg = `正在下载 - ${speed} - 已完成 ${downloaded_mb.toFixed(1)}MB`;
                    updateProgressDetails(speed, `${downloaded_mb.toFixed(1)} MB`);
                }
                
                updateProgress(realPercent, progressMsg);
                showMessage(statusMsg, 'downloading');
                setButtonState('downloading', `下载中 ${Math.round(realPercent)}%`);
                break;
                
            case 'finished':
                updateProgress(95, '下载完成，正在处理文件...');
                updateProgressDetails('处理中...', state.lastProgressData?.downloaded_mb ? `${state.lastProgressData.downloaded_mb.toFixed(1)} MB` : '');
                showMessage('视频下载完成，正在进行后处理...', 'downloading');
                setButtonState('processing');
                break;
                
            case 'completed':
                console.log('✅ 下载任务完成');
                updateProgress(100, '下载完成！');
                updateProgressDetails('已完成', filename || '');
                
                // 简化成功消息 - 只显示"下载完成"
                let successMessage = '下载完成！';
                
                showMessage(successMessage, 'success');
                setButtonState('completed');
                
                // 显示成功动画
                showSuccessAnimation();
                
                // 处理文件下载
                if (download_url) {
                    handleFileDownload(download_url, filename);
                } else {
                    console.warn('⚠️ 没有收到下载链接');
                    showMessage('下载完成，但无法获取文件链接', 'warning');
                }
                
                // 延迟重置状态
                setTimeout(() => {
                    completeReset();
                }, 5000);
                break;
                
            case 'failed':
                console.log('❌ 下载任务失败');
                const errorMsg = error || message || '下载失败';
                const errorType = identifyErrorType(errorMsg);
                
                // 根据错误类型决定处理方式
                const fatalErrors = ['payment_required', 'auth_required', 'region_blocked', 'access_denied', 'age_restricted', 'live_content'];
                const isFatalError = fatalErrors.includes(errorType) || 
                                   fatalErrors.includes(progressData.error_type) || 
                                   progressData.fatal === true;
                
                if (isFatalError) {
                    console.log('💀 失败状态下检测到致命错误，不回退进度条');
                    handleSpecificError(errorType, errorMsg, progressData.error_type, progressData.fatal);
                } else {
                    // 非致命错误才允许重置进度条
                    updateProgress(0, '下载失败', true); // 允许重置
                    updateProgressDetails('失败', '');
                    showMessage(`下载失败: ${errorMsg}`, 'error');
                    handleDownloadError(new Error(errorMsg));
                }
                break;
                
            default:
                console.log('❓ 未知状态:', status);
                const defaultPercent = Math.max(35, percent || 0);
                updateProgress(defaultPercent, message || '处理中...');
                showMessage(message || '正在处理...', 'info');
                break;
        }
    }

    // 取消下载
    function cancelDownload() {
        console.log('🛑 用户取消下载');
        
        // 取消所有请求
        if (state.abortController) {
            state.abortController.abort();
        }
        
        stopProgressPolling();
        
        // 通知服务器取消下载（如果有API）
        if (state.currentDownloadId) {
            fetch(`/cancel/${state.currentDownloadId}`, { method: 'POST' }).catch(() => {
                // 忽略取消请求的错误
            });
        }
        
        showMessage('下载已取消', 'warning');
        completeReset();
    }

    // 处理文件下载 - 移动设备优化版
    function handleFileDownload(downloadUrl, filename) {
        try {
            console.log('📥 开始文件下载 (移动设备优化):', filename);
            
            // 检测是否为移动设备
            const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
            
            if (isMobile) {
                showMessage('📱 移动设备下载中，请稍候...', 'downloading');
                console.log('📱 检测到移动设备，使用优化下载方式');
            } else {
                showMessage('💻 PC端下载中，请稍候...', 'downloading');
            }
            
            // 显示下载结果界面
            showDownloadResult(downloadUrl, filename);
            
            // 移动设备优化的下载处理
            const downloadWithRetry = (retryCount = 0) => {
                const maxRetries = 3;
                
                const link = document.createElement('a');
                link.href = downloadUrl;
                link.download = filename || 'video.mp4';
                link.style.display = 'none';
                
                // 移动设备优化设置
                if (isMobile) {
                    link.target = '_blank'; // 移动设备在新标签页打开
                    link.rel = 'noopener noreferrer';
                }
                
                // 监听下载成功/失败
                const handleDownloadSuccess = () => {
                    console.log('✅ 文件下载成功');
                    if (isMobile) {
                        showMessage('📱 下载完成！已优化移动设备兼容性，音频已修复', 'success');
                    } else {
                        showMessage('💻 下载完成！文件已保存到下载文件夹', 'success');
                    }
                };
                
                const handleDownloadError = (error) => {
                    console.error(`❌ 下载失败 (尝试 ${retryCount + 1}/${maxRetries + 1}):`, error);
                    
                    if (retryCount < maxRetries) {
                        console.log(`🔄 ${isMobile ? '移动设备' : 'PC端'}下载重试 ${retryCount + 1}/${maxRetries}`);
                        showMessage(`下载重试中... (${retryCount + 1}/${maxRetries})`, 'warning');
                        
                        setTimeout(() => {
                            downloadWithRetry(retryCount + 1);
                        }, 2000); // 2秒后重试
                    } else {
                        console.error('❌ 下载最终失败，已达到最大重试次数');
                        showMessage('❌ 下载失败，请检查网络连接或稍后再试', 'error');
                    }
                };
                
                try {
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    
                    // 设置成功检测延迟
                    setTimeout(() => {
                        handleDownloadSuccess();
                    }, isMobile ? 3000 : 1000); // 移动设备给更多时间
                    
                } catch (error) {
                    handleDownloadError(error);
                }
            };
            
            // 延迟启动下载，给移动设备更多准备时间
            setTimeout(() => {
                downloadWithRetry();
            }, isMobile ? 2000 : 500);
            
        } catch (error) {
            console.error('❌ 文件下载初始化失败:', error);
            showMessage('下载初始化失败，请刷新页面重试', 'error');
        }
    }

    // 显示下载结果 - 移动端优化版
    function showDownloadResult(downloadUrl, filename) {
        if (!elements.downloadResult) {
            console.warn('下载结果容器未找到');
            return;
        }

        try {
            // 隐藏进度容器
            if (elements.progressContainer) {
                elements.progressContainer.style.display = 'none';
            }

            // 更新文件信息
            const resultFileName = document.getElementById('resultFileName');
            const resultFileSize = document.getElementById('resultFileSize');
            
            if (resultFileName) {
                resultFileName.textContent = filename || '下载文件';
            }
            
            if (resultFileSize && state.lastProgressData?.file_size_mb) {
                resultFileSize.textContent = `${state.lastProgressData.file_size_mb.toFixed(2)} MB`;
            }

            // 显示下载结果
            elements.downloadResult.style.display = 'block';

            // 设置下载按钮事件 - 移动端优化
            setupDownloadFileButton(downloadUrl, filename);

            console.log('✅ 下载结果界面已显示');

        } catch (error) {
            console.error('❌ 显示下载结果失败:', error);
        }
    }

    // 设置文件下载按钮 - 移动端完美支持
    function setupDownloadFileButton(downloadUrl, filename) {
        const downloadFileBtn = document.getElementById('downloadFileBtn');
        if (!downloadFileBtn) {
            console.warn('下载文件按钮未找到');
            return;
        }

        // 移除所有现有事件监听器
        const newBtn = downloadFileBtn.cloneNode(true);
        downloadFileBtn.parentNode.replaceChild(newBtn, downloadFileBtn);

        // 确保按钮可点击
        newBtn.style.pointerEvents = 'auto';
        newBtn.style.cursor = 'pointer';
        newBtn.style.touchAction = 'manipulation';
        newBtn.style.webkitTapHighlightColor = 'transparent';
        newBtn.style.webkitTouchCallout = 'none';
        newBtn.style.userSelect = 'none';
        newBtn.style.webkitUserSelect = 'none';

        const handleFileDownload = (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('📥 文件下载按钮被点击');

            try {
                const link = document.createElement('a');
                link.href = downloadUrl;
                link.download = filename || 'video.mp4';
                link.style.display = 'none';
                
                // 移动设备优化
                const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
                if (isMobile) {
                    link.target = '_blank';
                    link.rel = 'noopener noreferrer';
                }

                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);

                // 反馈消息
                if (isMobile) {
                    showMessage('📱 移动设备下载启动！请检查下载文件夹', 'success');
                } else {
                    showMessage('💻 文件下载已启动！', 'success');
                }

            } catch (error) {
                console.error('❌ 文件下载失败:', error);
                showMessage('下载失败，请重试', 'error');
            }
        };

        // PC端点击事件
        newBtn.addEventListener('click', handleFileDownload, { passive: false });

        // 移动端触摸事件
        newBtn.addEventListener('touchstart', (e) => {
            newBtn.style.transform = 'scale(0.98)';
            newBtn.style.opacity = '0.9';
        }, { passive: true });

        newBtn.addEventListener('touchend', (e) => {
            newBtn.style.transform = '';
            newBtn.style.opacity = '';
        }, { passive: true });

        console.log('✅ 文件下载按钮事件已设置');
    }

    // 处理下载错误（通用错误处理）- 终极修复版
    function handleDownloadError(error) {
        console.error('❌ 处理下载错误:', error);
        
        stopProgressPolling();
        
        const errorMessage = error.message || '未知错误';
        const errorType = identifyErrorType(errorMessage);
        
        // 致命错误完全禁用重试
        const fatalErrors = ['payment_required', 'auth_required', 'region_blocked', 'access_denied', 'age_restricted', 'live_content'];
        if (fatalErrors.includes(errorType) || state.fatalErrorOccurred) {
            console.log('💀 致命错误不进行重试，直接终止');
            state.fatalErrorOccurred = true;
            state.isDownloading = false;
            handleSpecificError(errorType, errorMessage);
            return;
        }
        
        // 非致命错误的处理
        updateProgress(0, '下载失败', true); // 允许重置进度条
        updateProgressDetails('失败', '');
        showMessage(`下载失败: ${errorMessage}`, 'error');
        setButtonState('error');
        
        // 重试逻辑（仅对可恢复错误）
        const currentTime = Date.now();
        const timeSinceLastRetry = currentTime - state.lastRetryTime;
        
        if (state.retryCount < state.maxRetries && timeSinceLastRetry >= state.retryInterval && !state.isRetrying) {
            state.isRetrying = true; // 防止重复重试
            
            setTimeout(() => {
                state.retryCount++;
                state.lastRetryTime = Date.now();
                console.log(`🔄 自动重试 (${state.retryCount}/${state.maxRetries})`);
                showMessage(`正在重试... (${state.retryCount}/${state.maxRetries})`, 'warning');
                
                // 重新开始下载
                const url = elements.videoUrl.value.trim();
                if (url && state.retryCount <= state.maxRetries && !state.fatalErrorOccurred) {
                    // 重置重试状态
                    state.isRetrying = false;
                    state.isDownloading = false; // 允许重新下载
                    startDownloadProcess(url);
                } else {
                    state.isRetrying = false;
                    completeReset();
                }
            }, state.retryInterval);
        } else {
            // 重置状态
            setTimeout(() => {
                completeReset();
            }, 5000);
        }
    }

    // 显示成功动画
    function showSuccessAnimation() {
        if (elements.successAnimation) {
            elements.successAnimation.style.display = 'block';
            
            // 创建彩带效果
            createConfetti();
            
            setTimeout(() => {
                if (elements.successAnimation) {
                    elements.successAnimation.style.display = 'none';
                }
            }, 3000);
        }
    }

    // 创建彩带效果
    function createConfetti() {
        const colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#ffeaa7', '#dda0dd'];
        const confettiContainer = document.querySelector('.confetti-container');
        
        if (!confettiContainer) return;
        
        for (let i = 0; i < 50; i++) {
            const confetti = document.createElement('div');
            confetti.className = 'confetti';
            confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
            confetti.style.left = Math.random() * 100 + '%';
            confetti.style.animationDelay = Math.random() * 3 + 's';
            confetti.style.animationDuration = Math.random() * 2 + 2 + 's';
            
            confettiContainer.appendChild(confetti);
            
            // 清理
            setTimeout(() => {
                if (confetti.parentNode) {
                    confetti.remove();
                }
            }, 5000);
        }
    }

    // ========================================
    // 移动端优化事件监听器设置 - 修复版
    // ========================================

    // 确保下载按钮可点击
    function setupDownloadButton() {
        if (!elements.downloadButton) {
            console.error('❌ 下载按钮未找到');
            return;
        }

        // 确保按钮样式正确
        elements.downloadButton.style.pointerEvents = 'auto';
        elements.downloadButton.style.cursor = 'pointer';
        elements.downloadButton.style.userSelect = 'none';
        elements.downloadButton.style.touchAction = 'manipulation';
        
        const handleDownloadClick = async (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('🎯 === 下载按钮被点击 ===');
            
            // 防重复点击和状态检查
            if (state.isDownloading || state.isRetrying) {
                console.log('⚠️ 下载任务进行中或正在重试，忽略重复点击');
                showMessage('下载任务正在进行中，请勿重复点击', 'warning');
                return;
            }
            
            const url = elements.videoUrl.value.trim();
            if (!url) {
                showMessage('请输入有效的视频URL', 'error');
                elements.videoUrl.focus();
                return;
            }
            
            // URL验证 - 支持多平台
            const platform = detectPlatform(url);
            if (platform === 'unknown') {
                showMessage('请输入支持的平台视频链接', 'error');
                elements.videoUrl.focus();
                return;
            }
            
            console.log(`✅ URL验证通过，检测到${supportedPlatforms[platform].name}链接:`, url);
            
            // 重置状态
            resetStateForNewDownload();
            
            // 开始下载
            await startDownloadProcess(url);
        };

        // PC端点击事件
        elements.downloadButton.addEventListener('click', handleDownloadClick, { passive: false });
        
        // 移动端触摸事件支持
        elements.downloadButton.addEventListener('touchstart', (e) => {
            if (!state.isDownloading && !state.isRetrying) {
                elements.downloadButton.style.transform = 'translateY(1px)';
                elements.downloadButton.style.opacity = '0.9';
            }
        }, { passive: true });
        
        elements.downloadButton.addEventListener('touchend', (e) => {
            elements.downloadButton.style.transform = '';
            elements.downloadButton.style.opacity = '';
        }, { passive: true });
        
        console.log('✅ 下载按钮事件监听器已设置');
    }

    // 主下载按钮事件 - 替换为新的处理方式
    setupDownloadButton();

    // ========================================
    // 事件监听器设置
    // ========================================

    // 页面可见性变化处理
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            console.log('👁️ 页面隐藏');
        } else if (state.currentDownloadId && !state.progressInterval && state.isDownloading) {
            console.log('👁️ 页面显示，恢复轮询');
            startProgressPolling();
        }
    });

    // 页面卸载前清理
    window.addEventListener('beforeunload', (e) => {
        if (state.isDownloading) {
            e.preventDefault();
            e.returnValue = '下载正在进行中，确定要离开吗？';
        }
        
        console.log('🚪 页面卸载，清理资源');
        completeReset();
    });

    // 全局错误处理
    window.addEventListener('error', (event) => {
        console.error('❌ 全局错误:', event.error);
    });

    // 未捕获的Promise错误处理
    window.addEventListener('unhandledrejection', (event) => {
        console.error('❌ 未捕获的Promise错误:', event.reason);
        event.preventDefault();
    });

    // 页面初始化设置 - 放在最后执行
    initializeApp();

    console.log('✅ === 🐻🐻专属视频下载器 - 多平台增强版 v2.4 初始化完成! ===');
});

// 移动设备网络检测和优化
function initMobileOptimizations() {
    console.log('🚀 初始化移动端优化...');
    
    // 检测移动设备
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    const isTablet = /iPad|Android.*(?=.*Tablet)|(?=.*Mobile).*Android.*(?=.*Chrome)/i.test(navigator.userAgent);
    
    if (isMobile || isTablet) {
        document.body.classList.add('is-mobile');
        
        // 添加触摸反馈
        addTouchFeedback();
        
        // 优化虚拟键盘体验
        optimizeVirtualKeyboard();
        
        // 添加移动端专用状态指示器
        createMobileStatusIndicator();
        
        // 优化滚动体验
        optimizeScrolling();
        
        console.log('✅ 移动端优化完成');
    }
}

// 添加触摸反馈
function addTouchFeedback() {
    const buttons = document.querySelectorAll('button, .download-btn, .theme-toggle');
    buttons.forEach(button => {
        button.classList.add('touch-feedback');
        
        button.addEventListener('touchstart', function(e) {
            this.style.transform = 'scale(0.98)';
        });
        
        button.addEventListener('touchend', function(e) {
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
        });
    });
}

// 优化虚拟键盘体验
function optimizeVirtualKeyboard() {
    const videoInput = elements.videoUrl;
    if (!videoInput) return;
    
    let initialViewportHeight = window.innerHeight;
    
    videoInput.addEventListener('focus', function() {
        // 虚拟键盘弹出时的处理
        setTimeout(() => {
            if (window.innerHeight < initialViewportHeight * 0.75) {
                document.body.classList.add('keyboard-open');
                this.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }, 300);
    });
    
    videoInput.addEventListener('blur', function() {
        // 虚拟键盘收起时的处理
        document.body.classList.remove('keyboard-open');
    });
    
    // 监听窗口大小变化
    window.addEventListener('resize', function() {
        if (window.innerHeight >= initialViewportHeight * 0.9) {
            document.body.classList.remove('keyboard-open');
        }
    });
}

// 创建移动端状态指示器
function createMobileStatusIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'mobile-status-indicator';
    indicator.id = 'mobileStatusIndicator';
    document.body.appendChild(indicator);
}

// 显示移动端状态
function showMobileStatus(message, type = 'info', duration = 3000) {
    const indicator = document.getElementById('mobileStatusIndicator');
    if (!indicator) return;
    
    indicator.textContent = message;
    indicator.className = `mobile-status-indicator ${type} show`;
    
    // 自动隐藏
    setTimeout(() => {
        indicator.classList.remove('show');
    }, duration);
}

// 优化滚动体验
function optimizeScrolling() {
    // 平滑滚动
    document.documentElement.style.scrollBehavior = 'smooth';
    
    // 防止过度滚动
    document.body.addEventListener('touchmove', function(e) {
        if (e.target.closest('.progress-container, .input-container')) {
            e.stopPropagation();
        }
    }, { passive: true });
}

// 移动端专用进度显示
function updateMobileProgress(percent, message) {
    const isMobile = document.body.classList.contains('is-mobile');
    if (!isMobile) return;
    
    // 显示移动端状态指示器
    if (percent >= 100) {
        showMobileStatus('下载完成！', 'success', 5000);
    } else if (percent > 0) {
        showMobileStatus(`${message} ${Math.round(percent)}%`, 'downloading', 1000);
    }
}

// 移动端专用错误处理
function showMobileError(message) {
    const isMobile = document.body.classList.contains('is-mobile');
    if (!isMobile) return;
    
    showMobileStatus(message, 'error', 5000);
    
    // 添加震动反馈（如果支持）
    if (navigator.vibrate) {
        navigator.vibrate([200, 100, 200]);
    }
}

    // ========================================
    // 最终初始化代码 - 确保所有功能正常
    // ========================================
    
    // 初始化主题管理器
    try {
        themeManager.init();
        console.log('✅ 主题管理器初始化成功');
    } catch (error) {
        console.error('❌ 主题管理器初始化失败:', error);
    }
    
    // 修复移动端点击问题的最终保障
    function ensureMobileInteraction() {
        // 确保所有关键元素都可点击
        const criticalElements = [
            elements.downloadButton,
            elements.themeToggle,
            elements.videoUrl
        ];
        
        criticalElements.forEach(element => {
            if (element) {
                element.style.pointerEvents = 'auto';
                element.style.touchAction = 'manipulation';
                element.style.webkitTapHighlightColor = 'transparent';
                element.style.webkitTouchCallout = 'none';
            }
        });
        
        console.log('✅ 移动端交互优化已应用');
    }
    
    // 应用移动端交互优化
    ensureMobileInteraction();
    
    // 页面完全加载后的最终检查
    window.addEventListener('load', () => {
        setTimeout(() => {
            ensureMobileInteraction();
            console.log('🎯 页面加载完成，移动端优化已确认');
        }, 100);
    });
    
    console.log('🎉 === 视频下载器初始化完成 ===');
    console.log('🔧 移动端和PC端完美兼容');
    console.log('🎨 主题切换功能已启用');
    console.log('📱 触摸交互已优化');