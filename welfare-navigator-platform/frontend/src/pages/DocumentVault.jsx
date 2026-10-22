import React, { useState } from 'react';
import { Upload, FileText, CheckCircle2, AlertTriangle, AlertCircle, Download, Minimize2, Eye, ShieldAlert } from 'lucide-react';
import { api } from '../api/client';

export default function DocumentVault({ citizen }) {
  const [docType, setDocType] = useState('INCOME');
  const [auditResult, setAuditResult] = useState(null);
  const [compressResult, setCompressResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [compressing, setCompressing] = useState(false);

  const sampleArtifacts = [
    { name: 'Artifact_B1: Identity Card (Ramesh S. Patil)', file: 'Artifact_B1_IdentityCard_Ramesh_Shamrao_Patil.jpg', type: 'IDENTITY' },
    { name: 'Artifact_B2: Expired Income Cert 2023 (Fuzz <85 & Expiry Alert)', file: 'Artifact_B2_IncomeCert_Ramesh_S_Patil_Expired2023.jpg', type: 'INCOME' },
    { name: 'Artifact_B3: Valid Caste Cert (Kunbi OBC)', file: 'Artifact_B3_Valid_Caste_Cert.jpg', type: 'CASTE' }
  ];

  const handleTestSample = async (sample) => {
    setLoading(true);
    setAuditResult(null);
    setCompressResult(null);
    setDocType(sample.type);

    try {
      // Fetch sample file as blob
      const res = await fetch(`http://localhost:8000/sample_artifacts/${sample.file}`);
      const blob = await res.blob();
      const file = new File([blob], sample.file, { type: 'image/jpeg' });

      // Run audit
      const audit = await api.auditDocument(citizen?.id || 'c-patil-ramesh-001', sample.type, file);
      setAuditResult(audit);
    } catch (err) {
      console.error('Audit failed:', err);
      alert('Audit failed. Ensure backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setLoading(true);
    setAuditResult(null);
    setCompressResult(null);

    try {
      const audit = await api.auditDocument(citizen?.id || 'c-patil-ramesh-001', docType, file);
      setAuditResult(audit);
    } catch (err) {
      console.error('Audit failed:', err);
      alert('Audit failed: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCompress = async () => {
    if (!auditResult) return;
    setCompressing(true);
    try {
      // Re-fetch audited file or test file
      const filename = auditResult.filename;
      const res = await fetch(`http://localhost:8000/sample_artifacts/${filename}`);
      const blob = await res.blob();
      const file = new File([blob], filename, { type: 'image/jpeg' });

      const comp = await api.compressDocument(file);
      setCompressResult(comp);
    } catch (err) {
      console.error('Compression failed:', err);
      alert('Compression failed.');
    } finally {
      setCompressing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
        <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
          <FileText className="h-5 w-5 text-govblue-800" />
          <span>Pre-Flight Document Quality Gate & 20KB–50KB Compressor</span>
        </h2>
        <p className="text-xs text-slate-500 mt-1">
          Automated OCR extraction with PII redaction, RapidFuzz name mismatch cross-validation (&lt;85 alert),
          certificate expiry checks vs 2026-10-22, and automated Self-Declaration Affidavit generation.
        </p>

        {/* Quick Test Vectors */}
        <div className="mt-4 pt-4 border-t border-slate-100">
          <span className="text-xs font-semibold text-slate-600 block mb-2">
            Load Pre-Configured Test Artifacts:
          </span>
          <div className="flex flex-wrap gap-2">
            {sampleArtifacts.map((s, idx) => (
              <button
                key={idx}
                onClick={() => handleTestSample(s)}
                disabled={loading}
                className="px-3 py-1.5 bg-slate-100 hover:bg-govblue-50 hover:text-govblue-800 border border-slate-200 rounded-lg text-xs font-medium transition-all"
              >
                {s.name}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload Form Box */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 space-y-4">
          <h3 className="text-sm font-bold text-slate-800">Upload Certificate File</h3>

          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Document Category:</label>
            <select
              value={docType}
              onChange={(e) => setDocType(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs font-medium"
            >
              <option value="INCOME">Income Certificate</option>
              <option value="CASTE">Caste / Category Certificate</option>
              <option value="IDENTITY">National Citizen Identity Card</option>
              <option value="LAND">7/12 Agricultural Land Record</option>
            </select>
          </div>

          <div className="border-2 border-dashed border-slate-300 rounded-xl p-6 text-center hover:border-govblue-600 transition-colors">
            <Upload className="h-8 w-8 text-slate-400 mx-auto mb-2" />
            <span className="text-xs font-medium text-slate-600 block mb-1">Upload Document (JPEG / PNG / PDF)</span>
            <input
              type="file"
              onChange={handleFileUpload}
              className="block w-full text-xs text-slate-500 file:mr-4 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-govblue-50 file:text-govblue-800 hover:file:bg-govblue-100 cursor-pointer"
            />
          </div>

          {loading && (
            <div className="p-3 bg-blue-50 text-govblue-800 text-xs rounded-lg text-center font-medium animate-pulse">
              Executing OCR, RapidFuzz String Distance & Expiry Audit...
            </div>
          )}
        </div>

        {/* Audit Results Panel */}
        <div className="lg:col-span-2 space-y-4">
          {auditResult ? (
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 space-y-5">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div>
                  <h3 className="text-base font-bold text-slate-900">Pre-Flight Audit Report</h3>
                  <span className="text-xs text-slate-500">File: {auditResult.filename}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="bg-emerald-50 text-emerald-700 text-xs font-bold px-2.5 py-1 rounded-full border border-emerald-200">
                    {auditResult.pii_badge}
                  </span>
                  <span className={`text-xs font-bold px-2.5 py-1 rounded-full border ${
                    auditResult.quality_status === 'PASS'
                      ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                      : 'bg-red-50 text-red-700 border-red-200'
                  }`}>
                    Blur Score: {auditResult.blur_score} ({auditResult.quality_status})
                  </span>
                </div>
              </div>

              {/* Critical Alerts (RapidFuzz Mismatch & Expiry) */}
              <div className="space-y-3">
                {auditResult.name_mismatch_alert && (
                  <div className="p-4 bg-amber-50 border border-amber-300 rounded-xl flex items-start gap-3">
                    <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <div className="text-xs font-bold text-amber-900">
                        RapidFuzz Token Sort Mismatch Alert (Score: {auditResult.rapidfuzz_name_score} &lt; 85)
                      </div>
                      <p className="text-xs text-amber-800 mt-0.5">{auditResult.name_validation_message}</p>
                      {auditResult.affidavit_pdf_url && (
                        <a
                          href={`http://localhost:8000${auditResult.affidavit_pdf_url}`}
                          target="_blank"
                          rel="noreferrer"
                          className="mt-2 inline-flex items-center gap-1.5 px-3 py-1 bg-amber-600 hover:bg-amber-700 text-white rounded text-xs font-semibold shadow-sm"
                        >
                          <Download className="h-3.5 w-3.5" />
                          <span>Download Pre-Filled Name Mismatch Affidavit PDF</span>
                        </a>
                      )}
                    </div>
                  </div>
                )}

                {auditResult.expiry_status === 'EXPIRED' && (
                  <div className="p-4 bg-red-50 border border-red-300 rounded-xl flex items-start gap-3">
                    <ShieldAlert className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />
                    <div>
                      <div className="text-xs font-bold text-red-900">Statutory Certificate Expired</div>
                      <p className="text-xs text-red-800 mt-0.5">{auditResult.expiry_message}</p>
                      <p className="text-[11px] text-red-700 mt-1 font-medium">
                        Remediation: Scheme applications requiring valid income certification will flag as Near-Miss until renewed at Tehsil/Aaple Sarkar.
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {/* Extracted OCR Table */}
              <div>
                <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                  Extracted Document Fields (With PII Redaction)
                </h4>
                <div className="bg-slate-50 rounded-xl border border-slate-200 overflow-hidden">
                  <table className="w-full text-xs text-left">
                    <tbody className="divide-y divide-slate-200">
                      {Object.entries(auditResult.extracted_fields || {}).map(([key, val]) => (
                        <tr key={key} className="hover:bg-white">
                          <td className="px-4 py-2 font-semibold text-slate-600 capitalize">{key.replace('_', ' ')}</td>
                          <td className="px-4 py-2 font-mono text-slate-800">{String(val)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* 20KB-50KB Compressor Action */}
              <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-bold text-slate-800">MahaDBT File Bracket Gate (20KB - 50KB)</h4>
                  <p className="text-[11px] text-slate-500">Binary-search Pillow compression to prevent portal upload rejections.</p>
                </div>
                <button
                  onClick={handleCompress}
                  disabled={compressing}
                  className="px-4 py-2 bg-govblue-800 hover:bg-govblue-900 text-white rounded-lg text-xs font-bold shadow flex items-center gap-2"
                >
                  <Minimize2 className="h-3.5 w-3.5" />
                  <span>{compressing ? 'Compressing...' : '1-Click Compress to 20KB-50KB'}</span>
                </button>
              </div>

              {/* Compression Result Card */}
              {compressResult && (
                <div className="p-4 bg-emerald-50 rounded-xl border border-emerald-200 flex items-center justify-between text-xs">
                  <div>
                    <span className="font-bold text-emerald-900 block">Compression Succeeded!</span>
                    <span className="text-slate-600">
                      Original: {compressResult.original_size_kb} KB &rarr;{' '}
                      <b className="text-emerald-700 font-mono text-sm">{compressResult.compressed_size_kb} KB</b> (Target: 20KB-50KB)
                    </span>
                  </div>
                  <a
                    href={`http://localhost:8000${compressResult.download_url}`}
                    target="_blank"
                    rel="noreferrer"
                    className="px-3 py-1.5 bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg font-bold flex items-center gap-1.5 shadow-sm"
                  >
                    <Download className="h-3.5 w-3.5" />
                    <span>Download Ready File</span>
                  </a>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-white p-12 rounded-2xl shadow-sm border border-slate-200 text-center text-slate-400">
              <FileText className="h-12 w-12 mx-auto mb-3 opacity-30" />
              <p className="text-sm font-semibold text-slate-600">No Document Audited Yet</p>
              <p className="text-xs text-slate-400 mt-1">Select one of the sample artifacts above or upload a certificate to inspect.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
