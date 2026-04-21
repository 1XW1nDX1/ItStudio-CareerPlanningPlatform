
import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as echarts from 'echarts';
import { resumeApi } from '../api/resume';
import { fetchDashboard } from '../api/mock';
import type { DashboardData, RadarScore } from '../api/types';

/* ===== 维度标签映射 ===== */
const DIMENSION_META: { key: keyof Omit<RadarScore, 'totalScore'>; label: string; icon: string }[] = [
    { key: 'professionalSkill', label: '专业技能', icon: '⚡' },
    { key: 'projectExperience', label: '项目经验', icon: '🚀' },
    { key: 'communication', label: '沟通表达', icon: '💬' },
    { key: 'stressResistance', label: '抗压能力', icon: '🛡️' },
    { key: 'learningAbility', label: '学习能力', icon: '📖' },
    { key: 'innovation', label: '创新能力', icon: '💡' },
];

/** 从 DashboardData.radar 构造 RadarScore（兼容已有后端） */
function toRadarScore(d: DashboardData): RadarScore {
    const map: Record<string, number> = {};
    d.radar.forEach(r => { map[r.dimension] = r.value; });
    return {
        professionalSkill: map['专业技能'] ?? 0,
        projectExperience: map['项目经验'] ?? map['竞赛成果'] ?? 0,
        communication: map['沟通表达'] ?? 0,
        stressResistance: map['抗压能力'] ?? 0,
        learningAbility: map['学习能力'] ?? 70,
        innovation: map['创新能力'] ?? 65,
        totalScore: d.score,
    };
}

const MOCK_MATCH_LIST = [
    { id: 1, title: "Python后端研发工程师", company: "米哈游 (miHoYo)", matchRate: 86, tags: ["FastAPI", "异步I/O", "微服务架构"] },
    { id: 2, title: "AI Infra 部署工程师", company: "阿里云 (Alibaba Cloud)", matchRate: 82, tags: ["LLM本地部署", "Linux底层", "显存优化"] },
    { id: 3, title: "数据开发工程师 (ETL)", company: "字节跳动 (ByteDance)", matchRate: 79, tags: ["Pandas", "数据流水线", "特征工程"] }
];

const MOCK_MATCH_DETAILS: Record<number, Record<string, any>> = {
    1: {
        "岗位名称": "Python后端开发与微服务架构师 (实习)",
        "地理位置": { "超一线城市": 60.0, "一线城市": 30.0, "二线城市": 10.0, "三线城市": 0.0 },
        "工作时间": "弹性工时制，核心协作时间 10:30-17:30，周末双休。鼓励极客文化，适合夜猫子型开发者。",
        "岗位评分": { "专业技能": ["Python", "FastAPI/Django", "异步I/O (asyncio)", "Linux运维", "Git版本控制", "RESTful API设计"], "实习能力_score": 7, "沟通能力_score": 8, "抗压能力_score": 8, "学习能力_score": 9, "创新能力_score": 8, "总分": 8.0 },
        "薪资水平": "实习日薪 300-500元/天，转正后年薪 25W-40W。提供顶配 MacBook Pro 与独立服务器资源。"
    },
    2: {
        "岗位名称": "AI Infra 模型部署与算力优化工程师",
        "地理位置": { "超一线城市": 75.0, "一线城市": 20.0, "海外/远程": 5.0, "三线城市": 0.0 },
        "工作时间": "标准工时，但算力集群扩容或大模型训练冲刺期需接受排班与技术攻坚，享有算力自由。",
        "岗位评分": { "专业技能": ["LLMs本地化部署", "GPU显存优化", "Linux底层架构", "PyTorch运算底层", "硬件资源评估", "Python脚本自动化"], "实习能力_score": 6, "沟通能力_score": 7, "抗压能力_score": 9, "学习能力_score": 9, "创新能力_score": 9, "总分": 8.5 },
        "薪资水平": "处于行业风口，起薪极高。校招总包 40W 起步，核心算力调度团队配发期权与顶尖硬件实验环境。"
    },
    3: {
        "岗位名称": "数据开发与ETL流水线工程专家",
        "地理位置": { "超一线城市": 45.0, "一线城市": 35.0, "二线城市": 20.0, "三线城市": 0.0 },
        "工作时间": "早9晚6，业务高峰期需跟进数据跑批任务。注重代码复用性与流水线高内聚低耦合。",
        "岗位评分": { "专业技能": ["Python", "Pandas/NumPy", "数据清洗与验证", "正则表达式", "统计算法(分层抽样)", "海量CSV/JSON解析"], "实习能力_score": 8, "沟通能力_score": 8, "抗压能力_score": 7, "学习能力_score": 8, "创新能力_score": 7, "总分": 7.6 },
        "薪资水平": "数据中台核心骨干岗位。实习期薪水丰厚，正式岗在一线城市普遍 20W-35W 之间，具有广阔的业务晋升空间。"
    }
};

/* ===== 进度条子组件 ===== */
const ScoreBar: React.FC<{ label: string; value: number; max?: number }> = ({ label, value, max = 10 }) => {
    const pct = Math.min((value / max) * 100, 100);
    return (
        <div className="jd-score-row">
            <span className="jd-score-label">{label}</span>
            <div className="jd-bar-track">
                <div className="jd-bar-fill" style={{ width: `${pct}%` }} />
            </div>
            <span className="jd-score-value">{value}<span style={{ opacity: 0.5 }}>/{max}</span></span>
        </div>
    );
};

/* ===== 岗位详情弹窗 ===== */
const JobDetailModal: React.FC<{ detail: Record<string, any>; outerTags: string[]; onClose: () => void }> = ({ detail, outerTags, onClose }) => {
    const locationEntries = Object.entries(detail["地理位置"]).sort((a: any, b: any) => b[1] - a[1]);
    const maxLoc = Math.max(...locationEntries.map((e: any) => e[1]), 1);
    const scoring = detail["岗位评分"];

    return (
        <div className="jd-overlay" onClick={onClose}>
            <div className="jd-modal" onClick={e => e.stopPropagation()}>
                {/* 头部 */}
                <div className="jd-header">
                    <h2 className="jd-title">{detail["岗位名称"]}</h2>
                    <button className="jd-close" onClick={onClose}>✕</button>
                </div>

                <div className="jd-body">
                    {/* 综合评分 */}
                    <div className="jd-section">
                        <div className="jd-total-badge">
                            <span className="jd-total-num">{scoring["总分"]}</span>
                            <span className="jd-total-label">综合评分</span>
                        </div>
                    </div>

                    {/* 专业技能标签 */}
                    <div className="jd-section">
                        <h4 className="jd-section-title">⚡ 专业技能栈</h4>
                        <div className="jd-tags">
                            {scoring["专业技能"].map((s: string) => {
                                const isMatched = outerTags.some(ot => s.toLowerCase().includes(ot.toLowerCase()) || ot.toLowerCase().includes(s.toLowerCase()));
                                return (
                                    <span
                                        key={s}
                                        className="jd-tag"
                                        style={isMatched ? {
                                            border: '1px solid var(--primary-color, #0ea5e9)',
                                            color: 'var(--primary-color, #0ea5e9)',
                                            boxShadow: '0 0 8px rgba(14,165,233,0.3)',
                                            fontWeight: 600,
                                            background: 'rgba(14,165,233,0.05)'
                                        } : {}}
                                    >
                                        {s}
                                        {isMatched && <span style={{ marginLeft: '4px' }}>✨</span>}
                                    </span>
                                );
                            })}
                        </div>
                    </div>

                    {/* 能力评分 */}
                    <div className="jd-section">
                        <h4 className="jd-section-title">📊 能力维度评分</h4>
                        <ScoreBar label="实习能力" value={scoring["实习能力_score"]} max={10} />
                        <ScoreBar label="沟通能力" value={scoring["沟通能力_score"]} max={10} />
                        <ScoreBar label="抗压能力" value={scoring["抗压能力_score"]} max={10} />
                        <ScoreBar label="学习能力" value={scoring["学习能力_score"]} max={10} />
                        <ScoreBar label="创新能力" value={scoring["创新能力_score"]} max={10} />
                    </div>

                    {/* 地理分布 */}
                    <div className="jd-section">
                        <h4 className="jd-section-title">📍 岗位地理分布</h4>
                        {locationEntries.map(([city, pct]: any) => (
                            <div key={city} className="jd-loc-row">
                                <span className="jd-loc-city">{city}</span>
                                <div className="jd-loc-track">
                                    <div className="jd-loc-fill" style={{ width: `${(pct / maxLoc) * 100}%` }} />
                                </div>
                                <span className="jd-loc-pct">{pct}%</span>
                            </div>
                        ))}
                    </div>

                    {/* 工作时间 */}
                    <div className="jd-section">
                        <h4 className="jd-section-title">🕐 工作时间</h4>
                        <p className="jd-text">{detail["工作时间"]}</p>
                    </div>

                    {/* 薪资水平 */}
                    <div className="jd-section">
                        <h4 className="jd-section-title">💰 薪资水平</h4>
                        <p className="jd-text">{detail["薪资水平"]}</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

/* ===== 主页面 ===== */
const Home: React.FC = () => {
    const [dashboard, setDashboard] = useState<DashboardData | null>(null);
    const [radarScore, setRadarScore] = useState<RadarScore | null>(null);

    const [matchList] = useState(MOCK_MATCH_LIST);
    const [selectedJobDetail, setSelectedJobDetail] = useState<{ detail: Record<string, any>, outerTags: string[] } | null>(null);

    const [loading, setLoading] = useState(true);
    const radarRef = useRef<HTMLDivElement>(null);
    const chartInstance = useRef<echarts.ECharts | null>(null);

    // 优先真实 API，失败则 Mock 降级
    useEffect(() => {
        let cancelled = false;
        (async () => {
            let d: DashboardData;
            try {
                d = await resumeApi.getDashboard();
            } catch {
                d = await fetchDashboard();
            }
            if (cancelled) return;
            setDashboard(d);
            setRadarScore(toRadarScore(d));
            setLoading(false);
        })();
        return () => { cancelled = true; };
    }, []);

    // 渲染 ECharts 雷达图
    useEffect(() => {
        if (!dashboard || !radarRef.current) return;

        if (!chartInstance.current) {
            chartInstance.current = echarts.init(radarRef.current);
        }
        const chart = chartInstance.current;

        chart.setOption({
            radar: {
                indicator: dashboard.radar.map((r) => ({ name: r.dimension, max: 100 })),
                shape: 'polygon',
                splitNumber: 4,
                axisName: { color: '#64748b', fontSize: 12, fontWeight: 600 },
                splitLine: { lineStyle: { color: 'rgba(203,213,225,0.4)' } },
                splitArea: { areaStyle: { color: ['rgba(14,165,233,0.02)', 'rgba(14,165,233,0.05)'] } },
                axisLine: { lineStyle: { color: 'rgba(203,213,225,0.4)' } },
            },
            series: [{
                type: 'radar',
                data: [{
                    value: dashboard.radar.map((r) => r.value),
                    name: '能力值',
                    areaStyle: { color: 'rgba(14,165,233,0.15)' },
                    lineStyle: { color: '#0ea5e9', width: 2 },
                    itemStyle: { color: '#0ea5e9' },
                    symbol: 'circle',
                    symbolSize: 6,
                }],
            }],
        });

        const onResize = () => chart.resize();
        window.addEventListener('resize', onResize);
        return () => {
            window.removeEventListener('resize', onResize);
        };
    }, [dashboard]);

    useEffect(() => {
        return () => { chartInstance.current?.dispose(); };
    }, []);

    const handleJobClick = useCallback((jobId: number, outerTags: string[]) => {
        if (MOCK_MATCH_DETAILS[jobId]) {
            setSelectedJobDetail({ detail: MOCK_MATCH_DETAILS[jobId], outerTags });
        }
    }, []);

    if (loading) {
        return (
            <div className="fade-in" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                <div className="loader"></div>
            </div>
        );
    }

    return (
        <div className="fade-in">
            <header style={{ marginBottom: '40px' }}>
                <h1 className="text-gradient" style={{ fontSize: '32px', margin: '0 0 8px 0' }}>欢迎探索你的无限可能</h1>
                <p style={{ color: '#64748b', margin: 0 }}>GLSL 底层引擎正在实时渲染 10,000+ 岗位知识图谱节点</p>
            </header>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '24px' }}>
                {/* 竞争力评分卡 — 总分 + 六维网格 */}
                <div className="glass-panel" style={{ padding: '24px' }}>
                    <h3 style={{ margin: '0 0 16px 0', color: '#1e293b' }}>全息竞争力</h3>
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '16px' }}>
                        <span className="text-gradient" style={{ fontSize: '64px', fontWeight: 900, lineHeight: 1 }}>{radarScore?.totalScore ?? dashboard?.score}</span>
                        <span style={{ fontSize: '14px', fontWeight: 700, color: '#64748b' }}>INDEX</span>
                    </div>
                    {/* 六维数值网格 */}
                    {radarScore && (
                        <div className="radar-grid">
                            {DIMENSION_META.map(dm => (
                                <div key={dm.key} className="radar-grid-item">
                                    <span className="radar-grid-icon">{dm.icon}</span>
                                    <span className="radar-grid-val">{radarScore[dm.key]}</span>
                                    <span className="radar-grid-label">{dm.label}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* 六维雷达图 */}
                <div className="glass-panel" style={{ padding: '24px', gridColumn: 'span 2', display: 'flex', flexDirection: 'column' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px' }}>
                        <h3 style={{ margin: 0, color: '#1e293b' }}>六维能力拓扑图</h3>
                        <span style={{ padding: '4px 10px', background: 'rgba(14,165,233,0.1)', color: '#0ea5e9', borderRadius: '8px', fontSize: '12px', fontWeight: 700 }}>AI 分析</span>
                    </div>
                    <div ref={radarRef} style={{ flex: 1, minHeight: '260px' }} />
                </div>

                {/* AI 匹配岗位列表 — 可点击 */}
                <div className="glass-panel" style={{ padding: '24px', gridColumn: 'span 3' }}>
                    <h3 style={{ margin: '0 0 20px 0', color: '#1e293b' }}>AI 匹配序列</h3>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
                        {matchList.map(job => {
                            let matchColor = '#64748b'; // 常规色
                            if (job.matchRate > 85) matchColor = '#10b981'; // 极品高亮色（翠绿） / 或者 #0ea5e9
                            else if (job.matchRate > 80) matchColor = '#0ea5e9'; // 次高亮色

                            return (
                                <div
                                    key={job.id}
                                    className="job-card"
                                    onClick={() => handleJobClick(job.id, job.tags)}
                                >
                                    <div>
                                        <h4 style={{ margin: '0 0 4px 0', fontSize: '16px', color: '#1e293b' }}>{job.title}</h4>
                                        <p style={{ margin: '0 0 8px 0', fontSize: '13px', color: '#64748b' }}>{job.company || ''}</p>
                                        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                                            {job.tags.map(tag => <span key={tag} className="job-tag">{tag}</span>)}
                                        </div>
                                    </div>
                                    <span style={{ fontSize: '24px', fontWeight: 900, flexShrink: 0, color: matchColor }}>
                                        {job.matchRate}%
                                    </span>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>

            {/* 岗位详情弹窗 */}
            {selectedJobDetail && (
                <JobDetailModal
                    detail={selectedJobDetail.detail}
                    outerTags={selectedJobDetail.outerTags}
                    onClose={() => setSelectedJobDetail(null)}
                />
            )}
        </div>
    );
};

export default Home;