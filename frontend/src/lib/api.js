const API_BASE = 'http://127.0.0.1:8000';

async function request(path, options = {}) {
  const headers = options.body instanceof FormData
    ? { ...(options.headers || {}) }
    : {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
      };

  // 默认 5 分钟超时（爬虫需要较长时间）
  const timeout = options.timeout || 300000;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
      signal: controller.signal,
    });

    if (!response.ok) {
      let message = 'Request failed';
      try {
        const data = await response.json();
        message = data.detail || message;
      } catch {
        message = `${message}: ${response.status}`;
      }
      throw new Error(message);
    }

    return response.status === 204 ? null : response.json();
  } catch (err) {
    if (err.name === 'AbortError') {
      throw new Error('请求超时，请稍后重试');
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

export function fetchOverview() {
  return request('/overview');
}

export function saveResumeProfile(payload) {
  return request('/resume-profile', {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export function uploadResume(file) {
  const formData = new FormData();
  formData.append('file', file);
  return request('/resume-profile/upload', {
    method: 'POST',
    body: formData,
  });
}

export function generateBeautifiedResume() {
  return request('/resume-profile/generate/beautified', { method: 'POST' });
}

export function generateMarketResume() {
  return request('/resume-profile/generate/market', { method: 'POST' });
}

export function importJob(payload) {
  return request('/jobs/import', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function fetchUrl(url) {
  return request('/jobs/fetch-url', {
    method: 'POST',
    body: JSON.stringify({ url }),
  });
}

export function prepareApplication(jobId, matchMode = 'local') {
  return request(`/jobs/${jobId}/prepare?match_mode=${matchMode}`, {
    method: 'POST',
  });
}

export function confirmApplication(applicationId) {
  return request(`/applications/${applicationId}/confirm`, {
    method: 'POST',
  });
}

export function refreshRecommendations() {
  return request('/recommendations/refresh', {
    method: 'POST',
  });
}

export function importRecommendation(recommendationId) {
  return request(`/recommendations/${recommendationId}/import`, {
    method: 'POST',
  });
}

export function dismissRecommendation(recommendationId) {
  return request(`/recommendations/${recommendationId}/dismiss`, {
    method: 'POST',
  });
}

export function clearRecommendations() {
  return request('/recommendations/clear', {
    method: 'POST',
  });
}

export function clearJobs() {
  return request('/jobs/clear', {
    method: 'POST',
  });
}

export function fetchProviders() {
  return request('/settings/providers');
}

export function fetchPreferences() {
  return request('/preferences');
}

export function savePreferences(payload) {
  return request('/preferences', {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export function fetchSettings() {
  return request('/settings');
}

export function saveSettings(payload) {
  return request('/settings', {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export function testApiConnection(provider, apiBaseUrl, apiKey, model) {
  return request('/settings/test', {
    method: 'POST',
    body: JSON.stringify({ provider, api_base_url: apiBaseUrl, api_key: apiKey, model }),
  });
}
