// The Aiges Engine - Central API Client

const BASE_URL = ''; // Relative path leverages Vite dev proxy; falls back to window.location.origin

export const getToken = () => localStorage.getItem('aiges_token') || localStorage.getItem('vishwas_token');
export const setToken = (token) => {
  if (token) {
    localStorage.setItem('aiges_token', token);
  } else {
    localStorage.removeItem('aiges_token');
    localStorage.removeItem('vishwas_token');
  }
};

export async function apiFetch(endpoint, options = {}) {
  const token = getToken();
  const headers = {
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Set default JSON Content-Type if not sending FormData or form-urlencoded
  if (!headers['Content-Type'] && !(options.body instanceof FormData) && !(options.body instanceof URLSearchParams)) {
    headers['Content-Type'] = 'application/json';
  }

  const url = `${BASE_URL}${endpoint}`;
  let response;

  try {
    response = await fetch(url, { ...options, headers });
  } catch (err) {
    throw new Error('Network error: Unable to reach backend server.');
  }

  // Global 401 unauthorized handling
  if (response.status === 401) {
    setToken(null);
    window.dispatchEvent(new CustomEvent('auth:logout'));
    let detail = 'Session expired or invalid credentials.';
    try {
      const errorJson = await response.json();
      detail = errorJson.detail || detail;
    } catch (_) {}
    throw new Error(detail);
  }

  // Parse response
  let data;
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    data = await response.json();
  } else {
    data = await response.text();
  }

  if (!response.ok) {
    const errorMsg = data?.detail || (typeof data === 'string' ? data : 'API request failed');
    throw new Error(errorMsg);
  }

  return data;
}

export const authApi = {
  signup: (email, password) =>
    apiFetch('/api/auth/signup', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  login: async (email, password) => {
    const params = new URLSearchParams();
    params.append('username', email);
    params.append('password', password);
    const data = await apiFetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: params,
    });
    if (data.access_token) {
      setToken(data.access_token);
    }
    return data;
  },

  getMe: () => apiFetch('/api/auth/me'),

  logout: () => {
    setToken(null);
    window.dispatchEvent(new CustomEvent('auth:logout'));
  }
};

export const metaApi = {
  getMeta: () => apiFetch('/api/meta'),
};

export const auditApi = {
  createAudit: (auditData) =>
    apiFetch('/api/audits', {
      method: 'POST',
      body: JSON.stringify(auditData),
    }),

  auditLink: (linkData) =>
    apiFetch('/api/audits/link', {
      method: 'POST',
      body: JSON.stringify(linkData),
    }),

  auditAccount: (accountData) =>
    apiFetch('/api/audits/account', {
      method: 'POST',
      body: JSON.stringify(accountData),
    }),

  listAudits: () => apiFetch('/api/audits'),

  getAudit: (id) => apiFetch(`/api/audits/${id}`),
};

export const healthApi = {
  getHealth: () => apiFetch('/api/health'),
};

export const mentionsApi = {
  ingestMentions: (payload) =>
    apiFetch('/api/mentions/ingest', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getMentions: (params = {}) => {
    const query = new URLSearchParams();
    if (params.sentiment) query.append('sentiment', params.sentiment);
    if (params.language) query.append('language', params.language);
    if (params.flagged_only) query.append('flagged_only', 'true');
    if (params.post_id) query.append('post_id', params.post_id);
    if (params.limit) query.append('limit', params.limit);
    if (params.skip) query.append('skip', params.skip);
    const qs = query.toString();
    return apiFetch(`/api/mentions${qs ? `?${qs}` : ''}`);
  },

  getSummary: () => apiFetch('/api/mentions/summary'),

  cleanupMentions: (daysRetention = 90) =>
    apiFetch('/api/mentions/cleanup', {
      method: 'POST',
      body: JSON.stringify({ days_retention: daysRetention }),
    }),

  draftReply: (mentionId, payload = {}) =>
    apiFetch(`/api/mentions/${mentionId}/draft-reply`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  approveReply: (mentionId, payload = {}) =>
    apiFetch(`/api/mentions/${mentionId}/approve`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  listMonitoredResources: () => apiFetch('/api/mentions/monitor'),

  addMonitoredResource: (payload) =>
    apiFetch('/api/mentions/monitor', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  deleteMonitoredResource: (resourceId) =>
    apiFetch(`/api/mentions/monitor/${resourceId}`, {
      method: 'DELETE',
    }),
};

export const adAllocationApi = {
  listCampaigns: () => apiFetch('/api/campaigns'),

  getCampaign: (id) => apiFetch(`/api/campaigns/${id}`),

  createCampaign: (payload) =>
    apiFetch('/api/campaigns', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  addChannel: (campaignId, payload) =>
    apiFetch(`/api/campaigns/${campaignId}/channels`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  generateRecommendation: (campaignId) =>
    apiFetch(`/api/campaigns/${campaignId}/recommend`, {
      method: 'POST',
    }),

  approveRecommendation: (recommendationId, payload = {}) =>
    apiFetch(`/api/recommendations/${recommendationId}/approve`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};
