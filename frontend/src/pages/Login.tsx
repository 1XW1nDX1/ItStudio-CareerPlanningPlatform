import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ShaderBackground from '../components/ui/ShaderBackground';
import { authApi } from '../api/auto';

type AuthMode = 'login' | 'register' | 'reset';

const Login: React.FC = () => {
    const [mode, setMode] = useState<AuthMode>('login');
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [email, setEmail] = useState('');
    const [code, setCode] = useState('');
    const [loading, setLoading] = useState(false);
    const [countdown, setCountdown] = useState(0);
    const navigate = useNavigate();

    // 验证码倒计时
    useEffect(() => {
        if (countdown <= 0) return;
        const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
        return () => clearTimeout(timer);
    }, [countdown]);

    // 切换模式时清空表单
    const switchMode = (m: AuthMode) => {
        setMode(m);
        setUsername('');
        setPassword('');
        setEmail('');
        setCode('');
    };

    const handleSendCode = async () => {
        if (!email) { alert('请输入邮箱'); return; }
        if (countdown > 0) return;
        try {
            await authApi.askCode(email, mode === 'register' ? 'register' : 'reset');
            setCountdown(60);
        } catch (e: any) {
            alert('发送失败: ' + (e.message || '请稍后重试'));
        }
    };

    const handleLogin = async () => {
        if (!username || !password) { alert('请输入账号和密码'); return; }
        setLoading(true);
        try {
            const res = await authApi.login({ username, password });
            localStorage.setItem('token', res.token);
            localStorage.setItem('username', res.username || username);
            localStorage.setItem('role', res.role || '');
            navigate('/');
        } catch (e: any) {
            alert('登录失败: ' + (e.message || '请检查后端是否启动'));
        } finally {
            setLoading(false);
        }
    };

    const handleRegister = async () => {
        if (!email || !code || !username || !password) { alert('请填写所有字段'); return; }
        setLoading(true);
        try {
            await authApi.register({ email, code, username, password });
            alert('注册成功，请登录');
            switchMode('login');
        } catch (e: any) {
            alert('注册失败: ' + (e.message || '请稍后重试'));
        } finally {
            setLoading(false);
        }
    };

    const handleReset = async () => {
        if (!email || !code || !password) { alert('请填写所有字段'); return; }
        setLoading(true);
        try {
            await authApi.reset({ email, code, password });
            alert('密码重置成功，请登录');
            switchMode('login');
        } catch (e: any) {
            alert('重置失败: ' + (e.message || '请稍后重试'));
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = () => {
        if (mode === 'login') handleLogin();
        else if (mode === 'register') handleRegister();
        else handleReset();
    };

    const titles: Record<AuthMode, string> = { login: '登录', register: '注册', reset: '重置密码' };
    const submitLabels: Record<AuthMode, string> = { login: '登录系统', register: '注册账号', reset: '重置密码' };
    const loadingLabels: Record<AuthMode, string> = { login: '正在连接神枢...', register: '正在注册...', reset: '正在重置...' };

    const inputStyle: React.CSSProperties = {
        width: '100%', padding: '14px 16px', borderRadius: '12px',
        border: '1px solid rgba(255,255,255,0.8)', background: 'rgba(255,255,255,0.5)',
        outline: 'none', fontSize: '14px', color: '#1e293b',
    };

    return (
        <div style={{ position: 'relative', width: '100vw', height: '100vh', overflow: 'hidden', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
            <ShaderBackground />
            <div className="glass-panel" style={{ zIndex: 10, width: '420px', padding: '40px', display: 'flex', flexDirection: 'column', alignItems: 'center', animation: 'fadeIn 0.6s ease-out' }}>
                <div className="logo-glow" style={{ width: '48px', height: '48px', marginBottom: '16px', boxShadow: '0 0 30px #0ea5e9' }}></div>
                <h2 className="text-gradient" style={{ margin: '0 0 8px 0', fontSize: '28px', fontWeight: 800 }}>雪雪职业AI</h2>
                <p style={{ color: '#64748b', fontSize: '14px', marginBottom: '24px' }}>Neo4j 知识图谱 · AI 生涯引擎</p>

                {/* 模式切换 Tab */}
                <div style={{ display: 'flex', gap: '4px', width: '100%', background: 'rgba(241,245,249,0.7)', borderRadius: '12px', padding: '4px', marginBottom: '24px' }}>
                    {(['login', 'register', 'reset'] as AuthMode[]).map(m => (
                        <button key={m} onClick={() => switchMode(m)} style={{
                            flex: 1, padding: '10px', border: 'none', borderRadius: '10px',
                            fontSize: '13px', fontWeight: 700, cursor: 'pointer', transition: 'all 0.2s',
                            background: mode === m ? '#ffffff' : 'transparent',
                            color: mode === m ? '#0ea5e9' : '#64748b',
                            boxShadow: mode === m ? '0 2px 8px rgba(0,0,0,0.06)' : 'none',
                        }}>
                            {titles[m]}
                        </button>
                    ))}
                </div>

                {/* 表单字段 */}
                <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '14px', marginBottom: '24px' }}>
                    {/* 邮箱 - 注册 & 重置 */}
                    {mode !== 'login' && (
                        <input type="email" placeholder="请输入邮箱" value={email}
                            onChange={e => setEmail(e.target.value)} style={inputStyle} />
                    )}

                    {/* 验证码 + 发送按钮 - 注册 & 重置 */}
                    {mode !== 'login' && (
                        <div style={{ display: 'flex', gap: '10px' }}>
                            <input type="text" placeholder="验证码" value={code}
                                onChange={e => setCode(e.target.value)}
                                style={{ ...inputStyle, flex: 1 }} />
                            <button onClick={handleSendCode} disabled={countdown > 0} style={{
                                padding: '14px 16px', borderRadius: '12px', border: 'none',
                                background: countdown > 0 ? '#cbd5e1' : 'linear-gradient(135deg, #0ea5e9, #6366f1)',
                                color: 'white', fontSize: '13px', fontWeight: 700,
                                cursor: countdown > 0 ? 'not-allowed' : 'pointer',
                                whiteSpace: 'nowrap', minWidth: '110px',
                            }}>
                                {countdown > 0 ? `${countdown}s 后重发` : '发送验证码'}
                            </button>
                        </div>
                    )}

                    {/* 用户名 - 登录 & 注册 */}
                    {mode !== 'reset' && (
                        <input type="text" placeholder="请输入账号" value={username}
                            onChange={e => setUsername(e.target.value)} style={inputStyle} />
                    )}

                    {/* 密码 */}
                    <input type="password" placeholder={mode === 'reset' ? '请输入新密码' : '请输入密码'}
                        value={password} onChange={e => setPassword(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && handleSubmit()} style={inputStyle} />
                </div>

                {/* 提交按钮 */}
                <button onClick={handleSubmit} disabled={loading} style={{
                    width: '100%', padding: '14px', borderRadius: '12px', border: 'none',
                    background: 'linear-gradient(135deg, #0ea5e9, #6366f1)', color: 'white',
                    fontSize: '16px', fontWeight: 700,
                    cursor: loading ? 'not-allowed' : 'pointer',
                    boxShadow: '0 10px 20px rgba(14, 165, 233, 0.2)', transition: 'transform 0.2s',
                }}>
                    {loading ? loadingLabels[mode] : submitLabels[mode]}
                </button>

                {/* 底部快捷链接 */}
                {mode === 'login' && (
                    <div style={{ marginTop: '20px', display: 'flex', gap: '24px', fontSize: '13px' }}>
                        <span style={{ color: '#64748b', cursor: 'pointer' }} onClick={() => switchMode('register')}>没有账号？注册</span>
                        <span style={{ color: '#64748b', cursor: 'pointer' }} onClick={() => switchMode('reset')}>忘记密码</span>
                    </div>
                )}
                {mode !== 'login' && (
                    <div style={{ marginTop: '20px', fontSize: '13px' }}>
                        <span style={{ color: '#64748b', cursor: 'pointer' }} onClick={() => switchMode('login')}>← 返回登录</span>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Login;