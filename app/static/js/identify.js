const MAX_SIZE = 5 * 1024 * 1024;
const ALLOWED_TYPES = ['image/jpeg', 'image/png'];
const STEPS = ['Resize 180×180 · chuẩn hoá 0–1', '4 khối Conv · trích đặc trưng', 'GlobalAveragePooling', 'Softmax · 5 loài hoa + Khác'];
const OTHER_CODE = 'other';

let currentFile = null;

function setVisible(id, visible) {
  if (visible) show(id);
  else hide(id);
}

function setState(state) {
  setVisible('dropZone', state === 'empty');
  setVisible('sideCol', state !== 'empty');
  setVisible('imageBox', state !== 'empty');
  setVisible('previewBar', state === 'chosen');
  setVisible('analyzing', state === 'analyzing');
  setVisible('analyzePanel', state === 'analyzing');
  setVisible('fileTag', state === 'result');
  setVisible('result', state === 'result');
  setVisible('aboutSection', state === 'result');
}

function reset() {
  currentFile = null;
  $('previewImg').removeAttribute('src');
  hide('dropError');
  hide('predictError');
  setState('empty');
}

function showDropError(message) {
  reset();
  $('dropErrorText').textContent = message;
  show('dropError');
}

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
  $('previewImg').src = URL.createObjectURL(file);
  $('previewName').textContent = file.name;
  $('previewSize').textContent = formatSize(file.size);
  $('fileTagName').textContent = file.name;
  setState('chosen');
}

async function pickSample() {
  try {
    const flowers = await callApi('/api/flowers');
    const samples = [];
    for (const flower of flowers) {
      for (const url of flower.samples) samples.push(url);
    }
    if (samples.length === 0) {
      showDropError('Chưa có ảnh mẫu — hãy chép vài ảnh vào app/static/samples/<mã loài>/.');
      return;
    }

    const url = samples[Math.floor(Math.random() * samples.length)];
    const response = await fetch(url);
    const blob = await response.blob();
    const fileName = url.split('/').pop();
    chooseFile(new File([blob], fileName, { type: blob.type }));
  } catch (error) {
    showDropError('Không tải được ảnh mẫu. ' + error.message);
  }
}

function wait(ms) {
  return new Promise(function (resolve) {
    setTimeout(resolve, ms);
  });
}

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

  const percent = (step + 1) * 20;
  $('analyzePct').textContent = percent + '%';
  $('progressBar').style.width = percent + '%';
  $('scanLine').style.top = (percent * 0.9) + '%';
  $('stepLabel').textContent = STEPS[step];
}

async function classify() {
  if (!currentFile) return;
  hide('predictError');
  setState('analyzing');

  const formData = new FormData();
  formData.append('image', currentFile);
  const request = callApi('/api/predict', 'POST', formData);

  const lastStep = STEPS.length - 1;
  for (let step = 0; step < lastStep; step++) {
    showStep(step);
    await wait(300);
  }
  showStep(lastStep);

  try {
    const data = await request;
    setState('result');
    showResult(data);
  } catch (error) {
    setState('chosen');
    $('predictErrorText').textContent = error.message;
    show('predictError');
  }
}

function showResult(data) {
  const best = data.top[0];

  $('resName').textContent = best.name_vi;
  $('resPct').textContent = formatPercent(best.confidence);
  $('resTop3').innerHTML = top3Html(data.top, data.uncertain);
  $('resHistLink').href = '/history/' + data.history_id;
  $('fileTagDot').style.setProperty('--h', best.hue);

  hide('resOther');
  hide('resUnsure');
  $('resPct').classList.remove('low');

  if (best.code === OTHER_CODE) {
    $('resEn').textContent = 'Không thuộc 5 loài Anthea nhận diện';
    show('resOther');
    hide('resLink');
    hide('aboutSection');
    return;
  }

  $('resEn').textContent = best.name_en + ' · ' + best.scientific;
  $('resLink').href = '/flowers/' + best.id;
  show('resLink');

  if (data.uncertain) {
    $('resPct').classList.add('low');
    $('resThreshold').textContent = formatPercent(data.threshold);
    show('resUnsure');
  }

  $('aboutName').innerHTML = `${best.name_vi} <em>— ${best.name_en}</em>`;
  $('aboutDesc').textContent = best.description;
  $('aboutMeaning').textContent = best.meaning;
  $('aboutSeason').textContent = best.season;

  let html = '';
  for (let i = 0; i < 3; i++) {
    const src = best.samples[i];
    html += `<div class="stripe" style="--h:${best.hue}"><img class="cover" src="${src}" alt=""></div>`;
  }
  $('aboutGallery').innerHTML = html;
}

$('btnPick').onclick = function () {
  $('fileInput').click();
};
$('btnSample').onclick = pickSample;
$('btnOther').onclick = reset;
$('btnAgain').onclick = reset;
$('btnClassify').onclick = classify;

$('fileInput').onchange = function () {
  chooseFile($('fileInput').files[0]);
  $('fileInput').value = '';
};

const dropZone = $('dropZone');

dropZone.addEventListener('dragover', function (event) {
  event.preventDefault();
  dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', function (event) {
  if (!dropZone.contains(event.relatedTarget)) dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', function (event) {
  event.preventDefault();
  dropZone.classList.remove('dragover');
  chooseFile(event.dataTransfer.files[0]);
});

window.addEventListener('dragover', function (event) { event.preventDefault(); });
window.addEventListener('drop', function (event) { event.preventDefault(); });
