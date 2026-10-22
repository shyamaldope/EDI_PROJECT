import React, { useEffect, useState } from 'react';
import { X, MessageSquare, Send, CheckCircle2, RefreshCw } from 'lucide-react';
import { api } from '../api/client';

export default function OutboxDrawer({ isOpen, onClose }) {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchOutbox = async () => {
    setLoading(true);
    try {
      const data = await api.getOutbox();
      setMessages(data);
    } catch (err) {
      console.error('Failed to load outbox:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchOutbox();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/40 backdrop-blur-sm flex justify-end">
      <div className="w-full max-w-md bg-white h-full shadow-2xl flex flex-col transform transition-transform duration-300">
        {/* Header */}
        <div className="p-4 bg-govblue-800 text-white flex items-center justify-between border-b border-blue-700">
          <div className="flex items-center space-x-2">
            <MessageSquare className="h-5 w-5 text-govorange-500" />
            <h2 className="text-base font-bold">Proactive Citizen Outbox</h2>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={fetchOutbox}
              className="p-1 hover:bg-white/10 rounded text-blue-200 hover:text-white"
              title="Refresh"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={onClose}
              className="p-1 hover:bg-white/10 rounded text-blue-200 hover:text-white"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Subhead Notice */}
        <div className="p-3 bg-amber-50 border-b border-amber-200 text-xs text-amber-800 flex items-start gap-2">
          <span className="font-bold shrink-0">[SIMULATED GATEWAY]:</span>
          <span>
            Demonstrates proactive WhatsApp & SMS alerts triggered by Reverse Matcher when newly approved schemes activate.
          </span>
        </div>

        {/* Message List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.length === 0 ? (
            <div className="text-center py-12 text-slate-400">
              <Send className="h-10 w-10 mx-auto mb-2 opacity-30" />
              <p className="text-sm">No outbox dispatches yet.</p>
              <p className="text-xs mt-1">Approve a draft scheme in Admin mode to trigger reverse matching.</p>
            </div>
          ) : (
            messages.map((m) => (
              <div key={m.id} className="p-3.5 rounded-xl border border-slate-200 bg-slate-50 hover:bg-white transition-all shadow-sm">
                <div className="flex items-center justify-between text-xs text-slate-500 mb-1.5">
                  <span className="font-semibold text-slate-800">{m.citizen_name}</span>
                  <span className="flex items-center gap-1 text-[11px] text-emerald-600 font-medium">
                    <CheckCircle2 className="h-3 w-3" />
                    {m.channel} ({m.status})
                  </span>
                </div>
                <p className="text-xs text-slate-700 bg-white p-2.5 rounded-lg border border-slate-100 font-sans leading-relaxed">
                  {m.message}
                </p>
                <div className="text-[10px] text-slate-400 mt-2 text-right">
                  {m.sent_at ? new Date(m.sent_at).toLocaleTimeString() : 'Just now'}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-slate-100 bg-slate-50 text-center text-[11px] text-slate-500">
          Phone Numbers Stored as Salted SHA-256 Hashes &bull; DPDP Act 2023 Aligned
        </div>
      </div>
    </div>
  );
}
