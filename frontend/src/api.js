const API_BASE = import.meta.env.PROD ? '' : 'http://localhost:8000';

export const api = {
  // Dashboard & Analytics
  async getDashboard() {
    const res = await fetch(`${API_BASE}/data/dashboard`);
    return res.json();
  },

  async getAnalyticsOverview() {
    const res = await fetch(`${API_BASE}/analytics/overview`);
    return res.json();
  },

  async getDriftDetection(windowDays = 90) {
    const res = await fetch(`${API_BASE}/analytics/drift-detection?window_days=${windowDays}`);
    return res.json();
  },

  async getSupplierPerformance() {
    const res = await fetch(`${API_BASE}/analytics/supplier-performance`);
    return res.json();
  },

  async getPeriodComparison(p1Start, p1End, p2Start, p2End) {
    let url = `${API_BASE}/analytics/period-comparison`;
    if (p1Start) {
      url += `?period1_start=${p1Start}&period1_end=${p1End}&period2_start=${p2Start}&period2_end=${p2End}`;
    }
    const res = await fetch(url);
    return res.json();
  },

  async getAnomalies(days = 30) {
    const res = await fetch(`${API_BASE}/analytics/anomalies?days=${days}`);
    return res.json();
  },

  async getYearlySummary() {
    const res = await fetch(`${API_BASE}/analytics/yearly-summary`);
    return res.json();
  },

  async getEquipmentAnalysis() {
    const res = await fetch(`${API_BASE}/analytics/equipment-analysis`);
    return res.json();
  },

  // Data
  async getBatches(limit = 50) {
    const res = await fetch(`${API_BASE}/data/batches?limit=${limit}`);
    return res.json();
  },

  async getTrends(parameter = 'hardness', days = 30) {
    const res = await fetch(`${API_BASE}/data/trends/${parameter}?days=${days}`);
    return res.json();
  },

  async getComplaints(status = null) {
    const url = status ? `${API_BASE}/data/complaints?status=${status}` : `${API_BASE}/data/complaints`;
    const res = await fetch(url);
    return res.json();
  },

  async getCapas(status = null) {
    const url = status ? `${API_BASE}/data/capas?status=${status}` : `${API_BASE}/data/capas`;
    const res = await fetch(url);
    return res.json();
  },

  // Chat
  async getConversations() {
    const res = await fetch(`${API_BASE}/chat/conversations`);
    return res.json();
  },

  async createConversation() {
    const res = await fetch(`${API_BASE}/chat/conversations`, { method: 'POST' });
    return res.json();
  },

  async deleteConversation(convId) {
    const res = await fetch(`${API_BASE}/chat/conversations/${convId}`, { method: 'DELETE' });
    return res.json();
  },

  async chat(convId, message) {
    const res = await fetch(`${API_BASE}/chat/${convId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });
    return res.json();
  },

  streamSummary(onChunk, onDone, onError) {
    const eventSource = new EventSource(`${API_BASE}/chat/summary/stream`);
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.done) {
        eventSource.close();
        onDone?.();
      } else if (data.error) {
        eventSource.close();
        onError?.(data.error);
      } else if (data.text) {
        onChunk(data.text);
      }
    };
    eventSource.onerror = () => {
      eventSource.close();
      onError?.('Connection error');
    };
    return eventSource;
  },

  async getReport(startDate = null, endDate = null, title = null, save = true) {
    let url = `${API_BASE}/chat/report?save=${save}`;
    if (startDate) url += `&start_date=${startDate}`;
    if (endDate) url += `&end_date=${endDate}`;
    if (title) url += `&title=${encodeURIComponent(title)}`;
    const res = await fetch(url);
    return res.json();
  },

  async getReportHistory(limit = 20) {
    const res = await fetch(`${API_BASE}/chat/reports/history?limit=${limit}`);
    return res.json();
  },

  async getSavedReport(reportId) {
    const res = await fetch(`${API_BASE}/chat/reports/${reportId}`);
    return res.json();
  },

  async deleteReport(reportId) {
    const res = await fetch(`${API_BASE}/chat/reports/${reportId}`, { method: 'DELETE' });
    return res.json();
  },

  async getChatHistory(convId) {
    const res = await fetch(`${API_BASE}/chat/${convId}/history`);
    return res.json();
  },

  async uploadFile(file, dataType) {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/data/upload?data_type=${dataType}`, {
      method: 'POST',
      body: formData
    });
    return res.json();
  },

  async getUploads() {
    const res = await fetch(`${API_BASE}/data/uploads`);
    return res.json();
  },

  // Data Generation Backoffice
  async getDataTypes() {
    const res = await fetch(`${API_BASE}/generate/data-types`);
    return res.json();
  },

  async previewMonthGeneration(year, month, batchesPerDay = 20, dataTypes = null) {
    const res = await fetch(`${API_BASE}/generate/month/preview`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        year,
        month,
        batches_per_day: batchesPerDay,
        data_types: dataTypes
      })
    });
    return res.json();
  },

  async downloadMonthData(year, month, batchesPerDay = 20, dataTypes = null) {
    const res = await fetch(`${API_BASE}/generate/month/download`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        year,
        month,
        batches_per_day: batchesPerDay,
        data_types: dataTypes
      })
    });
    return res.blob();
  },

  async downloadYearData(year, batchesPerDay = 20, dataTypes = null) {
    const res = await fetch(`${API_BASE}/generate/year/download`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        year,
        batches_per_day: batchesPerDay,
        data_types: dataTypes
      })
    });
    return res.blob();
  },

  async downloadCustomData(startDate, endDate, batchesPerDay = 20, dataTypes = null) {
    const res = await fetch(`${API_BASE}/generate/custom/download`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        start_date: startDate,
        end_date: endDate,
        batches_per_day: batchesPerDay,
        data_types: dataTypes
      })
    });
    return res.blob();
  },

  async downloadSingleDataType(dataType, year, month, batchesPerDay = 20) {
    const res = await fetch(
      `${API_BASE}/generate/single/${dataType}?year=${year}&month=${month}&batches_per_day=${batchesPerDay}`
    );
    return res.blob();
  },

  async getScenarios() {
    const res = await fetch(`${API_BASE}/generate/scenarios`);
    return res.json();
  },

  // APR Report Generation (Hierarchical System)
  async generateAPR(year, forceRegenerate = false) {
    const res = await fetch(`${API_BASE}/reports/apr/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ year, force_regenerate: forceRegenerate })
    });
    return res.json();
  },

  async getAPR(year) {
    const res = await fetch(`${API_BASE}/reports/apr/${year}`);
    if (!res.ok) return null;
    return res.json();
  },

  async downloadAPRPdf(year) {
    const res = await fetch(`${API_BASE}/reports/apr/${year}/pdf`);
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to download PDF');
    }
    return res.blob();
  },

  async getReportHierarchyStatus(year) {
    const res = await fetch(`${API_BASE}/reports/hierarchy/${year}`);
    return res.json();
  },

  async generateAllReports(year) {
    const res = await fetch(`${API_BASE}/reports/generate-all/${year}`, { method: 'POST' });
    return res.json();
  }
};
