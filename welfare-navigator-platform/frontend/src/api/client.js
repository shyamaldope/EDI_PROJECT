const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const WS_BASE = API_BASE.replace(/^http/, 'ws');

// --- IndexedDB Offline Storage Helper (for CSC Kiosk Mode) ---
const DB_NAME = 'WelfareKioskOfflineDB';
const STORE_NAME = 'offline_queue';

function openKioskDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1);
    request.onupgradeneeded = (e) => {
      const db = e.target.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'id', autoIncrement: true });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export const offlineQueue = {
  async enqueue(action, payload) {
    try {
      const db = await openKioskDB();
      const tx = db.transaction(STORE_NAME, 'readwrite');
      const store = tx.objectStore(STORE_NAME);
      const record = { action, payload, queuedAt: new Date().toISOString() };
      store.add(record);
      return new Promise((res) => { tx.oncomplete = () => res(true); });
    } catch (err) {
      console.warn('IndexedDB not available, skipping queue:', err);
      return false;
    }
  },

  async getAll() {
    try {
      const db = await openKioskDB();
      const tx = db.transaction(STORE_NAME, 'readonly');
      const store = tx.objectStore(STORE_NAME);
      const req = store.getAll();
      return new Promise((res) => { req.onsuccess = () => res(req.result); });
    } catch {
      return [];
    }
  },

  async clear() {
    try {
      const db = await openKioskDB();
      const tx = db.transaction(STORE_NAME, 'readwrite');
      tx.objectStore(STORE_NAME).clear();
    } catch {}
  }
};

// --- HTTP Client ---
async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  try {
    const res = await fetch(url, options);
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `HTTP Error ${res.status}`);
    }
    return await res.json();
  } catch (error) {
    console.error(`API Call failed [${endpoint}]:`, error);
    throw error;
  }
}

export const api = {
  // Citizens & DPDP Act Vault
  getCitizens: () => request('/api/v1/citizens'),
  getCitizen: (id) => request(`/api/v1/citizens/${id}`),
  saveCitizen: (data) => request('/api/v1/citizens', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  }),
  purgeVault: (id) => request(`/api/v1/citizens/${id}/purge`, { method: 'DELETE' }),

  // Schemes & Rule Engine
  getSchemes: (status) => request(status ? `/api/v1/schemes?status=${status}` : '/api/v1/schemes'),
  getCitizenSchemes: (citizenId) => request(`/api/v1/citizens/${citizenId}/schemes`),
  getHouseholdSchemes: (householdId) => request(`/api/v1/households/${householdId}/schemes`),

  // Vernacular Voice & Chat
  processVoiceOrText: (text, language = 'mr') => request('/api/v1/voice/process', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, language })
  }),
  getNextQuestion: (currentProfile) => request('/api/v1/voice/next-question', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(currentProfile)
  }),

  // Document Auditor & Compressor
  auditDocument: (citizenId, docType, file) => {
    const fd = new FormData();
    fd.append('citizen_id', citizenId);
    fd.append('doc_type', docType);
    fd.append('file', file);
    return request('/api/v1/documents/audit', { method: 'POST', body: fd });
  },
  compressDocument: (file) => {
    const fd = new FormData();
    fd.append('file', file);
    return request('/api/v1/documents/compress', { method: 'POST', body: fd });
  },

  // Admin Ingestion & HITL Approval
  getIncomingGRs: () => request('/api/v1/admin/gr-files'),
  ingestGR: (formData) => request('/api/v1/admin/ingest-gr', { method: 'POST', body: formData }),
  diffSchemes: (oldAst, newAst) => request('/api/v1/admin/schemes/diff', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ old_ast: oldAst, new_ast: newAst })
  }),
  approveScheme: (schemeId) => request(`/api/v1/admin/schemes/${schemeId}/approve`, { method: 'POST' }),

  // SLA Tracker & RTS Appeals
  getApplications: () => request('/api/v1/tracker/applications'),
  draftGrievance: (applicationId) => request('/api/v1/tracker/grievance/draft', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ application_id: applicationId })
  }),

  // Policy Twin Simulator & Goal-Seek
  simulateWhatIf: (payload) => request('/api/v1/policy/simulate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  }),
  goalSeek: (payload) => request('/api/v1/policy/goal-seek', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  }),

  // Outbox
  getOutbox: () => request('/api/v1/outbox'),

  // RPA Playwright WebSocket
  createRPAWebSocket: (sessionId, onEvent, onError, onClose) => {
    const ws = new WebSocket(`${WS_BASE}/ws/rpa/copilot/${sessionId}`);
    ws.onmessage = (msg) => {
      try {
        const data = typeof msg.data === 'string' ? JSON.parse(msg.data) : msg.data;
        onEvent(data);
      } catch (err) {
        onEvent({ type: 'ERROR', message: 'Failed to parse incoming runner event', raw: msg.data });
      }
    };
    if (onError) {
      ws.onerror = (err) => {
        onError(err);
      };
    }
    if (onClose) {
      ws.onclose = (evt) => {
        onClose(evt);
      };
    }
    return ws;
  }
};
