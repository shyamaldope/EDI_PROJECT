import React from 'react';
import { ShieldCheck, Bell, Globe, User, Terminal, FileText, BarChart3, Store } from 'lucide-react';

export default function Navbar({ currentRole, setRole, language, setLanguage, outboxCount, toggleOutbox }) {
  const roles = [
    { id: 'CITIZEN', label: 'Citizen Portal', icon: User },
    { id: 'KIOSK', label: 'CSC Kiosk Mode', icon: Store },
    { id: 'ADMIN', label: 'Scheme Admin (HITL)', icon: FileText },
    { id: 'COLLECTOR', label: 'District Collector (Twin)', icon: BarChart3 }
  ];

  return (
    <header className="bg-govblue-800 text-white shadow-md border-b-4 border-govorange-500 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 py-3 flex flex-wrap items-center justify-between gap-4">
        {/* Logo & Platform Title */}
        <div className="flex items-center space-x-3">
          <div className="bg-white p-2 rounded-lg shadow-sm">
            <ShieldCheck className="h-7 w-7 text-govblue-800" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight">Welfare Navigator Platform</h1>
              <span className="bg-emerald-500/20 text-emerald-300 text-xs px-2 py-0.5 rounded-full font-mono border border-emerald-400/30">
                DPDP 2023 ALIGNED
              </span>
            </div>
            <p className="text-xs text-blue-200">
              Autonomous Agentic Citizen Welfare & Policy Intelligence &bull; Ref: 2026-10-22
            </p>
          </div>
        </div>

        {/* Role Switcher */}
        <div className="flex items-center bg-govblue-900/80 p-1 rounded-xl border border-blue-700/50">
          {roles.map((r) => {
            const Icon = r.icon;
            const isActive = currentRole === r.id;
            return (
              <button
                key={r.id}
                onClick={() => setRole(r.id)}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  isActive
                    ? 'bg-govorange-500 text-white shadow-sm'
                    : 'text-blue-200 hover:text-white hover:bg-white/5'
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                <span>{r.label}</span>
              </button>
            );
          })}
        </div>

        {/* Vernacular Language Selector & Outbox */}
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1 bg-white/10 px-2 py-1 rounded-lg text-xs">
            <Globe className="h-3.5 w-3.5 text-blue-300" />
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="bg-transparent text-white text-xs font-medium focus:outline-none cursor-pointer"
            >
              <option value="mr" className="text-slate-900">मराठी (Marathi)</option>
              <option value="hi" className="text-slate-900">हिंदी (Hindi)</option>
              <option value="en" className="text-slate-900">English</option>
            </select>
          </div>

          <button
            onClick={toggleOutbox}
            className="relative bg-white/10 hover:bg-white/20 p-2 rounded-lg text-blue-200 hover:text-white transition-all flex items-center gap-1.5 text-xs font-medium"
            title="View Proactive WhatsApp & SMS Outbox"
          >
            <Bell className="h-4 w-4" />
            <span>Outbox</span>
            {outboxCount > 0 && (
              <span className="bg-govorange-500 text-white text-[10px] font-bold px-1.5 py-0.2 rounded-full">
                {outboxCount}
              </span>
            )}
          </button>
        </div>
      </div>
    </header>
  );
}
