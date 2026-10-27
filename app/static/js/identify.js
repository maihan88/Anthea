/* Trang Nhận diện: chọn ảnh → phân loại → hiện kết quả. Người phụ trách: Nghi
   4 trạng thái (empty / chosen / analyzing / result) đều có sẵn trong identify.html,
   file này chỉ bật/tắt class d-none và điền dữ liệu từ /api/predict.
   Cách hoạt động bám theo bản thiết kế Anthea.dc.html. */

const MAX_BYTES = 5 * 1024 * 1024;
const TYPES = ['image/jpeg', 'image/png'];
const STEPS = ['Resize ảnh về 180×180 px', 'Conv2D · trích xuất đặc trưng', 'Dense · softmax 5 lớp', 'Tổng hợp xác suất'];
// Ảnh mẫu đặt ở app/static/samples/mau_<key>.jpg; chưa có file thì hiện khung sọc như thiết kế
const SAMPLES = [
  { key: 'rose', hue: 10 }, { key: 'sunflower', hue: 85 }, { key: 'daisy', hue: 140 },
  { key: 'tulip', hue: 345 }, { key: 'dandelion', hue: 60 },
];

const $ = id => document.getElementById(id);
const show = (el, on) => el.classList.toggle('d-none', !on);
const pct = p => fmt.pct(p, 0);                        // trang này hiện phần trăm làm tròn: 87%

let currentFile = null;
let previewUrl = null;

// ---------------- Chuyển trạng thái ----------------
function setState(s) {
  show($('dropZone'), s === 'empty');
  show($('tipsPanel'), s === 'empty');
  show($('imageBox'), s !== 'empty');
  show($('previewBar'), s === 'chosen');
  show($('analyzing'), s === 'analyzing');
  show($('analyzePanel'), s === 'analyzing');
  show($('fileTag'), s === 'result');
  show($('result'), s === 'result');
  show($('aboutSection'), s === 'result');
}

function hideErrors() {
  show($('dropError'), false);
  show($('predictError'), false);
}

function clearPreview() {
  if (previewUrl) URL.revokeObjectURL(previewUrl);
  previewUrl = null;
  $('previewImg').removeAttribute('src');
}

function reset() {
  hideErrors();
  currentFile = null;
  clearPreview();
  setState('empty');
}

// Giống thiết kế: ảnh không hợp lệ thì quay về màn trống, báo lỗi trong khung kéo-thả
function showDropError(msg) {
  reset();
  $('dropError').lastElementChild.textContent = msg;
  show($('dropError'), true);
}

// ---------------- Chọn ảnh ----------------
// hue: màu khung sọc của ô ảnh (thiết kế: theo loài của ảnh mẫu, mặc định 140)
function chooseFile(file, hue = 140) {
  if (!file) return;
  if (!TYPES.includes(file.type)) return showDropError('Định dạng chưa được hỗ trợ — vui lòng chọn ảnh JPG hoặc PNG.');
  if (file.size > MAX_BYTES) return showDropError(`Ảnh nặng ${(file.size / 1024 / 1024).toFixed(1)} MB — vượt giới hạn 5 MB.`);
  setChosen(file, { src: URL.createObjectURL(file), size: fmt.size(file.size), hue });
}

// src = null: không có ảnh xem trước, hiện "[ ảnh mẫu · tên file ]" trên khung sọc
function setChosen(file, { src, size, hue }) {
  hideErrors();
  clearPreview();
  currentFile = file;
  previewUrl = src;
  if (src) $('previewImg').src = src;
  show($('imgPlaceholder'), !src);
  $('imgPlaceholder').firstElementChild.textContent = `[ ảnh mẫu · ${file.name} ]`;
  $('imageBox').style.setProperty('--h', hue);
  $('previewName').textContent = file.name;
  $('previewSize').textContent = size;
  $('fileTag').lastElementChild.textContent = file.name;
  setState('chosen');
}

async function pickSample() {
  const s = SAMPLES[Math.floor(Math.random() * SAMPLES.length)];
  const name = `mau_${s.key}.jpg`;
  const res = await fetch(`/static/samples/${name}`).catch(() => null);
  if (res && res.ok) {
    const blob = await res.blob();
    return chooseFile(new File([blob], name, { type: blob.type }), s.hue);
  }
  setChosen(await placeholderFile(name), { src: null, size: '1.2 MB', hue: s.hue });
}

// Ảnh giữ chỗ gửi lên API khi chưa có ảnh mẫu thật; màu ngẫu nhiên để mỗi lần là một ảnh khác
function placeholderFile(name) {
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = 180;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = `hsl(${Math.floor(Math.random() * 360)}, 40%, 80%)`;
  ctx.fillRect(0, 0, 180, 180);
  return new Promise(resolve => canvas.toBlob(b => resolve(new File([b], name, { type: 'image/jpeg' })), 'image/jpeg'));
}

// ---------------- Phân loại ----------------
function predict(file) {
  const form = new FormData();
  form.append('image', file);
  return api.post('/api/predict', form);
}

const scanLine = $('analyzing').querySelector('.scan-line');
const stepList = $('analyzePanel').querySelector('.a-steps');

// p: tiến độ 0..100; mỗi 25% là một bước, vạch quét chạy từ 8% xuống 92% khung ảnh
function renderProgress(p) {
  const v = Math.min(p, 100);
  const cur = Math.min(STEPS.length - 1, Math.floor(v / 25));
  $('analyzePct').textContent = v.toFixed(0) + '%';
  $('progressBar').style.width = v.toFixed(0) + '%';
  scanLine.style.top = (8 + v * 0.84).toFixed(0) + '%';
  $('stepLabel').textContent = STEPS[cur];
  stepList.innerHTML = STEPS.map((t, k) =>
    k < cur ? `<li class="done"><span>✓</span>${t}</li>`
            : `<li${k === cur ? ' class="current"' : ''}><span>${k + 1}</span>${t}</li>`
  ).join('');
}

// Giống thiết kế: mỗi 140 ms tăng ngẫu nhiên 6–18%, chạm 100% là xong (khoảng 1 giây)
function playProgress() {
  return new Promise(resolve => {
    let p = 0;
    const timer = setInterval(() => {
      p += 6 + Math.random() * 12;
      if (p >= 100) {
        clearInterval(timer);
        resolve();
      } else {
        renderProgress(p);
      }
    }, 140);
  });
}

async function classify() {
  if (!currentFile) return;
  hideErrors();
  renderProgress(0);
  setState('analyzing');
  // Chạy hiệu ứng song song với request, chờ cả hai xong mới hiện kết quả
  const [res] = await Promise.allSettled([predict(currentFile), playProgress()]);
  if (res.status === 'rejected') {
    setState('chosen');
    $('predictError').lastElementChild.textContent = res.reason.message;
    return show($('predictError'), true);
  }
  renderResult(res.value);
  setState('result');
}

function renderResult({ top, threshold, uncertain, history_id }) {
  const best = top[0];

  $('resName').textContent = best.name_vi;
  $('resEn').textContent = `${best.name_en} · ${best.scientific}`;
  $('resPct').textContent = pct(best.confidence);
  $('resPct').classList.toggle('low', uncertain);
  $('resThreshold').textContent = pct(threshold);
  show($('resUnsure'), uncertain);

  renderTop3($('resTop3'), top, uncertain);

  $('resHistLink').href = history_id != null ? `/history/${history_id}` : '/history';
  $('resLink').href = `/flowers/${best.id}`;
  $('fileTag').querySelector('.dot').style.setProperty('--h', best.hue);

  // Về loài hoa này
  $('aboutName').innerHTML = `${best.name_vi} <em>— ${best.name_en}</em>`;
  $('aboutDesc').textContent = best.description;
  $('aboutMeaning').textContent = best.meaning;
  $('aboutSeason').textContent = best.season;
  $('aboutGallery').innerHTML = [1, 2, 3].map(k =>
    `<div class="stripe" style="--h:${best.hue}"><span class="ph-label">[ ${k === 1 ? best.name_en + ' · ' : ''}mẫu ${k} ]</span></div>`
  ).join('');
}

// ---------------- Gắn sự kiện ----------------
const fileInput = $('fileInput');
const dropZone = $('dropZone');

$('btnPick').addEventListener('click', () => fileInput.click());
$('btnSample').addEventListener('click', pickSample);
$('btnOther').addEventListener('click', reset);
$('btnClassify').addEventListener('click', classify);
$('btnAgain').addEventListener('click', reset);

fileInput.addEventListener('change', () => {
  chooseFile(fileInput.files[0]);
  fileInput.value = '';                                // cho phép chọn lại đúng file vừa chọn
});

// Kéo & thả
['dragenter', 'dragover'].forEach(ev => dropZone.addEventListener(ev, e => {
  e.preventDefault();
  dropZone.classList.add('dragover');
}));
dropZone.addEventListener('dragleave', e => {
  if (!dropZone.contains(e.relatedTarget)) dropZone.classList.remove('dragover');
});
dropZone.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  chooseFile(e.dataTransfer.files[0]);
});
// Thả ảnh lệch ra ngoài khung thì trình duyệt không tự mở ảnh
window.addEventListener('dragover', e => e.preventDefault());
window.addEventListener('drop', e => e.preventDefault());
