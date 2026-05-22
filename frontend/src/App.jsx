import { useEffect, useMemo, useState, useCallback } from 'react';
import {
  confirmApplication,
  clearRecommendations,
  dismissRecommendation,
  fetchOverview,
  fetchPreferences,
  fetchProviders,
  fetchSettings,
  fetchUrl,
  importJob,
  importRecommendation,
  prepareApplication,
  refreshRecommendations,
  savePreferences,
  saveResumeProfile,
  saveSettings,
  testApiConnection,
  uploadResume,
} from './lib/api';
import regions from './data/regions';

const defaultProfileForm = {
  full_name: 'Demo Candidate',
  job_intention: 'AI 应用开发工程师',
  political_status: '',
  birth_date: '',
  hometown: '',
  contact: '',
  email: '',
  hobbies: '',
  strengths: '',
  self_evaluation: '偏向本地自动化、AI 工作流与数据处理的应用开发。',
  education_background: '学校：示例大学 | 时间：2021-2025 | 学历：本科',
  internship_experiences: '',
  project_experiences: '项目名：校园创新项目 | 角色：全栈开发 | 时间：2024-2025 | 总结：负责本地 Web 工具的前后端实现与自动化流程编排。 | 技能：Python, FastAPI, React, SQLite | 亮点：搭建本地 Web 管理台，支持表单录入、状态追踪与结果导出。',
  campus_experiences: '',
  honors_and_certificates: '',
  training_experiences: '',
  skills_text: 'Python, FastAPI, SQL, Playwright, React, Prompt Engineering, LLM Integration',
  other_text: '',
};

const defaultJobForm = {
  source_platform: '',
  source_url: '',
  raw_text: '',
};

function detectPlatform(url) {
  if (!url) return '';
  const u = url.toLowerCase();
  if (u.includes('zhipin.com')) return 'boss';
  if (u.includes('zhaopin.com')) return 'zhaopin';
  if (u.includes('51job.com') || u.includes('qiancheng.com')) return '51job';
  if (u.includes('yingjiesheng.com')) return 'yingjiesheng';
  if (u.includes('liepin.com')) return 'liepin';
  if (u.includes('linkedin.com')) return 'linkedin';
  return 'manual';
}

const PLATFORM_LABELS = {
  boss: 'BOSS直聘', zhaopin: '智联招聘', '51job': '前程无忧',
  yingjiesheng: '应届生求职', liepin: '猎聘', linkedin: 'LinkedIn', manual: '手动导入',
};

function parsePreviewFields(rawText) {
  if (!rawText) return null;
  const lines = rawText.split('\n').map(l => l.trim()).filter(Boolean);
  if (!lines.length) return null;
  let title = '', company = '', city = '', salary = '';
  const salaryRe = /(\d[\d.]+[-~—至到]\d[\d.]+\s*[kK万元]?[/月年]?(?:\s*·\s*\d{1,2}薪)?)/;
  const companySizeRe = /^\d{1,5}[-~—至到]\d{1,5}$/;
  const cityRe = /(北京|上海|天津|重庆|深圳|广州|杭州|成都|武汉|苏州|南京|西安|长沙|郑州|合肥|青岛|济南|大连|厦门|宁波|无锡|昆明|哈尔滨|沈阳|贵阳|南宁|兰州|太原|石家庄|海口|珠海|佛山|东莞|中山|惠州|温州|嘉兴|绍兴|金华|常州|徐州|南通|烟台|潍坊|洛阳|绵阳|遵义|大理|远程|海外|全国)/;
  const hrRe = /女士|先生|小时前|在线|已认证|招聘经理|HR|猎头|登录|注册|首页|搜索|简历|收藏|设置|关注|粉丝|投递|沟通|聊一聊|分享|举报|投诉|微信|扫码|收藏|感兴趣|立即/;
  const jobTitleRe = /经理|工程师|专员|主管|总监|助理|架构师|开发|设计|运营|分析|顾问|实习|员|师/;
  const companyRe = /有限公司|集团|股份|公司|企业|研究所|学院/;

  for (const line of lines) {
    if (!salary) {
      const m = line.match(salaryRe);
      if (m && !companySizeRe.test(m[1].trim())) salary = m[1];
    }
    if (!city) { const m = line.match(cityRe); if (m) city = m[1]; }
  }

  // Find title: line containing job title keywords, skip HR/nav noise
  for (const line of lines) {
    if (line.length < 2 || line.length > 60) continue;
    if (hrRe.test(line)) continue;
    if (salaryRe.test(line) && !jobTitleRe.test(line)) continue;
    if (line === city) continue;
    if (jobTitleRe.test(line)) { title = line; break; }
  }

  // Find company: line containing company keywords
  for (const line of lines) {
    if (hrRe.test(line)) continue;
    if (companyRe.test(line)) { company = line; break; }
  }

  return { title: title || '', company: company || '', city, salary };
}

function splitCsv(text) {
  return text
    .split(/[，,\n]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function profileToForm(profile) {
  if (!profile) {
    return defaultProfileForm;
  }

  const pi = profile.personal_info || {};
  return {
    full_name: pi.full_name || '',
    job_intention: pi.job_intention || '',
    political_status: pi.political_status || '',
    birth_date: pi.birth_date || '',
    hometown: pi.hometown || '',
    contact: pi.contact || '',
    email: pi.email || '',
    hobbies: pi.hobbies || '',
    strengths: pi.strengths || '',
    self_evaluation: (profile.self_evaluation || {}).content || '',
    education_background: entriesToText(profile.education_background || [], 'education'),
    internship_experiences: entriesToText(profile.internship_experiences || [], 'internship'),
    project_experiences: entriesToText(profile.project_experiences || [], 'project'),
    campus_experiences: entriesToText(profile.campus_experiences || [], 'campus'),
    honors_and_certificates: entriesToText(profile.honors_and_certificates || [], 'honor'),
    training_experiences: entriesToText(profile.training_experiences || [], 'training'),
    skills_text: ((profile.skills_and_other || {}).skills || []).join(', '),
    other_text: (profile.skills_and_other || {}).other || '',
  };
}

function parsedProfileToForm(profile) {
  return profileToForm(profile);
}

function parseJsonArray(text, fallback) {
  try {
    const parsed = JSON.parse(text);
    return Array.isArray(parsed) ? parsed : fallback;
  } catch {
    return fallback;
  }
}

const ENTRY_FIELDS = {
  education: [
    { key: 'school_name', label: '学校' },
    { key: 'attendance_period', label: '时间' },
    { key: 'degree', label: '学历' },
    { key: 'ranking', label: '排名' },
    { key: 'major_courses', label: '主修课程' },
  ],
  internship: [
    { key: 'company', label: '公司' },
    { key: 'role', label: '岗位' },
    { key: 'duration', label: '时间' },
    { key: 'summary', label: '总结' },
    { key: 'skills', label: '技能', isArr: true },
    { key: 'highlights', label: '亮点', isArr: true },
  ],
  project: [
    { key: 'project_name', label: '项目名' },
    { key: 'role', label: '角色' },
    { key: 'duration', label: '时间' },
    { key: 'summary', label: '总结' },
    { key: 'skills', label: '技能', isArr: true },
    { key: 'highlights', label: '亮点', isArr: true },
  ],
  campus: [
    { key: 'organization', label: '组织' },
    { key: 'role', label: '角色' },
    { key: 'duration', label: '时间' },
    { key: 'summary', label: '总结' },
    { key: 'highlights', label: '亮点', isArr: true },
  ],
  honor: [
    { key: 'name', label: '名称' },
    { key: 'time', label: '时间' },
    { key: 'issuer', label: '颁发机构' },
  ],
  training: [
    { key: 'course_name', label: '课程' },
    { key: 'institution', label: '机构' },
    { key: 'duration', label: '时间' },
    { key: 'summary', label: '总结' },
  ],
};

function entriesToText(entries, type) {
  if (!entries || !entries.length) return '';
  const fields = ENTRY_FIELDS[type] || [];
  return entries.map((entry) =>
    fields
      .filter((f) => entry[f.key])
      .map((f) => {
        const val = Array.isArray(entry[f.key]) ? entry[f.key].join(', ') : entry[f.key];
        return f.label + '：' + val;
      })
      .join(' | ')
  ).join('\n');
}

function textToEntries(text, type, fallback) {
  if (!text || !text.trim()) return fallback;
  const fields = ENTRY_FIELDS[type] || [];
  const lines = text.split('\n').map((l) => l.trim()).filter(Boolean);
  if (!lines.length) return fallback;
  return lines.map((line) => {
    const obj = {};
    line.split(' | ').forEach((part) => {
      const idx = part.indexOf('：');
      if (idx < 0) return;
      const label = part.slice(0, idx).trim();
      const value = part.slice(idx + 1).trim();
      const field = fields.find((f) => f.label === label);
      if (field) {
        obj[field.key] = field.isArr ? value.split(/[,，]/).map((s) => s.trim()).filter(Boolean) : value;
      }
    });
    return obj;
  }).filter((obj) => Object.keys(obj).length > 0);
}

export default function App() {
  const [overview, setOverview] = useState({ profile: null, jobs: [], applications: [], recommended_jobs: [] });
  const [profileForm, setProfileForm] = useState(defaultProfileForm);
  const [jobForm, setJobForm] = useState(defaultJobForm);
  const [parsedFields, setParsedFields] = useState(null);
  const [prepared, setPrepared] = useState(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [resumeFile, setResumeFile] = useState(null);
  const [resumeParseResult, setResumeParseResult] = useState(null);
  const [expanded, setExpanded] = useState({});

  const toggleSection = useCallback((name) => {
    setExpanded((prev) => ({ ...prev, [name]: !prev[name] }));
  }, []);

  const [showSettings, setShowSettings] = useState(false);
  const [providers, setProviders] = useState({});
  const [settingsForm, setSettingsForm] = useState({ provider: 'anthropic', api_base_url: '', api_key: '', model: '' });
  const [availableModels, setAvailableModels] = useState([]);
  const [testingApi, setTestingApi] = useState(false);
  const [testingResult, setTestingResult] = useState('');
  const [btnStatus, setBtnStatus] = useState({ test: '', upload: '', refresh: '' });

  const [prefs, setPrefs] = useState({ regions: [], overseas: false, industry: [], job_titles: [], platforms: ['boss'] });
  const [regionPicker, setRegionPicker] = useState({ open: false, province: null });
  const [titleInput, setTitleInput] = useState('');

  const latestApplication = useMemo(() => overview.applications?.[0] || null, [overview]);

  async function loadOverview() {
    setLoading(true);
    setError('');
    try {
      const data = await fetchOverview();
      setOverview(data);
      setProfileForm(profileToForm(data.profile));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadOverview();
    fetchPreferences().then(setPrefs).catch(() => {});
  }, []);

  async function handleProfileSave(event) {
    event.preventDefault();
    setBusy(true);
    setMessage('');
    setError('');
    try {
      await saveResumeProfile({
        personal_info: {
          full_name: profileForm.full_name,
          job_intention: profileForm.job_intention,
          political_status: profileForm.political_status,
          birth_date: profileForm.birth_date,
          hometown: profileForm.hometown,
          contact: profileForm.contact,
          email: profileForm.email,
          hobbies: profileForm.hobbies,
          strengths: profileForm.strengths,
        },
        self_evaluation: { content: profileForm.self_evaluation },
        education_background: textToEntries(profileForm.education_background, 'education', []),
        internship_experiences: textToEntries(profileForm.internship_experiences, 'internship', []),
        project_experiences: textToEntries(profileForm.project_experiences, 'project', []),
        campus_experiences: textToEntries(profileForm.campus_experiences, 'campus', []),
        honors_and_certificates: textToEntries(profileForm.honors_and_certificates, 'honor', []),
        training_experiences: textToEntries(profileForm.training_experiences, 'training', []),
        skills_and_other: {
          skills: splitCsv(profileForm.skills_text),
          other: profileForm.other_text,
        },
      });
      await loadOverview();
      setMessage('简历资料已保存。');
    } catch (err) {
      setError(err.message || '保存失败');
    } finally {
      setBusy(false);
    }
  }

  async function handleResumeUpload() {
    if (!resumeFile) {
      setError('请先选择 PDF 或 DOCX 简历文件。');
      return;
    }
    setBusy(true);
    setBtnStatus((s) => ({ ...s, upload: 'loading' }));
    setMessage('');
    setError('');
    try {
      const data = await uploadResume(resumeFile);
      setResumeParseResult(data);
      setProfileForm(parsedProfileToForm(data.profile));
      setMessage('简历已解析并回填到资料表单，请检查后保存。');
      setBtnStatus((s) => ({ ...s, upload: 'done' }));
      setTimeout(() => setBtnStatus((s) => ({ ...s, upload: '' })), 3000);
    } catch (err) {
      setError(err.message || '简历解析失败');
      setBtnStatus((s) => ({ ...s, upload: '' }));
    } finally {
      setBusy(false);
    }
  }

  async function handleJobImport(event) {
    event.preventDefault();
    if (!jobForm.raw_text.trim()) return;
    setBusy(true);
    setPrepared(null);
    setMessage('');
    setError('');
    try {
      await importJob(jobForm);
      await loadOverview();
      setJobForm(defaultJobForm);
      setParsedFields(null);
      setMessage('岗位已导入。');
    } catch (err) {
      setError(err.message || '导入失败');
    } finally {
      setBusy(false);
    }
  }

  async function handleRefreshRecommendations() {
    setBusy(true);
    setBtnStatus((s) => ({ ...s, refresh: 'loading' }));
    setMessage('');
    setError('');
    try {
      await refreshRecommendations();
      await loadOverview();
      setMessage('推荐岗位已刷新。');
      setBtnStatus((s) => ({ ...s, refresh: 'done' }));
      setTimeout(() => setBtnStatus((s) => ({ ...s, refresh: '' })), 3000);
    } catch (err) {
      setError(err.message || '刷新推荐失败');
      setBtnStatus((s) => ({ ...s, refresh: '' }));
    } finally {
      setBusy(false);
    }
  }

  async function handleImportRecommendation(recommendationId) {
    setBusy(true);
    setMessage('');
    setError('');
    try {
      await importRecommendation(recommendationId);
      await loadOverview();
      setMessage('推荐岗位已导入到岗位列表。');
    } catch (err) {
      setError(err.message || '导入推荐岗位失败');
    } finally {
      setBusy(false);
    }
  }

  async function handleDismissRecommendation(recommendationId) {
    setOverview((prev) => ({
      ...prev,
      recommended_jobs: prev.recommended_jobs.filter((j) => j.id !== recommendationId),
    }));
    try {
      await dismissRecommendation(recommendationId);
    } catch (err) {
      setError(err.message || '忽略推荐岗位失败');
    }
  }

  const handleClearRecommendations = useCallback(async () => {
    if (!window.confirm('确定要清空所有推荐岗位吗？此操作不可撤销。')) return;
    setBusy(true);
    setError('');
    setMessage('');
    try {
      await clearRecommendations();
      await loadOverview();
      setMessage('推荐岗位已清空。');
    } catch (err) {
      setError(err.message || '清空推荐岗位失败');
    } finally {
      setBusy(false);
    }
  }, []);

  async function handlePrepare(jobId) {
    setBusy(true);
    setMessage('');
    setError('');
    try {
      const data = await prepareApplication(jobId);
      setPrepared(data);
      await loadOverview();
      setMessage('已生成匹配分析与定制简历。');
    } catch (err) {
      setError(err.message || '生成失败');
    } finally {
      setBusy(false);
    }
  }

  async function handleConfirm(applicationId) {
    setBusy(true);
    setMessage('');
    setError('');
    try {
      const confirmed = await confirmApplication(applicationId);
      setPrepared((current) => (current ? { ...current, application: confirmed } : current));
      await loadOverview();
      setMessage('申请状态已确认。');
    } catch (err) {
      setError(err.message || '确认失败');
    } finally {
      setBusy(false);
    }
  }

  const updateField = (field) => (event) =>
    setProfileForm((current) => ({ ...current, [field]: event.target.value }));

  async function handleOpenSettings() {
    setShowSettings(true);
    setTestingResult('');
    setAvailableModels([]);
    try {
      const [provData, settingsData] = await Promise.all([fetchProviders(), fetchSettings()]);
      setProviders(provData);
      const pid = settingsData.provider || 'anthropic';
      const prov = provData[pid] || {};
      setSettingsForm({
        provider: pid,
        api_base_url: settingsData.api_base_url || prov.base_url || '',
        api_key: '',
        model: settingsData.model || (prov.models && prov.models[0]) || '',
      });
    } catch {
      // keep defaults
    }
  }

  function handleProviderChange(newProvider) {
    const prov = providers[newProvider] || {};
    setSettingsForm((c) => ({
      ...c,
      provider: newProvider,
      api_base_url: prov.base_url || '',
      model: (prov.models && prov.models[0]) || '',
    }));
    setAvailableModels([]);
    setTestingResult('');
  }

  async function handleTestApi() {
    setTestingApi(true);
    setBtnStatus((s) => ({ ...s, test: 'loading' }));
    setTestingResult('');
    setAvailableModels([]);
    try {
      const data = await testApiConnection(settingsForm.provider, settingsForm.api_base_url, settingsForm.api_key, settingsForm.model);
      setAvailableModels(data.models || []);
      const msg = data.hint || '检测成功，找到 {} 个可用模型'.replace('{}', (data.models || []).length);
      setTestingResult(msg);
      setBtnStatus((s) => ({ ...s, test: 'done' }));
      setTimeout(() => setBtnStatus((s) => ({ ...s, test: '' })), 3000);
    } catch (err) {
      setTestingResult(err.message || '检测失败');
      setBtnStatus((s) => ({ ...s, test: '' }));
    } finally {
      setTestingApi(false);
    }
  }

  async function handleSaveSettings() {
    setBusy(true);
    setMessage('');
    setError('');
    try {
      await saveSettings(settingsForm);
      await loadOverview();
      setShowSettings(false);
      setMessage('API 设置已保存。');
    } catch (err) {
      setError(err.message || '保存设置失败');
    } finally {
      setBusy(false);
    }
  }

  function savePrefsDebounced(updated) {
    setPrefs(updated);
    savePreferences(updated).catch(() => {});
  }

  function selectRegion(label) {
    const updated = { ...prefs, regions: [label] };
    setRegionPicker({ open: false, province: null });
    savePrefsDebounced(updated);
  }

  function removeRegion() {
    const updated = { ...prefs, regions: [] };
    savePrefsDebounced(updated);
  }

  function addJobTitle() {
    const v = titleInput.trim();
    if (!v || prefs.job_titles.length >= 3 || prefs.job_titles.includes(v)) return;
    const updated = { ...prefs, job_titles: [...prefs.job_titles, v], industry: [] };
    setTitleInput('');
    savePrefsDebounced(updated);
  }

  function removeJobTitle(t) {
    const updated = { ...prefs, job_titles: prefs.job_titles.filter((x) => x !== t) };
    savePrefsDebounced(updated);
  }

  function selectIndustry(industry) {
    if (prefs.industry.includes(industry)) return;
    const updated = { ...prefs, industry: [industry], job_titles: [] };
    savePrefsDebounced(updated);
  }

  function removeIndustry(t) {
    const updated = { ...prefs, industry: prefs.industry.filter((x) => x !== t) };
    savePrefsDebounced(updated);
  }

  function toggleOverseas() {
    const updated = { ...prefs, overseas: !prefs.overseas };
    savePrefsDebounced(updated);
  }

  const PLATFORM_OPTIONS = [
    { id: 'boss', label: 'BOSS直聘' },
    { id: 'zhaopin', label: '智联招聘' },
    { id: 'liepin', label: '猎聘' },
    { id: '51job', label: '前程无忧' },
    { id: 'yingjiesheng', label: '应届生求职' },
    { id: 'linkedin', label: 'LinkedIn领英（需科学上网）' },
  ];

  const INDUSTRY_OPTIONS = [
    'AI/互联网/IT',
    '电子/通信/半导体',
    '金融',
    '消费品',
    '医疗健康',
    '汽车',
    '机械/制造',
    '教育培训/科研',
    '专业服务',
    '房地产/建筑',
  ];

  function togglePlatform(platformId) {
    const current = prefs.platforms || [];
    if (current.includes(platformId)) return;
    const newPrefs = { ...prefs, platforms: [platformId] };
    savePrefsDebounced(newPrefs);
  }

  return (
    <div className="page">
      <div className="shell">
        <section className="hero">
          <div className="hero-card">
            <div className="hero-title">
              <h1>make-jobs-ai</h1>
              <img src="/logo.png" alt="logo" className="hero-logo" />
            </div>
            <p>
              本地控制台：导入岗位、匹配分析、定制简历、人工确认投递。
            </p>
            <div className="badges">
              <span className="badge">本地 Web 应用</span>
              <span className="badge">FastAPI + React</span>
              <span className="badge">AI 生成 + 人工确认</span>
            </div>
            <div className="actions" style={{ marginTop: '10px' }}>
              <button type="button" className="ghost" onClick={handleOpenSettings}>API 设置</button>
            </div>
          </div>
          <div className="hero-card">
            <div className="kpis">
              <div className="kpi">
                <span>简历资料</span>
                <strong>{overview.profile ? 1 : 0}</strong>
              </div>
              <div className="kpi">
                <span>已导入岗位</span>
                <strong>{overview.jobs?.length || 0}</strong>
              </div>
              <div className="kpi">
                <span>投递记录</span>
                <strong>{overview.applications?.length || 0}</strong>
              </div>
            </div>
            {latestApplication ? (
              <div className="inline-meta">
                <small>最近状态：{latestApplication.status}</small>
                <small>平台：{latestApplication.platform_label}</small>
              </div>
            ) : (
              <small>还没有投递记录。</small>
            )}
          </div>
        </section>

        {error ? <div className="notice error">{error}</div> : null}
        {message ? <div className="notice success">{message}</div> : null}

        <div className="grid">
          <div className="stack">
            <section className="panel">
              <h2>简历资料库</h2>
              <div className="upload-box">
                <label className="full upload-field">
                  本地上传简历（PDF / DOCX）
                  <input
                    type="file"
                    accept=".pdf,.docx"
                    onChange={(event) => setResumeFile(event.target.files?.[0] || null)}
                  />
                </label>
                <div className="actions">
                  <button type="button" onClick={handleResumeUpload} disabled={busy}>
                    {btnStatus.upload === 'loading' ? <><span className="spinner" /> 解析中…</> : btnStatus.upload === 'done' ? '解析完成' : '上传并解析'}
                  </button>
                  {resumeFile ? <small>已选择：{resumeFile.name}</small> : <small>请选择本地简历文件。</small>}
                </div>
                {resumeParseResult ? (
                  <div className="notice parse-note">
                    <strong>最近解析：</strong> {resumeParseResult.file_name}
                    <div className="excerpt">{resumeParseResult.parsed_text_excerpt}</div>
                  </div>
                ) : null}
              </div>

              <form className="resume-form" onSubmit={handleProfileSave}>
                <div className="section-toggle">
                  <h3 onClick={() => toggleSection('个人信息')}>{expanded['个人信息'] ? '▾' : '▸'} 个人信息</h3>
                  {expanded['个人信息'] && (
                    <div className="form-grid">
                      <label>
                        姓名
                        <input value={profileForm.full_name} onChange={updateField('full_name')} />
                      </label>
                      <label>
                        求职意向
                        <input value={profileForm.job_intention} onChange={updateField('job_intention')} />
                      </label>
                      <label>
                        联系方式
                        <input value={profileForm.contact} onChange={updateField('contact')} placeholder="手机号" />
                      </label>
                      <label>
                        邮箱
                        <input value={profileForm.email} onChange={updateField('email')} />
                      </label>
                      <label>
                        出生年月
                        <input value={profileForm.birth_date} onChange={updateField('birth_date')} />
                      </label>
                      <label>
                        籍贯
                        <input value={profileForm.hometown} onChange={updateField('hometown')} />
                      </label>
                      <label>
                        政治面貌
                        <input value={profileForm.political_status} onChange={updateField('political_status')} />
                      </label>
                      <label>
                        兴趣爱好
                        <input value={profileForm.hobbies} onChange={updateField('hobbies')} />
                      </label>
                      <label className="full">
                        个人特长
                        <input value={profileForm.strengths} onChange={updateField('strengths')} />
                      </label>
                    </div>
                  )}
                </div>

                <div className="section-toggle">
                  <h3 onClick={() => toggleSection('自我评价')}>{expanded['自我评价'] ? '▾' : '▸'} 自我评价</h3>
                  {expanded['自我评价'] && (
                    <label className="full">
                      <textarea value={profileForm.self_evaluation} onChange={updateField('self_evaluation')} />
                    </label>
                  )}
                </div>

                <div className="section-toggle">
                  <h3 onClick={() => toggleSection('教育背景')}>{expanded['教育背景'] ? '▾' : '▸'} 教育背景</h3>
                  {expanded['教育背景'] && (
                    <label className="full">
                      <textarea
                        rows={4}
                        value={profileForm.education_background}
                        onChange={updateField('education_background')}
                      />
                    </label>
                  )}
                </div>

                <div className="section-toggle">
                  <h3 onClick={() => toggleSection('实习经历')}>{expanded['实习经历'] ? '▾' : '▸'} 实习经历</h3>
                  {expanded['实习经历'] && (
                    <label className="full">
                      <textarea
                        rows={6}
                        value={profileForm.internship_experiences}
                        onChange={updateField('internship_experiences')}
                      />
                    </label>
                  )}
                </div>

                <div className="section-toggle">
                  <h3 onClick={() => toggleSection('项目经历')}>{expanded['项目经历'] ? '▾' : '▸'} 项目经历</h3>
                  {expanded['项目经历'] && (
                    <label className="full">
                      <textarea
                        rows={6}
                        value={profileForm.project_experiences}
                        onChange={updateField('project_experiences')}
                      />
                    </label>
                  )}
                </div>

                <div className="section-toggle">
                  <h3 onClick={() => toggleSection('校园经历')}>{expanded['校园经历'] ? '▾' : '▸'} 校园经历</h3>
                  {expanded['校园经历'] && (
                    <label className="full">
                      <textarea
                        rows={4}
                        value={profileForm.campus_experiences}
                        onChange={updateField('campus_experiences')}
                      />
                    </label>
                  )}
                </div>

                <div className="section-toggle">
                  <h3 onClick={() => toggleSection('荣誉证书')}>{expanded['荣誉证书'] ? '▾' : '▸'} 荣誉证书</h3>
                  {expanded['荣誉证书'] && (
                    <label className="full">
                      <textarea
                        rows={3}
                        value={profileForm.honors_and_certificates}
                        onChange={updateField('honors_and_certificates')}
                      />
                    </label>
                  )}
                </div>

                <div className="section-toggle">
                  <h3 onClick={() => toggleSection('培训经历')}>{expanded['培训经历'] ? '▾' : '▸'} 培训经历</h3>
                  {expanded['培训经历'] && (
                    <label className="full">
                      <textarea
                        rows={3}
                        value={profileForm.training_experiences}
                        onChange={updateField('training_experiences')}
                      />
                    </label>
                  )}
                </div>

                <div className="section-toggle">
                  <h3 onClick={() => toggleSection('技能及其他')}>{expanded['技能及其他'] ? '▾' : '▸'} 技能及其他</h3>
                  {expanded['技能及其他'] && (
                    <div className="form-grid">
                      <label className="full">
                        技能（逗号分隔）
                        <textarea value={profileForm.skills_text} onChange={updateField('skills_text')} />
                      </label>
                      <label className="full">
                        其他说明
                        <textarea value={profileForm.other_text} onChange={updateField('other_text')} />
                      </label>
                    </div>
                  )}
                </div>

                <div className="actions">
                  <button disabled={busy}>保存资料</button>
                  {loading ? <small>加载中…</small> : null}
                </div>
              </form>
            </section>

            <section className="panel">
              <div className="panel-header">
                <h2>推荐岗位</h2>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button type="button" className="secondary" disabled={busy} onClick={handleRefreshRecommendations}>
                    {btnStatus.refresh === 'loading' ? <><span className="spinner" /> 刷新中…</> : btnStatus.refresh === 'done' ? '刷新成功' : '刷新推荐岗位'}
                  </button>
                  <button type="button" className="ghost" disabled={busy} onClick={handleClearRecommendations}>
                    🗑️ 清空
                  </button>
                </div>
              </div>

              <div className="prefs-section">
                <div className="prefs-row">
                  <span className="prefs-label">招聘平台</span>
                  <div className="platform-checks">
                    {PLATFORM_OPTIONS.map((p) => (
                      <label className="platform-check" key={p.id}>
                        <input
                          type="checkbox"
                          checked={(prefs.platforms || []).includes(p.id)}
                          onChange={() => togglePlatform(p.id)}
                        />
                        {p.label}
                      </label>
                    ))}
                    <span className="prefs-hint">（每次选择1个平台）</span>
                  </div>
                </div>
                <div className="prefs-row">
                  <span className="prefs-label">意向地区</span>
                  <div className="tag-input-wrap">
                    {prefs.regions.map((r) => (
                      <span className="tag-item" key={r}>{r}<button type="button" onClick={() => removeRegion()}>×</button></span>
                    ))}
                    <button type="button" className="ghost" style={{ padding: '4px 10px', fontSize: 12 }} onClick={() => setRegionPicker({ open: true, province: null })}>
                      {prefs.regions.length ? '更换地区' : '+ 选择地区'}
                    </button>
                    <label className="overseas-check">
                      <input type="checkbox" checked={prefs.overseas} onChange={toggleOverseas} />
                      海外
                    </label>
                  </div>
                  {!prefs.regions.length && !prefs.overseas ? <small className="prefs-hint">不选默认全国</small> : null}
                </div>

                {regionPicker.open ? (
                  <div className="region-picker">
                    <div className="region-picker-header">
                      <small>
                        {!regionPicker.province ? '选择省份' : `${regionPicker.province} > 选择城市`}
                      </small>
                      <button type="button" className="ghost" style={{ padding: '2px 6px', fontSize: 11 }} onClick={() => setRegionPicker({ open: false, province: null })}>关闭</button>
                    </div>
                    <div className="region-picker-list">
                      {!regionPicker.province ? (
                        regions.map((prov) => (
                          <button key={prov.label} type="button" className="region-option" onClick={() => {
                            if (prov.children && !prov.children[0]?.children) {
                              // Children are flat districts (直辖市) -> select directly
                              selectRegion(prov.label);
                            } else if (prov.children) {
                              // Children have sub-children (provinces with cities) -> show city list
                              setRegionPicker((c) => ({ ...c, province: prov.label }));
                            } else {
                              selectRegion(prov.label);
                            }
                          }}>
                            {prov.label}
                          </button>
                        ))
                      ) : (
                        (regions.find((p) => p.label === regionPicker.province)?.children || []).map((city) => (
                          <button key={city.label} type="button" className="region-option" onClick={() => selectRegion(city.label)}>
                            {city.label}
                          </button>
                        ))
                      )}
                    </div>
                    {regionPicker.province ? (
                      <button type="button" className="ghost" style={{ padding: '4px 8px', fontSize: 11, marginTop: 4 }} onClick={() => setRegionPicker((c) => ({ ...c, province: null }))}>
                        ← 返回省份
                      </button>
                    ) : null}
                  </div>
                ) : null}

                <div className="prefs-row">
                  <span className="prefs-label">意向行业</span>
                  <div className="tag-input-wrap">
                    {prefs.industry.map((t) => (
                      <span className="tag-item" key={t}>{t}<button type="button" onClick={() => removeIndustry(t)}>×</button></span>
                    ))}
                    {prefs.industry.length === 0 && prefs.job_titles.length === 0 ? (
                      <select
                        className="tag-input"
                        value=""
                        onChange={(e) => { if (e.target.value) selectIndustry(e.target.value); }}
                      >
                        <option value="" disabled>选择行业</option>
                        {INDUSTRY_OPTIONS.map((ind) => (
                          <option key={ind} value={ind}>{ind}</option>
                        ))}
                      </select>
                    ) : null}
                  </div>
                  {prefs.job_titles.length > 0 ? (
                    <span className="prefs-hint">已选择岗位推荐，如需行业推荐请先清空岗位</span>
                  ) : null}
                </div>

                <div className="prefs-row">
                  <span className="prefs-label">意向岗位</span>
                  <div className="tag-input-wrap">
                    {prefs.job_titles.map((t) => (
                      <span className="tag-item" key={t}>{t}<button type="button" onClick={() => removeJobTitle(t)}>×</button></span>
                    ))}
                    {prefs.job_titles.length < 3 && prefs.industry.length === 0 ? (
                      <input
                        className="tag-input"
                        value={titleInput}
                        onChange={(e) => setTitleInput(e.target.value)}
                        onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addJobTitle(); } }}
                        onBlur={addJobTitle}
                        placeholder="输入岗位名，回车添加"
                      />
                    ) : null}
                  </div>
                  {prefs.industry.length > 0 ? (
                    <span className="prefs-hint">已选择行业推荐，如需岗位推荐请先清空行业</span>
                  ) : null}
                </div>
              </div>

              <div className="list scrollable-list">
                {(overview.recommended_jobs || []).map((job) => (
                  <article className="card" key={job.id}>
                    <header>
                      <div>
                        <h4>{job.job_title}</h4>
                        <p>{job.company_name}{job.company_name === '待确认公司' ? '，请进详情查看' : ''}</p>
                      </div>
                      <strong>{job.match_score} 分</strong>
                    </header>
                    <div className="inline-meta">
                      <small>{job.platform_label}</small>
                      {job.city ? <small>{job.city}</small> : null}
                      {job.salary_range ? <small>{job.salary_range}</small> : null}
                      <small>状态：{job.status}</small>
                    </div>
                    <p>{job.recommendation}</p>
                    <div className="tags">
                      {(job.matched_skills || []).map((skill) => (
                        <span className="tag" key={`${job.id}-${skill}`}>{skill}</span>
                      ))}
                    </div>
                    <div className="actions">
                      {job.source_url ? (
                        <button type="button" className="ghost" onClick={() => window.open(job.source_url, '_blank')}>
                          岗位详情
                        </button>
                      ) : null}
                      <button type="button" className="secondary" disabled={busy} onClick={() => handleImportRecommendation(job.id)}>
                        导入到岗位列表
                      </button>
                      <button type="button" className="ghost" disabled={busy} onClick={() => handleDismissRecommendation(job.id)}>
                        忽略
                      </button>
                    </div>
                  </article>
                ))}
                {!overview.recommended_jobs?.length ? <small>还没有推荐岗位，请先保存简历资料后刷新。</small> : null}
              </div>
            </section>

            <section className="panel">
              <h2>岗位导入</h2>
              <form onSubmit={handleJobImport}>
                <div className="form-grid">
                  <label className="full">
                    来源链接
                    <div style={{ display: 'flex', gap: 8 }}>
                      <input
                        value={jobForm.source_url}
                        onChange={(event) =>
                          setJobForm((current) => ({ ...current, source_url: event.target.value }))
                        }
                        placeholder="粘贴岗位链接后点击读取，平台自动识别"
                        style={{ flex: 1 }}
                      />
                      <button
                        type="button"
                        disabled={busy || !jobForm.source_url.trim()}
                        onClick={async () => {
                          setBusy(true);
                          setError('');
                          setMessage('');
                          try {
                            const platform = detectPlatform(jobForm.source_url.trim());
                            const data = await fetchUrl(jobForm.source_url.trim());
                            if (data.error) {
                              setError(data.error);
                            } else {
                              setJobForm((current) => ({
                                ...current,
                                raw_text: data.raw_text,
                                source_platform: platform,
                              }));
                              // Only set parsedFields if AI returned meaningful data
                              const hasFields = data.job_title || data.company_name;
                              setParsedFields(hasFields ? {
                                job_title: data.job_title || '',
                                company_name: data.company_name || '',
                                city: data.city || '',
                                salary_range: data.salary_range || '',
                              } : null);
                            }
                          } catch (err) {
                            setError(err.message || '读取失败');
                          } finally {
                            setBusy(false);
                          }
                        }}
                      >
                        读取
                      </button>
                    </div>
                  </label>
                  {jobForm.raw_text ? (() => {
                    const preview = parsedFields || parsePreviewFields(jobForm.raw_text);
                    const platformLabel = PLATFORM_LABELS[jobForm.source_platform] || '';
                    return (
                      <div className="full">
                        <article className="card" style={{ margin: 0 }}>
                          <header>
                            <div>
                              <h4>{preview?.job_title || preview?.title || '未知岗位'}</h4>
                              <p>{preview?.company_name || preview?.company || ''}</p>
                            </div>
                            <button type="submit" className="secondary" disabled={busy}>导入岗位</button>
                          </header>
                          <div className="inline-meta">
                            {platformLabel ? <small>{platformLabel}</small> : null}
                            {preview?.city ? <small>{preview.city}</small> : null}
                            {preview?.salary_range || preview?.salary ? <small>{preview.salary_range || preview.salary}</small> : null}
                          </div>
                        </article>
                      </div>
                    );
                  })() : (
                    <div className="full">
                      <article className="card" style={{ margin: 0, opacity: 0.5 }}>
                        <header>
                          <div>
                            <h4 style={{ color: '#999' }}>粘贴链接后点击读取</h4>
                            <p style={{ color: '#bbb' }}>岗位信息将显示在此处</p>
                          </div>
                        </header>
                      </article>
                    </div>
                  )}
                </div>
              </form>
            </section>
          </div>

          <div className="stack">
            <section className="panel">
              <h2>岗位列表</h2>
              <div className="list scrollable-list">
                {(overview.jobs || []).map((job) => (
                  <article className="card" key={job.id}>
                    <header>
                      <div>
                        <h4>{job.job_title}</h4>
                        <p>{job.company_name}{job.company_name === '待确认公司' ? '，请进详情查看' : ''}</p>
                      </div>
                      <button className="secondary" disabled={busy} onClick={() => handlePrepare(job.id)}>
                        生成定制简历
                      </button>
                    </header>
                    <div className="inline-meta">
                      <small>{job.platform_label}</small>
                      {job.city ? <small>{job.city}</small> : null}
                      {job.salary_range ? <small>{job.salary_range}</small> : null}
                    </div>
                    <div className="tags">
                      {(job.skills || []).map((skill) => (
                        <span className="tag" key={`${job.id}-${skill}`}>
                          {skill}
                        </span>
                      ))}
                    </div>
                  </article>
                ))}
                {!overview.jobs?.length ? <small>还没有导入岗位。</small> : null}
              </div>
            </section>

            <section className="panel">
              <h2>匹配分析与投递确认</h2>
              <div className="scrollable-list">
              {prepared ? (
                <>
                  <div className="card">
                    <header>
                      <div>
                        <h4>{prepared.job.job_title}</h4>
                        <p>{prepared.job.company_name}</p>
                      </div>
                      <strong>{prepared.analysis.match_score} 分</strong>
                    </header>
                    <p>{prepared.analysis.recommendation}</p>
                    <h3>命中技能</h3>
                    <div className="tags">
                      {(prepared.analysis.matched_skills || []).map((skill) => (
                        <span className="tag" key={skill}>{skill}</span>
                      ))}
                    </div>
                    <h3>缺口项</h3>
                    <div className="tags">
                      {(prepared.analysis.missing_skills || []).map((skill) => (
                        <span className="tag" key={skill}>{skill}</span>
                      ))}
                      {!prepared.analysis.missing_skills?.length ? <small>暂无明显缺口。</small> : null}
                    </div>
                    <h3>投递草稿</h3>
                    <div className="inline-meta">
                      <small>平台：{prepared.application.platform_label}</small>
                      <small>状态：{prepared.application.status}</small>
                      <small>
                        {prepared.application.auto_supported ? '支持自动化投递' : '当前为手动投递流'}
                      </small>
                    </div>
                    <div className="actions">
                      <button
                        disabled={busy || prepared.application.status === 'confirmed'}
                        onClick={() => handleConfirm(prepared.application.id)}
                      >
                        确认投递
                      </button>
                    </div>
                  </div>
                  <div className="panel" style={{ padding: 0, border: '0', boxShadow: 'none' }}>
                    <h3>定制简历 Markdown</h3>
                    <div className="markdown">{prepared.tailored_resume.rendered_markdown}</div>
                  </div>
                </>
              ) : (
                <small>从岗位列表选择"生成定制简历"后，这里会展示匹配分析与简历预览。</small>
              )}
              </div>
            </section>

            <section className="panel">
              <h2>投递记录</h2>
              <div className="list scrollable-list">
                {(overview.applications || []).map((item) => (
                  <article className="card" key={item.id}>
                    <header>
                      <div>
                        <h4>{item.platform_label}</h4>
                        <p>状态：{item.status}</p>
                      </div>
                      <span className="tag">#{item.job_id}</span>
                    </header>
                    <p>{item.notes || '暂无备注'}</p>
                    <div className="inline-meta">
                      <small>{item.auto_supported ? '自动化平台' : '手动平台'}</small>
                      {item.target_url ? <small>{item.target_url}</small> : null}
                    </div>
                  </article>
                ))}
                {!overview.applications?.length ? <small>还没有投递记录。</small> : null}
              </div>
            </section>
          </div>
        </div>
      </div>

      {showSettings ? (
        <div className="modal-overlay" onMouseDown={(e) => { if (e.target === e.currentTarget) setShowSettings(false); }}>
          <div className="modal" onMouseDown={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>API 设置</h2>
              <button type="button" className="ghost modal-close" onClick={() => setShowSettings(false)}>✕</button>
            </div>
            <div className="modal-body">
              <label>
                AI 提供商
                <select
                  value={settingsForm.provider}
                  onChange={(e) => handleProviderChange(e.target.value)}
                >
                  {Object.entries(providers).map(([id, p]) => (
                    <option key={id} value={id}>{p.name}</option>
                  ))}
                </select>
              </label>
              <label>
                API 地址
                <input
                  value={settingsForm.api_base_url}
                  onChange={(e) => setSettingsForm((c) => ({ ...c, api_base_url: e.target.value }))}
                  placeholder="https://api.anthropic.com"
                />
              </label>
              <label>
                API 密钥
                <input
                  type="password"
                  value={settingsForm.api_key}
                  onChange={(e) => setSettingsForm((c) => ({ ...c, api_key: e.target.value }))}
                  placeholder="留空则不修改已有密钥"
                />
              </label>
              <div className="actions">
                <button type="button" className="secondary" onClick={handleTestApi} disabled={testingApi}>
                  {btnStatus.test === 'loading' ? <><span className="spinner" /> 检测中…</> : btnStatus.test === 'done' ? '检测完成' : '检测可用模型'}
                </button>
                {testingResult ? <small>{testingResult}</small> : null}
              </div>
              <label>
                模型
                <input
                  value={settingsForm.model}
                  onChange={(e) => setSettingsForm((c) => ({ ...c, model: e.target.value }))}
                  placeholder="输入模型名称"
                />
              </label>
              {availableModels.length > 0 ? (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: -4 }}>
                  {availableModels.map((m) => (
                    <button
                      key={m}
                      type="button"
                      className="ghost"
                      style={{ padding: '4px 10px', fontSize: 12, borderRadius: 999 }}
                      onClick={() => setSettingsForm((c) => ({ ...c, model: m }))}
                    >
                      {m}
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
            <div className="modal-footer">
              <button type="button" className="ghost" onClick={() => setShowSettings(false)}>取消</button>
              <button type="button" onClick={handleSaveSettings} disabled={busy}>保存</button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
