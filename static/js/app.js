/**
 * 文萍专属视频下载器 - 多平台增强版 v2.2 (修复无限循环)
 * 支持实时进度显示、多平台下载、智能错误处理、付费内容识别
 * Created with ❤️ by 一慧
 */

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 === 🐻🐻专属视频下载器 - 多平台增强版 v2.2 启动 ===');
    
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
        platformIndicator: document.getElementById('platformIndicator') // 平台指示器
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
        progressStatusText: !!elements.progressStatusText
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
        abortController: null // 用于取消请求
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
     * 更新进度条
     */
    function updateProgress(percent, message) {
        const safePercent = Math.max(0, Math.min(100, percent));
        
        if (elements.downloadProgress) {
            elements.downloadProgress.value = safePercent;
        }
        
        if (elements.progressPercentage) {
            elements.progressPercentage.textContent = `${Math.round(safePercent)}%`;
        }
        
        if (elements.progressStatusText) {
            elements.progressStatusText.textContent = message || '';
        }
        
        console.log(`📊 进度更新: ${safePercent.toFixed(1)}% - ${message}`);
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
     * 完全重置所有状态 - 修复版
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
        updateProgress(0, '');
        updateProgressDetails('等待中...', '0 MB');
        
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
     * 模拟进度更新
     */
    async function simulateProgress(targetPercent, duration, message) {
        const currentPercent = elements.downloadProgress ? elements.downloadProgress.value : 0;
        const steps = Math.max(1, Math.floor(duration / 50));
        const increment = (targetPercent - currentPercent) / steps;
        
        for (let i = 0; i < steps; i++) {
            if (!state.isDownloading) break; // 如果已取消下载，停止模拟
            
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
            
            // 阶段1：验证链接
            console.log(`📋 阶段1：验证${platformName}视频链接`);
            await simulateProgress(5, 800, `正在验证${platformName}视频链接...`);
            showMessage(`${platformName}链接验证成功，正在连接服务器...`, 'info');
            
            // 阶段2：连接服务器
            console.log('🌐 阶段2：连接服务器');
            await simulateProgress(15, 600, '正在连接下载服务器...');
            showMessage('服务器连接成功，正在发送下载请求...', 'info');
            
            // 阶段3：发送下载请求
            console.log('📤 阶段3：发送下载请求');
            setButtonState('analyzing');
            updateProgress(20, '正在发送下载请求...');
            
            const response = await fetchWithTimeout('/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: url })
            }, 30000); // 30秒超时
            
            console.log('📥 收到服务器响应:', response.status, response.statusText);
            
            await simulateProgress(30, 400, '正在处理服务器响应...');
            
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
                handleSpecificError(errorType, result.error, result.error_type, result.fatal);
                return;
            }
            
            if (result.download_id) {
                // 阶段4：开始实际下载
                console.log('🎬 阶段4：开始下载任务');
                state.currentDownloadId = result.download_id;
                
                await simulateProgress(35, 300, '下载任务已创建...');
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
            handleSpecificError(errorType, error.message);
        }
    }

    /**
     * 处理特定错误类型 - 修复版
     */
    function handleSpecificError(errorType, errorMessage, backendErrorType = null, isFatal = null) {
        console.log(`🔍 错误类型: ${errorType}, 后端类型: ${backendErrorType}, 消息: ${errorMessage}`);
        
        // 停止所有轮询
        stopProgressPolling();
        
        // 使用后端提供的错误类型（如果有）
        const finalErrorType = backendErrorType || errorType;
        const finalIsFatal = isFatal !== null ? isFatal : ['payment_required', 'auth_required', 'region_blocked', 'access_denied', 'age_restricted'].includes(finalErrorType);
        
        if (finalIsFatal) {
            state.fatalErrorOccurred = true;
        }
        
        switch (finalErrorType) {
            case 'payment_required':
                setButtonState('blocked', '付费内容');
                showMessage('该视频为付费内容，需要购买后才能下载', 'blocked');
                updateProgress(0, '付费内容无法下载');
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
                updateProgress(0, '需要登录认证');
                
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
                updateProgress(0, '地区限制');
                
                setTimeout(() => {
                    completeReset();
                }, 5000);
                break;
                
            case 'access_denied':
                setButtonState('error', '无法访问');
                showMessage('视频无法访问，可能已被删除或设为私有', 'error');
                updateProgress(0, '访问被拒绝');
                
                setTimeout(() => {
                    completeReset();
                }, 5000);
                break;
                
            case 'age_restricted':
                setButtonState('blocked', '年龄限制');
                showMessage('该视频有年龄限制，需要验证身份', 'blocked');
                updateProgress(0, '年龄限制');
                
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
                updateProgress(0, '直播内容');
                
                setTimeout(() => {
                    showMessage('💡 请等待直播结束后尝试下载回放', 'info');
                }, 3000);
                
                setTimeout(() => {
                    completeReset();
                }, 6000);
                break;
                
            case 'network_error':
                handleDownloadError(new Error(errorMessage));
                break;
                
            default:
                handleDownloadError(new Error(errorMessage));
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
                
                // 检查是否是致命错误（如付费内容）
                if (progressData.error) {
                    const errorType = identifyErrorType(progressData.error);
                    const fatalErrors = ['payment_required', 'auth_required', 'region_blocked', 'access_denied', 'age_restricted', 'live_content'];
                    
                    if (fatalErrors.includes(errorType) || fatalErrors.includes(progressData.error_type) || progressData.fatal) {
                        stopProgressPolling();
                        handleSpecificError(errorType, progressData.error, progressData.error_type, progressData.fatal);
                        return;
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
                const startPercent = Math.max(35, percent || 0);
                updateProgress(startPercent, '正在分析视频格式...');
                updateProgressDetails('分析中...', `${downloaded_mb || 0} MB`);
                showMessage('正在分析视频信息和可用格式...', 'downloading');
                setButtonState('analyzing');
                break;
                
            case 'downloading':
                const realPercent = Math.min(Math.max(35, percent || 0), 99);
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
                showMessage(`下载完成！${filename ? ` 文件: ${filename}` : ''}`, 'success');
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
                if (fatalErrors.includes(errorType) || fatalErrors.includes(progressData.error_type) || progressData.fatal) {
                    handleSpecificError(errorType, errorMsg, progressData.error_type, progressData.fatal);
                } else {
                    updateProgress(0, '下载失败');
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

    // 处理文件下载
    function handleFileDownload(downloadUrl, filename) {
        try {
            console.log('📥 开始自动文件下载:', filename);
            
            showMessage('准备下载文件到本地...', 'downloading');
            
            setTimeout(() => {
                const link = document.createElement('a');
                link.href = downloadUrl;
                link.download = filename || 'video.mp4';
                link.style.display = 'none';
                
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                
                console.log('✅ 文件下载触发成功');
                showMessage('文件下载已开始，请检查下载文件夹', 'success');
                
            }, 1000);
            
        } catch (error) {
            console.error('❌ 文件下载失败:', error);
            showMessage('自动下载失败，请手动下载文件', 'error');
        }
    }

    // 处理下载错误（通用错误处理）- 修复版
    function handleDownloadError(error) {
        console.error('❌ 处理下载错误:', error);
        
        stopProgressPolling();
        
        const errorMessage = error.message || '未知错误';
        const errorType = identifyErrorType(errorMessage);
        
        // 特殊错误类型不进行重试
        const fatalErrors = ['payment_required', 'auth_required', 'region_blocked', 'access_denied', 'age_restricted', 'live_content'];
        if (fatalErrors.includes(errorType) || state.fatalErrorOccurred) {
            handleSpecificError(errorType, errorMessage);
            return;
        }
        
        updateProgress(0, '下载失败');
        updateProgressDetails('失败', '');
        showMessage(`下载失败: ${errorMessage}`, 'error');
        setButtonState('error');
        
        // 重试逻辑（仅对可恢复错误）- 修复版
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
                if (url && state.retryCount <= state.maxRetries) {
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
    // 主下载按钮事件监听 - 修复版
    // ========================================

    // 主下载按钮事件
    elements.downloadButton.addEventListener('click', async () => {
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
    });

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

    console.log('✅ === 🐻🐻专属视频下载器 - 多平台增强版 v2.2 初始化完成! ===');
});