import React, { useState, useEffect } from 'react';
import { FileUp, GitCompare, CheckCircle2, ShieldCheck, AlertTriangle, Eye, ArrowRight, Play, BookOpen } from 'lucide-react';
import { api } from '../api/client';

export default function AdminIngestion() {
  const [incomingFiles, setIncomingFiles] = useState([]);
  const [ingestedScheme, setIngestedScheme] = useState(null);
  const [diffResult, setDiffResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [approving, setApproving] = useState(false);
  const [approvedSuccess, setApprovedSuccess] = useState(null);

  useEffect(() => {
    loadFiles();
  }, []);

  const loadFiles = async () => {
    try {
      const data = await api.getIncomingGRs();
      setIncomingFiles(data.incoming_gr_files || []);
    } catch (err) {
      console.error('Failed to load incoming GR files:', err);
    }
  };

  const handleIngestSample = async (filename) => {
    setLoading(true);
    setIngestedScheme(null);
    setDiffResult(null);
    setApprovedSuccess(null);

    try {
      const fd = new FormData();
      if (filename) {
        fd.append('filename', filename);
      }
      const candidate = await api.ingestGR(fd);
      setIngestedScheme(candidate);

      // Perform sample AST diff with existing version
      const oldAst = {
        operator: 'AND',
        children: [
          { field: 'occupation', operator: 'EQUALS', value: 'Farmer', label: 'Active farmer' },
          { field: 'landholding_acres', operator: 'LESS_EQUAL', value: 2.0, label: 'Landholding <= 2.0 acres' },
          { field: 'annual_income', operator: 'LESS_EQUAL', value: 150000.0, label: 'Family income <= 1.5 Lakhs' }
        ]
      };
      const diff = await api.diffSchemes(oldAst, candidate.ast_rule);
      setDiffResult(diff);
    } catch (err) {
      console.error('Ingestion failed:', err);
      alert('Ingestion failed: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!ingestedScheme) return;
    setApproving(true);
    try {
      const res = await api.approveScheme(ingestedScheme.id);
      setApprovedSuccess(res);
      setIngestedScheme({ ...ingestedScheme, status: 'ACTIVE' });
    } catch (err) {
      console.error('Approval failed:', err);
      alert('Approval failed: ' + err.message);
    } finally {
      setApproving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
        <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
          <BookOpen className="h-5 w-5 text-govblue-800" />
          <span>Zero-Touch Government Resolution (GR) Ingestion & HITL Governance</span>
        </h2>
        <p className="text-xs text-slate-500 mt-1">
          Scans state administrative gazettes, compiles unstructured administrative prose into nested AST rules,
          computes visual AST diffs, and strictly enforces <b>Human-in-the-Loop Quarantine</b> (<span className="font-mono text-amber-700">status = DRAFT_HITL</span>) until Admin approval.
        </p>

        {/* Action Trigger */}
        <div className="mt-4 pt-4 border-t border-slate-100 flex flex-wrap items-center gap-3">
          <span className="text-xs font-semibold text-slate-600">Available Gazette PDFs:</span>
          <button
            onClick={() => handleIngestSample('Artifact_A_Maharashtra_GR_2026.pdf')}
            disabled={loading}
            className="px-4 py-2 bg-govblue-800 hover:bg-govblue-900 text-white rounded-xl text-xs font-bold shadow flex items-center gap-2 transition-all"
          >
            <FileUp className="h-4 w-4" />
            <span>{loading ? 'Compiling GR PDF to AST...' : 'Ingest Maha Krishi Urja GR 2026 PDF'}</span>
          </button>
        </div>
      </div>

      {/* Approval Success Alert */}
      {approvedSuccess && (
        <div className="p-4 bg-emerald-50 border border-emerald-300 rounded-2xl shadow-sm flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="h-6 w-6 text-emerald-600" />
            <div>
              <div className="text-sm font-bold text-emerald-900">
                Scheme Approved & Activated: {approvedSuccess.scheme_name}
              </div>
              <p className="text-xs text-emerald-700 mt-0.5">
                Status transitioned to ACTIVE. Asynchronous reverse-matching dispatched across all 50 registered citizens.
              </p>
            </div>
          </div>
          <span className="text-xs font-bold bg-emerald-600 text-white px-3 py-1.5 rounded-lg shadow-sm">
            Notifications Queued in Outbox
          </span>
        </div>
      )}

      {/* Split Screen Ingestion & AST Review */}
      {ingestedScheme && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left: Administrative Details & Citations */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <h3 className="text-sm font-bold text-slate-900">Administrative Metadata & Citations</h3>
                <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${
                  ingestedScheme.status === 'ACTIVE'
                    ? 'bg-emerald-100 text-emerald-800'
                    : 'bg-amber-100 text-amber-800 border border-amber-300'
                }`}>
                  Status: {ingestedScheme.status}
                </span>
              </div>

              <div className="space-y-2 text-xs">
                <div>
                  <span className="font-semibold text-slate-500">Scheme Name:</span>
                  <p className="font-bold text-slate-800 text-sm mt-0.5">{ingestedScheme.scheme_name}</p>
                </div>
                <div>
                  <span className="font-semibold text-slate-500">Department:</span>
                  <p className="text-slate-800">{ingestedScheme.department}</p>
                </div>
                <div className="grid grid-cols-2 gap-2 pt-2">
                  <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-100">
                    <span className="text-[10px] text-slate-500 block uppercase">Benefit Amount</span>
                    <span className="text-sm font-bold text-emerald-700">₹{ingestedScheme.benefit_amount?.toLocaleString()}</span>
                  </div>
                  <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-100">
                    <span className="text-[10px] text-slate-500 block uppercase">Statutory SLA</span>
                    <span className="text-sm font-bold text-govblue-800">{ingestedScheme.sla_days} Days</span>
                  </div>
                </div>
              </div>

              {/* Exact Citations Table */}
              <div className="pt-2">
                <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                  Statutory Rule Citations (From PDF Gazette)
                </h4>
                <div className="bg-slate-50 rounded-xl border border-slate-200 overflow-hidden">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-slate-100 text-slate-600 font-semibold border-b border-slate-200">
                      <tr>
                        <th className="px-3 py-2">Condition Field</th>
                        <th className="px-3 py-2">Page</th>
                        <th className="px-3 py-2">Paragraph / Clause</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200">
                      {(ingestedScheme.citations || []).map((c, i) => (
                        <tr key={i} className="hover:bg-white">
                          <td className="px-3 py-2 font-mono font-medium text-slate-700">{c.field}</td>
                          <td className="px-3 py-2 text-slate-600">{c.page}</td>
                          <td className="px-3 py-2 text-slate-600 font-medium">{c.clause}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Right: Compiled Candidate AST JSON */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <h3 className="text-sm font-bold text-slate-900">Executable AST Schema (Deterministic)</h3>
                <span className="text-[11px] font-mono bg-blue-50 text-govblue-800 px-2 py-0.5 rounded">
                  Zero LLM Evaluation
                </span>
              </div>

              <div className="bg-slate-900 rounded-xl p-4 font-mono text-xs text-emerald-400 overflow-x-auto max-h-[340px] shadow-inner">
                <pre>{JSON.stringify(ingestedScheme.ast_rule, null, 2)}</pre>
              </div>

              {/* Mandatory HITL Approve Button */}
              {ingestedScheme.status === 'DRAFT_HITL' && (
                <div className="p-4 bg-amber-50 rounded-xl border border-amber-300 flex items-center justify-between">
                  <div>
                    <span className="text-xs font-bold text-amber-900 block">Mandatory Human-in-the-Loop Review</span>
                    <span className="text-[11px] text-amber-800">
                      Review side-by-side citations and AST before authorizing citizen reverse-matching.
                    </span>
                  </div>
                  <button
                    onClick={handleApprove}
                    disabled={approving}
                    className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold shadow flex items-center gap-1.5 transition-all"
                  >
                    <CheckCircle2 className="h-4 w-4" />
                    <span>{approving ? 'Activating...' : 'Approve Scheme & Activate'}</span>
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Visual AST Diffing Component */}
          {diffResult && (
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 space-y-3">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <GitCompare className="h-4 w-4 text-govblue-800" />
                <span>Visual Git-Style AST Diff (Amended Policy vs Prior Version)</span>
              </h3>
              <p className="text-xs text-slate-500">
                Tracks structural alterations in eligibility criteria (relaxed thresholds in orange, added in green, removed in red).
              </p>

              <div className="space-y-2 mt-3">
                {diffResult.diff_summary.map((line, idx) => {
                  const isMod = line.startsWith('~');
                  const isAdd = line.startsWith('+');
                  const isRem = line.startsWith('-');
                  return (
                    <div
                      key={idx}
                      className={`p-3 rounded-lg text-xs font-mono font-medium flex items-center gap-2 ${
                        isMod
                          ? 'bg-amber-50 text-amber-900 border border-amber-200'
                          : isAdd
                          ? 'bg-emerald-50 text-emerald-900 border border-emerald-200'
                          : 'bg-red-50 text-red-900 border border-red-200'
                      }`}
                    >
                      <span>{line}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
