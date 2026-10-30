/* Trang Lịch sử: các lần phân loại (mới nhất trước), xóa từng mục hoặc toàn bộ. Người phụ trách: Nghi */

// HTML một dòng của bảng. item là một mục của GET /api/history
function historyRowHtml(item) {
  const fileName = escapeHtml(item.original_name);     // tên do người dùng đặt: phải escape

  let badge = '';
  let barClass = 'conf-fill';
  if (item.uncertain) {                                 // dưới ngưỡng của chính lần phân loại đó
    badge = '<span class="badge-unsure">Chưa chắc chắn</span>';
    barClass = 'conf-fill low';
  }

  return `
    <tr>
      <td style="width:88px">
        <div class="history-thumb stripe" style="--h:${item.flower.hue}">
          <img class="cover" src="${item.image_url}" alt="" loading="lazy">
        </div>
      </td>
      <td>
        <div class="d-flex align-items-center flex-wrap" style="gap:10px">
          <span class="history-name">${item.flower.name_vi}</span>
          ${badge}
        </div>
        <div class="history-file" title="${fileName}">${fileName}</div>
      </td>
      <td style="width:200px">
        <div class="d-flex align-items-center" style="gap:10px">
          <div class="conf-track"><div class="${barClass}" style="width:${item.confidence * 100}%"></div></div>
          <span class="conf-pct mono" style="font-size:13px">${formatPercent(item.confidence, 1)}</span>
        </div>
      </td>
      <td class="history-time">${formatDateTime(item.created_at)}</td>
      <td class="text-end" style="width:120px">
        <div class="d-inline-flex gap-2">
          <a class="btn-view-one" href="/history/${item.id}" title="Xem chi tiết">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="M13 6l6 6-6 6"/></svg>
          </a>
          <button type="button" class="btn-del-one" title="Xóa" onclick="deleteOne(${item.id})">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7h16"/><path d="M9 7V4h6v3"/><path d="M6 7l1 13h10l1-13"/></svg>
          </button>
        </div>
      </td>
    </tr>`;
}

async function loadHistory() {
  hide('loadError');
  try {
    const data = await callApi('/api/history');
    const items = data.items;

    let html = '';
    for (const item of items) {
      html += historyRowHtml(item);
    }
    $('historyBody').innerHTML = html;
    $('countLabel').textContent = formatNumber(items.length) + ' lần phân loại';

    // Có mục thì hiện bảng + nút "Xóa toàn bộ"; không có thì hiện khối "Chưa có lịch sử"
    if (items.length > 0) {
      show('historyWrap');
      show('btnClearAll');
      hide('emptyState');
    } else {
      hide('historyWrap');
      hide('btnClearAll');
      show('emptyState');
    }
  } catch (error) {
    $('countLabel').textContent = 'Lịch sử phân loại';
    showLoadError('Không tải được lịch sử. ' + error.message);
  }
}

// Nút thùng rác ở mỗi dòng gọi hàm này (onclick trong historyRowHtml)
function deleteOne(id) {
  askConfirm('Xóa mục này?', 'Kết quả này và ảnh đã tải lên sẽ bị xóa. Không thể hoàn tác.', async function () {
    try {
      await callApi('/api/history/' + id, 'DELETE');
    } catch (error) {
      showLoadError('Chưa xóa được. ' + error.message);
      return;
    }
    loadHistory();                                    // tải lại bảng cho khớp với CSDL
  });
}

function deleteAll() {
  askConfirm('Xóa toàn bộ lịch sử?', 'Mọi lần phân loại và ảnh đã tải lên sẽ bị xóa. Không thể hoàn tác.', async function () {
    try {
      await callApi('/api/history', 'DELETE');
    } catch (error) {
      showLoadError('Chưa xóa được. ' + error.message);
      return;
    }
    loadHistory();
  });
}

$('btnClearAll').onclick = deleteAll;
loadHistory();
