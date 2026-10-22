import React, { useState, useEffect } from 'react';
import { Clock, AlertTriangle, CheckCircle2, FileText, Download, ShieldAlert, ArrowUpRight, Scale } from 'lucide-react';
import { api } from '../api/client';

export default function ApplicationTracker({ citizen }) {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [grievanceResult, setGrievanceResult] = useState(null);
  const [generatingAppId, setGeneratingAppId] = useState(null);

  const fetchApplications = async () => {
    setLoading(true);
    try {
      const data = await api.getApplications();
      setApplications(data);
    } catch (err) {
      console.error('Failed to load applications:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApplications();
  }, []);

  const handleDraftGrievance = async (appId) => {
    setGeneratingAppId(appId);
    try {
      const res = await api.draftGrievance(appId);
      setGrievanceResult(res);
      await fetchApplications(); // Refresh list to reflect grievance_filed
    } catch (err) {
      console.error('Grievance draft failed:', err);
      alert('Failed to generate grievance appeal.');
    } finally {
      setGeneratingAppId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Clock className="h-5 w-5 text-govblue-800" />
              <span>Right to Public Services (RTS) Act SLA Tracker</span>
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              Monitors statutory delivery deadlines under Maharashtra Right to Public Services Act, 2015.
              Breached applications automatically unlock legal Form-1 Appellate Grievance drafting.
            </p>
          </div>
          <span className="text-xs bg-slate-100 text-slate-600 px-3 py-1 rounded-full font-mono font-medium">
            Evaluation Date: 2026-10-22
          </span>
        </div>
      </div>

      {/* Grievance Ready Modal / Alert */}
      {grievanceResult && (
        <div className="p-4 bg-red-50 border border-red-300 rounded-2xl flex items-center justify-between shadow-sm">
          <div className="flex items-center gap-3">
            <Scale className="h-6 w-6 text-red-600" />
            <div>
              <div className="text-sm font-bold text-red-900">
                Maharashtra RTS Act 2015 Form-1 First Appeal Generated!
              </div>
              <p className="text-xs text-red-700 mt-0.5">
                Statutory fine notice under Section 9(1) of Maharashtra Act No. XXXI of 2015 prepared for submission to Appellate Authority.
              </p>
            </div>
          </div>
          <a
            href={`http://localhost:8000${grievanceResult.pdf_url}`}
            target="_blank"
            rel="noreferrer"
            className="px-4 py-2 bg-red-700 hover:bg-red-800 text-white rounded-lg text-xs font-bold shadow flex items-center gap-1.5"
          >
            <Download className="h-4 w-4" />
            <span>Download Form-1 Appeal PDF</span>
          </a>
        </div>
      )}

      {/* Applications List */}
      <div className="space-y-4">
        {loading ? (
          <div className="text-center py-12 text-slate-400">Loading statutory SLA timelines...</div>
        ) : applications.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-2xl border border-slate-200 text-slate-400">
            No active applications found. Use the RPA Co-Pilot to submit an application.
          </div>
        ) : (
          applications.map((app) => {
            const isBreached = app.is_breached;
            return (
              <div
                key={app.application_id}
                className={`p-6 bg-white rounded-2xl shadow-sm border transition-all ${
                  isBreached ? 'border-red-300 ring-1 ring-red-200' : 'border-slate-200'
                }`}
              >
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-base font-bold text-slate-900">{app.scheme_name}</h3>
                      <span className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full ${
                        isBreached
                          ? 'bg-red-100 text-red-800 border border-red-300'
                          : 'bg-blue-100 text-blue-800 border border-blue-200'
                      }`}>
                        {isBreached ? 'SLA BREACHED' : 'WITHIN STATUTORY SLA'}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-1">
                      Department: {app.department} &bull; Tracking ID: <span className="font-mono font-semibold text-slate-700">{app.portal_tracking_id || 'MHA-2026-981245'}</span> &bull; Applicant: <b>{app.citizen_name}</b>
                    </p>
                  </div>

                  {/* Grievance Action */}
                  <div>
                    {isBreached && (
                      <button
                        onClick={() => handleDraftGrievance(app.application_id)}
                        disabled={generatingAppId === app.application_id}
                        className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-xl text-xs font-bold shadow flex items-center gap-2 transition-all"
                      >
                        <Scale className="h-4 w-4" />
                        <span>
                          {generatingAppId === app.application_id
                            ? 'Drafting Appeal PDF...'
                            : '1-Click Draft RTS Grievance Appeal'}
                        </span>
                      </button>
                    )}
                  </div>
                </div>

                {/* Timeline Bar */}
                <div className="mt-5 space-y-2">
                  <div className="flex justify-between text-xs text-slate-600 font-medium">
                    <span>Submitted: {app.submitted_at}</span>
                    <span>
                      <b>{app.days_elapsed} Days Elapsed</b> / Statutory Limit: {app.sla_limit_days} Days
                    </span>
                    {isBreached && (
                      <span className="text-red-600 font-bold">
                        Delay: +{app.days_overdue} Days Overdue
                      </span>
                    )}
                  </div>

                  <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all duration-500 ${
                        isBreached ? 'bg-red-500' : 'bg-govblue-600'
                      }`}
                      style={{ width: `${Math.min(100, app.progress_percentage)}%` }}
                    />
                  </div>
                </div>

                {/* Statutory RTS Notice */}
                {isBreached && (
                  <div className="mt-4 p-3 bg-red-50/70 rounded-xl border border-red-200 text-xs text-red-900 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <ShieldAlert className="h-4 w-4 text-red-600 shrink-0" />
                      <span>
                        Under Section 9(1) of Maharashtra RTS Act 2015, Designated Officer is liable to a statutory penalty fine up to Rs. 5,000 for service delivery failure.
                      </span>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
