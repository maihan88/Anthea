/* Trang Mô hình: mọi con số đọc từ GET /api/model-info (models/model_info.json + số ảnh trong CSDL).
   Không gõ số tay ở đây: thay mô hình mới chỉ cần thay file trong models/, trang tự đổi theo.
   Người phụ trách: Nghi */

// Cộng các giá trị của một object hoặc mảng: { daisy: 445, roses: 449 } -> 894;  [77, 8, 3] -> 88
function sumValues(obj) {
  let total = 0;
  for (const value of Object.values(obj)) {
    total += value;
  }
  return total;
}

// ---------------- Số liệu chính ----------------
function showStats(info) {
  const train = sumValues(info.num_images.train);
  const val = sumValues(info.num_images.val);
  const test = sumValues(info.num_images.test);
  const all = train + val + test;

  $('statAcc').textContent = formatPercent(info.test_accuracy, 1);
  $('statAccSub').textContent = `Mô hình ${info.version} · ${formatNumber(test)} ảnh test`;

  // Số ảnh trong bộ dữ liệu: cộng số ảnh từng loài (lấy từ bảng dataset_images)
  let tf = 0;
  let web = 0;
  for (const flower of info.flowers) {
    tf += flower.image_counts.tf_flowers;
    web += flower.image_counts.web;
  }
  $('statImages').textContent = formatNumber(tf + web);
  $('statImagesSub').textContent = `${formatNumber(tf)} TF Flowers + ${formatNumber(web)} tự thu thập`;

  // Tỉ lệ chia tập, ví dụ "70/15/15"
  const trainPct = Math.round(train / all * 100);
  const valPct = Math.round(val / all * 100);
  const testPct = Math.round(test / all * 100);
  $('statSplit').textContent = `${trainPct}/${valPct}/${testPct}`;
  $('statSplitSub').textContent = `train ${formatNumber(train)} · validation ${formatNumber(val)} · test ${formatNumber(test)}`;
}

// ---------------- Kiến trúc ----------------
// layers: ["Input 180×180×3", "Rescaling 1/255", ..., "Softmax 5"]
function showArchitecture(layers) {
  let html = '';
  for (let i = 0; i < layers.length; i++) {
    let style = '';
    if (layers[i].startsWith('Conv')) style = 'background:#d3dccb';                   // khối Conv: xanh nhạt
    if (i === layers.length - 1) style = 'background:var(--forest);color:#f5f3ec';   // lớp cuối: xanh đậm

    if (i > 0) html += '<span class="arrow">→</span>';
    html += `<span class="layer" style="${style}">${layers[i]}</span>`;
  }
  $('arch').innerHTML = html;
}

// ---------------- Quá trình huấn luyện (Chart.js) ----------------
let chart = null;                                       // biểu đồ, tạo một lần rồi đổi dữ liệu
let trainingHistory = null;                             // { accuracy: [...], val_accuracy: [...], loss: [...], val_loss: [...] }

function showTrainingChart(info) {
  trainingHistory = info.history;
  $('epochInfo').textContent = `${info.epochs_trained} epoch · tốt nhất ở epoch ${info.best_epoch}`;

  // Nhãn trục ngang: 1, 2, 3, ... số epoch
  const epochs = [];
  for (let i = 1; i <= trainingHistory.accuracy.length; i++) {
    epochs.push(i);
  }

  chart = new Chart($('trainChart'), {
    type: 'line',
    data: {
      labels: epochs,
      datasets: [
        { label: 'Train', data: trainingHistory.accuracy, borderColor: '#2f4a37', backgroundColor: '#2f4a37', pointRadius: 0 },
        { label: 'Validation', data: trainingHistory.val_accuracy, borderColor: '#c9734f', backgroundColor: '#c9734f', borderDash: [5, 5], pointRadius: 0 },
      ],
    },
    options: {
      interaction: { mode: 'index', intersect: false },   // rê chuột: hiện cả 2 đường của epoch đó
      scales: { x: { title: { display: true, text: 'epoch' } } },
    },
  });
}

// type: 'accuracy' hoặc 'loss'
function switchChart(type) {
  chart.data.datasets[0].data = trainingHistory[type];
  chart.data.datasets[1].data = trainingHistory['val_' + type];
  chart.update();

  // Tô sáng nút đang chọn
  $('btnAccuracy').classList.toggle('active', type === 'accuracy');
  $('btnLoss').classList.toggle('active', type === 'loss');
}

// ---------------- Ma trận nhầm lẫn ----------------
// matrix[r][c] = số ảnh thực tế là loài r mà mô hình đoán là loài c
function showConfusionMatrix(matrix, names) {
  let html = '<span></span>';                           // ô trống ở góc trên bên trái
  for (const name of names) {
    html += `<span class="cm-head">${name}</span>`;
  }

  for (let r = 0; r < matrix.length; r++) {
    html += `<span class="cm-row-label">${names[r]}</span>`;
    const rowTotal = sumValues(matrix[r]);              // tổng số ảnh của hàng

    for (let c = 0; c < matrix[r].length; c++) {
      const value = matrix[r][c];
      const ratio = value / rowTotal;                   // tô màu theo TỈ LỆ trong hàng (các loài có số ảnh khác nhau)

      let background;
      let color = '#4d5a4f';
      if (r === c) {
        background = `rgba(47, 74, 55, ${ratio})`;       // đường chéo = đoán đúng: xanh, càng nhiều càng đậm
        if (ratio > 0.5) color = '#f5f3ec';
      } else {
        background = `rgba(201, 115, 79, ${ratio * 2})`;  // ngoài đường chéo = đoán nhầm: màu đất
      }
      html += `<span class="cm-cell" style="background:${background};color:${color}" title="${formatPercent(ratio, 1)} của hàng">${value}</span>`;
    }
  }
  $('cm').innerHTML = html;
}

// ---------------- Số ảnh theo loài ----------------
function showImageCounts(flowers) {
  // Loài nhiều ảnh nhất có thanh dài 100%
  let max = 1;
  for (const flower of flowers) {
    const total = flower.image_counts.tf_flowers + flower.image_counts.web;
    if (total > max) max = total;
  }

  let html = '';
  for (const flower of flowers) {
    const tf = flower.image_counts.tf_flowers;
    const web = flower.image_counts.web;
    html += `
      <div class="count-row">
        <span class="count-name">${flower.name_vi}</span>
        <div class="count-bar" title="${formatNumber(tf)} TF Flowers + ${formatNumber(web)} tự thu thập">
          <div style="width:${tf / max * 100}%;background:var(--forest)"></div>
          <div style="width:${web / max * 100}%;background:var(--sage-2)"></div>
        </div>
        <span class="num-r">${formatNumber(tf + web)}</span>
      </div>`;
  }
  $('counts').innerHTML = html;
}

// ---------------- F1 theo loài ----------------
function showF1(info, names) {
  let html = '';
  for (let i = 0; i < info.class_names.length; i++) {
    const scores = info.per_class[info.class_names[i]];   // { precision, recall, f1 }
    html += `
      <div class="cmp-row" title="precision ${formatPercent(scores.precision, 1)} · recall ${formatPercent(scores.recall, 1)}">
        <span class="cmp-name">${names[i]}</span>
        <div style="height:6px;width:${scores.f1 * 100}%;background:var(--forest);border-radius:4px"></div>
        <span class="num-r"><strong style="color:var(--ink)">${scores.f1.toFixed(2).replace('.', ',')}</strong></span>
      </div>`;
  }
  $('f1List').innerHTML = html;
  $('f1Legend').textContent = `Mô hình ${info.version} · độ chính xác ${formatPercent(info.test_accuracy, 1)}`;
}

// ---------------- Tải dữ liệu ----------------
async function loadModelInfo() {
  try {
    const info = await callApi('/api/model-info');

    // Tên tiếng Việt các loài, đúng thứ tự class_names (máy chủ đã sắp sẵn info.flowers theo thứ tự đó)
    const names = [];
    for (const flower of info.flowers) {
      names.push(flower.name_vi);
    }

    showStats(info);
    showArchitecture(info.architecture);
    showConfusionMatrix(info.confusion_matrix, names);
    showImageCounts(info.flowers);
    showF1(info, names);
    show('content');
    showTrainingChart(info);                            // vẽ sau khi khối đã hiện, để Chart.js đo đúng kích thước
  } catch (error) {
    showLoadError('Không tải được thông tin mô hình. ' + error.message);
  }
  hide('loadStatus');
}

$('btnAccuracy').onclick = function () { switchChart('accuracy'); };
$('btnLoss').onclick = function () { switchChart('loss'); };
loadModelInfo();
