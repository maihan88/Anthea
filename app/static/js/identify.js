/* Trang Nhận diện: chọn ảnh → phân loại → hiện kết quả. Người phụ trách: Nghi
   Trang có 4 trạng thái, mọi khối đều viết sẵn trong identify.html:
     empty     : chưa có ảnh (khung kéo-thả + mẹo chụp ảnh)
     chosen    : đã chọn ảnh, chờ bấm "Phân loại"
     analyzing : đang gửi ảnh lên máy chủ
     result    : có kết quả */

const MAX_SIZE = 5 * 1024 * 1024;                       // 5 MB
const ALLOWED_TYPES = ['image/jpeg', 'image/png'];
// 4 bước hiện trong lúc chờ, khớp kiến trúc mô hình (models/model_info.json → architecture)
const STEPS = ['Resize 180×180 · chuẩn hoá 0–1', '4 khối Conv · trích đặc trưng', 'GlobalAveragePooling', 'Softmax · 5 loài hoa'];

let currentFile = null;                                 // ảnh đang chọn

// ---------------- Chuyển trạng thái ----------------

// visible = true thì hiện, false thì ẩn
function setVisible(id, visible) {
  if (visible) show(id);
  else hide(id);
}

function setState(state) {
  setVisible('dropZone', state === 'empty');
  setVisible('tipsPanel', state === 'empty');
  setVisible('imageBox', state !== 'empty');
  setVisible('previewBar', state === 'chosen');
  setVisible('analyzing', state === 'analyzing');
  setVisible('analyzePanel', state === 'analyzing');
  setVisible('fileTag', state === 'result');
  setVisible('result', state === 'result');
  setVisible('aboutSection', state === 'result');
}

// Quay về màn hình trống
function reset() {
  currentFile = null;
  $('previewImg').removeAttribute('src');
  hide('dropError');
  hide('predictError');
  setState('empty');
}

// Ảnh không hợp lệ: quay về màn hình trống, báo lỗi trong khung kéo-thả
function showDropError(message) {
  reset();
  $('dropErrorText').textContent = message;
  show('dropError');
}

// ---------------- Chọn ảnh ----------------

function chooseFile(file) {
  if (!file) return;
  if (!ALLOWED_TYPES.includes(file.type)) {
    showDropError('Định dạng chưa được hỗ trợ — vui lòng chọn ảnh JPG hoặc PNG.');
    return;
  }
  if (file.size > MAX_SIZE) {
    showDropError('Ảnh nặng ' + formatSize(file.size) + ' — vượt giới hạn 5 MB.');
    return;
  }

  currentFile = file;
  hide('dropError');
  hide('predictError');
  $('previewImg').src = URL.createObjectURL(file);      // xem trước ảnh ngay trên trình duyệt
  $('previewName').textContent = file.name;
  $('previewSize').textContent = formatSize(file.size);
  $('fileTagName').textContent = file.name;
  setState('chosen');
}

// Nút "Thử với ảnh mẫu": lấy ngẫu nhiên một ảnh trong app/static/samples/<mã loài>/
async function pickSample() {
  try {
    const flowers = await callApi('/api/flowers');
    const samples = [];
    for (const flower of flowers) {
      if (flower.in_model) {
        for (const url of flower.samples) samples.push(url);
      }
    }
    if (samples.length === 0) {
      showDropError('Chưa có ảnh mẫu — hãy chép vài ảnh vào app/static/samples/<mã loài>/.');
      return;
    }

    const url = samples[Math.floor(Math.random() * samples.length)];
    const response = await fetch(url);
    const blob = await response.blob();                 // nội dung ảnh
    const fileName = url.split('/').pop();
    chooseFile(new File([blob], fileName, { type: blob.type }));
  } catch (error) {
    showDropError('Không tải được ảnh mẫu. ' + error.message);
  }
}

// ---------------- Phân loại ----------------

// Chờ ms mili-giây (dùng với await)
function wait(ms) {
  return new Promise(function (resolve) {
    setTimeout(resolve, ms);
  });
}

// Tô màu bước thứ `step` (0..3): các bước trước là "done", bước này là "current"
function showStep(step) {
  let html = '';
  for (let i = 0; i < STEPS.length; i++) {
    if (i < step) {
      html += `<li class="done"><span>✓</span>${STEPS[i]}</li>`;
    } else if (i === step) {
      html += `<li class="current"><span>${i + 1}</span>${STEPS[i]}</li>`;
    } else {
      html += `<li><span>${i + 1}</span>${STEPS[i]}</li>`;
    }
  }
  $('stepList').innerHTML = html;

  const percent = (step + 1) * 25;
  $('analyzePct').textContent = percent + '%';
  $('progressBar').style.width = percent + '%';
  $('scanLine').style.top = (percent * 0.9) + '%';      // vạch quét chạy dần xuống dưới ảnh
  $('stepLabel').textContent = STEPS[step];
}

async function classify() {
  if (!currentFile) return;
  hide('predictError');
  setState('analyzing');

  // Gửi ảnh lên máy chủ. Chưa "await" ngay, để hiệu ứng bên dưới chạy trong lúc chờ.
  const formData = new FormData();
  formData.append('image', currentFile);
  const request = callApi('/api/predict', 'POST', formData);

  // Hiệu ứng 4 bước, mỗi bước 0,3 giây
  for (let step = 0; step < STEPS.length; step++) {
    showStep(step);
    await wait(300);
  }

  try {
    const data = await request;                          // giờ mới chờ kết quả
    showResult(data);
    setState('result');
  } catch (error) {
    setState('chosen');
    $('predictErrorText').textContent = error.message;
    show('predictError');
  }
}

// data là kết quả của POST /api/predict: { top: [3 loài], threshold, uncertain, history_id }
function showResult(data) {
  const best = data.top[0];                              // loài có độ tin cậy cao nhất

  $('resName').textContent = best.name_vi;
  $('resEn').textContent = best.name_en + ' · ' + best.scientific;
  $('resPct').textContent = formatPercent(best.confidence);
  $('resTop3').innerHTML = top3Html(data.top, data.uncertain);
  $('resHistLink').href = '/history/' + data.history_id;
  $('resLink').href = '/flowers/' + best.id;
  $('fileTagDot').style.setProperty('--h', best.hue);

  // Dưới ngưỡng: số màu cam + khối "Chưa chắc chắn"
  if (data.uncertain) {
    $('resPct').classList.add('low');
    $('resThreshold').textContent = formatPercent(data.threshold);
    show('resUnsure');
  } else {
    $('resPct').classList.remove('low');
    hide('resUnsure');
  }

  // Khối "Về loài hoa này"
  $('aboutName').innerHTML = `${best.name_vi} <em>— ${best.name_en}</em>`;
  $('aboutDesc').textContent = best.description;
  $('aboutMeaning').textContent = best.meaning;
  $('aboutSeason').textContent = best.season;

  let html = '';
  for (let i = 0; i < 3; i++) {
    const src = best.samples[i];
    if (src) {
      html += `<div class="stripe" style="--h:${best.hue}"><img class="cover" src="${src}" alt=""></div>`;
    } else {
      html += `<div class="stripe" style="--h:${best.hue}"><span class="ph-label">[ mẫu ${i + 1} ]</span></div>`;
    }
  }
  $('aboutGallery').innerHTML = html;
}

// ---------------- Gắn sự kiện cho các nút ----------------

$('btnPick').onclick = function () {
  $('fileInput').click();                               // mở hộp chọn file của máy
};
$('btnSample').onclick = pickSample;
$('btnOther').onclick = reset;
$('btnAgain').onclick = reset;
$('btnClassify').onclick = classify;

$('fileInput').onchange = function () {
  chooseFile($('fileInput').files[0]);
  $('fileInput').value = '';                            // để chọn lại đúng file đó vẫn nhận
};

// ---------------- Kéo & thả ảnh ----------------

const dropZone = $('dropZone');

dropZone.addEventListener('dragover', function (event) {
  event.preventDefault();                               // bắt buộc, nếu không sự kiện "drop" sẽ không chạy
  dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', function (event) {
  // Rê qua phần tử con bên trong khung cũng sinh "dragleave": chỉ bỏ hiệu ứng khi rời hẳn khung
  if (!dropZone.contains(event.relatedTarget)) dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', function (event) {
  event.preventDefault();
  dropZone.classList.remove('dragover');
  chooseFile(event.dataTransfer.files[0]);
});

// Thả ảnh lệch ra ngoài khung thì trình duyệt không tự mở ảnh đó
window.addEventListener('dragover', function (event) { event.preventDefault(); });
window.addEventListener('drop', function (event) { event.preventDefault(); });
