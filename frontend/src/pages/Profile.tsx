import React, { useRef, useState } from 'react';
import { uploadApi } from '../api/auto';

const ACCEPTED_TYPES = '.pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document';

const Profile: React.FC = () => {
    const [currentStatus, setCurrentStatus] = useState<'upload' | 'parsing' | 'ready'>('upload');
    const [chatInput, setChatInput] = useState('');
    const [uploadError, setUploadError] = useState('');
    const fileInputRef = useRef<HTMLInputElement>(null);

    const [resumeData, setResumeData] = useState<{
        name: string;
        targetRole: string;
        education: string;
        skills: string[];
        projects: { title: string; desc: string }[];
    } | null>(null);

    const [chatHistory, setChatHistory] = useState<{ role: string; content: string }[]>([]);

    const handleUpload = async (file: File) => {
        setUploadError('');
        setCurrentStatus('parsing');
        try {
            const res = await uploadApi.uploadFile(file, 'resume');
            // 如果后端返回了解析后的简历数据，填充到 state
            if (res) {
                setResumeData({
                    name: res.name || '',
                    targetRole: res.targetRole || '',
                    education: res.education || '',
                    skills: res.skills || [],
                    projects: res.projects || [],
                });
                setChatHistory([{
                    role: 'ai',
                    content: '你好！我已成功读取你上传的简历。有什么需要我帮你优化的吗？✨',
                }]);
            }
            setCurrentStatus('ready');
        } catch (e: any) {
            setUploadError(e.message || '上传失败，请稍后重试');
            setCurrentStatus('upload');
        }
    };

    const onFileSelected = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        // 重置 input 以便重复选择同一文件
        e.target.value = '';
        handleUpload(file);
    };

    const sendMessage = () => {
        if (!chatInput.trim()) return;
        const newHistory = [...chatHistory, { role: 'user', content: chatInput }];
        setChatHistory(newHistory);
        setChatInput('');

    };

    return (
        <div className="parser-workspace">

            {currentStatus === 'upload' && (
                <div className="upload-center glass-panel">
                    <div className="upload-icon">📄</div>
                    <h2>上传你的简历原件</h2>
                    <p>支持 PDF / Word 格式，或者直接跳过让 AI 从零开始引导你创建</p>
                    {uploadError && (
                        <p style={{ color: '#ef4444', fontSize: '14px', margin: '8px 0 0 0' }}>{uploadError}</p>
                    )}
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept={ACCEPTED_TYPES}
                        style={{ display: 'none' }}
                        onChange={onFileSelected}
                    />
                    <div className="action-buttons">
                        <button className="btn-primary" onClick={() => fileInputRef.current?.click()}>选择 PDF/Word 上传</button>
                        <button className="btn-outline" onClick={() => setCurrentStatus('ready')}>没有简历？AI 帮我写</button>
                    </div>
                </div>
            )}

            {currentStatus === 'parsing' && (
                <div className="parsing-center glass-panel">
                    <div className="loader"></div>
                    <h3>AI 正在解构你的生涯轨迹...</h3>
                    <p className="text-muted">正在进行语义抽取与能力量化</p>
                </div>
            )}

            {currentStatus === 'ready' && (
                <div className="workspace-split">

                    <div className="left-preview glass-panel">
                        <div className="panel-header">
                            <span className="title">全息简历模型</span>
                            <span className="status-tag">实时同步中</span>
                        </div>

                        <div className="resume-paper">
                            {resumeData ? (
                                <>
                                    <header className="resume-head">
                                        <h1>{resumeData.name}</h1>
                                        <p className="target-role">意向岗位：{resumeData.targetRole}</p>
                                        <p className="text-muted">{resumeData.education}</p>
                                    </header>

                                    <section className="resume-section">
                                        <h3>核心技能矩阵</h3>
                                        <div className="skill-tags">
                                            {resumeData.skills.map(skill => (
                                                <span key={skill} className="skill-tag">{skill}</span>
                                            ))}
                                            <button className="add-skill-btn">+ AI 挖掘更多</button>
                                        </div>
                                    </section>

                                    <section className="resume-section">
                                        <h3>项目实战经历</h3>
                                        {resumeData.projects.map((proj, idx) => (
                                            <div key={idx} className="project-item highlight-warn">
                                                <div className="proj-head">
                                                    <h4>{proj.title}</h4>
                                                    <button className="ai-fix-btn">✨ AI 润色</button>
                                                </div>
                                                <p className="proj-desc">{proj.desc}</p>
                                            </div>
                                        ))}
                                    </section>
                                </>
                            ) : (
                                <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>
                                    <p>暂无简历数据，请先上传简历或让 AI 引导你创建</p>
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="right-copilot glass-panel">
                        <div className="panel-header">
                            <span className="title"><i className="ai-icon">✨</i> 简历辅导引擎</span>
                        </div>

                        <div className="chat-flow">
                            {chatHistory.map((msg, index) => (
                                <div key={index} className={`chat-bubble ${msg.role === 'ai' ? 'ai-bubble' : 'user-bubble'}`}>
                                    <div className="avatar">{msg.role === 'ai' ? '🤖' : '🧑‍🎓'}</div>
                                    <div className="message-content">{msg.content}</div>
                                </div>
                            ))}
                        </div>

                        <div className="chat-input-area">
                            <input
                                type="text"
                                value={chatInput}
                                onChange={(e) => setChatInput(e.target.value)}
                                onKeyDown={(e) => { if (e.key === 'Enter') sendMessage(); }}
                                placeholder="告诉 AI 你的想法，比如：'我在学生会做过外联'..."
                            />
                            <button className="send-btn" onClick={sendMessage}>发送</button>
                        </div>
                    </div>

                </div>
            )}
        </div>
    );
};

export default Profile;