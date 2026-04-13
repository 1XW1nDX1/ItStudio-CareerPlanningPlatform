import React from 'react';

const Home: React.FC = () => {
    const dashboardData = { score: 95, rank: '超越 92% 竞争者' };
    const matchedJobs = [
        { id: 1, title: 'AI 大模型研究员', company: '百度 (Baidu)', matchRate: '98%', tags: ['算法', 'Python'] },
        { id: 2, title: '全栈开发工程师', company: '字节跳动 (ByteDance)', matchRate: '91%', tags: ['React', 'Spring'] },
    ];

    return (
        <div className="fade-in">
            <header style={{ marginBottom: '40px' }}>
                <h1 className="text-gradient" style={{ fontSize: '32px', margin: '0 0 8px 0' }}>欢迎探索你的无限可能</h1>
                <p style={{ color: '#64748b', margin: 0 }}>GLSL 底层引擎正在实时渲染 10,000+ 岗位知识图谱节点</p>
            </header>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '24px' }}>
                <div className="glass-panel" style={{ padding: '24px' }}>
                    <h3 style={{ margin: '0 0 20px 0', color: '#1e293b' }}>全息竞争力</h3>
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '12px' }}>
                        <span className="text-gradient" style={{ fontSize: '64px', fontWeight: 900, lineHeight: 1 }}>{dashboardData.score}</span>
                        <span style={{ fontSize: '14px', fontWeight: 700, color: '#64748b' }}>INDEX</span>
                    </div>
                    <div style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '13px', fontWeight: 700, color: '#10b981', background: '#ecfdf5', padding: '4px 10px', borderRadius: '12px' }}>
                        ↗ {dashboardData.rank}
                    </div>
                </div>

                <div className="glass-panel" style={{ padding: '24px', gridColumn: 'span 2', display: 'flex', flexDirection: 'column' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px' }}>
                        <h3 style={{ margin: 0, color: '#1e293b' }}>六维能力拓扑图</h3>
                        <span style={{ padding: '4px 10px', background: 'rgba(14,165,233,0.1)', color: '#0ea5e9', borderRadius: '8px', fontSize: '12px', fontWeight: 700 }}>实时运算中</span>
                    </div>
                    <div style={{ flex: 1, border: '1px dashed #cbd5e1', borderRadius: '16px', display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '220px', background: 'rgba(248,250,252,0.5)' }}>
                        <span style={{ color: '#64748b', fontWeight: 600, fontSize: '14px' }}>[ 预留 Echarts 区域 ]</span>
                    </div>
                </div>

                <div className="glass-panel" style={{ padding: '24px', gridColumn: 'span 3' }}>
                    <h3 style={{ margin: '0 0 20px 0', color: '#1e293b' }}>AI 匹配序列</h3>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
                        {matchedJobs.map(job => (
                            <div key={job.id} style={{ padding: '20px', background: '#ffffff', borderRadius: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', border: '1px solid #e2e8f0' }}>
                                <div>
                                    <h4 style={{ margin: '0 0 8px 0', fontSize: '16px', color: '#1e293b' }}>{job.title}</h4>
                                    <div style={{ display: 'flex', gap: '6px' }}>
                                        {job.tags.map(tag => <span key={tag} style={{ padding: '2px 8px', border: '1px solid #cbd5e1', borderRadius: '6px', fontSize: '11px', color: '#64748b' }}>{tag}</span>)}
                                    </div>
                                </div>
                                <span className="text-gradient" style={{ fontSize: '24px', fontWeight: 900 }}>{job.matchRate}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Home;