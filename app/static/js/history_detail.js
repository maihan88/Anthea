/* Trang Chi tiết lịch sử (/history/<id>). Người phụ trách: Nghi */

const $ = id => document.getElementById(id);
const show = (el, on) => el.classList.toggle('d-none', !on);
const ID = $('historyDetail').dataset.id;

let current = null;                                    // mục đang hiện, dùng cho nút Xóa

function showError(msg) {
  $('loadError').lastElementChild.textContent = msg;
  show($('loadError'), Boolean(msg));
}

function render(p) {
  const f = p.flower;
  const { date, time } = fmt.parts(p.created_at);
  document.title = `${f.name_vi} #${p.id} · Anthea`;

  $('imageBox').style.setProperty('--h', f.hue);
  $('image').src = p.image_url;
  $('image').alt = `Ảnh đã tải lên: ${p.original_name}`;
  $('imageLabel').textContent = `[ ảnh đã tải lên · ${p.original_name} ]`;
  $('code').textContent = `#${p.id}`;
  $('metaTime').textContent = `${time} · ${date}`;
  $('metaFile').textContent = p.original_name;
  $('metaSize').textContent = fmt.size(p.file_size);
  $('metaModel').textContent = p.model_version;        // phiên bản lúc phân loại, không phải phiên bản hiện tại
  $('metaThreshold').textContent = fmt.pct(p.threshold, 0);

  $('dot').style.setProperty('--h', f.hue);
  $('nameVi').textContent = f.name_vi;
  $('nameEn').textContent = `${f.name_en} · ${f.scientific}`;
  $('pct').textContent = fmt.pct(p.confidence, 0);
  $('pct').classList.toggle('low', p.uncertain);
  $('unsureThreshold').textContent = fmt.pct(p.threshold, 0);
  show($('unsure'), p.uncertain);
  renderTop3($('top3'), p.top, p.uncertain);
  $('flowerLink').href = `/flowers/${f.id}`;
}

async function load() {
  showError('');
  [$('detail'), $('notFound')].forEach(el => show(el, false));
  show($('loadStatus'), true);
  try {
    current = await api.get(`/api/history/${ID}`);
    render(current);
    show($('detail'), true);
  } catch (e) {
    current = null;
    if (e.status === 404) show($('notFound'), true);
    else showError(`Không tải được mục này. ${e.message}`);
  } finally {
    show($('loadStatus'), false);
  }
}

async function deleteThis() {
  if (!current) return;
  const label = `Kết quả “${current.flower.name_vi}” lúc ${fmt.datetime(current.created_at)}`;
  if (!await confirmDialog('Xóa mục này?', `${label} và ảnh đã tải lên sẽ bị xóa. Không thể hoàn tác.`)) return;
  try {
    await api.del(`/api/history/${ID}`);
  } catch (e) {
    if (e.status !== 404) return showError(`Chưa xóa được. ${e.message}`);
  }
  location.href = '/history';                          // xóa xong (hoặc đã bị xóa từ trước) thì về danh sách
}

$('image').addEventListener('error', () => $('image').removeAttribute('src'));   // file ảnh mất: hiện khung sọc + tên file
$('btnDelete').addEventListener('click', deleteThis);
// Xóa xong rồi bấm Back: trình duyệt có thể hiện lại bản cũ đã lưu sẵn, nên hỏi lại API để báo "đã bị xóa"
window.addEventListener('pageshow', e => { if (e.persisted) load(); });
load();
