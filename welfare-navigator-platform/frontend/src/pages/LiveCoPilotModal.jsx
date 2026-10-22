import React, { useState, useEffect, useRef } from 'react';
import { X, Play, CheckCircle2, AlertTriangle, ShieldCheck, Download, Loader2, ArrowRight, RotateCcw } from 'lucide-react';
import { api } from '../api/client';

export default function LiveCoPilotModal({ isOpen, onClose, citizen, scheme }) {
  const [sessionState, setSessionState] = useState('IDLE'); // IDLE, RUNNING, PAUSED, COMPLETED, ERROR
  const [currentStep, setCurrentStep] = useState('');
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState('');
  const [screenshot, setScreenshot] = useState(null);
  const [captchaHint, setCaptchaHint] = useState('');
  const [otpHint, setOtpHint] = useState('');
  const [userCaptcha, setUserCaptcha] = useState('');
  const [userOtp, setUserOtp] = useState('');
  const [trackingId, setTrackingId] = useState('');
  const [receiptUrl, setReceiptUrl] = useState('');
  const wsRef = useRef(null);
  const timeoutRef = useRef(null);

  const clearExistingTimers = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  };

  const cleanupSocket = () => {
    if (wsRef.current) {
      try {
        wsRef.current.close();
      } catch (_) {}
      wsRef.current = null;
    }
  };

  useEffect(() => {
    if (isOpen) {
      setSessionState('IDLE');
      setProgress(0);
      setStatusMessage('Ready to launch Agentic RPA Co-Pilot on mock government portal.');
      setScreenshot(null);
      setTrackingId('');
      setReceiptUrl('');
      setUserCaptcha('');
      setUserOtp('');
    }
    return () => {
      clearExistingTimers();
      cleanupSocket();
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const startAutomation = () => {
    clearExistingTimers();
    cleanupSocket();

    setSessionState('RUNNING');
    setProgress(10);
    setStatusMessage('Connecting to Playwright execution runner...');

    // Safety timeout: abort and show actionable error if no runner response within 15 seconds
    timeoutRef.current = setTimeout(() => {
      cleanupSocket();
      setSessionState('ERROR');
      setStatusMessage('Connection timed out waiting for Playwright runner response. Ensure backend is running on port 8000.');
    }, 15000);

    const sessionId = 'session_' + Math.random().toString(36).substring(2, 9);

    const ws = api.createRPAWebSocket(
      sessionId,
      (data) => {
        // Defensive parsing for string or object payload
        let evt = data;
        if (typeof data === 'string') {
          try {
            evt = JSON.parse(data);
          } catch (e) {
            evt = { type: 'ERROR', message: data };
          }
        }

        // Active response received: clear the connection timeout
        clearExistingTimers();

        if (evt.type === 'PROGRESS') {
          setSessionState('RUNNING');
          setCurrentStep(evt.step || '');
          setProgress(evt.progress || 10);
          setStatusMessage(evt.message || 'Executing automation step...');
        } else if (evt.type === 'AWAITING_INPUT') {
          setSessionState('PAUSED');
          setCurrentStep(evt.step || 'AWAITING_INPUT');
          setProgress(evt.progress || 75);
          setStatusMessage(evt.message || 'Paused awaiting human OTP and CAPTCHA entry.');
          setScreenshot(evt.screenshot_base64 || null);
          setCaptchaHint(evt.captcha_hint || 'MHA782');
          setOtpHint(evt.otp_hint || '491820');
          setUserCaptcha(evt.captcha_hint || '');
          setUserOtp(evt.otp_hint || '');
        } else if (evt.type === 'COMPLETED') {
          setSessionState('COMPLETED');
          setProgress(100);
          setStatusMessage(evt.message || 'Application submitted successfully.');
          setTrackingId(evt.tracking_id || '');
          setReceiptUrl(evt.receipt_url || '');
        } else if (evt.type === 'ERROR') {
          setSessionState('ERROR');
          setStatusMessage(evt.message || 'Automation runner encountered an error.');
        }
      },
      (error) => {
        clearExistingTimers();
        setSessionState('ERROR');
        setStatusMessage('WebSocket connection error. Unable to communicate with the Playwright execution runner.');
      },
      (closeEvent) => {
        clearExistingTimers();
        // If closed while running or paused without completion
        setSessionState((prev) => {
          if (prev === 'RUNNING' || prev === 'PAUSED') {
            setStatusMessage('Connection to Playwright runner was terminated unexpectedly.');
            return 'ERROR';
          }
          return prev;
        });
      }
    );

    ws.onopen = () => {
      try {
        ws.send(JSON.stringify({
          action: 'START_SUBMISSION',
          portal_key: scheme?.dom_mapping_key === 'pmkisan_registration' ? 'pmkisan' : 'mahadbt',
          citizen_data: {
            full_name: citizen?.full_name || 'Ramesh Shamrao Patil',
            annual_income: citizen?.annual_income || 180000,
            district: citizen?.district || 'Kolhapur'
          }
        }));
      } catch (e) {
        clearExistingTimers();
        setSessionState('ERROR');
        setStatusMessage('Failed to send submission request to runner.');
      }
    };

    wsRef.current = ws;
  };

  const submitOtpAndCaptcha = () => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      setSessionState('ERROR');
      setStatusMessage('WebSocket connection lost before OTP could be submitted.');
      return;
    }
    setSessionState('RUNNING');
    setStatusMessage('Submitting verified human credentials to mock portal...');

    wsRef.current.send(JSON.stringify({
      action: 'SUBMIT_OTP_CAPTCHA',
      otp: userOtp,
      captcha: userCaptcha
    }));
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-2xl bg-white rounded-2xl shadow-2xl overflow-hidden border border-slate-200">
        {/* Modal Header */}
        <div className="bg-govblue-800 text-white p-4 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="h-6 w-6 text-govorange-500" />
            <div>
              <h3 className="text-base font-bold">Agentic RPA Co-Pilot & Mock Portal Automation</h3>
              <p className="text-xs text-blue-200">
                Target: {scheme?.scheme_name || 'MahaDBT Post-Matric Scholarship'} &bull; [DEMO SIMULATION]
              </p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-white/10 rounded-lg text-blue-200 hover:text-white">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-slate-100 h-2">
          <div
            className={`h-full transition-all duration-500 ${
              sessionState === 'COMPLETED'
                ? 'bg-emerald-500'
                : sessionState === 'ERROR'
                ? 'bg-rose-500'
                : 'bg-govblue-600'
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>

        <div className="p-6 space-y-6">
          {/* Status Banner */}
          <div className={`p-4 rounded-xl flex items-center gap-3 text-sm font-medium ${
            sessionState === 'COMPLETED'
              ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
              : sessionState === 'PAUSED'
              ? 'bg-amber-50 text-amber-800 border border-amber-300'
              : sessionState === 'ERROR'
              ? 'bg-rose-50 text-rose-800 border border-rose-300'
              : 'bg-blue-50 text-blue-800 border border-blue-200'
          }`}>
            {sessionState === 'RUNNING' && <Loader2 className="h-5 w-5 animate-spin text-blue-600 shrink-0" />}
            {sessionState === 'PAUSED' && <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0" />}
            {sessionState === 'COMPLETED' && <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0" />}
            {sessionState === 'ERROR' && <AlertTriangle className="h-5 w-5 text-rose-600 shrink-0" />}
            <div>
              <div className="font-bold">{statusMessage}</div>
              <div className="text-xs opacity-80 mt-0.5">Step: {currentStep || 'INITIALIZATION'} &bull; Progress: {progress}%</div>
            </div>
          </div>

          {/* Screenshot Streaming Canvas */}
          {screenshot && (
            <div className="rounded-xl overflow-hidden border border-slate-300 bg-slate-900 shadow-inner">
              <div className="bg-slate-800 px-3 py-1.5 text-xs text-slate-300 flex items-center justify-between">
                <span>Playwright Headless Browser Stream</span>
                <span className="text-govorange-500 font-mono text-[10px]">LIVE FEED</span>
              </div>
              <img src={screenshot} alt="Playwright Screen" className="w-full h-auto object-contain" />
            </div>
          )}

          {/* Human-in-the-Loop OTP & CAPTCHA Form */}
          {sessionState === 'PAUSED' && (
            <div className="p-4 bg-amber-50/60 rounded-xl border border-amber-300 space-y-4">
              <div className="flex items-center gap-2 text-amber-900 font-bold text-sm">
                <ShieldCheck className="h-4 w-4 text-amber-600" />
                <span>Human-in-the-Loop Verification Required</span>
              </div>
              <p className="text-xs text-slate-600">
                Ethical RPA constraint: The automated runner has paused at the portal verification screen. Please enter the OTP and CAPTCHA to confirm submission.
              </p>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Security CAPTCHA (Hint: <span className="font-mono text-blue-600">{captchaHint}</span>):
                  </label>
                  <input
                    type="text"
                    value={userCaptcha}
                    onChange={(e) => setUserCaptcha(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm font-mono uppercase font-bold"
                    placeholder="Enter CAPTCHA"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    SMS OTP (Hint: <span className="font-mono text-emerald-600">{otpHint}</span>):
                  </label>
                  <input
                    type="text"
                    value={userOtp}
                    onChange={(e) => setUserOtp(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm font-mono font-bold"
                    placeholder="6-digit OTP"
                  />
                </div>
              </div>

              <button
                onClick={submitOtpAndCaptcha}
                className="w-full py-2.5 bg-govorange-500 hover:bg-govorange-600 text-white rounded-lg font-bold text-sm shadow transition-all flex items-center justify-center gap-2"
              >
                <span>Authorize & Resume Submission</span>
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          )}

          {/* Completed State */}
          {sessionState === 'COMPLETED' && (
            <div className="text-center p-6 bg-emerald-50/50 rounded-xl border border-emerald-200 space-y-4">
              <CheckCircle2 className="h-12 w-12 text-emerald-600 mx-auto" />
              <div>
                <h4 className="text-base font-bold text-slate-900">Application Submitted to Government Portal!</h4>
                <p className="text-xs text-slate-600 mt-1">Official Portal Tracking Identifier:</p>
                <div className="text-2xl font-mono font-extrabold text-govblue-800 mt-1 tracking-wider">
                  {trackingId}
                </div>
              </div>

              <div className="flex justify-center gap-3 pt-2">
                <a
                  href={receiptUrl.startsWith('http') ? receiptUrl : `http://localhost:8000${receiptUrl}`}
                  target="_blank"
                  rel="noreferrer"
                  className="px-4 py-2 bg-govblue-800 hover:bg-govblue-900 text-white rounded-lg text-xs font-bold flex items-center gap-2 shadow hover:bg-opacity-95 transition-all"
                >
                  <Download className="h-4 w-4" />
                  <span>Download Verifiable Receipt PDF</span>
                </a>
              </div>
            </div>
          )}

          {/* Action Trigger Buttons */}
          {sessionState === 'IDLE' && (
            <div className="text-center py-4">
              <button
                onClick={startAutomation}
                className="px-6 py-3 bg-govblue-800 hover:bg-govblue-900 text-white rounded-xl font-bold text-sm shadow-md transition-all flex items-center gap-2 mx-auto"
              >
                <Play className="h-4 w-4 fill-white" />
                <span>Start Automated Form-Filling Co-Pilot</span>
              </button>
              <p className="text-xs text-slate-500 mt-3">
                Pre-conditions: Document compressed to 20KB-50KB bracket &bull; Target: Self-hosted Mock Portal
              </p>
            </div>
          )}

          {sessionState === 'ERROR' && (
            <div className="text-center py-4 space-y-3">
              <button
                onClick={startAutomation}
                className="px-5 py-2.5 bg-govblue-800 hover:bg-govblue-900 text-white rounded-xl font-bold text-sm shadow-md transition-all flex items-center gap-2 mx-auto"
              >
                <RotateCcw className="h-4 w-4" />
                <span>Retry Automation</span>
              </button>
              <p className="text-xs text-slate-500">
                You can retry the automation session or close this modal.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
