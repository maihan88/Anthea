function $(id) {
  return document.getElementById(id);
}

function show(id) {
  $(id).classList.remove('d-none');
}

function hide(id) {
  $(id).classList.add('d-none');
}

async function callApi(url, method = 'GET', body = null) {
  let response;
  try {
    response = await fetch(url, { method: method, body: body });
  } catch (error) {
    throw new Error('Không kết nối được tới máy chủ.');
  }

  let data;
  try {
    data = await response.json();
  } catch (error) {
    data = { error: 'Máy chủ gặp lỗi, vui lòng thử lại.' };
  }

  if (!response.ok) {
    const error = new Error(data.error);
    error.status = response.status;
    throw error;
  }
  return data;
}

function showLoadError(message) {
  $('loadErrorText').textContent = message;
  show('loadError');
}

function formatPercent(value, digits = 0) {
  return (value * 100).toFixed(digits).replace('.', ',') + '%';
}

function formatNumber(value) {
  return value.toLocaleString('vi-VN');
}

function formatSize(bytes) {
  const MB = 1024 * 1024;
  if (bytes >= MB) {
    return (bytes / MB).toFixed(1).replace('.', ',') + ' MB';
  }
  return Math.round(bytes / 1024) + ' KB';
}

function formatDateTime(isoText) {
  const d = new Date(isoText);
  const day = String(d.getDate()).padStart(2, '0');
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const hour = String(d.getHours()).padStart(2, '0');
  const minute = String(d.getMinutes()).padStart(2, '0');
  return `${day}/${month}/${d.getFullYear()} ${hour}:${minute}`;
}

function escapeHtml(text) {
  return text.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
}

function top3Html(top, uncertain) {
  let html = '';
  for (let i = 0; i < top.length; i++) {
    const flower = top[i];
    const width = flower.confidence * 100;

    let barClass = 'bar-fill';
    let nameStyle = '';
    if (i === 0) {
      barClass = 'bar-fill main';
      nameStyle = 'font-weight:600';
      if (uncertain) barClass = 'bar-fill main low';
    }

    html += `
      <div class="top3-row">
        <span class="top3-rank">0${i + 1}</span>
        <span style="${nameStyle}">${flower.name_vi}</span>
        <div class="bar-track"><div class="${barClass}" style="width:${width}%"></div></div>
        <span class="top3-pct">${formatPercent(flower.confidence)}</span>
      </div>`;
  }
  return html;
}

function askConfirm(title, text, onConfirm) {
  const modal = bootstrap.Modal.getOrCreateInstance($('confirmModal'));
  $('confirmTitle').textContent = title;
  $('confirmText').textContent = text;
  $('btnConfirm').onclick = function () {
    modal.hide();
    onConfirm();
  };
  modal.show();
}
