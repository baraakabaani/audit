import { useState, useEffect } from 'react';
import {
  getEngagement, updateEngagement, uploadFile, getFiles, analyzeTB,
  classify, getMappings, validate, generate,
  approveMapping, bulkApprove, updateMapping, getAggregatedBalances,
  downloadUrl, downloadMappingUrl, downloadAuditTrailUrl, downloadValidationUrl,
  type Engagement, type AccountMapping, type ValidationResult,
} from '../api';

interface Props {
  engagementId: number;
  onBack: () => void;
}

type Tab = 'setup' | 'upload' | 'analysis' | 'mapping' | 'validation' | 'generate';

const CONFIDENCE_COLORS: Record<string, string> = {
  HIGH: '#16a34a',
  MEDIUM: '#d97706',
  LOW: '#dc2626',
};

const FS_LINE_LABELS: Record<string, string> = {
  PPE: 'Property, plant & equipment',
  INTANGIBLES: 'Intangible assets',
  INVESTMENTS: 'Investments',
  OTHER_NCA: 'Other non-current assets',
  INVENTORIES: 'Inventories',
  TRADE_RECEIVABLES: 'Trade & other receivables',
  CASH: 'Cash & bank balances',
  REVALUATION_RESERVE: 'Revaluation reserve',
  ACCUMULATED_LOSSES: 'Accumulated losses',
  EOSB: 'Provision for EOSB',
  TRADE_PAYABLES: 'Trade & other payables',
  REVENUE: 'Revenue',
  COS: 'Cost of revenue',
  GRANT_INCOME: 'Grant received',
  OTHER_INCOME: 'Other income',
  ADMIN_EXPENSES: 'G&A expenses',
  FINANCE_COST: 'Finance cost',
  UNCLASSIFIED: '⚠ Unclassified',
};

export default function EngagementDashboard({ engagementId, onBack }: Props) {
  const [tab, setTab] = useState<Tab>('upload');
  const [engagement, setEngagement] = useState<Engagement | null>(null);
  const [files, setFiles] = useState<any[]>([]);
  const [tbAnalysis, setTbAnalysis] = useState<any>(null);
  const [_classifyResult, setClassifyResult] = useState<any>(null);
  const [mappings, setMappings] = useState<AccountMapping[]>([]);
  const [validation, setValidation] = useState<any>(null);
  const [generateResult, setGenerateResult] = useState<any>(null);
  const [aggregated, setAggregated] = useState<any>(null);
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [filter, setFilter] = useState('');
  const [filterConf, setFilterConf] = useState('');
  const [editingCode, setEditingCode] = useState<string | null>(null);
  const [editLine, setEditLine] = useState('');
  const [editNote, setEditNote] = useState('');

  // Materiality inputs
  const [matOverall, setMatOverall] = useState('');
  const [matPerf, setMatPerf] = useState('');
  const [matTrivial, setMatTrivial] = useState('');

  useEffect(() => {
    loadEngagement();
    loadFiles();
  }, [engagementId]);

  async function loadEngagement() {
    const e = await getEngagement(engagementId);
    setEngagement(e);
    if (e.overall_materiality) setMatOverall(String(e.overall_materiality));
    if (e.performance_materiality) setMatPerf(String(e.performance_materiality));
    if (e.trivial_threshold) setMatTrivial(String(e.trivial_threshold));
  }

  async function loadFiles() {
    const f = await getFiles(engagementId);
    setFiles(f);
  }

  function msg(s: string) { setSuccess(s); setError(''); setTimeout(() => setSuccess(''), 4000); }
  function err(s: string) { setError(s); setSuccess(''); }

  async function handleUpload(file: File, fileType: string) {
    setBusy(`Uploading ${file.name}…`);
    try {
      await uploadFile(engagementId, file, fileType);
      await loadFiles();
      msg(`Uploaded ${file.name}`);
    } catch (e: any) {
      err(e?.response?.data?.detail || 'Upload failed');
    }
    setBusy('');
  }

  async function runAnalyzeTB() {
    setBusy('Analyzing Trial Balance…');
    setError('');
    try {
      const result = await analyzeTB(engagementId);
      setTbAnalysis(result);
      await loadEngagement();
      msg('Trial Balance analyzed successfully.');
      setTab('analysis');
    } catch (e: any) {
      err(e?.response?.data?.detail || 'TB analysis failed');
    }
    setBusy('');
  }

  async function runClassify(useAI: boolean) {
    setBusy(useAI ? 'Classifying accounts (AI + rules)…' : 'Classifying accounts (rules only)…');
    setError('');
    try {
      const result = await classify(engagementId, useAI);
      setClassifyResult(result);
      const maps = await getMappings(engagementId);
      setMappings(maps);
      msg(`Classified ${result.total} accounts. ${result.low_confidence} need review.`);
      setTab('mapping');
    } catch (e: any) {
      err(e?.response?.data?.detail || 'Classification failed');
    }
    setBusy('');
  }

  async function runValidate() {
    setBusy('Running validation checks…');
    setError('');
    try {
      const result = await validate(engagementId);
      setValidation(result);
      const agg = await getAggregatedBalances(engagementId);
      setAggregated(agg);
      setTab('validation');
    } catch (e: any) {
      err(e?.response?.data?.detail || 'Validation failed');
    }
    setBusy('');
  }

  async function runGenerate(genAudit: boolean, genFS: boolean) {
    setBusy('Generating Excel outputs…');
    setError('');
    try {
      const result = await generate(engagementId, genAudit, genFS);
      setGenerateResult(result);
      msg('Files generated successfully. Ready to download.');
    } catch (e: any) {
      err(e?.response?.data?.detail || 'Generation failed');
    }
    setBusy('');
  }

  async function saveMateriality() {
    setBusy('Saving materiality…');
    try {
      await updateEngagement(engagementId, {
        overall_materiality: matOverall ? parseFloat(matOverall) : null,
        performance_materiality: matPerf ? parseFloat(matPerf) : null,
        trivial_threshold: matTrivial ? parseFloat(matTrivial) : null,
      });
      await loadEngagement();
      msg('Materiality saved.');
    } catch {
      err('Failed to save materiality.');
    }
    setBusy('');
  }

  async function handleApprove(code: string) {
    await approveMapping(engagementId, code);
    const maps = await getMappings(engagementId);
    setMappings(maps);
  }

  async function handleBulkApproveHigh() {
    const highCodes = mappings
      .filter(m => m.confidence_level === 'HIGH' && !m.user_approved)
      .map(m => m.account_code);
    if (!highCodes.length) { msg('No high-confidence accounts to approve.'); return; }
    await bulkApprove(engagementId, highCodes);
    const maps = await getMappings(engagementId);
    setMappings(maps);
    msg(`Approved ${highCodes.length} high-confidence accounts.`);
  }

  async function handleSaveEdit(code: string) {
    await updateMapping(engagementId, code, {
      fs_line_item: editLine || undefined,
      user_note: editNote || undefined,
      user_approved: 1,
    });
    setEditingCode(null);
    const maps = await getMappings(engagementId);
    setMappings(maps);
    msg('Mapping updated and approved.');
  }

  const filesByType = (type: string) => files.filter(f => f.file_type === type);

  const filteredMappings = mappings.filter(m => {
    const q = filter.toLowerCase();
    const matchText = !q || m.account_code.includes(q) || m.account_name.toLowerCase().includes(q);
    const matchConf = !filterConf || m.confidence_level === filterConf;
    return matchText && matchConf;
  });

  const approvedCount = mappings.filter(m => m.user_approved).length;
  const unapprovedLow = mappings.filter(m => m.confidence_level === 'LOW' && !m.user_approved).length;

  const tabs: { id: Tab; label: string }[] = [
    { id: 'upload', label: '1. Upload' },
    { id: 'analysis', label: '2. Analysis' },
    { id: 'mapping', label: '3. Mapping Review' },
    { id: 'validation', label: '4. Validation' },
    { id: 'generate', label: '5. Generate & Export' },
  ];

  return (
    <div className="app-root">
      <header className="app-header">
        <div className="header-inner">
          <button className="btn-ghost" onClick={onBack}>← Back</button>
          <div>
            <h1>{engagement?.name || 'Loading…'}</h1>
            {engagement?.entity_name && <p className="subtitle">{engagement.entity_name} · {engagement.period}</p>}
          </div>
        </div>
        <div className="disclaimer-bar">
          ⚠ AI-generated classifications are subject to auditor review and approval.
          This system does not replace professional judgment.
        </div>
      </header>

      {(busy || error || success) && (
        <div className={`status-bar ${busy ? 'status-busy' : error ? 'status-error' : 'status-success'}`}>
          {busy || error || success}
        </div>
      )}

      <div className="tab-nav">
        {tabs.map(t => (
          <button
            key={t.id}
            className={`tab-btn ${tab === t.id ? 'tab-active' : ''}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      <main className="main-content">

        {/* ── UPLOAD TAB ─────────────────────────────────────────────── */}
        {tab === 'upload' && (
          <div>
            <h2>Upload Files</h2>

            {/* Materiality */}
            <div className="card mb-4">
              <h3 className="card-title">Audit Materiality (Optional)</h3>
              <p className="text-sm text-muted mb-2">
                Materiality must be set by the auditor. If not set, material accounts cannot be flagged.
              </p>
              <div className="grid-3">
                <div>
                  <label className="label">Overall Materiality (AED)</label>
                  <input className="input" type="number" value={matOverall} onChange={e => setMatOverall(e.target.value)} placeholder="e.g. 500000" />
                </div>
                <div>
                  <label className="label">Performance Materiality (AED)</label>
                  <input className="input" type="number" value={matPerf} onChange={e => setMatPerf(e.target.value)} placeholder="e.g. 350000" />
                </div>
                <div>
                  <label className="label">Clearly Trivial (AED)</label>
                  <input className="input" type="number" value={matTrivial} onChange={e => setMatTrivial(e.target.value)} placeholder="e.g. 25000" />
                </div>
              </div>
              <button className="btn-primary mt-2" onClick={saveMateriality} disabled={!!busy}>Save Materiality</button>
            </div>

            {/* File uploads */}
            <div className="grid-2">
              <UploadCard
                label="Trial Balance (TB)"
                fileType="tb"
                uploaded={filesByType('tb')}
                onUpload={f => handleUpload(f, 'tb')}
                required
              />
              <UploadCard
                label="Prior Year TB (Optional)"
                fileType="prior_tb"
                uploaded={filesByType('prior_tb')}
                onUpload={f => handleUpload(f, 'prior_tb')}
              />
              <UploadCard
                label="Financial Statement Template"
                fileType="fs_template"
                uploaded={filesByType('fs_template')}
                onUpload={f => handleUpload(f, 'fs_template')}
                required
              />
              <UploadCard
                label="Audit File Template"
                fileType="audit_template"
                uploaded={filesByType('audit_template')}
                onUpload={f => handleUpload(f, 'audit_template')}
                required
              />
            </div>

            <div className="card mt-4">
              <h3 className="card-title">Next: Analyze</h3>
              <p className="text-sm text-muted mb-2">
                Upload the Trial Balance and templates above, then click Analyze.
              </p>
              <button
                className="btn-primary"
                onClick={runAnalyzeTB}
                disabled={!!busy || filesByType('tb').length === 0}
              >
                Analyze Trial Balance →
              </button>
            </div>
          </div>
        )}

        {/* ── ANALYSIS TAB ───────────────────────────────────────────── */}
        {tab === 'analysis' && (
          <div>
            <h2>TB Analysis</h2>
            {!tbAnalysis ? (
              <div className="card">
                <p className="text-muted">Run the analysis from the Upload tab first.</p>
                <button className="btn-primary mt-2" onClick={runAnalyzeTB} disabled={!!busy}>
                  Analyze Trial Balance
                </button>
              </div>
            ) : (
              <>
                <div className="stats-grid">
                  <StatCard label="Total Accounts" value={tbAnalysis.account_count} />
                  <StatCard label="TB Balance" value={tbAnalysis.balanced ? '✓ Balanced' : '✗ NOT BALANCED'} color={tbAnalysis.balanced ? 'green' : 'red'} />
                  <StatCard label="Net Difference" value={`AED ${Number(tbAnalysis.total_ending).toLocaleString()}`} />
                  <StatCard label="Zero-Balance Accounts" value={tbAnalysis.zero_count} />
                  <StatCard label="Unusual Balances" value={tbAnalysis.unusual_count} color={tbAnalysis.unusual_count > 0 ? 'amber' : undefined} />
                </div>

                {tbAnalysis.metadata?.entity_name && (
                  <div className="card mb-4">
                    <h3 className="card-title">Entity Information</h3>
                    <table className="info-table">
                      <tbody>
                        <tr><td>Entity</td><td><strong>{tbAnalysis.metadata.entity_name}</strong></td></tr>
                        <tr><td>Period</td><td>{tbAnalysis.metadata.period}</td></tr>
                        <tr><td>Amount Type</td><td>{tbAnalysis.metadata.amount_type}</td></tr>
                      </tbody>
                    </table>
                  </div>
                )}

                <div className="card mb-4">
                  <h3 className="card-title">Balances by Account Type</h3>
                  <table className="data-table">
                    <thead><tr><th>Account Type</th><th className="text-right">Ending Balance (AED)</th></tr></thead>
                    <tbody>
                      {Object.entries(tbAnalysis.by_type || {}).map(([type, bal]: [string, any]) => (
                        <tr key={type}>
                          <td>{type}</td>
                          <td className="text-right">{Number(bal).toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="card mb-4">
                  <h3 className="card-title">Validation Checks</h3>
                  {tbAnalysis.validation?.map((v: any, i: number) => (
                    <div key={i} className={`check-row check-${v.result.toLowerCase()}`}>
                      <span className={`badge badge-${v.result.toLowerCase()}`}>{v.result}</span>
                      <span><strong>{v.check}</strong> — {v.explanation}</span>
                    </div>
                  ))}
                </div>

                <div className="card">
                  <h3 className="card-title">Classify Accounts</h3>
                  <p className="text-sm text-muted mb-2">
                    This will classify all {tbAnalysis.account_count} accounts using deterministic rules
                    and optionally Groq AI for ambiguous cases.
                  </p>
                  <div className="btn-row">
                    <button className="btn-primary" onClick={() => runClassify(true)} disabled={!!busy}>
                      Classify with AI (Recommended)
                    </button>
                    <button className="btn-secondary" onClick={() => runClassify(false)} disabled={!!busy}>
                      Rules Only (No API)
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        )}

        {/* ── MAPPING REVIEW TAB ─────────────────────────────────────── */}
        {tab === 'mapping' && (
          <div>
            <h2>Account Mapping Review</h2>

            {mappings.length === 0 ? (
              <div className="card">
                <p className="text-muted">No mappings yet. Run classification from the Analysis tab.</p>
              </div>
            ) : (
              <>
                <div className="stats-grid mb-4">
                  <StatCard label="Total Accounts" value={mappings.length} />
                  <StatCard label="Approved" value={approvedCount} color="green" />
                  <StatCard label="Pending" value={mappings.length - approvedCount} color="amber" />
                  <StatCard label="Low Confidence" value={unapprovedLow} color={unapprovedLow > 0 ? 'red' : undefined} />
                </div>

                <div className="card mb-4">
                  <div className="toolbar">
                    <input
                      className="input input-sm"
                      placeholder="Filter by code or name…"
                      value={filter}
                      onChange={e => setFilter(e.target.value)}
                    />
                    <select className="select" value={filterConf} onChange={e => setFilterConf(e.target.value)}>
                      <option value="">All confidence levels</option>
                      <option value="HIGH">HIGH only</option>
                      <option value="MEDIUM">MEDIUM only</option>
                      <option value="LOW">LOW only</option>
                    </select>
                    <button className="btn-secondary" onClick={handleBulkApproveHigh}>
                      Approve all HIGH
                    </button>
                  </div>
                </div>

                <div className="mapping-table-wrap">
                  <table className="data-table mapping-table">
                    <thead>
                      <tr>
                        <th>Code</th>
                        <th>Account Name</th>
                        <th className="text-right">Balance (AED)</th>
                        <th>Type</th>
                        <th>FS Line</th>
                        <th>Confidence</th>
                        <th>Source</th>
                        <th>IFRS</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredMappings.map(m => (
                        editingCode === m.account_code ? (
                          <tr key={m.account_code} className="editing-row">
                            <td>{m.account_code}</td>
                            <td>{m.account_name}</td>
                            <td className="text-right">{Number(m.ending_balance).toLocaleString()}</td>
                            <td>{m.account_type_raw}</td>
                            <td>
                              <select className="select select-sm" value={editLine} onChange={e => setEditLine(e.target.value)}>
                                {Object.entries(FS_LINE_LABELS).map(([k, v]) => (
                                  <option key={k} value={k}>{v}</option>
                                ))}
                              </select>
                            </td>
                            <td colSpan={2}>
                              <input className="input input-sm" placeholder="Note/reason" value={editNote} onChange={e => setEditNote(e.target.value)} />
                            </td>
                            <td colSpan={2}>
                              <div className="btn-row">
                                <button className="btn-xs btn-primary" onClick={() => handleSaveEdit(m.account_code)}>Save</button>
                                <button className="btn-xs btn-secondary" onClick={() => setEditingCode(null)}>Cancel</button>
                              </div>
                            </td>
                          </tr>
                        ) : (
                          <tr key={m.account_code} className={m.is_unusual ? 'row-unusual' : ''}>
                            <td className="code-cell">{m.account_code}</td>
                            <td>
                              {m.account_name}
                              {m.is_unusual && <span className="badge badge-warning ml-1" title={m.unusual_reason || ''}>!</span>}
                            </td>
                            <td className="text-right">{Number(m.ending_balance).toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                            <td className="type-cell">{m.account_type_raw}</td>
                            <td>
                              <span className="fs-line">{FS_LINE_LABELS[m.fs_line_item] || m.fs_line_item}</span>
                              <div className="reason-text">{m.reason}</div>
                            </td>
                            <td>
                              <span className="conf-badge" style={{ color: CONFIDENCE_COLORS[m.confidence_level] }}>
                                {m.confidence_level} {(m.confidence * 100).toFixed(0)}%
                              </span>
                            </td>
                            <td>
                              <span className={`source-badge source-${m.source.toLowerCase()}`}>{m.source}</span>
                            </td>
                            <td className="ifrs-cell">{m.ifrs_reference || '—'}</td>
                            <td>
                              <div className="btn-row">
                                {!m.user_approved ? (
                                  <button className="btn-xs btn-success" onClick={() => handleApprove(m.account_code)}>✓ Approve</button>
                                ) : (
                                  <span className="approved-badge">✓ Approved</span>
                                )}
                                <button className="btn-xs btn-secondary" onClick={() => {
                                  setEditingCode(m.account_code);
                                  setEditLine(m.fs_line_item);
                                  setEditNote(m.user_note || '');
                                }}>Edit</button>
                              </div>
                            </td>
                          </tr>
                        )
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="card mt-4">
                  <button className="btn-primary" onClick={runValidate} disabled={!!busy}>
                    Run Validation Checks →
                  </button>
                </div>
              </>
            )}
          </div>
        )}

        {/* ── VALIDATION TAB ─────────────────────────────────────────── */}
        {tab === 'validation' && (
          <div>
            <h2>Validation &amp; Quality Control</h2>

            {!validation ? (
              <div className="card">
                <p className="text-muted">Run mapping review first, then click Validate.</p>
                <button className="btn-primary mt-2" onClick={runValidate} disabled={!!busy}>Run Validation</button>
              </div>
            ) : (
              <>
                <div className="stats-grid mb-4">
                  <StatCard label="Total Checks" value={validation.total_checks} />
                  <StatCard label="Pass" value={validation.passes} color="green" />
                  <StatCard label="Warnings" value={validation.warnings} color="amber" />
                  <StatCard label="Errors" value={validation.errors} color={validation.errors > 0 ? 'red' : undefined} />
                </div>

                {validation.errors > 0 && (
                  <div className="alert alert-error mb-4">
                    <strong>{validation.errors} critical error(s) found.</strong> Resolve before generating.
                  </div>
                )}

                {aggregated && (
                  <div className="card mb-4">
                    <h3 className="card-title">Aggregated Balances Preview</h3>
                    <div className="grid-2">
                      <div>
                        <h4>Balance Sheet</h4>
                        <table className="data-table">
                          <tbody>
                            {['PPE','INTANGIBLES','INVESTMENTS','INVENTORIES','TRADE_RECEIVABLES','CASH'].map(k => (
                              aggregated[k] ? <tr key={k}>
                                <td>{FS_LINE_LABELS[k]}</td>
                                <td className="text-right">{Number(aggregated[k].cy).toLocaleString(undefined,{minimumFractionDigits:2})}</td>
                              </tr> : null
                            ))}
                            <tr className="total-row"><td><strong>Assets</strong></td><td className="text-right"><strong>{
                              Object.entries(aggregated)
                                .filter(([k]) => ['PPE','INTANGIBLES','INVESTMENTS','INVENTORIES','TRADE_RECEIVABLES','CASH'].includes(k))
                                .reduce((s,[,v]:any) => s + (v.cy||0), 0)
                                .toLocaleString(undefined,{minimumFractionDigits:2})
                            }</strong></td></tr>
                            <tr className="spacer-row"><td colSpan={2}></td></tr>
                            {['REVALUATION_RESERVE','ACCUMULATED_LOSSES','EOSB','TRADE_PAYABLES'].map(k => (
                              aggregated[k] ? <tr key={k}>
                                <td>{FS_LINE_LABELS[k]}</td>
                                <td className="text-right">{Number(aggregated[k].cy).toLocaleString(undefined,{minimumFractionDigits:2})}</td>
                              </tr> : null
                            ))}
                            <tr className="total-row"><td><strong>Equity + Liabilities</strong></td><td className="text-right"><strong>{
                              Object.entries(aggregated)
                                .filter(([k]) => ['REVALUATION_RESERVE','ACCUMULATED_LOSSES','EOSB','TRADE_PAYABLES'].includes(k))
                                .reduce((s,[,v]:any) => s + (v.cy||0), 0)
                                .toLocaleString(undefined,{minimumFractionDigits:2})
                            }</strong></td></tr>
                          </tbody>
                        </table>
                      </div>
                      <div>
                        <h4>Profit &amp; Loss</h4>
                        <table className="data-table">
                          <tbody>
                            {['REVENUE','COS','GRANT_INCOME','OTHER_INCOME','ADMIN_EXPENSES','FINANCE_COST'].map(k => (
                              aggregated[k] ? <tr key={k}>
                                <td>{FS_LINE_LABELS[k]}</td>
                                <td className="text-right">{Number(aggregated[k].cy).toLocaleString(undefined,{minimumFractionDigits:2})}</td>
                              </tr> : null
                            ))}
                            <tr className="total-row"><td><strong>Net Profit</strong></td><td className="text-right"><strong>{
                              ((aggregated['REVENUE']?.cy||0)+(aggregated['GRANT_INCOME']?.cy||0)+(aggregated['OTHER_INCOME']?.cy||0)
                               -(aggregated['COS']?.cy||0)-(aggregated['ADMIN_EXPENSES']?.cy||0)-(aggregated['FINANCE_COST']?.cy||0))
                              .toLocaleString(undefined,{minimumFractionDigits:2})
                            }</strong></td></tr>
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                )}

                <div className="card mb-4">
                  <h3 className="card-title">QC Checklist</h3>
                  {validation.results?.map((r: ValidationResult, i: number) => (
                    <div key={i} className={`check-row check-${r.result.toLowerCase()}`}>
                      <span className={`badge badge-${r.result.toLowerCase()}`}>{r.result}</span>
                      <div>
                        <strong>{r.check_name}</strong>
                        <div className="text-sm">{r.explanation}</div>
                        {r.result !== 'PASS' && r.expected && (
                          <div className="text-xs text-muted">Expected: {r.expected} · Actual: {r.actual} · Diff: {r.difference}</div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                <div className="card">
                  <button className="btn-primary" onClick={() => setTab('generate')} disabled={!!busy}>
                    Proceed to Generate →
                  </button>
                </div>
              </>
            )}
          </div>
        )}

        {/* ── GENERATE TAB ───────────────────────────────────────────── */}
        {tab === 'generate' && (
          <div>
            <h2>Generate &amp; Export</h2>

            <div className="card mb-4">
              <h3 className="card-title">Generate Outputs</h3>
              <p className="text-sm text-muted mb-2">
                This will create populated copies of your audit firm's templates. Original templates are never modified.
              </p>
              <div className="btn-row">
                <button className="btn-primary" onClick={() => runGenerate(true, true)} disabled={!!busy}>
                  Generate Both Files
                </button>
                <button className="btn-secondary" onClick={() => runGenerate(false, true)} disabled={!!busy}>
                  Financial Statements Only
                </button>
                <button className="btn-secondary" onClick={() => runGenerate(true, false)} disabled={!!busy}>
                  Audit File Only
                </button>
              </div>
            </div>

            {generateResult && (
              <div className="card mb-4">
                <h3 className="card-title">Generated Files</h3>
                {generateResult.generated?.map((g: any, i: number) => (
                  <div key={i} className="generated-file-row">
                    <div>
                      <strong>{g.filename}</strong>
                      <div className="text-sm text-muted">{g.cells_written} cells written</div>
                      {g.issues?.length > 0 && (
                        <div className="text-sm text-amber">
                          {g.issues.length} minor issue(s): {g.issues.slice(0, 2).join('; ')}
                        </div>
                      )}
                    </div>
                    <a className="btn-primary" href={downloadUrl(engagementId, g.type)} download={g.filename}>
                      ↓ Download
                    </a>
                  </div>
                ))}
              </div>
            )}

            <div className="card">
              <h3 className="card-title">Supporting Reports</h3>
              <div className="btn-row">
                <a className="btn-secondary" href={downloadMappingUrl(engagementId)} download>
                  ↓ Mapping Report
                </a>
                <a className="btn-secondary" href={downloadValidationUrl(engagementId)} download>
                  ↓ Validation Report
                </a>
                <a className="btn-secondary" href={downloadAuditTrailUrl(engagementId)} download>
                  ↓ Audit Trail
                </a>
              </div>
            </div>
          </div>
        )}

      </main>
    </div>
  );
}

// ── Sub-components ────────────────────────────────────────────────────────────

function UploadCard({ label, uploaded, onUpload, required }: {
  label: string; fileType?: string; uploaded: any[]; onUpload: (f: File) => void; required?: boolean;
}) {
  return (
    <div className="card upload-card">
      <h3 className="card-title">{label} {required && <span className="required">*</span>}</h3>
      {uploaded.length > 0 ? (
        <div className="uploaded-files">
          {uploaded.map((f, i) => (
            <div key={i} className="uploaded-file">
              <span>✓ {f.original_name}</span>
            </div>
          ))}
          <label className="btn-secondary upload-btn">
            Replace
            <input type="file" accept=".xlsx,.xls,.xlsm" hidden onChange={e => e.target.files?.[0] && onUpload(e.target.files[0])} />
          </label>
        </div>
      ) : (
        <label className="upload-drop">
          <div className="upload-icon">📂</div>
          <p>Click to select Excel file</p>
          <input type="file" accept=".xlsx,.xls,.xlsm" hidden onChange={e => e.target.files?.[0] && onUpload(e.target.files[0])} />
        </label>
      )}
    </div>
  );
}

function StatCard({ label, value, color }: { label: string; value: any; color?: string }) {
  const colors: Record<string, string> = { green: '#16a34a', red: '#dc2626', amber: '#d97706' };
  return (
    <div className="stat-card">
      <div className="stat-value" style={color ? { color: colors[color] } : undefined}>{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}
