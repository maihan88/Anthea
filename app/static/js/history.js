/* Trang Lịch sử: các lần phân loại (mới nhất trước), xóa từng mục hoặc toàn bộ. Người phụ trách: Nghi */

const $ = id => document.getElementById(id);
const show = (el, on) => el.classList.toggle('d-none', !on);

let total = 0;

// Cập nhật "N lần phân loại"; hết mục thì ẩn bảng, hiện emptyState
function setTotal(n) {
  total = n;
  $('countLabel').textContent = `${fmt.num(n)} lần phân loại`;
  show($('historyWrap'), n > 0);
  show($('btnClearAll'), n > 0);
  show($('emptyState'), n === 0);
}

function showError(msg) {
  $('loadError').lastElementChild.textContent = msg;
  show($('loadError'), Boolean(msg));
}

function renderRow(item) {
  const tr = $('rowTpl').content.firstElementChild.cloneNode(true);
  const name = item.flower.name_vi;
  const when = fmt.datetime(item.created_at);
  const img = tr.querySelector('img');
  const file = tr.querySelector('.history-file');
  const fill = tr.querySelector('.conf-fill');

  tr.querySelector('.history-thumb').style.setProperty('--h', item.flower.hue);
  img.src = item.image_url;
  img.addEventListener('error', () => img.removeAttribute('src'));   // file ảnh đã mất thì hiện khung sọc
  tr.querySelector('.history-name').textContent = name;
  show(tr.querySelector('.badge-unsure'), item.uncertain);
  file.textContent = item.original_name;
  file.title = item.original_name;                                     // tên dài bị cắt "…" thì rê chuột xem đủ
  fill.style.width = (item.confidence * 100).toFixed(1) + '%';
  fill.classList.toggle('low', item.uncertain);
  tr.querySelector('.conf-pct').textContent = fmt.pct(item.confidence);
  tr.querySelector('.history-time').textContent = when;

  const view = tr.querySelector('.btn-view-one');
  view.href = `/history/${item.id}`;
  view.setAttribute('aria-label', `Xem chi tiết ${name} lúc ${when}`);
  const del = tr.querySelector('.btn-del-one');
  del.setAttribute('aria-label', `Xóa mục ${name} lúc ${when}`);
  del.addEventListener('click', () => deleteOne(item.id, tr, `Kết quả “${name}” lúc ${when}`));
  return tr;
}

async function load() {
  showError('');
  try {
    const data = await api.get('/api/history');
    $('historyBody').replaceChildren(...data.items.map(renderRow));
    setTotal(data.total);
  } catch (e) {
    $('countLabel').textContent = 'Lịch sử phân loại';
    [$('historyWrap'), $('btnClearAll'), $('emptyState')].forEach(el => show(el, false));
    showError(`Không tải được lịch sử. ${e.message}`);
  }
}

async function deleteOne(id, tr, label) {
  if (!await confirmDialog('Xóa mục này?', `${label} và ảnh đã tải lên sẽ bị xóa. Không thể hoàn tác.`)) return;
  showError('');
  try {
    await api.del(`/api/history/${id}`);
  } catch (e) {
    if (e.status === 404) return load();     // mục đã bị xóa ở tab khác: tải lại cho khớp CSDL
    return showError(`Chưa xóa được. ${e.message}`);
  }
  tr.remove();
  setTotal(total - 1);
}

async function deleteAll() {
  const text = `Cả ${fmt.num(total)} lần phân loại và ảnh đã tải lên sẽ bị xóa. Không thể hoàn tác.`;
  if (!await confirmDialog('Xóa toàn bộ lịch sử?', text)) return;
  showError('');
  try {
    await api.del('/api/history');
  } catch (e) {
    return showError(`Chưa xóa được. ${e.message}`);
  }
  $('historyBody').replaceChildren();
  setTotal(0);
}

$('btnClearAll').addEventListener('click', deleteAll);
// Bấm Back quay về, trình duyệt có thể hiện lại bản cũ đã lưu sẵn: tải lại để khớp CSDL
window.addEventListener('pageshow', e => { if (e.persisted) load(); });
load();
