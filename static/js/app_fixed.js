// 🐻🐻专属视频下载器 - 完整修复版 v3.0
console.log('🚀 === 初始化视频下载器 v3.0 ===');

// 全局状态管理
const state = {
    isDownloading: false,
    isRetrying: false,
    currentDownloadId: null,
    currentPlatform: null,
    progressInterval: null,
    abortController: null,
    retryCount: 0,
    maxRetries: 3,
    retryInterval: 5000,
    lastRetryTime: 0,
    downloadStartTime: null,
    fatalErrorOccurred: false,
    currentPollCount: 0,
    maxProgressPolls: 300,
    lastProgressData: null,
    lastProgressTime: null,
    progressStuckThreshold: 30000,
    isProgressStuck: false
};

// DOM元素映射
const elements = {};

// 支持的平台配置
const supportedPlatforms = {
    youtube: {
        name: 'YouTube',
        patterns: [/youtube\.com\/watch\?v=/, /youtu\.be\//, /youtube\.com\/shorts\//],
        icon: '📺'
    },
    bilibili: {
        name: '哔哩哔哩',
        patterns: [/bilibili\.com\/video\//, /b23\.tv\//, /bilibili\.com\/bangumi\//],
        icon: '📺'
    },
    douyin: {
        name: '抖音',
        patterns: [/douyin\.com/, /v\.douyin\.com/],
        icon: '🎵'
    },
    xiaohongshu: {
        name: '小红书',
        patterns: [/xiaohongshu\.com/, /xhslink\.com/],
        icon: '📖'
    },
    weibo: {
        name: '微博',
        patterns: [/weibo\.com/, /m\.weibo\.cn/],
        icon: '🐦'
    },
    kuaishou: {
        name: '快手',
        patterns: [/kuaishou\.com/, /v\.kuaishou\.com/],
        icon: '⚡'
    }
};

// ========================================
// 核心初始化函数
// ========================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('📋 DOM内容加载完成，开始初始化...');
    
    // 初始化DOM元素
    initDOMElements();
    
    // 初始化主题管理器
    initThemeManager();
    
    // 设置事件监听器
    setupEventListeners();
    
    // 移动端优化
    initMobileOptimizations();
    
    console.log('✅ 应用初始化完成');
});

// 初始化DOM元素
function initDOMElements() {
    console.log('🎯 初始化DOM元素...');
    
    elements.videoUrl = document.getElementById('videoUrl');
    elements.downloadButton = document.getElementById('downloadButton');
    elements.themeToggle = document.getElementById('themeToggle');
    elements.progressContainer = document.getElementById('progressContainer');
    elements.downloadProgress = document.getElementById('downloadProgress');
    elements.progressPercentage = document.querySelector('.progress-percentage');
    elements.downloadSpeed = document.getElementById('downloadSpeed');
    elements.downloadSize = document.getElementById('downloadSize');
    elements.progressStatusText = document.getElementById('progressStatusText');
    elements.statusMessage = document.getElementById('statusMessage');
    elements.downloadResult = document.getElementById('downloadResult');
    elements.downloadFileBtn = document.getElementById('downloadFileBtn');
    elements.successAnimation = document.getElementById('successAnimation');
    elements.loadingOverlay = document.getElementById('loadingOverlay');
    elements.resultFileName = document.getElementById('resultFileName');
    elements.resultFileSize = document.getElementById('resultFileSize');
    
    // 验证关键元素
    if (!elements.videoUrl) console.error('❌ 视频URL输入框未找到');
    if (!elements.downloadButton) console.error('❌ 下载按钮未找到');
    if (!elements.themeToggle) console.error('❌ 主题切换按钮未找到');
    if (!elements.progressContainer) console.error('❌ 进度容器未找到');
    if (!elements.downloadProgress) console.error('❌ 进度条未找到');
    
    console.log('✅ DOM元素初始化完成');
}

// ========================================
// 主题管理器
// ========================================

const themeManager = {
    currentTheme: localStorage.getItem('theme-preference') || 'system',
    
    init() {
        console.log('🎨 初始化主题管理器...');
        this.applyTheme(this.currentTheme);
        this.setupThemeToggle();
        
        // 监听系统主题变化
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
                if (this.currentTheme === 'system') {
                    this.applyTheme('system');
                }
            });
        }
        
        console.log('✅ 主题管理器初始化完成');
    },
    
    applyTheme(theme) {
        this.currentTheme = theme;
        localStorage.setItem('theme-preference', theme);
        
        // 移除现有主题类
        document.documentElement.classList.remove('theme-light', 'theme-dark', 'theme-system');
        document.body.classList.remove('theme-light', 'theme-dark', 'theme-system');
        
        // 确定实际应用的主题
        let actualTheme = theme;
        if (theme === 'system') {
            if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                actualTheme = 'dark';
            } else {
                actualTheme = 'light';
            }
        }
        
        // 应用主题类
        document.documentElement.classList.add(`theme-${actualTheme}`);
        document.body.classList.add(`theme-${actualTheme}`);
        document.documentElement.setAttribute('data-theme', actualTheme);
        
        // 设置CSS自定义属性
        this.setCSSProperties(actualTheme);
        
        // 更新主题切换按钮
        this.updateThemeToggleIcon();
        
        console.log(`🎨 主题已切换为: ${theme} (实际显示: ${actualTheme})`);
    },
    
    setCSSProperties(theme) {
        const root = document.documentElement;
        
        if (theme === 'dark') {
            // 深色模式颜色
            root.style.setProperty('--primary-color', '#4a90e2');
            root.style.setProperty('--primary-hover', '#357abd');
            root.style.setProperty('--secondary-color', '#6c757d');
            root.style.setProperty('--success-color', '#28a745');
            root.style.setProperty('--danger-color', '#dc3545');
            root.style.setProperty('--warning-color', '#ffc107');
            root.style.setProperty('--info-color', '#17a2b8');
            
            // 背景和表面
            root.style.setProperty('--bg-color', '#1a1a1a');
            root.style.setProperty('--bg-color-secondary', '#2d2d2d');
            root.style.setProperty('--surface-color', '#333333');
            
            // 文字颜色
            root.style.setProperty('--text-color', '#ffffff');
            root.style.setProperty('--text-color-secondary', '#cccccc');
            root.style.setProperty('--text-color-muted', '#999999');
            
            // 边框
            root.style.setProperty('--border-color', '#444444');
            
        } else {
            // 浅色模式颜色
            root.style.setProperty('--primary-color', '#007bff');
            root.style.setProperty('--primary-hover', '#0056b3');
            root.style.setProperty('--secondary-color', '#6c757d');
            root.style.setProperty('--success-color', '#28a745');
            root.style.setProperty('--danger-color', '#dc3545');
            root.style.setProperty('--warning-color', '#ffc107');
            root.style.setProperty('--info-color', '#17a2b8');
            
            // 背景和表面
            root.style.setProperty('--bg-color', '#ffffff');
            root.style.setProperty('--bg-color-secondary', '#f8f9fa');
            root.style.setProperty('--surface-color', '#ffffff');
            
            // 文字颜色
            root.style.setProperty('--text-color', '#212529');
            root.style.setProperty('--text-color-secondary', '#495057');
            root.style.setProperty('--text-color-muted', '#6c757d');
            
            // 边框
            root.style.setProperty('--border-color', '#dee2e6');
        }
    },
    
    updateThemeToggleIcon() {
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
        
        const themeIcon = elements.themeToggle.querySelector('.theme-icon');
        const themeText = elements.themeToggle.querySelector('.theme-text');
        
        if (themeIcon) {
            themeIcon.textContent = icons[this.currentTheme];
        }
        
        if (themeText) {
            themeText.textContent = texts[this.currentTheme];
        }
        
        elements.themeToggle.setAttribute('data-theme', this.currentTheme);
    },
    
    toggleTheme() {
        const themes = ['system', 'light', 'dark'];
        const currentIndex = themes.indexOf(this.currentTheme);
        const nextIndex = (currentIndex + 1) % themes.length;
        const nextTheme = themes[nextIndex];
        
        this.applyTheme(nextTheme);
        
        // 显示切换提示
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
        
        const themeNames = {
            system: '跟随系统主题',
            light: '浅色模式',
            dark: '深色模式'
        };
        
        const themeIcons = {
            system: '🌐',
            light: '☀️',
            dark: '🌙'
        };
        
        toast.innerHTML = `
            <span class="toast-icon">${themeIcons[this.currentTheme]}</span>
            <span class="toast-text">${themeNames[this.currentTheme]}</span>
        `;
        
        // 添加样式
        Object.assign(toast.style, {
            position: 'fixed',
            top: '80px',
            right: '20px',
            background: 'rgba(0, 0, 0, 0.8)',
            color: 'white',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            borderRadius: '12px',
            padding: '12px 16px',
            fontSize: '14px',
            fontWeight: '500',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            zIndex: '10000',
            backdropFilter: 'blur(12px)',
            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.3)',
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
    
    setupThemeToggle() {
        if (!elements.themeToggle) {
            console.warn('⚠️ 主题切换按钮未找到');
            return;
        }
        
        // 移除所有现有事件监听器
        const newToggle = elements.themeToggle.cloneNode(true);
        elements.themeToggle.parentNode.replaceChild(newToggle, elements.themeToggle);
        elements.themeToggle = newToggle;
        
        // 确保按钮可点击
        elements.themeToggle.style.pointerEvents = 'auto';
        elements.themeToggle.style.cursor = 'pointer';
        elements.themeToggle.style.touchAction = 'manipulation';
        elements.themeToggle.style.userSelect = 'none';
        elements.themeToggle.style.webkitUserSelect = 'none';
        elements.themeToggle.style.webkitTapHighlightColor = 'transparent';
        elements.themeToggle.style.webkitTouchCallout = 'none';
        elements.themeToggle.style.zIndex = '10000';
        
        // 主题切换处理函数
        const handleThemeToggle = (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('🎨 主题切换按钮被点击');
            this.toggleTheme();
        };
        
        // PC端点击事件
        elements.themeToggle.addEventListener('click', handleThemeToggle, { passive: false });
        
        // 移动端触摸事件
        elements.themeToggle.addEventListener('touchstart', (e) => {
            elements.themeToggle.style.transform = 'scale(0.95)';
            elements.themeToggle.style.opacity = '0.8';
        }, { passive: true });
        
        elements.themeToggle.addEventListener('touchend', (e) => {
            e.preventDefault();
            e.stopPropagation();
            elements.themeToggle.style.transform = '';
            elements.themeToggle.style.opacity = '';
            console.log('🎨 移动端主题切换按钮被触摸');
            setTimeout(() => this.toggleTheme(), 50);
        }, { passive: false });
        
        // 键盘快捷键
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.shiftKey && e.key === 'T') {
                e.preventDefault();
                this.toggleTheme();
            }
        });
        
        console.log('✅ 主题切换按钮事件已设置');
    }
};

// ========================================
// 平台检测和URL验证
// ========================================

function detectPlatform(url) {
    if (!url) return 'unknown';
    
    for (const [platform, config] of Object.entries(supportedPlatforms)) {
        if (config.patterns.some(pattern => pattern.test(url))) {
            return platform;
        }
    }
    return 'unknown';
}

function isValidUrl(url) {
    try {
        new URL(url);
        return true;
    } catch {
        return false;
    }
}

// ========================================
// UI状态管理
// ========================================

function setButtonState(state, text = null) {
    if (!elements.downloadButton) return;
    
    // 移除所有状态类
    elements.downloadButton.classList.remove('loading', 'downloading', 'completed', 'error', 'blocked', 'analyzing', 'processing');
    
    // 添加新状态类
    elements.downloadButton.classList.add(state);
    
    // 更新按钮图标和文本
    const btnIcon = elements.downloadButton.querySelector('.btn-icon i');
    const btnText = elements.downloadButton.querySelector('.btn-text');
    
    const stateConfigs = {
        loading: { icon: 'fas fa-spinner fa-spin', text: '验证中...' },
        analyzing: { icon: 'fas fa-search fa-spin', text: '分析中...' },
        downloading: { icon: 'fas fa-download fa-spin', text: '下载中...' },
        processing: { icon: 'fas fa-cog fa-spin', text: '处理中...' },
        completed: { icon: 'fas fa-check', text: '下载完成' },
        error: { icon: 'fas fa-redo', text: '重试' },
        blocked: { icon: 'fas fa-lock', text: '无法下载' },
        default: { icon: 'fas fa-download', text: '开始下载' }
    };
    
    const config = stateConfigs[state] || stateConfigs.default;
    
    if (btnIcon) {
        btnIcon.className = config.icon;
    }
    
    if (btnText) {
        btnText.textContent = text || config.text;
    }
    
    // 禁用/启用按钮
    const disabledStates = ['loading', 'downloading', 'analyzing', 'processing'];
    elements.downloadButton.disabled = disabledStates.includes(state);
    
    console.log(`🎯 按钮状态: ${state} - ${text || config.text}`);
}

function showMessage(message, type = 'info') {
    if (!elements.statusMessage) {
        console.error('❌ statusMessage 元素不存在');
        return;
    }
    
    // 消息类型配置
    const messageTypes = {
        info: { icon: 'fas fa-info-circle', class: 'status-info' },
        success: { icon: 'fas fa-check-circle', class: 'status-success' },
        error: { icon: 'fas fa-exclamation-triangle', class: 'status-error' },
        warning: { icon: 'fas fa-exclamation-triangle', class: 'status-warning' },
        downloading: { icon: 'fas fa-download', class: 'status-downloading' },
        blocked: { icon: 'fas fa-lock', class: 'status-error' }
    };
    
    const messageConfig = messageTypes[type] || messageTypes.info;
    
    // 更新消息内容
    const statusIcon = elements.statusMessage.querySelector('.status-icon i');
    const statusText = elements.statusMessage.querySelector('.status-text');
    
    if (statusIcon) {
        statusIcon.className = messageConfig.icon;
    }
    
    if (statusText) {
        statusText.textContent = message;
    }
    
    // 更新消息容器类 - 重要：添加 visible 类以显示消息
    elements.statusMessage.className = `status-message ${messageConfig.class} visible`;
    elements.statusMessage.style.display = 'block';
    elements.statusMessage.style.opacity = '1';
    elements.statusMessage.style.visibility = 'visible';
    
    console.log(`💬 状态消息 [${type}]: ${message}`);
}

function updateProgress(percent, text, allowReset = false) {
    if (state.fatalErrorOccurred && !allowReset) {
        console.log('💀 致命错误状态下禁止更新进度条');
        return;
    }
    
    const safePercent = Math.max(0, Math.min(100, percent));
    
    // 更新进度条
    if (elements.downloadProgress) {
        elements.downloadProgress.value = safePercent;
    }
    
    // 更新百分比显示
    if (elements.progressPercentage) {
        elements.progressPercentage.textContent = `${Math.round(safePercent)}%`;
    }
    
    // 更新状态文本
    if (elements.progressStatusText) {
        elements.progressStatusText.textContent = text || '';
    }
    
    console.log(`📊 进度更新: ${safePercent}% - ${text}`);
}

function updateProgressDetails(speed, size) {
    if (elements.downloadSpeed) {
        elements.downloadSpeed.textContent = speed || '等待中...';
    }
    if (elements.downloadSize) {
        elements.downloadSize.textContent = size || '0 MB';
    }
}

function hideMessage() {
    if (elements.statusMessage) {
        elements.statusMessage.classList.remove('visible');
        elements.statusMessage.style.opacity = '0';
        setTimeout(() => {
            if (elements.statusMessage) {
                elements.statusMessage.style.display = 'none';
            }
        }, 300);
        console.log('💬 状态消息已隐藏');
    }
}

// 完全重置所有状态和UI
function completeReset() {
    console.log('🧹 === 执行完全状态重置 ===');
    
    // 停止所有进行中的操作
    stopProgressPolling();
    
    if (state.abortController) {
        state.abortController.abort();
        state.abortController = null;
    }
    
    // 重置状态
    Object.assign(state, {
        isDownloading: false,
        isRetrying: false,
        currentDownloadId: null,
        currentPlatform: null,
        progressInterval: null,
        retryCount: 0,
        downloadStartTime: null,
        fatalErrorOccurred: false,
        currentPollCount: 0,
        lastProgressData: null,
        lastProgressTime: null,
        isProgressStuck: false
    });
    
    // 重置UI
    setButtonState('normal');
    hideMessage();
    hideProgressContainer();
    
    // 隐藏下载结果
    if (elements.downloadResult) {
        elements.downloadResult.style.display = 'none';
        elements.downloadResult.classList.remove('visible');
    }
    
    // 重置进度条
    updateProgress(0, '', true);
    updateProgressDetails('等待中...', '0 MB');
    
    // 清空输入框
    if (elements.videoUrl) {
        elements.videoUrl.value = '';
    }
    
    console.log('✅ 完全状态重置完成');
}

// ========================================
// 网络请求工具
// ========================================

function fetchWithTimeout(url, options = {}, timeout = 10000) {
    return new Promise((resolve, reject) => {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => {
            controller.abort();
            reject(new Error('请求超时'));
        }, timeout);
        
        fetch(url, {
            ...options,
            signal: controller.signal
        })
        .then(response => {
            clearTimeout(timeoutId);
            resolve(response);
        })
        .catch(error => {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                reject(new Error('请求超时'));
            } else {
                reject(error);
            }
        });
    });
}

// ========================================
// 错误处理和分析
// ========================================

function identifyErrorType(errorMessage) {
    const errorKeywords = {
        payment_required: ['付费', 'payment', 'premium', 'subscription', 'vip', 'member'],
        auth_required: ['登录', 'login', 'authentication', 'sign in', 'unauthorized'],
        region_blocked: ['地区', 'region', 'country', 'location', 'geo', 'blocked'],
        access_denied: ['私有', 'private', 'access denied', 'forbidden', '403'],
        age_restricted: ['年龄', 'age restricted', '18+', 'mature'],
        live_content: ['直播', 'live', 'streaming', 'broadcast'],
        network_error: ['网络', 'network', 'connection', 'timeout', 'connect']
    };
    
    const message = errorMessage.toLowerCase();
    
    for (const [type, keywords] of Object.entries(errorKeywords)) {
        if (keywords.some(keyword => message.includes(keyword))) {
            return type;
        }
    }
    
    return 'unknown';
}

// ========================================
// 状态重置和清理
// ========================================

function resetStateForNewDownload() {
    console.log('🔄 重置状态准备新下载');
    
    state.isDownloading = false;
    state.isRetrying = false;
    state.currentDownloadId = null;
    state.fatalErrorOccurred = false;
    state.retryCount = 0;
    state.lastRetryTime = 0;
    state.downloadStartTime = null;
    state.currentPollCount = 0;
    state.lastProgressData = null;
    state.lastProgressTime = null;
    state.isProgressStuck = false;
    
    // 取消现有的AbortController
    if (state.abortController) {
        state.abortController.abort();
    }
    state.abortController = new AbortController();
    
    stopProgressPolling();
    
    // 重置UI元素
    hideProgressContainer();
    hideMessage();
    
    if (elements.downloadResult) {
        elements.downloadResult.style.display = 'none';
    }
    
    if (elements.loadingOverlay) {
        elements.loadingOverlay.style.display = 'none';
    }
    
    if (elements.successAnimation) {
        elements.successAnimation.style.display = 'none';
    }
}

// 完全重置应用状态
function completeReset() {
    console.log('🔄 完全重置应用状态');
    
    resetStateForNewDownload();
    setButtonState('default');
    updateProgress(0, '等待开始下载...', true);
    updateProgressDetails('等待中...', '0 MB');
    
    // 隐藏所有状态元素
    if (elements.statusMessage) {
        elements.statusMessage.style.display = 'none';
    }
    
    if (elements.progressContainer) {
        elements.progressContainer.style.display = 'none';
    }
    
    if (elements.downloadResult) {
        elements.downloadResult.style.display = 'none';
    }
    
    if (elements.loadingOverlay) {
        elements.loadingOverlay.style.display = 'none';
    }
    
    if (elements.successAnimation) {
        elements.successAnimation.style.display = 'none';
    }
    
    console.log('✅ 应用状态重置完成');
}

function stopProgressPolling() {
    if (state.progressInterval) {
        clearInterval(state.progressInterval);
        state.progressInterval = null;
        console.log('⏹️ 进度轮询已停止');
    }
}

// ========================================
// ========================================
// 模拟进度更新
// ========================================

function simulateProgress(targetPercent, duration, message) {
    return new Promise((resolve) => {
        if (state.fatalErrorOccurred) {
            console.log('💀 致命错误状态，跳过进度模拟');
            resolve();
            return;
        }
        
        const currentPercent = elements.downloadProgress ? elements.downloadProgress.value : 0;
        const increment = (targetPercent - currentPercent) / 10;
        let current = currentPercent;
        
        const interval = setInterval(() => {
            if (!state.isDownloading || state.fatalErrorOccurred) {
                clearInterval(interval);
                resolve();
                return;
            }
            
            current += increment;
            if (current >= targetPercent) {
                current = targetPercent;
                clearInterval(interval);
                resolve();
            }
            updateProgress(current, message);
        }, duration / 10);
    });
}

// ========================================
// 下载流程
// ========================================

async function startDownloadProcess(url) {
    console.log('🚀 === 开始下载流程 ===');
    
    try {
        // 检查是否已在下载中
        if (state.isDownloading) {
            console.log('⚠️ 已有下载任务进行中，跳过新请求');
            return;
        }
        
        // 先隐藏之前的下载结果（如果有）
        if (elements.downloadResult) {
            elements.downloadResult.style.display = 'none';
            elements.downloadResult.classList.remove('visible');
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
        await simulateProgress(15, 800, `正在验证${platformName}视频链接...`);
        showMessage(`${platformName}链接验证成功，正在连接服务器...`, 'info');
        
        // 阶段2：连接服务器
        await simulateProgress(25, 600, '正在连接下载服务器...');
        showMessage('服务器连接成功，正在发送下载请求...', 'info');
        
        // 阶段3：发送下载请求
        setButtonState('analyzing');
        updateProgress(30, '正在发送下载请求...');
        
        const response = await fetchWithTimeout('/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: url })
        }, 30000);
        
        console.log('📥 收到服务器响应:', response.status);
        
        await simulateProgress(35, 400, '正在处理服务器响应...');
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ 
                error: `服务器响应错误: ${response.status}` 
            }));
            throw new Error(errorData.error || `服务器错误: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('📊 解析响应数据:', result);
        
        // 检查是否立即失败
        if (result.error) {
            const errorType = identifyErrorType(result.error);
            const fatalErrors = ['payment_required', 'auth_required', 'region_blocked', 'access_denied', 'age_restricted', 'live_content'];
            
            if (fatalErrors.includes(errorType) || result.fatal) {
                console.log('💀 服务器返回致命错误，立即停止');
                state.fatalErrorOccurred = true;
                handleSpecificError(errorType, result.error, result.error_type, result.fatal);
                return;
            }
            
            throw new Error(result.error);
        }
        
        if (result.download_id) {
            // 阶段4：开始实际下载
            console.log('🎬 开始下载任务');
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
        handleDownloadError(error);
    }
}

// ========================================
// 进度轮询
// ========================================

function startProgressPolling() {
    if (!state.currentDownloadId) {
        console.error('❌ 没有下载ID，无法开始轮询');
        handleDownloadError(new Error('下载ID丢失'));
        return;
    }
    
    console.log('🔄 开始进度轮询:', state.currentDownloadId);
    
    state.currentPollCount = 0;
    state.lastProgressTime = Date.now();
    
    stopProgressPolling();
    
    state.progressInterval = setInterval(async () => {
        if (!state.isDownloading || !state.currentDownloadId) {
            console.log('❌ 下载已停止或ID丢失，停止轮询');
            stopProgressPolling();
            return;
        }
        
        state.currentPollCount++;
        
        try {
            console.log(`📊 第${state.currentPollCount}次进度查询`);
            
            if (state.currentPollCount >= state.maxProgressPolls) {
                throw new Error('下载超时，请重试');
            }
            
            const response = await fetchWithTimeout(`/progress/${state.currentDownloadId}`, {}, 8000);
            
            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error('下载任务不存在或已过期');
                }
                throw new Error(`无法获取进度: ${response.status}`);
            }
            
            const progressData = await response.json();
            console.log('📈 进度数据:', progressData);
            
            // 检查致命错误
            if (progressData.error) {
                const errorType = identifyErrorType(progressData.error);
                const fatalErrors = ['payment_required', 'auth_required', 'region_blocked', 'access_denied', 'age_restricted', 'live_content'];
                
                if (fatalErrors.includes(errorType) || progressData.fatal) {
                    console.log('💀 检测到致命错误，立即停止轮询');
                    stopProgressPolling();
                    handleSpecificError(errorType, progressData.error, progressData.error_type, progressData.fatal);
                    return;
                }
            }
            
            state.lastProgressData = progressData;
            state.lastProgressTime = Date.now();
            handleProgressUpdate(progressData);
            
            if (['completed', 'failed'].includes(progressData.status)) {
                stopProgressPolling();
                return;
            }
            
        } catch (error) {
            console.error('❌ 进度查询失败:', error);
            stopProgressPolling();
            handleDownloadError(error);
        }
    }, 2000);
}

function handleProgressUpdate(progressData) {
    const { status, percent, message, filename, speed, downloaded_mb, download_url, error } = progressData;
    
    console.log(`📊 处理进度更新:`, status, `${percent || 0}%`);
    
    switch (status) {
        case 'starting':
            if (error) {
                const errorType = identifyErrorType(error);
                const fatalErrors = ['payment_required', 'auth_required', 'region_blocked', 'access_denied', 'age_restricted', 'live_content'];
                
                if (fatalErrors.includes(errorType) || progressData.fatal) {
                    stopProgressPolling();
                    handleSpecificError(errorType, error, progressData.error_type, progressData.fatal);
                    return;
                }
            }
            
            const startPercent = Math.max(40, percent || 0);
            updateProgress(startPercent, '正在分析视频格式...');
            updateProgressDetails('分析中...', `${downloaded_mb || 0} MB`);
            showMessage('正在分析视频信息和可用格式...', 'downloading');
            setButtonState('analyzing');
            break;
            
        case 'downloading':
            const realPercent = Math.min(Math.max(40, percent || 0), 99);
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
            
            showMessage('下载完成！', 'success');
            setButtonState('completed');
            
            if (download_url) {
                handleFileDownload(download_url, filename);
            } else {
                console.warn('⚠️ 没有收到下载链接');
                showMessage('下载完成，但无法获取文件链接', 'warning');
            }
            
            setTimeout(() => {
                completeReset();
            }, 5000);
            break;
            
        case 'failed':
            console.log('❌ 下载任务失败');
            const errorMsg = error || message || '下载失败';
            const errorType = identifyErrorType(errorMsg);
            
            const fatalErrors = ['payment_required', 'auth_required', 'region_blocked', 'access_denied', 'age_restricted', 'live_content'];
            const isFatalError = fatalErrors.includes(errorType) || progressData.fatal;
            
            if (isFatalError) {
                handleSpecificError(errorType, errorMsg, progressData.error_type, progressData.fatal);
            } else {
                updateProgress(0, '下载失败', true);
                updateProgressDetails('失败', '');
                showMessage(`下载失败: ${errorMsg}`, 'error');
                handleDownloadError(new Error(errorMsg));
            }
            break;
            
        default:
            const defaultPercent = Math.max(35, percent || 0);
            updateProgress(defaultPercent, message || '处理中...');
            showMessage(message || '正在处理...', 'info');
            break;
    }
}

// ========================================
// 错误处理
// ========================================

function handleSpecificError(errorType, errorMessage, backendErrorType = null, isFatal = null) {
    console.log(`🔍 处理特定错误: ${errorType}`);
    
    stopProgressPolling();
    
    if (state.abortController) {
        state.abortController.abort();
    }
    
    const finalErrorType = backendErrorType || errorType;
    const finalIsFatal = isFatal !== null ? isFatal : ['payment_required', 'auth_required', 'region_blocked', 'access_denied', 'age_restricted', 'live_content'].includes(finalErrorType);
    
    if (finalIsFatal) {
        state.fatalErrorOccurred = true;
        state.isDownloading = false;
    }
    
    switch (finalErrorType) {
        case 'payment_required':
            setButtonState('blocked', '付费内容');
            showMessage('该视频为付费内容，需要购买后才能下载', 'blocked');
            if (elements.progressText) {
                elements.progressText.textContent = '付费内容无法下载';
            }
            break;
            
        case 'auth_required':
            setButtonState('error', '需要登录');
            showMessage('需要登录相应平台账号才能下载该视频', 'error');
            break;
            
        case 'region_blocked':
            setButtonState('blocked', '地区限制');
            showMessage('该视频在当前地区不可观看', 'blocked');
            break;
            
        case 'access_denied':
            setButtonState('error', '无法访问');
            showMessage('视频无法访问，可能已被删除或设为私有', 'error');
            break;
            
        case 'age_restricted':
            setButtonState('blocked', '年龄限制');
            showMessage('该视频有年龄限制，需要验证身份', 'blocked');
            break;
            
        case 'live_content':
            setButtonState('blocked', '直播内容');
            showMessage('检测到直播内容，暂不支持直播下载', 'blocked');
            break;
            
        default:
            if (finalIsFatal) {
                setButtonState('error', '无法下载');
                showMessage(`该视频无法下载: ${errorMessage}`, 'error');
            } else {
                handleDownloadError(new Error(errorMessage));
            }
            break;
    }
    
    setTimeout(() => {
        completeReset();
    }, finalIsFatal ? 8000 : 5000);
}

function handleDownloadError(error) {
    console.error('❌ 处理下载错误:', error);
    
    stopProgressPolling();
    
    const errorMessage = error.message || '未知错误';
    const errorType = identifyErrorType(errorMessage);
    
    const fatalErrors = ['payment_required', 'auth_required', 'region_blocked', 'access_denied', 'age_restricted', 'live_content'];
    if (fatalErrors.includes(errorType) || state.fatalErrorOccurred) {
        state.fatalErrorOccurred = true;
        state.isDownloading = false;
        handleSpecificError(errorType, errorMessage);
        return;
    }
    
    updateProgress(0, '下载失败', true);
    updateProgressDetails('失败', '');
    showMessage(`下载失败: ${errorMessage}`, 'error');
    setButtonState('error');
    
    // 重试逻辑
    const currentTime = Date.now();
    const timeSinceLastRetry = currentTime - state.lastRetryTime;
    
    if (state.retryCount < state.maxRetries && timeSinceLastRetry >= state.retryInterval && !state.isRetrying) {
        state.isRetrying = true;
        
        setTimeout(() => {
            state.retryCount++;
            state.lastRetryTime = Date.now();
            console.log(`🔄 自动重试 (${state.retryCount}/${state.maxRetries})`);
            showMessage(`正在重试... (${state.retryCount}/${state.maxRetries})`, 'warning');
            
            const url = elements.videoUrl.value.trim();
            if (url && state.retryCount <= state.maxRetries && !state.fatalErrorOccurred) {
                state.isRetrying = false;
                state.isDownloading = false;
                startDownloadProcess(url);
            } else {
                state.isRetrying = false;
                completeReset();
            }
        }, state.retryInterval);
    } else {
        setTimeout(() => {
            completeReset();
        }, 5000);
    }
}

// ========================================
// 文件下载处理
// ========================================

function handleFileDownload(downloadUrl, filename) {
    try {
        console.log('📥 开始文件下载:', filename);
        
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        
        if (isMobile) {
            showMessage('📱 移动设备下载中，请稍候...', 'downloading');
        }
        
        showDownloadResult(downloadUrl, filename);
        
        setTimeout(() => {
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.download = filename || 'video.mp4';
            link.style.display = 'none';
            
            if (isMobile) {
                link.target = '_blank';
                link.rel = 'noopener noreferrer';
            }
            
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            if (isMobile) {
                showMessage('📱 下载完成！已优化移动设备兼容性', 'success');
            } else {
                showMessage('💻 下载完成！文件已保存到下载文件夹', 'success');
            }
        }, isMobile ? 2000 : 500);
        
    } catch (error) {
        console.error('❌ 文件下载失败:', error);
        showMessage('下载失败，请重试', 'error');
    }
}

function showDownloadResult(downloadUrl, filename) {
    if (!elements.downloadResult) {
        console.error('❌ downloadResult 元素不存在');
        return;
    }
    
    try {
        // 隐藏进度容器
        if (elements.progressContainer) {
            elements.progressContainer.style.display = 'none';
        }
        
        // 更新文件信息
        if (elements.resultFileName) {
            elements.resultFileName.textContent = filename || '视频文件';
        }
        
        if (elements.resultFileSize && state.lastProgressData?.file_size_mb) {
            elements.resultFileSize.textContent = `${state.lastProgressData.file_size_mb.toFixed(2)} MB`;
        } else if (elements.resultFileSize) {
            elements.resultFileSize.textContent = '完成';
        }
        
        // 显示下载结果 - 重要：添加visible类
        elements.downloadResult.style.display = 'block';
        elements.downloadResult.style.opacity = '1';
        elements.downloadResult.style.visibility = 'visible';
        elements.downloadResult.classList.add('visible');
        
        // 成功动画
        if (elements.successAnimation) {
            elements.successAnimation.style.display = 'block';
            setTimeout(() => {
                if (elements.successAnimation) {
                    elements.successAnimation.style.display = 'none';
                }
            }, 3000);
        }
        
        // 设置下载按钮事件
        setupDownloadFileButton(downloadUrl, filename);
        
        console.log('✅ 下载结果界面已显示');
        
    } catch (error) {
        console.error('❌ 显示下载结果失败:', error);
    }
}

function setupDownloadFileButton(downloadUrl, filename) {
    if (!elements.downloadFileBtn) {
        console.warn('下载文件按钮未找到');
        return;
    }
    
    // 移除所有现有事件监听器
    const newBtn = elements.downloadFileBtn.cloneNode(true);
    elements.downloadFileBtn.parentNode.replaceChild(newBtn, elements.downloadFileBtn);
    elements.downloadFileBtn = newBtn;
    
    // 确保按钮可点击
    elements.downloadFileBtn.style.pointerEvents = 'auto';
    elements.downloadFileBtn.style.cursor = 'pointer';
    elements.downloadFileBtn.style.touchAction = 'manipulation';
    elements.downloadFileBtn.style.userSelect = 'none';
    elements.downloadFileBtn.style.webkitTapHighlightColor = 'transparent';
    
    const handleFileDownload = (e) => {
        e.preventDefault();
        e.stopPropagation();
        
        try {
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.download = filename || 'video.mp4';
            link.style.display = 'none';
            
            const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
            if (isMobile) {
                link.target = '_blank';
                link.rel = 'noopener noreferrer';
            }
            
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            showMessage(isMobile ? '📱 移动设备下载启动！' : '💻 文件下载已启动！', 'success');
            
        } catch (error) {
            console.error('❌ 文件下载失败:', error);
            showMessage('下载失败，请重试', 'error');
        }
    };
    
    // PC端点击事件
    elements.downloadFileBtn.addEventListener('click', handleFileDownload, { passive: false });
    
    // 移动端触摸反馈
    elements.downloadFileBtn.addEventListener('touchstart', (e) => {
        elements.downloadFileBtn.style.transform = 'scale(0.98)';
        elements.downloadFileBtn.style.opacity = '0.9';
    }, { passive: true });
    
    elements.downloadFileBtn.addEventListener('touchend', (e) => {
        elements.downloadFileBtn.style.transform = '';
        elements.downloadFileBtn.style.opacity = '';
    }, { passive: true });
    
    console.log('✅ 文件下载按钮事件已设置');
}

// ========================================
// 事件监听器设置
// ========================================

function setupEventListeners() {
    console.log('🎯 设置事件监听器...');
    
    // 设置下载按钮
    setupDownloadButton();
    
    // URL输入框事件
    if (elements.videoUrl) {
        elements.videoUrl.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                if (!state.isDownloading && !state.isRetrying) {
                    elements.downloadButton?.click();
                }
            }
        });
        
        elements.videoUrl.addEventListener('paste', () => {
            setTimeout(() => {
                const url = elements.videoUrl.value.trim();
                if (url && detectPlatform(url) !== 'unknown') {
                    showMessage('检测到支持的视频链接', 'info');
                }
            }, 100);
        });
    }
    
    // 页面可见性变化处理
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden && state.currentDownloadId && !state.progressInterval && state.isDownloading) {
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
        completeReset();
    });
    
    console.log('✅ 事件监听器设置完成');
}

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
    elements.downloadButton.style.webkitTapHighlightColor = 'transparent';
    
    const handleDownloadClick = async (e) => {
        e.preventDefault();
        e.stopPropagation();
        console.log('🎯 === 下载按钮被点击 ===');
        
        if (state.isDownloading || state.isRetrying) {
            console.log('⚠️ 下载任务进行中，忽略重复点击');
            showMessage('下载任务正在进行中，请勿重复点击', 'warning');
            return;
        }
        
        const url = elements.videoUrl.value.trim();
        if (!url) {
            showMessage('请输入有效的视频URL', 'error');
            elements.videoUrl.focus();
            return;
        }
        
        const platform = detectPlatform(url);
        if (platform === 'unknown') {
            showMessage('请输入支持的平台视频链接', 'error');
            elements.videoUrl.focus();
            return;
        }
        
        console.log(`✅ URL验证通过，检测到${supportedPlatforms[platform].name}链接`);
        
        resetStateForNewDownload();
        await startDownloadProcess(url);
    };
    
    // PC端点击事件
    elements.downloadButton.addEventListener('click', handleDownloadClick, { passive: false });
    
    // 移动端触摸事件
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

// ========================================
// 移动端优化
// ========================================

function initMobileOptimizations() {
    console.log('🚀 初始化移动端优化...');
    
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    const isTablet = /iPad|Android.*(?=.*Tablet)/i.test(navigator.userAgent);
    
    if (isMobile || isTablet) {
        document.body.classList.add('is-mobile');
        
        // 创建移动端状态指示器
        createMobileStatusIndicator();
        
        // 优化触摸体验
        optimizeTouchExperience();
        
        // 优化虚拟键盘
        optimizeVirtualKeyboard();
        
        console.log('✅ 移动端优化完成');
    }
}

function createMobileStatusIndicator() {
    if (document.getElementById('mobileStatusIndicator')) return;
    
    const indicator = document.createElement('div');
    indicator.className = 'mobile-status-indicator';
    indicator.id = 'mobileStatusIndicator';
    document.body.appendChild(indicator);
}

function showMobileStatus(message, type = 'info', duration = 3000) {
    const indicator = document.getElementById('mobileStatusIndicator');
    if (!indicator) return;
    
    indicator.textContent = message;
    indicator.className = `mobile-status-indicator ${type} show`;
    
    setTimeout(() => {
        indicator.classList.remove('show');
    }, duration);
}

function updateMobileProgress(percent, message) {
    const isMobile = document.body.classList.contains('is-mobile');
    if (!isMobile) return;
    
    if (percent >= 100) {
        showMobileStatus('下载完成！', 'success', 5000);
    } else if (percent > 0) {
        showMobileStatus(`${message} ${Math.round(percent)}%`, 'downloading', 1000);
    }
}

function optimizeTouchExperience() {
    const interactiveElements = document.querySelectorAll('button, .download-btn, .theme-toggle, input');
    
    interactiveElements.forEach(element => {
        element.style.touchAction = 'manipulation';
        element.style.webkitTapHighlightColor = 'transparent';
        element.style.webkitTouchCallout = 'none';
        element.style.userSelect = 'none';
        element.style.webkitUserSelect = 'none';
        
        // 触摸反馈
        element.addEventListener('touchstart', function(e) {
            if (!this.disabled) {
                this.style.transform = 'scale(0.98)';
                this.style.opacity = '0.9';
            }
        }, { passive: true });
        
        element.addEventListener('touchend', function(e) {
            this.style.transform = '';
            this.style.opacity = '';
        }, { passive: true });
    });
}

function optimizeVirtualKeyboard() {
    if (!elements.videoUrl) return;
    
    let initialViewportHeight = window.innerHeight;
    
    elements.videoUrl.addEventListener('focus', function() {
        setTimeout(() => {
            if (window.innerHeight < initialViewportHeight * 0.75) {
                document.body.classList.add('keyboard-open');
                this.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }, 300);
    });
    
    elements.videoUrl.addEventListener('blur', function() {
        document.body.classList.remove('keyboard-open');
    });
    
    window.addEventListener('resize', function() {
        if (window.innerHeight >= initialViewportHeight * 0.9) {
            document.body.classList.remove('keyboard-open');
        }
    });
}

// ========================================
// 初始化主题管理器
// ========================================

function initThemeManager() {
    try {
        themeManager.init();
        console.log('✅ 主题管理器初始化成功');
    } catch (error) {
        console.error('❌ 主题管理器初始化失败:', error);
    }
}

// ========================================
// 页面加载完成后的最终设置
// ========================================

window.addEventListener('load', () => {
    setTimeout(() => {
        // 确保所有交互元素都能正常工作
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
            }
        });
        
        console.log('🎯 页面加载完成，所有功能已就绪');
    }, 100);
});

console.log('🎉 === 视频下载器 v3.0 初始化完成 ===');
console.log('🔧 PC端和移动端完美兼容');
console.log('🎨 主题切换功能已启用');
console.log('📱 触摸交互已优化');
