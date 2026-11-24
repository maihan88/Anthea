function sumValues(obj) {
  let total = 0;
  for (const value of Object.values(obj)) {
    total += value;
  }
  return total;
}

function showStats(info) {
  const train = sumValues(info.num_images.train);
  const val = sumValues(info.num_images.val);
  const test = sumValues(info.num_images.test);
  const all = train + val + test;

  $('statAcc').textContent = formatPercent(info.test_accuracy, 1);
  $('statAccSub').textContent = `Mô hình ${info.version} · ${formatNumber(test)} ảnh test`;

  let other = 0;
  if (info.class_names.includes('other')) {
    other = info.num_images.train.other + info.num_images.val.other + info.num_images.test.other;
  }
  $('statImages').textContent = formatNumber(all);
  if (other > 0) {
    $('statImagesSub').textContent = `${formatNumber(all - other)} ảnh 5 loài hoa + ${formatNumber(other)} ảnh Khác`;
  } else {
    $('statImagesSub').textContent = `${formatNumber(all)} ảnh 5 loài hoa`;
  }

  const trainPct = Math.round(train / all * 100);
  const valPct = Math.round(val / all * 100);
  const testPct = Math.round(test / all * 100);
  $('statSplit').textContent = `${trainPct}/${valPct}/${testPct}`;
  $('statSplitSub').textContent = `train ${formatNumber(train)} · validation ${formatNumber(val)} · test ${formatNumber(test)}`;
}

function showArchitecture(layers) {
  let html = '';
  for (let i = 0; i < layers.length; i++) {
    let style = '';
    if (layers[i].startsWith('Conv')) style = 'background:#d3dccb';
    if (i === layers.length - 1) style = 'background:var(--forest);color:#f5f3ec';

    if (i > 0) html += '<span class="arrow">→</span>';
    html += `<span class="layer" style="${style}">${layers[i]}</span>`;
  }
  $('arch').innerHTML = html;
}

let chart = null;
let trainingHistory = null;

function showTrainingChart(info) {
  trainingHistory = info.history;
  $('epochInfo').textContent = `${info.epochs_trained} epoch · tốt nhất ở epoch ${info.best_epoch}`;

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
      interaction: { mode: 'index', intersect: false },
      scales: { x: { title: { display: true, text: 'epoch' } } },
    },
  });
}

function switchChart(type) {
  chart.data.datasets[0].data = trainingHistory[type];
  chart.data.datasets[1].data = trainingHistory['val_' + type];
  chart.update();

  $('btnAccuracy').classList.toggle('active', type === 'accuracy');
  $('btnLoss').classList.toggle('active', type === 'loss');
}

function showConfusionMatrix(matrix, names) {
  let html = '<span></span>';
  for (const name of names) {
    html += `<span class="cm-head">${name}</span>`;
  }

  for (let r = 0; r < matrix.length; r++) {
    html += `<span class="cm-row-label">${names[r]}</span>`;
    const rowTotal = sumValues(matrix[r]);

    for (let c = 0; c < matrix[r].length; c++) {
      const value = matrix[r][c];
      const ratio = value / rowTotal;

      let background;
      let color = '#4d5a4f';
      if (r === c) {
        background = `rgba(47, 74, 55, ${ratio})`;
        if (ratio > 0.5) color = '#f5f3ec';
      } else {
        background = `rgba(201, 115, 79, ${ratio * 2})`;
      }
      html += `<span class="cm-cell" style="background:${background};color:${color}" title="${formatPercent(ratio, 1)} của hàng">${value}</span>`;
    }
  }
  $('cm').style.setProperty('--n', names.length);
  $('cm').innerHTML = html;
}

function showImageCounts(info, names) {
  const counts = info.num_images;

  let max = 1;
  for (const code of info.class_names) {
    const total = counts.train[code] + counts.val[code] + counts.test[code];
    if (total > max) max = total;
  }

  let html = '';
  for (let i = 0; i < info.class_names.length; i++) {
    const code = info.class_names[i];
    const train = counts.train[code];
    const val = counts.val[code];
    const test = counts.test[code];
    html += `
      <div class="count-row">
        <span class="count-name">${names[i]}</span>
        <div class="count-bar" title="train ${formatNumber(train)} · validation ${formatNumber(val)} · test ${formatNumber(test)}">
          <div style="width:${train / max * 100}%;background:var(--forest)"></div>
          <div style="width:${val / max * 100}%;background:var(--sage-2)"></div>
          <div style="width:${test / max * 100}%;background:#b9b4a6"></div>
        </div>
        <span class="num-r">${formatNumber(train + val + test)}</span>
      </div>`;
  }
  $('counts').innerHTML = html;
}

function showF1(info, names) {
  let html = '';
  for (let i = 0; i < info.class_names.length; i++) {
    const scores = info.per_class[info.class_names[i]];
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

async function loadModelInfo() {
  try {
    const info = await callApi('/api/model-info');

    const names = [];
    for (const flower of info.flowers) {
      names.push(flower.name_vi);
    }

    showStats(info);
    showArchitecture(info.architecture);
    showConfusionMatrix(info.confusion_matrix, names);
    showImageCounts(info, names);
    showF1(info, names);
    show('content');
    showTrainingChart(info);
  } catch (error) {
    showLoadError('Không tải được thông tin mô hình. ' + error.message);
  }
  hide('loadStatus');
}

$('btnAccuracy').onclick = function () { switchChart('accuracy'); };
$('btnLoss').onclick = function () { switchChart('loss'); };
loadModelInfo();
