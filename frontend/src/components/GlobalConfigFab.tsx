import React, { useState, useEffect, useRef, useCallback } from 'react';

/* ===== 常量 ===== */
const LS_KEY = 'global-config';

const FONT_OPTIONS = [
    { value: "'Segoe UI', 'Microsoft YaHei', sans-serif", label: '现代无衬线 (Sans-serif)' },
    { value: "Georgia, 'Noto Serif SC', serif", label: '经典阅读 (Serif)' },
    { value: "'JetBrains Mono', 'Courier New', monospace", label: '极客等宽 (Monospace)' },
];

interface Config {
    darkMode: boolean;
    accentColor: string;
    fontFamily: string;
}

const DEFAULT_CONFIG: Config = {
    darkMode: true,
    accentColor: '#00f3ff',
    fontFamily: FONT_OPTIONS[0].value,
};

function loadConfig(): Config {
    try {
        const raw = localStorage.getItem(LS_KEY);
        if (raw) return { ...DEFAULT_CONFIG, ...JSON.parse(raw) };
    } catch { /* ignore */ }
    return { ...DEFAULT_CONFIG };
}

function saveConfig(cfg: Config) {
    localStorage.setItem(LS_KEY, JSON.stringify(cfg));
}

function applyConfig(cfg: Config) {
    const root = document.documentElement;
    root.style.setProperty('--primary-color', cfg.accentColor);
    root.style.setProperty('--font-family', cfg.fontFamily);
    document.body.style.fontFamily = cfg.fontFamily;
    document.body.classList.toggle('dark-mode', cfg.darkMode);
    document.body.classList.toggle('light-mode', !cfg.darkMode);
}

/* ===== 组件 ===== */
const GlobalConfigFab: React.FC = () => {
    const [open, setOpen] = useState(false);
    const [config, setConfig] = useState<Config>(loadConfig);
    const wrapperRef = useRef<HTMLDivElement>(null);

    useEffect(() => { applyConfig(config); }, []);

    const update = useCallback((patch: Partial<Config>) => {
        setConfig(prev => {
            const next = { ...prev, ...patch };
            saveConfig(next);
            applyConfig(next);
            return next;
        });
    }, []);

    useEffect(() => {
        const handler = (e: MouseEvent) => {
            if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
                setOpen(false);
            }
        };
        document.addEventListener('mousedown', handler);
        return () => document.removeEventListener('mousedown', handler);
    }, []);

    return (
        <div className="gcf-wrapper" ref={wrapperRef}>
            <button
                className={`gcf-fab ${open ? 'gcf-fab--open' : ''}`}
                title="设置"
                onClick={() => setOpen(v => !v)}
            >
                <svg viewBox="0 0 24 24" width="22" height="22" stroke="currentColor" strokeWidth="2" fill="none">
                    <circle cx="12" cy="12" r="3" />
                    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
                </svg>
            </button>

            {open && (
                <div className="gcf-panel">
                    <h3 className="gcf-title">UI 定制引擎</h3>

                    {/* 视觉模式 */}
                    <div className="gcf-item">
                        <label className="gcf-label">视觉模式 (Theme)</label>
                        <div className="gcf-theme-switch" onClick={() => update({ darkMode: !config.darkMode })}>
                            <div className={`gcf-switch-track ${config.darkMode ? '' : 'is-light'}`} />
                            <span className={`gcf-switch-label ${config.darkMode ? 'active' : ''}`}>🌙 暗黑</span>
                            <span className={`gcf-switch-label ${!config.darkMode ? 'active' : ''}`}>☀️ 明亮</span>
                        </div>
                    </div>

                    {/* 点缀色 */}
                    <div className="gcf-item">
                        <label className="gcf-label">主题点缀色 (Accent)</label>
                        <div className="gcf-color-row">
                            <input
                                type="color"
                                className="gcf-color"
                                value={config.accentColor}
                                onChange={e => update({ accentColor: e.target.value })}
                            />
                            <span className="gcf-color-hex">{config.accentColor.toUpperCase()}</span>
                        </div>
                    </div>

                    {/* 字体 */}
                    <div className="gcf-item">
                        <label className="gcf-label">全局字体 (Font)</label>
                        <select
                            className="gcf-select"
                            value={config.fontFamily}
                            onChange={e => update({ fontFamily: e.target.value })}
                        >
                            {FONT_OPTIONS.map(f => (
                                <option key={f.value} value={f.value}>{f.label}</option>
                            ))}
                        </select>
                    </div>
                </div>
            )}
        </div>
    );
};

export default GlobalConfigFab;
