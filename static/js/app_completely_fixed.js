// 🐻🐻专属视频解析器 - 完全修复版 v3.1
console.log('🚀 === 初始化视频解析器 v3.1 ===');

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
    isProgressStuck: false,
    themeMode: localStorage.getItem('theme-preference') || 'system',
    // 新增：下载状态跟踪
    hasDownloaded: false, // 用户是否已点击过下载
    parseSuccessful: false, // 解析是否成功
    currentVideoUrl: '', // 当前解析的视频URL
    currentFilename: '' // 当前文件名
};

// DOM元素映射
const elements = {};

// 支持的平台配置
const supportedPlatforms = {
    bilibili: {
        name: '哔哩哔哩',
        patterns: ['bilibili.com', 'b23.tv', 'acg.tv'],
        icon: '📺',
        color: '#fb7299'
    },
    youtube: {
        name: 'YouTube',
        patterns: ['youtube.com', 'youtu.be'],
        icon: '🎥',
        color: '#ff0000'
    },
    douyin: {
        name: '抖音',
        patterns: ['douyin.com', 'iesdouyin.com'],
        icon: '🎵',
        color: '#fe2c55'
    },
    kuaishou: {
        name: '快手',
        patterns: ['kuaishou.com', 'gifshow.com'],
        icon: '⚡',
        color: '#ff6600'
    },
    weibo: {
        name: '微博',
        patterns: ['weibo.com', 'weibo.cn'],
        icon: '🐦',
        color: '#e6162d'
    },
    xiaohongshu: {
        name: '小红书',
        patterns: ['xiaohongshu.com', 'xhslink.com'],
        icon: '📖',
        color: '#ff2442'
    },
    xigua: {
        name: '西瓜视频',
        patterns: ['ixigua.com'],
        icon: '🍉',
        color: '#20b955'
    },
    twitter: {
        name: 'Twitter/X',
        patterns: ['twitter.com', 'x.com'],
        icon: '🐦',
        color: '#1da1f2'
    },
    instagram: {
        name: 'Instagram',
        patterns: ['instagram.com'],
        icon: '📷',
        color: '#e4405f'
    },
    tiktok: {
        name: 'TikTok',
        patterns: ['tiktok.com'],
        icon: '🎭',
        color: '#ff0050'
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
    if (!elements.downloadButton) console.error('❌ 解析按钮未找到');
    if (!elements.themeToggle) console.error('❌ 主题切换按钮未找到');
    if (!elements.progressContainer) console.error('❌ 进度容器未找到');
    if (!elements.downloadProgress) console.error('❌ 进度条未找到');
    
    console.log('✅ DOM元素初始化完成');
}

// ========================================
// 主题管理器
// ========================================

const themeManager = {
    init() {
        console.log('🎨 初始化主题管理器...');
        this.applyTheme();
        this.setupThemeToggle();
        
        // 监听系统主题变化
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
                if (state.themeMode === 'system') {
                    this.applyTheme();
                }
            });
        }
        
        console.log('✅ 主题管理器初始化完成');
    },
    
    applyTheme() {
        const root = document.documentElement;
        const body = document.body;
        
        // 移除现有主题类
        root.classList.remove('theme-light', 'theme-dark', 'theme-system');
        body.classList.remove('theme-light', 'theme-dark', 'theme-system');
        
        // 确定实际应用的主题
        let actualTheme = state.themeMode;
        if (state.themeMode === 'system') {
            if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                actualTheme = 'dark';
            } else {
                actualTheme = 'light';
            }
        }
        
        // 应用主题类
        root.classList.add(`theme-${actualTheme}`);
        body.classList.add(`theme-${actualTheme}`);
        root.setAttribute('data-theme', actualTheme);
        
        // 设置CSS自定义属性
        this.setCSSProperties(actualTheme);
        
        // 更新主题切换按钮
        this.updateThemeToggleIcon();
        
        console.log(`🎨 主题已切换为: ${state.themeMode} (实际显示: ${actualTheme})`);
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
            themeIcon.textContent = icons[state.themeMode];
        }
        
        if (themeText) {
            themeText.textContent = texts[state.themeMode];
        }
        
        elements.themeToggle.setAttribute('data-theme', state.themeMode);
    },
    
    setupThemeToggle() {
        if (!elements.themeToggle) {
            console.warn('主题切换按钮未找到');
            return;
        }
        
        // 确保按钮在右上角并可点击
        elements.themeToggle.style.position = 'fixed';
        elements.themeToggle.style.top = '20px';
        elements.themeToggle.style.right = '20px';
        elements.themeToggle.style.zIndex = '10000';
        elements.themeToggle.style.pointerEvents = 'auto';
        elements.themeToggle.style.cursor = 'pointer';
        elements.themeToggle.style.userSelect = 'none';
        elements.themeToggle.style.touchAction = 'manipulation';
        elements.themeToggle.style.webkitTapHighlightColor = 'transparent';
        
        // 移除所有现有事件监听器
        const newToggle = elements.themeToggle.cloneNode(true);
        elements.themeToggle.parentNode.replaceChild(newToggle, elements.themeToggle);
        elements.themeToggle = newToggle;
        
        // 重新应用样式
        elements.themeToggle.style.position = 'fixed';
        elements.themeToggle.style.top = '20px';
        elements.themeToggle.style.right = '20px';
        elements.themeToggle.style.zIndex = '10000';
        elements.themeToggle.style.pointerEvents = 'auto';
        elements.themeToggle.style.cursor = 'pointer';
        elements.themeToggle.style.userSelect = 'none';
        
        const handleThemeClick = (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('🎨 主题切换按钮被点击');
            this.cycleTheme();
        };
        
        // PC端点击事件
        elements.themeToggle.addEventListener('click', handleThemeClick, { passive: false });
        
        // 移动端触摸支持
        elements.themeToggle.addEventListener('touchstart', (e) => {
            e.preventDefault();
            elements.themeToggle.style.transform = 'scale(0.95)';
        }, { passive: false });
        
        elements.themeToggle.addEventListener('touchend', (e) => {
            e.preventDefault();
            e.stopPropagation();
            elements.themeToggle.style.transform = '';
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
        const themes = ['system', 'light', 'dark'];
        const currentIndex = themes.indexOf(state.themeMode);
        const nextIndex = (currentIndex + 1) % themes.length;
        
        state.themeMode = themes[nextIndex];
        localStorage.setItem('theme-preference', state.themeMode);
        
        this.applyTheme();
        
        // 显示切换提示
        this.showThemeChangeToast();
    },
    
    showThemeChangeToast() {
        // 移除可能存在的旧提示
        const existingToast = document.querySelector('.theme-toast');
        if (existingToast) {
            existingToast.remove();
        }
        
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
        
        // 创建新的提示元素
        const toast = document.createElement('div');
        toast.className = 'theme-toast';
        toast.innerHTML = `
            <span class="toast-icon">${themeIcons[state.themeMode]}</span>
            <span class="toast-text">${themeNames[state.themeMode]}</span>
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
    }
};

function initThemeManager() {
    themeManager.init();
}

// ========================================
// 平台检测和URL验证
// ========================================

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

// 🔥URL提取和清理函数
function extractCleanUrl(input) {
    console.log('🧹 开始提取URL:', input);
    
    if (!input || typeof input !== 'string') {
        console.log('❌ 输入无效');
        return null;
    }
    
    // 去除首尾空格
    input = input.trim();
    
    // 🔥常见URL正则模式
    const urlPatterns = [
        // YouTube 完整URL和短链接
        /(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:watch\?v=|embed\/|v\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})/,
        // B站完整URL
        /(?:https?:\/\/)?(?:www\.)?bilibili\.com\/video\/([A-Za-z0-9]+)/,
        // B站短链接
        /(?:https?:\/\/)?b23\.tv\/([A-Za-z0-9]+)/,
        // 抖音URL
        /(?:https?:\/\/)?(?:www\.)?douyin\.com\/video\/(\d+)/,
        // 抖音短链接
        /(?:https?:\/\/)?v\.douyin\.com\/([A-Za-z0-9]+)/,
        // 快手URL
        /(?:https?:\/\/)?(?:www\.)?kuaishou\.com\/short-video\/(\d+)/,
        // 微博视频
        /(?:https?:\/\/)?(?:www\.)?weibo\.com\/tv\/show\/(\d+)/,
        // 西瓜视频
        /(?:https?:\/\/)?(?:www\.)?ixigua\.com\/(\d+)/,
        // 通用URL模式（最后兜底）
        /https?:\/\/[^\s]+/
    ];
    
    // 🔥方法1：尝试直接匹配URL模式
    for (const pattern of urlPatterns) {
        const match = input.match(pattern);
        if (match) {
            let extractedUrl = match[0];
            
            // 确保URL有协议
            if (!extractedUrl.startsWith('http')) {
                extractedUrl = 'https://' + extractedUrl;
            }
            
            console.log('✅ 通过正则提取到URL:', extractedUrl);
            return extractedUrl;
        }
    }
    
    // 🔥方法2：如果输入本身看起来像URL，直接使用
    if (input.includes('.com') || input.includes('.tv') || input.includes('.cn')) {
        // 移除可能的前缀文字
        const words = input.split(/\s+/);
        for (const word of words) {
            if (word.includes('.com') || word.includes('.tv') || word.includes('.cn')) {
                let cleanUrl = word;
                
                // 移除可能的标点符号
                cleanUrl = cleanUrl.replace(/[，。！？；：""''「」【】()（）\[\]]/g, '');
                
                // 确保有协议
                if (!cleanUrl.startsWith('http')) {
                    cleanUrl = 'https://' + cleanUrl;
                }
                
                console.log('✅ 通过域名匹配提取到URL:', cleanUrl);
                return cleanUrl;
            }
        }
    }
    
    // 🔥方法3：检查是否输入本身就是URL
    try {
        let testUrl = input;
        if (!testUrl.startsWith('http')) {
            testUrl = 'https://' + testUrl;
        }
        
        const url = new URL(testUrl);
        if (url.hostname && (url.hostname.includes('.com') || url.hostname.includes('.tv') || url.hostname.includes('.cn'))) {
            console.log('✅ 输入本身是有效URL:', testUrl);
            return testUrl;
        }
    } catch (e) {
        // URL构造失败，继续其他方法
    }
    
    console.log('❌ 未能提取到有效URL');
    return null;
}

// ========================================
// UI显示和状态管理函数
// ========================================

// 按钮状态配置
const buttonStates = {
    normal: {
        icon: 'fas fa-download',
        text: '开始解析',
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
        text: '解析中...',
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
    fatal: {
        icon: 'fas fa-exclamation-triangle',
        text: '无法下载',
        class: 'btn-fatal',
        disabled: true
    }
};

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
    
    console.log(`🎯 按钮状态: ${btnState} - ${customText || stateConfig.text}`);
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

function showProgressContainer() {
    if (elements.progressContainer) {
        elements.progressContainer.style.display = 'block';
        elements.progressContainer.style.opacity = '1';
        elements.progressContainer.style.visibility = 'visible';
        elements.progressContainer.classList.add('visible');
        console.log('📊 进度容器已显示');
    }
}

function hideProgressContainer() {
    if (elements.progressContainer) {
        elements.progressContainer.style.display = 'none';
        elements.progressContainer.classList.remove('visible');
        console.log('📊 进度容器已隐藏');
    }
}

function showDownloadResult(downloadUrl, filename) {
    if (!elements.downloadResult) {
        console.error('❌ downloadResult 元素不存在');
        return;
    }
    
    try {
        // 隐藏进度容器
        hideProgressContainer();
        
        // 更新文件信息
        if (elements.resultFileName) {
            elements.resultFileName.textContent = filename || '视频文件';
        }
        
        if (elements.resultFileSize && state.lastProgressData?.file_size_mb) {
            elements.resultFileSize.textContent = `${state.lastProgressData.file_size_mb.toFixed(2)} MB`;
        } else if (elements.resultFileSize) {
            elements.resultFileSize.textContent = '完成';
        }
        
        // 显示解析结果 - 重要：添加visible类
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
        
        // 设置返回解析界面按钮
        setupBackToParseButton();
        
        // 标记解析成功
        state.parseSuccessful = true;
        state.currentFilename = filename || '下载文件';
        
        console.log('✅ 解析结果界面已显示');
        
    } catch (error) {
        console.error('❌ 显示解析结果失败:', error);
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
        
        // 标记用户已下载
        state.hasDownloaded = true;
        console.log('✅ 用户已点击下载，状态已更新');
        
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

// 设置返回解析界面按钮
function setupBackToParseButton() {
    const backBtn = document.getElementById('backToParseBtn');
    if (!backBtn) {
        console.warn('返回解析界面按钮未找到');
        return;
    }

    // 移除所有现有事件监听器
    const newBackBtn = backBtn.cloneNode(true);
    backBtn.parentNode.replaceChild(newBackBtn, backBtn);

    // 确保按钮可点击
    newBackBtn.style.pointerEvents = 'auto';
    newBackBtn.style.cursor = 'pointer';
    newBackBtn.style.touchAction = 'manipulation';

    const handleBackToParseClick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        console.log('🔙 返回解析界面按钮被点击');

        // 检查用户是否已下载
        if (!state.hasDownloaded) {
            // 用户还没下载，弹出确认对话框
            const confirmReturn = confirm('您还没有下载视频文件，确定要返回解析界面吗？');
            if (!confirmReturn) {
                console.log('❌ 用户取消返回');
                return;
            }
        }

        // 执行返回操作
        console.log('✅ 执行返回解析界面');
        returnToParseInterface();
    };

    // PC端点击事件
    newBackBtn.addEventListener('click', handleBackToParseClick, { passive: false });

    // 移动端触摸事件
    newBackBtn.addEventListener('touchstart', (e) => {
        newBackBtn.style.transform = 'scale(0.98)';
        newBackBtn.style.opacity = '0.9';
    }, { passive: true });

    newBackBtn.addEventListener('touchend', (e) => {
        newBackBtn.style.transform = '';
        newBackBtn.style.opacity = '';
    }, { passive: true });

    console.log('✅ 返回解析界面按钮事件已设置');
}

// 返回解析界面函数
function returnToParseInterface() {
    console.log('🔄 开始返回解析界面');
    
    // 重置状态
    state.hasDownloaded = false;
    state.parseSuccessful = false;
    state.currentVideoUrl = '';
    state.currentFilename = '';
    state.isDownloading = false;
    state.currentDownloadId = null;
    state.fatalErrorOccurred = false;
    
    // 隐藏下载结果
    if (elements.downloadResult) {
        elements.downloadResult.style.display = 'none';
    }
    
    // 隐藏进度容器
    if (elements.progressContainer) {
        elements.progressContainer.style.display = 'none';
    }
    
    // 隐藏状态消息
    if (elements.statusMessage) {
        elements.statusMessage.style.display = 'none';
    }
    
    // 重置按钮状态
    setButtonState('initial');
    
    // 聚焦到输入框
    if (elements.videoUrl) {
        elements.videoUrl.focus();
    }
    
    console.log('✅ 已返回解析界面');
    showMessage('已返回解析界面，可以解析新的视频', 'info');
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
    
    // 隐藏解析结果
    if (elements.downloadResult) {
        elements.downloadResult.style.display = 'none';
        elements.downloadResult.classList.remove('visible');
    }
    
    // 重置进度条
    updateProgress(0, '', true);
    updateProgressDetails('等待中...', '0 MB');
    
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
        
        // 检测移动设备并添加适合的请求头
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        
        // 移动端优化的请求头
        const mobileHeaders = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        };
        
        // 合并请求头
        const enhancedOptions = {
            ...options,
            headers: {
                ...mobileHeaders,
                ...options.headers
            },
            signal: controller.signal
        };
        
        fetch(url, enhancedOptions)
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
        network_error: ['network', 'timeout', '网络', '超时', 'connection']
    };
    
    const message = errorMessage.toLowerCase();
    
    for (const [type, keywords] of Object.entries(errorKeywords)) {
        if (keywords.some(keyword => message.includes(keyword.toLowerCase()))) {
            return type;
        }
    }
    
    return 'unknown';
}

// ========================================
// 进度轮询管理
// ========================================

function stopProgressPolling() {
    if (state.progressInterval) {
        clearInterval(state.progressInterval);
        state.progressInterval = null;
        console.log('⏹️ 进度轮询已停止');
    }
}

function startProgressPolling() {
    if (!state.currentDownloadId) {
        console.error('❌ 没有解析ID，无法开始轮询');
        handleDownloadError(new Error('解析ID丢失'));
        return;
    }
    
    console.log('🔄 开始进度轮询:', state.currentDownloadId);
    
    state.currentPollCount = 0;
    state.lastProgressTime = Date.now();
    
    stopProgressPolling();
    
    state.progressInterval = setInterval(async () => {
        if (!state.isDownloading || !state.currentDownloadId) {
            console.log('❌ 解析已停止或ID丢失，停止轮询');
            stopProgressPolling();
            return;
        }
        
        state.currentPollCount++;
        
        try {
            console.log(`📊 第${state.currentPollCount}次进度查询`);
            
            if (state.currentPollCount >= state.maxProgressPolls) {
                throw new Error('解析超时，请重试');
            }
            
            const response = await fetchWithTimeout(`/progress/${state.currentDownloadId}`, {}, 8000);
            
            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error('解析任务不存在或已过期');
                }
                throw new Error(`无法获取进度: ${response.status}`);
            }
            
            const progressData = await response.json();
            console.log('📈 进度数据:', progressData);
            
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
            const startPercent = Math.max(40, percent || 0);
            updateProgress(startPercent, '正在分析视频格式...');
            updateProgressDetails('分析中...', `${downloaded_mb || 0} MB`);
            showMessage('正在分析视频信息和可用格式...', 'downloading');
            setButtonState('analyzing');
            break;
            
        case 'downloading':
            const realPercent = Math.min(Math.max(40, percent || 0), 99);
            let progressMsg = '正在解析视频文件...';
            let statusMsg = '正在解析视频...';
            
            if (speed && downloaded_mb !== undefined) {
                progressMsg = `解析中... (${speed})`;
                statusMsg = `正在解析 - ${speed} - 已完成 ${downloaded_mb.toFixed(1)}MB`;
                updateProgressDetails(speed, `${downloaded_mb.toFixed(1)} MB`);
            }
            
            updateProgress(realPercent, progressMsg);
            showMessage(statusMsg, 'downloading');
            setButtonState('downloading', `解析中 ${Math.round(realPercent)}%`);
            break;
            
        case 'finished':
            updateProgress(95, '解析完成，正在处理文件...');
            updateProgressDetails('处理中...', state.lastProgressData?.downloaded_mb ? `${state.lastProgressData.downloaded_mb.toFixed(1)} MB` : '');
            showMessage('视频解析完成，正在进行后处理...', 'downloading');
            setButtonState('processing');
            break;
            
        case 'completed':
            console.log('✅ 解析任务完成');
            updateProgress(100, '解析完成！');
            updateProgressDetails('已完成', filename || '');
            
            showMessage('下载完成！', 'success');
            setButtonState('completed');
            
            if (download_url) {
                showDownloadResult(download_url, filename);
            } else {
                console.warn('⚠️ 没有收到下载链接');
                showMessage('下载完成，但无法获取文件链接', 'warning');
            }
            
            setTimeout(() => {
                completeReset();
            }, 10000);
            break;
            
        case 'failed':
            console.log('❌ 下载任务失败');
            const errorMsg = error || message || '下载失败';
            updateProgress(0, '下载失败', true);
            updateProgressDetails('失败', '');
            showMessage(`下载失败: ${errorMsg}`, 'error');
            
            // 🔥使用后端提供的详细错误信息，包括fatal和error_type
            const errorInfo = {
                message: errorMsg,
                error_type: progressData.error_type || 'unknown_error',
                fatal: progressData.fatal !== undefined ? progressData.fatal : false,
                user_friendly: progressData.user_friendly || errorMsg
            };
            
            console.log('🔍 错误详情:', errorInfo);
            
            // 创建包含结构化信息的错误对象
            const structuredError = new Error(errorInfo.user_friendly);
            structuredError.error_type = errorInfo.error_type;
            structuredError.fatal = errorInfo.fatal;
            
            handleDownloadError(structuredError);
            break;
            
        default:
            const defaultPercent = Math.max(35, percent || 0);
            updateProgress(defaultPercent, message || '处理中...');
            showMessage(message || '正在处理...', 'info');
            break;
    }
}

// ========================================
// 下载流程
// ========================================

// 模拟进度更新
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
            throw new Error(result.error);
        }
        
        // 成功获取下载ID
        if (result.download_id) {
            state.currentDownloadId = result.download_id;
            console.log('✅ 获取下载ID:', state.currentDownloadId);
            
            updateProgress(40, '开始解析任务...');
            showMessage('解析任务已创建，正在开始解析...', 'downloading');
            setButtonState('downloading');
            
            // 开始进度轮询
            startProgressPolling();
        } else {
            throw new Error('未收到下载ID');
        }
        
    } catch (error) {
        console.error('❌ 下载流程出错:', error);
        handleDownloadError(error);
    }
}

function handleDownloadError(error) {
    console.error('❌ 下载错误:', error);
    
    stopProgressPolling();
    state.isDownloading = false;
    
    // 简化错误处理
    let errorMessage = '解析失败';
    let errorType = 'unknown_error';
    let isFatal = false;
    
    // 🔥优先检查结构化错误对象
    if (error && typeof error === 'object') {
        if (error.error_type !== undefined && error.fatal !== undefined) {
            errorMessage = error.user_friendly || error.error || error.message || '下载失败';
            errorType = error.error_type;
            isFatal = error.fatal;
            console.log('🎯 使用结构化错误信息:', { errorType, isFatal, errorMessage });
        } else if (error.message) {
            errorMessage = error.message;
        }
    } else if (typeof error === 'string') {
        errorMessage = error;
    }
    
    // 🔥简化的错误类型识别：只关心是否致命
    if (errorType === 'unknown_error') {
        const errorLower = errorMessage.toLowerCase();
        
        // 只有这些才是真正致命的
        if (errorLower.includes('付费内容') || errorLower.includes('payment_required')) {
            errorType = 'payment_required';
            isFatal = true;
        } else if (errorLower.includes('需要登录') || errorLower.includes('auth_required')) {
            errorType = 'auth_required';
            isFatal = true;
        } else if (errorLower.includes('已被删除') || errorLower.includes('私有') || errorLower.includes('不存在')) {
            errorType = 'access_denied';
            isFatal = true;
        } else {
            // 其他所有错误都可以重试
            errorType = 'retryable_error';
            isFatal = false;
            errorMessage = '下载遇到问题，正在准备重试...';
        }
    }
    
    console.log(`🔍 错误分析: 类型=${errorType}, 致命=${isFatal}, 消息=${errorMessage}`);
    
    // 更新UI
    updateProgress(0, '解析失败', true);
    updateProgressDetails('失败', '');
    
    if (isFatal) {
        showMessage(`❌ ${errorMessage}`, 'error');
        setButtonState('fatal');
        
        // 致命错误10秒后重置
        setTimeout(() => {
            if (!state.isDownloading) {
                setButtonState('normal');
            }
        }, 10000);
    } else {
        // 可重试错误
        showMessage(`⚠️ ${errorMessage}`, 'warning');
        setButtonState('error');
        
        // 可重试错误3秒后重置
        setTimeout(() => {
            if (!state.isDownloading) {
                setButtonState('normal');
            }
        }, 3000);
    }
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
        // 回车键快捷下载
        elements.videoUrl.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                if (!state.isDownloading && !state.isRetrying) {
                    elements.downloadButton?.click();
                }
            }
        });
        
        // 粘贴事件 - 平台检测和提示
        elements.videoUrl.addEventListener('paste', () => {
            setTimeout(() => {
                const url = elements.videoUrl.value.trim();
                if (url) {
                    const platform = detectPlatform(url);
                    if (platform !== 'unknown') {
                        const platformInfo = supportedPlatforms[platform];
                        showMessage(`${platformInfo.icon} 检测到${platformInfo.name}视频链接`, 'info');
                        console.log(`🎯 检测到平台: ${platformInfo.name}`);
                    } else {
                        showMessage('⚠️ 未识别的视频链接，请确认链接是否正确', 'warning');
                    }
                }
            }, 100);
        });
        
        // 输入事件 - 实时平台检测
        elements.videoUrl.addEventListener('input', () => {
            const url = elements.videoUrl.value.trim();
            if (url.length > 10) { // 避免输入太短时频繁检测
                const platform = detectPlatform(url);
                if (platform !== 'unknown') {
                    const platformInfo = supportedPlatforms[platform];
                    state.currentPlatform = platform;
                    // 不要每次输入都显示消息，只在识别到新平台时显示
                    if (state.currentPlatform !== platform) {
                        console.log(`🎯 平台检测: ${platformInfo.name}`);
                    }
                }
            }
        });
    }
    
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
    
    // 移除所有现有事件监听器
    const newButton = elements.downloadButton.cloneNode(true);
    elements.downloadButton.parentNode.replaceChild(newButton, elements.downloadButton);
    elements.downloadButton = newButton;
    
    // 重新确保样式
    elements.downloadButton.style.pointerEvents = 'auto';
    elements.downloadButton.style.cursor = 'pointer';
    elements.downloadButton.style.userSelect = 'none';
    elements.downloadButton.style.touchAction = 'manipulation';
    
    const handleDownloadClick = async (e) => {
        e.preventDefault();
        e.stopPropagation();
        console.log('🎯 === 下载按钮被点击 ===');
        
        if (state.isDownloading || state.isRetrying) {
            console.log('⚠️ 下载任务进行中，忽略重复点击');
            showMessage('下载任务正在进行中，请勿重复点击', 'warning');
            return;
        }
        
        const rawInput = elements.videoUrl.value.trim();
        if (!rawInput) {
            showMessage('请输入有效的视频URL', 'error');
            elements.videoUrl.focus();
            return;
        }
        
        console.log('🔍 原始输入:', rawInput);
        
        // 🔥提取纯净URL - 处理用户可能粘贴的"标题 + URL"格式
        const cleanUrl = extractCleanUrl(rawInput);
        if (!cleanUrl) {
            showMessage('未找到有效的视频链接，请检查输入', 'error');
            elements.videoUrl.focus();
            return;
        }
        
        console.log('🔗 提取的URL:', cleanUrl);
        
        // 🔥如果提取的URL与原始输入不同，更新输入框
        if (cleanUrl !== rawInput) {
            elements.videoUrl.value = cleanUrl;
            console.log('✨ 已自动清理输入框URL');
        }
        
        const platform = detectPlatform(cleanUrl);
        if (platform === 'unknown') {
            showMessage('请输入支持的平台视频链接', 'error');
            elements.videoUrl.focus();
            return;
        }
        
        console.log(`✅ URL验证通过，检测到${supportedPlatforms[platform].name}链接`);
        
        // 开始下载
        await startDownloadProcess(cleanUrl);
    };
    
    // PC端点击事件
    elements.downloadButton.addEventListener('click', handleDownloadClick, { passive: false });
    
    // 移动端触摸事件
    elements.downloadButton.addEventListener('touchstart', (e) => {
        elements.downloadButton.style.transform = 'scale(0.98)';
        elements.downloadButton.style.opacity = '0.9';
    }, { passive: true });
    
    elements.downloadButton.addEventListener('touchend', (e) => {
        elements.downloadButton.style.transform = '';
        elements.downloadButton.style.opacity = '';
    }, { passive: true });
    
    console.log('✅ 下载按钮事件已设置');
}

// ========================================
// 移动端优化
// ========================================

function initMobileOptimizations() {
    console.log('📱 初始化移动端优化...');
    
    // 检测移动设备
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    
    if (isMobile) {
        document.body.classList.add('is-mobile');
        
        // 防止双击缩放
        let lastTouchEnd = 0;
        document.addEventListener('touchend', function (event) {
            const now = (new Date()).getTime();
            if (now - lastTouchEnd <= 300) {
                event.preventDefault();
            }
            lastTouchEnd = now;
        }, false);
        
        // 优化触摸响应
        document.documentElement.style.setProperty('-webkit-tap-highlight-color', 'transparent');
        document.documentElement.style.setProperty('-webkit-touch-callout', 'none');
        document.documentElement.style.setProperty('-webkit-user-select', 'none');
        
        console.log('📱 移动端优化已应用');
    }
}

// 页面卸载前清理
window.addEventListener('beforeunload', (e) => {
    if (state.isDownloading) {
        e.preventDefault();
        e.returnValue = '下载正在进行中，确定要离开吗？';
    }
    completeReset();
});

console.log('✅ 视频下载器初始化脚本加载完成');
