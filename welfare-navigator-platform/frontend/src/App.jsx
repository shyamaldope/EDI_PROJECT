import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import OutboxDrawer from './components/OutboxDrawer';
import CitizenWorkspace from './pages/CitizenWorkspace';
import DocumentVault from './pages/DocumentVault';
import ApplicationTracker from './pages/ApplicationTracker';
import AdminIngestion from './pages/AdminIngestion';
import AuthorityDashboard from './pages/AuthorityDashboard';
import LiveCoPilotModal from './pages/LiveCoPilotModal';
import { api, offlineQueue } from './api/client';
import { User, FileText, Clock, WifiOff, RefreshCw } from 'lucide-react';

export default function App() {
  const [role, setRole] = useState('CITIZEN'); // CITIZEN, KIOSK, ADMIN, COLLECTOR
  const [citizenSubTab, setCitizenSubTab] = useState('WORKSPACE'); // WORKSPACE, VAULT, TRACKER
  const [language, setLanguage] = useState('mr');
  const [isOutboxOpen, setIsOutboxOpen] = useState(false);
  const [outboxCount, setOutboxCount] = useState(0);

  const [citizens, setCitizens] = useState([]);
  const [activeCitizen, setActiveCitizen] = useState(null);

  // RPA Modal state
  const [isRpaOpen, setIsRpaOpen] = useState(false);
  const [rpaScheme, setRpaScheme] = useState(null);

  // Offline queue indicator for Kiosk mode
  const [offlineItems, setOfflineItems] = useState([]);

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      const cList = await api.getCitizens();
      setCitizens(cList);
      if (cList.length > 0) {
        // Default to Ramesh Patil
        const ramesh = cList.find((c) => c.full_name === 'Ramesh Shamrao Patil') || cList[0];
        setActiveCitizen(ramesh);
      }
      const outbox = await api.getOutbox();
      setOutboxCount(outbox.length);

      const queued = await offlineQueue.getAll();
      setOfflineItems(queued);
    } catch (err) {
      console.warn('Backend connection issue or running offline mode:', err);
    }
  };

  const handleLaunchRpa = (scheme) => {
    setRpaScheme(scheme);
    setIsRpaOpen(true);
  };

  return (
    <div className={`min-h-screen ${role === 'KIOSK' ? 'bg-amber-50/40 text-lg' : 'bg-slate-50'}`}>
      <Navbar
        currentRole={role}
        setRole={setRole}
        language={language}
        setLanguage={setLanguage}
        outboxCount={outboxCount}
        toggleOutbox={() => setIsOutboxOpen(!isOutboxOpen)}
      />

      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* CSC KIOSK MODE BANNER */}
        {role === 'KIOSK' && (
          <div className="mb-6 p-4 bg-amber-500 text-slate-900 rounded-2xl shadow-sm flex items-center justify-between border border-amber-600 font-bold">
            <div className="flex items-center gap-2 text-sm">
              <span className="bg-slate-900 text-amber-300 text-xs px-2.5 py-1 rounded-lg uppercase">
                CSC Gramin Kiosk Mode
              </span>
              <span>High-contrast interface enabled &bull; IndexedDB Local Offline Sync Active</span>
            </div>
            {offlineItems.length > 0 && (
              <span className="text-xs bg-slate-900 text-white px-3 py-1 rounded-full flex items-center gap-1.5">
                <WifiOff className="h-3.5 w-3.5 text-amber-400" />
                {offlineItems.length} queued offline actions
              </span>
            )}
          </div>
        )}

        {/* CITIZEN & KIOSK PERSONA TABS */}
        {(role === 'CITIZEN' || role === 'KIOSK') && (
          <div className="space-y-6">
            {/* Sub-tabs */}
            <div className="flex space-x-2 bg-white p-1.5 rounded-2xl border border-slate-200 shadow-sm w-fit">
              <button
                onClick={() => setCitizenSubTab('WORKSPACE')}
                className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                  citizenSubTab === 'WORKSPACE'
                    ? 'bg-govblue-800 text-white shadow-sm'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }`}
              >
                <User className="h-4 w-4" />
                <span>Eligibility & Voice Discovery</span>
              </button>
              <button
                onClick={() => setCitizenSubTab('VAULT')}
                className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                  citizenSubTab === 'VAULT'
                    ? 'bg-govblue-800 text-white shadow-sm'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }`}
              >
                <FileText className="h-4 w-4" />
                <span>Document Vault & Compressor</span>
              </button>
              <button
                onClick={() => setCitizenSubTab('TRACKER')}
                className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                  citizenSubTab === 'TRACKER'
                    ? 'bg-govblue-800 text-white shadow-sm'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }`}
              >
                <Clock className="h-4 w-4" />
                <span>RTS Act SLA Tracker</span>
              </button>
            </div>

            {citizenSubTab === 'WORKSPACE' && (
              <CitizenWorkspace
                citizen={activeCitizen}
                citizens={citizens}
                onSelectCitizen={setActiveCitizen}
                onLaunchRpa={handleLaunchRpa}
                language={language}
              />
            )}

            {citizenSubTab === 'VAULT' && (
              <DocumentVault citizen={activeCitizen} />
            )}

            {citizenSubTab === 'TRACKER' && (
              <ApplicationTracker citizen={activeCitizen} />
            )}
          </div>
        )}

        {/* SCHEME ADMIN (HITL) */}
        {role === 'ADMIN' && <AdminIngestion />}

        {/* DISTRICT COLLECTOR (POLICY TWIN) */}
        {role === 'COLLECTOR' && <AuthorityDashboard />}
      </main>

      {/* Outbox Slide-Over Drawer */}
      <OutboxDrawer
        isOpen={isOutboxOpen}
        onClose={() => setIsOutboxOpen(false)}
      />

      {/* Live RPA Co-Pilot Modal */}
      <LiveCoPilotModal
        isOpen={isRpaOpen}
        onClose={() => setIsRpaOpen(false)}
        citizen={activeCitizen}
        scheme={rpaScheme}
      />
    </div>
  );
}
