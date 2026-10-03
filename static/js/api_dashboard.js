document.addEventListener('DOMContentLoaded', () => {
  function initToolbar(containerSelector, apiUrl) {
    const container = document.querySelector(containerSelector);
    if (!container) return;
    const searchInput = container.querySelector('.api-search');
    const viewJsonBtn = container.querySelector('.api-view-json');
    const exportBtn = container.querySelector('.api-export-json');
    const jsonPre = container.querySelector('.api-json-pre');
    const table = container.querySelector('.data-table');

    let cachedJson = null;

    async function fetchJson() {
      try {
        const res = await fetch(apiUrl);
        if (!res.ok) throw new Error('Network error');
        const data = await res.json();
        cachedJson = data;
        jsonPre.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        jsonPre.textContent = 'Error loading JSON: ' + err.message;
      }
    }

    if (viewJsonBtn) {
      viewJsonBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        if (!cachedJson) await fetchJson();
        jsonPre.classList.toggle('visible');
        if (jsonPre.classList.contains('visible')) viewJsonBtn.textContent = 'Hide JSON';
        else viewJsonBtn.textContent = 'View JSON';
      });
    }

    if (exportBtn) {
      exportBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        if (!cachedJson) await fetchJson();
        const blob = new Blob([JSON.stringify(cachedJson, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = apiUrl.replace(/\W+/g, '_').replace(/^_+|_+$/g, '') + '.json';
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
      });
    }

    if (searchInput && table) {
      searchInput.addEventListener('input', () => {
        const q = searchInput.value.toLowerCase().trim();
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach((r) => {
          const text = r.textContent.toLowerCase();
          r.style.display = text.includes(q) ? '' : 'none';
        });
      });
    }
  }

  // Initialize for each known container if present
  initToolbar('#api-patients-container', '/api/patients/');
  initToolbar('#api-doctors-container', '/api/doctors/');
  initToolbar('#api-appointments-container', '/api/appointments/');
});
