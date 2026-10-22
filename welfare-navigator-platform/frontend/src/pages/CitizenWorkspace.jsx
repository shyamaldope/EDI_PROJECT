import React, { useState, useEffect } from 'react';
import {
  Mic, Send, Sparkles, AlertCircle, ShieldAlert, CheckCircle2,
  Layers, Users, Trash2, Play, Volume2, ShieldCheck, ChevronRight, Hash, ArrowUpRight
} from 'lucide-react';
import { api } from '../api/client';

export default function CitizenWorkspace({
  citizen,
  citizens,
  onSelectCitizen,
  onLaunchRpa,
  language
}) {
  const [inputText, setInputText] = useState('');
  const [chatLog, setChatLog] = useState([
    {
      sender: 'system',
      text: 'नमस्कार रमेशजी! मी आपला कल्याणकारी योजना सहाय्यक आहे. आपण काय मदत हवी आहे? (उदा. "माझे २.५ एकर शेती आहे आणि १.८ लाख उत्पन्न आहे")',
      pii_badge: '[PII CLEAN]',
      audio: null
    }
  ]);
  const [loadingChat, setLoadingChat] = useState(false);
  const [eligibilityData, setEligibilityData] = useState(null);
  const [activeTab, setActiveTab] = useState('ELIGIBLE'); // ELIGIBLE, NEAR_MISS, MWIS_STACK, HOUSEHOLD
  const [nextQuestion, setNextQuestion] = useState(null);
  const [selectedAuditSig, setSelectedAuditSig] = useState(null);
  const [purgeSuccess, setPurgeSuccess] = useState(null);

  // Life Event quick triggers
  const lifeEvents = [
    { label: '🌾 पीक नुकसान (Crop Loss)', query: 'आमच्या शेतात अवकाळी पावसाने पीक नुकसान झाले आहे.' },
    { label: '🎓 उच्च शिक्षण प्रवेश (College Admission)', query: 'माझ्या मुलाने इंजिनिअरिंग कॉलेजमध्ये प्रवेश घेतला आहे.' },
    { label: '👵 वयाची ६५ वर्षे पूर्ण (Senior 65+)', query: 'माझे वय ६५ वर्षे पूर्ण झाले आहे, पेंशन सुरू करायची आहे.' },
    { label: '👧 मुलगी झाली (Girl Child Born)', query: 'आमच्या घरात कन्यारत्न जन्माला आले आहे.' }
  ];

  const loadEligibility = async (citizenId) => {
    try {
      const data = await api.getCitizenSchemes(citizenId);
      setEligibilityData(data);
    } catch (err) {
      console.error('Failed to load eligibility:', err);
    }
  };

  const loadNextQuestion = async (profile) => {
    try {
      const res = await api.getNextQuestion(profile);
      setNextQuestion(res.next_question);
    } catch (err) {
      console.error('Failed to load entropy question:', err);
    }
  };

  useEffect(() => {
    if (citizen) {
      loadEligibility(citizen.id);
      loadNextQuestion(citizen);
    }
  }, [citizen]);

  const handleSendMessage = async (customText = null) => {
    const textToSend = customText || inputText;
    if (!textToSend.trim()) return;

    const userEntry = { sender: 'user', text: textToSend };
    setChatLog((prev) => [...prev, userEntry]);
    if (!customText) setInputText('');
    setLoadingChat(true);

    try {
      const res = await api.processVoiceOrText(textToSend, language);
      const botEntry = {
        sender: 'system',
        text: res.response_text,
        pii_badge: res.pii_badge,
        audio: res.audio_uri,
        life_events: res.life_events
      };
      setChatLog((prev) => [...prev, botEntry]);

      // If slots extracted, refresh schemes
      if (citizen) {
        await loadEligibility(citizen.id);
      }
    } catch (err) {
      console.error('Chat error:', err);
    } finally {
      setLoadingChat(false);
    }
  };

  const handlePurgeVault = async () => {
    if (!citizen) return;
    const confirmPurge = window.confirm(
      `DPDP Act 2023 Mandatory Warning:\n\nAre you sure you want to permanently erase the citizen vault for '${citizen.full_name}'?\n\nThis will cryptographically wipe all uploaded certificates, audit signatures, and notification logs.`
    );
    if (!confirmPurge) return;

    try {
      const res = await api.purgeVault(citizen.id);
      setPurgeSuccess(res);
      setEligibilityData(null);
    } catch (err) {
      alert('Purge failed: ' + err.message);
    }
  };

  return (
    <div className="space-y-6">
      {/* Citizen Persona Selector & Vault Purge Bar */}
      <div className="bg-white p-4 rounded-2xl shadow-sm border border-slate-200 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="bg-govblue-50 text-govblue-800 p-2 rounded-xl font-bold text-xs">
            PERSONA
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500 font-semibold">Active Citizen:</span>
              <select
                value={citizen?.id || ''}
                onChange={(e) => {
                  const sel = citizens.find((c) => c.id === e.target.value);
                  if (sel) onSelectCitizen(sel);
                }}
                className="text-sm font-bold text-slate-900 bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1 focus:outline-none cursor-pointer"
              >
                {citizens.slice(0, 15).map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.full_name} ({c.occupation}, {c.district} &bull; ₹{c.annual_income?.toLocaleString()})
                  </option>
                ))}
              </select>
            </div>
            <div className="text-[11px] text-slate-400 mt-0.5">
              Household ID: <span className="font-mono text-slate-600">{citizen?.household_id?.substring(0, 16)}...</span> &bull; Phone Hash: <span className="font-mono text-slate-600">{citizen?.phone_hash?.substring(0, 16)}...</span>
            </div>
          </div>
        </div>

        {/* DPDP Act 2023 Purge Vault Action */}
        <button
          onClick={handlePurgeVault}
          className="px-3.5 py-2 bg-red-50 hover:bg-red-100 text-red-700 border border-red-200 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 shadow-sm"
          title="1-Click Permanent Data Erasure under DPDP Act 2023"
        >
          <Trash2 className="h-3.5 w-3.5" />
          <span>Purge My Citizen Vault</span>
        </button>
      </div>

      {/* Purge Success Banner */}
      {purgeSuccess && (
        <div className="p-4 bg-red-50 border border-red-300 rounded-2xl text-xs text-red-900 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-red-600 shrink-0" />
            <div>
              <span className="font-bold">Citizen Vault Cryptographically Purged!</span>
              <p className="text-[11px] text-red-700 mt-0.5 font-mono">Receipt Hash: {purgeSuccess.purge_receipt_hash}</p>
            </div>
          </div>
          <span className="font-bold bg-white text-red-700 px-3 py-1 rounded-lg border border-red-200">
            0 BYTES REMAINING
          </span>
        </div>
      )}

      {/* Main Grid: Vernacular Assistant & Schemes Discovery */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Voice/Text Assistant & Entropy Slot-Filler */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 flex flex-col h-[600px] overflow-hidden">
            {/* Header */}
            <div className="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Sparkles className="h-4 w-4 text-govorange-500" />
                <h3 className="text-sm font-bold text-slate-800">Vernacular Voice & Policy Assistant</h3>
              </div>
              <span className="text-[10px] font-mono bg-emerald-50 text-emerald-700 font-bold px-2 py-0.5 rounded border border-emerald-200">
                BHASHINI ULCA ADAPTER
              </span>
            </div>

            {/* Next Best Question Badge (Shannon Entropy Gain) */}
            {nextQuestion && (
              <div className="px-4 py-2.5 bg-blue-50/80 border-b border-blue-100 flex items-center justify-between text-xs">
                <div className="flex items-center gap-1.5 text-govblue-800">
                  <span className="font-bold">Next Question:</span>
                  <span>{nextQuestion.label_mr || nextQuestion.label}?</span>
                </div>
                <span className="text-[10px] font-mono text-blue-600 bg-white px-2 py-0.5 rounded-full border border-blue-200">
                  Info Gain: +{nextQuestion.information_gain_score}
                </span>
              </div>
            )}

            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {chatLog.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}
                >
                  <div
                    className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-xs font-sans leading-relaxed shadow-sm ${
                      msg.sender === 'user'
                        ? 'bg-govblue-800 text-white rounded-br-none'
                        : 'bg-slate-100 text-slate-800 rounded-bl-none border border-slate-200'
                    }`}
                  >
                    <p>{msg.text}</p>
                    {msg.pii_badge && (
                      <span className="inline-block mt-1.5 text-[10px] font-mono px-2 py-0.5 bg-white/20 text-slate-600 rounded">
                        {msg.pii_badge}
                      </span>
                    )}
                    {msg.audio && (
                      <div className="mt-2 pt-2 border-t border-slate-200/50 flex items-center gap-2">
                        <Volume2 className="h-3.5 w-3.5 text-govblue-800" />
                        <audio src={msg.audio} controls className="h-6 w-40" />
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {loadingChat && (
                <div className="text-xs text-slate-400 italic">Bhashini ASR/TTS processing...</div>
              )}
            </div>

            {/* Life Event Quick Chips */}
            <div className="p-3 bg-slate-50 border-t border-slate-200 space-y-1.5">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
                Proactive Life-Event Triggers:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {lifeEvents.map((ev, i) => (
                  <button
                    key={i}
                    onClick={() => handleSendMessage(ev.query)}
                    className="text-[11px] px-2.5 py-1 bg-white hover:bg-govblue-50 hover:text-govblue-800 border border-slate-200 rounded-full font-medium transition-all"
                  >
                    {ev.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Input Bar */}
            <div className="p-3 border-t border-slate-200 bg-white flex items-center gap-2">
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                placeholder="Type or speak (e.g. उत्पन्न २ लाख, शेती ३ एकर)..."
                className="flex-1 px-3 py-2 border border-slate-300 rounded-xl text-xs focus:outline-none focus:border-govblue-800"
              />
              <button
                onClick={() => handleSendMessage('मी शेतकरी आहे, माझं उत्पन्न १.८ लाख रुपये आणि २.५ एकर शेती आहे.')}
                className="p-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl"
                title="Simulate Speech Input (Mic)"
              >
                <Mic className="h-4 w-4" />
              </button>
              <button
                onClick={() => handleSendMessage()}
                disabled={!inputText.trim()}
                className="p-2 bg-govblue-800 hover:bg-govblue-900 disabled:opacity-40 text-white rounded-xl shadow-sm"
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Right Column: Tabbed Schemes Showcase & MWIS Stacker */}
        <div className="lg:col-span-7 space-y-4">
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
            {/* Tabs Header */}
            <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-100">
              <div className="flex space-x-2 bg-slate-100 p-1 rounded-xl">
                <button
                  onClick={() => setActiveTab('ELIGIBLE')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                    activeTab === 'ELIGIBLE'
                      ? 'bg-govblue-800 text-white shadow-sm'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Eligible ({eligibilityData?.eligible_count || 0})
                </button>
                <button
                  onClick={() => setActiveTab('NEAR_MISS')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                    activeTab === 'NEAR_MISS'
                      ? 'bg-amber-500 text-white shadow-sm'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Near-Miss 75-99% ({eligibilityData?.near_miss_count || 0})
                </button>
                <button
                  onClick={() => setActiveTab('MWIS_STACK')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                    activeTab === 'MWIS_STACK'
                      ? 'bg-emerald-600 text-white shadow-sm'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Optimal Benefit Stack
                </button>
              </div>

              <div className="flex items-center gap-1.5 text-xs text-slate-500 font-mono">
                <ShieldCheck className="h-4 w-4 text-emerald-600" />
                <span>Deterministic Zero-LLM</span>
              </div>
            </div>

            {/* TAB 1: ELIGIBLE SCHEMES */}
            {activeTab === 'ELIGIBLE' && (
              <div className="mt-5 space-y-4">
                {eligibilityData?.eligible_schemes?.length === 0 ? (
                  <div className="text-center py-12 text-slate-400">
                    No schemes fully matched yet. Check Near-Miss tab for remediation advice.
                  </div>
                ) : (
                  eligibilityData?.eligible_schemes?.map((s) => (
                    <div
                      key={s.id}
                      className="p-5 rounded-2xl border border-slate-200 bg-slate-50/50 hover:bg-white hover:border-govblue-600 transition-all shadow-sm space-y-3"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <div className="flex items-center gap-2">
                            <h4 className="text-sm font-bold text-slate-900">{s.scheme_name}</h4>
                            <span className="bg-emerald-100 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded-full border border-emerald-300">
                              ELIGIBLE
                            </span>
                          </div>
                          <p className="text-xs text-slate-500 mt-0.5">{s.scheme_name_mr} &bull; {s.department}</p>
                        </div>
                        <div className="text-right shrink-0">
                          <span className="text-xs text-slate-400 block">Annual Financial Support</span>
                          <span className="text-base font-extrabold text-emerald-700 font-mono">
                            ₹{s.benefit_amount?.toLocaleString()}
                          </span>
                        </div>
                      </div>

                      {/* Condition Audit Breakdown */}
                      <div className="space-y-1.5 pt-2 border-t border-slate-200/60">
                        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
                          Verified Statutory Criteria:
                        </span>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                          {s.condition_results?.map((c, i) => (
                            <div key={i} className="flex items-center gap-1.5 text-xs text-slate-700">
                              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 shrink-0" />
                              <span className="truncate">{c.label}</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="pt-3 border-t border-slate-200/60 flex items-center justify-between">
                        <button
                          onClick={() => setSelectedAuditSig(s.audit_signature)}
                          className="text-xs text-govblue-800 hover:underline flex items-center gap-1 font-semibold"
                        >
                          <Hash className="h-3.5 w-3.5" />
                          <span>View SHA-256 Decision Receipt</span>
                        </button>
                        <button
                          onClick={() => onLaunchRpa(s)}
                          className="px-4 py-2 bg-govblue-800 hover:bg-govblue-900 text-white rounded-xl text-xs font-bold shadow flex items-center gap-1.5 transition-all"
                        >
                          <Play className="h-3.5 w-3.5 fill-white" />
                          <span>1-Click Apply (Agentic Co-Pilot)</span>
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}

            {/* TAB 2: NEAR-MISS SCHEMES (75% - 99%) */}
            {activeTab === 'NEAR_MISS' && (
              <div className="mt-5 space-y-4">
                {eligibilityData?.near_miss_schemes?.length === 0 ? (
                  <div className="text-center py-12 text-slate-400">
                    No near-miss schemes found.
                  </div>
                ) : (
                  eligibilityData?.near_miss_schemes?.map((nm) => (
                    <div
                      key={nm.id}
                      className="p-5 rounded-2xl border border-amber-200 bg-amber-50/30 space-y-3"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <div className="flex items-center gap-2">
                            <h4 className="text-sm font-bold text-slate-900">{nm.scheme_name}</h4>
                            <span className="bg-amber-100 text-amber-800 text-[10px] font-bold px-2 py-0.5 rounded-full border border-amber-300">
                              {nm.match_percentage}% MATCH
                            </span>
                          </div>
                          <p className="text-xs text-slate-500 mt-0.5">{nm.scheme_name_mr}</p>
                        </div>
                        <span className="text-sm font-bold text-slate-800 font-mono">
                          Unlocks ₹{nm.benefit_amount?.toLocaleString()}
                        </span>
                      </div>

                      {/* Remediation Pathway */}
                      <div className="p-3 bg-white rounded-xl border border-amber-200 space-y-2">
                        <span className="text-[10px] font-bold text-amber-800 uppercase tracking-wider block">
                          Actionable Remediation Checklist:
                        </span>
                        {nm.remediations?.map((r, i) => (
                          <div key={i} className="text-xs space-y-0.5">
                            <div className="font-semibold text-slate-800 flex items-center gap-1.5">
                              <AlertCircle className="h-3.5 w-3.5 text-amber-600 shrink-0" />
                              <span>{r.message}</span>
                            </div>
                            <div className="text-slate-600 pl-5 text-[11px]">
                              <b>Step:</b> {r.action}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}

            {/* TAB 3: OPTIMAL BENEFIT STACK (MWIS SOLVER) */}
            {activeTab === 'MWIS_STACK' && (
              <div className="mt-5 space-y-4">
                <div className="p-5 bg-emerald-50 rounded-2xl border border-emerald-200 flex items-center justify-between">
                  <div>
                    <span className="text-xs text-emerald-800 font-bold block">
                      Maximum Weight Independent Set (MWIS) Global Optimum
                    </span>
                    <span className="text-2xl font-black text-emerald-900 font-mono">
                      ₹{eligibilityData?.optimal_benefit_stack?.total_benefit?.toLocaleString()} / Year
                    </span>
                  </div>
                  <span className="text-xs bg-emerald-600 text-white font-bold px-3 py-1.5 rounded-xl shadow-sm">
                    {eligibilityData?.optimal_benefit_stack?.total_schemes_count} Non-Conflicting Schemes
                  </span>
                </div>

                {eligibilityData?.optimal_benefit_stack?.conflicts_resolved?.length > 0 && (
                  <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-1.5 text-xs text-slate-700">
                    <span className="font-bold text-slate-900 block">Mutual Exclusion Conflicts Resolved:</span>
                    {eligibilityData.optimal_benefit_stack.conflicts_resolved.map((cr, idx) => (
                      <p key={idx} className="text-[11px] text-slate-600 flex items-center gap-1.5">
                        <ChevronRight className="h-3 w-3 text-govorange-500 shrink-0" />
                        <span>{cr}</span>
                      </p>
                    ))}
                  </div>
                )}

                <div className="space-y-3 pt-2">
                  {eligibilityData?.optimal_benefit_stack?.recommended_schemes?.map((rec) => (
                    <div
                      key={rec.id}
                      className="p-4 rounded-xl border border-slate-200 bg-white flex items-center justify-between"
                    >
                      <div>
                        <h5 className="text-xs font-bold text-slate-900">{rec.scheme_name}</h5>
                        <span className="text-[11px] text-slate-500">{rec.department}</span>
                      </div>
                      <span className="text-sm font-bold text-emerald-700 font-mono">
                        +₹{rec.benefit_amount?.toLocaleString()}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Audit Signature Modal */}
      {selectedAuditSig && (
        <div className="fixed inset-0 z-50 overflow-hidden bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg bg-white rounded-2xl shadow-2xl p-6 border border-slate-200 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                <Hash className="h-4 w-4 text-govblue-800" />
                <span>SHA-256 Decision Audit Signature</span>
              </h3>
              <button onClick={() => setSelectedAuditSig(null)} className="text-slate-400 hover:text-slate-600">
                &times;
              </button>
            </div>
            <p className="text-xs text-slate-600">
              Under the Neuro-Symbolic boundary, every eligibility verdict generates a tamper-evident cryptographic hash signing citizen data, statutory rule AST, verdict, and timestamp:
            </p>
            <div className="p-3 bg-slate-900 rounded-xl text-emerald-400 font-mono text-xs break-all shadow-inner">
              {selectedAuditSig}
            </div>
            <button
              onClick={() => setSelectedAuditSig(null)}
              className="w-full py-2 bg-govblue-800 text-white rounded-lg text-xs font-bold"
            >
              Close Receipt
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
