/* Trang Mô hình: mọi con số đọc từ GET /api/model-info (model_info.json + số ảnh trong CSDL). Người phụ trách: Nghi
   Không gõ số tay ở đây: gắn mô hình v2 chỉ cần thay file trong models/, trang tự đổi theo. */

const $ = id => document.getElementById(id);
const show = (el, on) => el.classList.toggle('d-none', !on);
const sum = arr => arr.reduce((a, b) => a + b, 0);
const SVG_NS = 'http://www.w3.org/2000/svg';
// Các khối Conv đậm dần theo độ sâu như thiết kế; lớp cuối (Softmax) màu xanh rừng
const CONV_SHADES = ['#e4e9dc', '#d3dccb', '#bfccb6', '#adbda3'];

function span(className, text) {
  const el = document.createElement('span');
  el.className = className;
  el.textContent = text;
  return el;
}

// ---------------- Số liệu chính ----------------
function renderStats(info) {
  // Số ảnh mỗi tập lấy từ num_images: đúng bộ dữ liệu mà mô hình đã học
  const splits = ['train', 'val', 'test'].map(s => sum(Object.values(info.num_images[s] || {})));
  const all = sum(splits);
  $('statAcc').textContent = fmt.pct(info.test_accuracy);
  $('statAccSub').textContent = `Mô hình ${info.version} · ${fmt.num(splits[2])} ảnh test`;

  // Số ảnh trong bộ dữ liệu lấy từ CSDL (dataset_images), giống Thư viện hoa
  const tf = sum(info.flowers.map(f => f.image_counts.tf_flowers));
  const web = sum(info.flowers.map(f => f.image_counts.web));
  $('statImages').textContent = fmt.num(tf + web);
  $('statImagesSub').textContent = web > 0
    ? `${fmt.num(tf)} TF Flowers + ${fmt.num(web)} tự thu thập`
    : 'TF Flowers · chưa có ảnh tự thu thập';

  $('statSplit').textContent = splits.map(n => Math.round(n / all * 100)).join('/');
  $('statSplitSub').textContent = `train ${fmt.num(splits[0])} · validation ${fmt.num(splits[1])} · test ${fmt.num(splits[2])}`;
}

// ---------------- Kiến trúc ----------------
function renderArch(layers) {
  let conv = 0;
  const nodes = layers.flatMap((name, i) => {
    const layer = span('layer', name);
    if (name.startsWith('Conv')) layer.style.background = CONV_SHADES[Math.min(conv++, CONV_SHADES.length - 1)];
    if (i === layers.length - 1) {
      layer.style.background = 'var(--forest)';
      layer.style.color = '#f5f3ec';
    }
    if (i === 0) return [layer];
    const arrow = span('arrow', '→');
    arrow.setAttribute('aria-hidden', 'true');
    return [arrow, layer];
  });
  $('arch').replaceChildren(...nodes);
}

// ---------------- Quá trình huấn luyện ----------------
function svgEl(tag, attrs) {
  const el = document.createElementNS(SVG_NS, tag);
  Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v));
  return el;
}

function svgText(x, y, content, anchor = 'start') {
  const t = svgEl('text', { x, y, 'text-anchor': anchor });
  t.textContent = content;
  return t;
}

// Vẽ 2 đường train/validation vào khung 560×230, vùng vẽ x 40→550, y 20→200.
// Trục dọc phải lật ngược: trong SVG y lớn nằm phía dưới, còn giá trị lớn phải nằm phía trên.
// best: epoch của bản mô hình được giữ lại; format: cách hiện một giá trị khi rê chuột
function drawChart(svg, train, val, { best, format }) {
  const values = [...train, ...val];
  const step = Math.max(...values) - Math.min(...values) > 0.8 ? 0.2 : 0.1;   // vạch ngang mỗi 0,1 hoặc 0,2
  const lo = Math.floor(Math.min(...values) / step) * step;
  const hi = Math.ceil(Math.max(...values) / step) * step;
  const n = train.length;
  const x = i => 40 + (n > 1 ? i / (n - 1) : 0) * 510;
  const y = v => 200 - (v - lo) / (hi - lo || 1) * 180;
  const nodes = [];
  const labels = svgEl('g', { 'font-size': 10, 'font-family': 'JetBrains Mono, monospace', fill: '#8a9387' });

  // Vạch ngang kèm nhãn trục dọc; vạch dưới cùng đậm hơn làm trục
  for (let k = 0; lo + k * step <= hi + 1e-9; k++) {
    const gy = y(lo + k * step);
    nodes.push(svgEl('line', { x1: 40, y1: gy, x2: 550, y2: gy, stroke: k === 0 ? 'rgba(31,42,34,.2)' : 'rgba(31,42,34,.08)' }));
    labels.append(svgText(32, gy + 4, (lo + k * step).toFixed(1), 'end'));
  }
  // Nhãn trục ngang: "epoch 1", mỗi 10 epoch, và epoch cuối
  labels.append(svgText(40, 222, 'epoch 1'));
  for (let e = 10; e < n - 2; e += 10) labels.append(svgText(x(e - 1), 222, String(e), 'middle'));
  labels.append(svgText(550, 222, String(n), 'end'));

  // Epoch tốt nhất: vạch đứng nét chấm và nhãn phía trên
  const bx = best ? x(best - 1) : null;
  if (best) {
    nodes.push(svgEl('line', { x1: bx, y1: 20, x2: bx, y2: 200, stroke: 'rgba(31,42,34,.35)', 'stroke-dasharray': '2 4' }));
    labels.append(bx > 300 ? svgText(bx - 6, 13, `tốt nhất · epoch ${best}`, 'end') : svgText(bx + 6, 13, `tốt nhất · epoch ${best}`));
  }
  nodes.push(labels);

  [[train, '#2f4a37', null], [val, 'oklch(0.66 0.12 35)', '5 5']].forEach(([data, color, dash]) => {
    const line = svgEl('polyline', {
      points: data.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(' '),
      fill: 'none', stroke: color, 'stroke-width': 2.5, 'stroke-linejoin': 'round', 'stroke-linecap': 'round',
    });
    if (dash) line.setAttribute('stroke-dasharray', dash);
    nodes.push(line);
  });
  if (best) nodes.push(svgEl('circle', { cx: bx, cy: y(val[best - 1]), r: 4, fill: 'oklch(0.66 0.12 35)', stroke: '#fbfaf6', 'stroke-width': 2 }));

  // Mỗi epoch một dải trong suốt: rê chuột vào thì trình duyệt hiện số của epoch đó
  const w = 510 / Math.max(n - 1, 1);
  train.forEach((v, i) => {
    const hit = svgEl('rect', { class: 'chart-hit', x: x(i) - w / 2, y: 20, width: w, height: 180 });
    const title = svgEl('title', {});
    title.textContent = `Epoch ${i + 1} — train ${format(v)} · validation ${format(val[i])}`;
    hit.append(title);
    nodes.push(hit);
  });
  svg.replaceChildren(...nodes);
}

function renderTraining(info) {
  $('epochInfo').textContent = `${info.epochs_trained} epoch · tốt nhất ở epoch ${info.best_epoch}`;
  const h = info.history;
  if (!h) {
    // model_info.json không có history: tạm hiện ảnh PNG (accuracy và loss cạnh nhau), cho ô rộng hết hàng
    // để chữ trong ảnh đủ to; ảnh có chú thích riêng nên ẩn chú thích Train/Validation
    $('curvesImg').src = info.charts.training_curves;
    show($('curvesImg'), true);
    $('trainCol').classList.replace('col-lg-6', 'col-12');
    return;
  }
  drawChart($('chartAcc'), h.accuracy, h.val_accuracy, { best: info.best_epoch, format: v => fmt.pct(v) });
  drawChart($('chartLoss'), h.loss, h.val_loss, { best: info.best_epoch, format: v => fmt.num(v, 3) });
  [$('chartSeg'), $('legendLines'), $('chartAcc')].forEach(el => show(el, true));
}

function pickChart(btn) {
  $('chartSeg').querySelectorAll('button').forEach(b => {
    b.classList.toggle('active', b === btn);
    b.setAttribute('aria-pressed', b === btn);
  });
  show($('chartAcc'), btn.dataset.chart === 'acc');
  show($('chartLoss'), btn.dataset.chart === 'loss');
}

// ---------------- Ma trận nhầm lẫn ----------------
// Tô màu theo tỉ lệ trên tổng hàng, không theo số tuyệt đối: bồ công anh có 134 ảnh test, cúc chỉ 94,
// tô theo số thì hàng bồ công anh luôn trông đậm hơn dù đoán đúng tỉ lệ như nhau.
function cellColors(ratio, diagonal) {
  if (diagonal) return [`oklch(${(0.92 - 0.55 * ratio).toFixed(3)} 0.06 150)`, ratio > 0.45 ? '#f5f3ec' : '#4d5a4f'];
  if (ratio < 0.03) return ['#f1efe8', '#4d5a4f'];
  return [`oklch(${(0.95 - 0.6 * ratio).toFixed(3)} 0.05 35)`, '#4d5a4f'];   // nhầm nhiều: ngả màu đất
}

function renderMatrix(matrix, names) {
  const nodes = [document.createElement('span'), ...names.map(n => span('cm-head', n))];
  matrix.forEach((row, r) => {
    const total = sum(row);
    nodes.push(span('cm-row-label', names[r]));
    row.forEach((v, c) => {
      const ratio = total ? v / total : 0;
      const cell = span('cm-cell', fmt.num(v));
      [cell.style.background, cell.style.color] = cellColors(ratio, r === c);
      cell.title = `Thực tế ${names[r]}, đoán ${names[c]}: ${fmt.num(v)} ảnh (${fmt.pct(ratio)} của hàng)`;
      nodes.push(cell);
    });
  });
  $('cm').style.setProperty('--n', names.length);
  $('cm').replaceChildren(...nodes);
}

// ---------------- Số ảnh theo loài ----------------
function renderCounts(flowers) {
  const totals = flowers.map(f => f.image_counts.tf_flowers + f.image_counts.web);
  const max = Math.max(...totals, 1);                  // loài nhiều ảnh nhất = thanh dài nhất
  $('counts').replaceChildren(...flowers.map((f, i) => {
    const { tf_flowers: tf, web } = f.image_counts;
    const row = $('countTpl').content.firstElementChild.cloneNode(true);
    row.querySelector('.count-name').textContent = f.name_vi;
    row.querySelector('.count-tf').style.width = (tf / max * 100).toFixed(1) + '%';
    row.querySelector('.count-web').style.width = (web / max * 100).toFixed(1) + '%';
    row.querySelector('.count-bar').title = `${fmt.num(tf)} TF Flowers + ${fmt.num(web)} tự thu thập`;
    row.querySelector('.num-r').textContent = fmt.num(totals[i]);
    return row;
  }));
}

// ---------------- F1 theo loài ----------------
// Chưa có v2: mỗi loài một thanh F1 của mô hình hiện tại (per_class). Khi model_info.json có trường comparison
// thì thêm thanh "trước" để so sánh; dạng trường đó chốt với Hân lúc xuất v2 rồi mới viết phần này.
function renderF1(info, names) {
  $('compare').replaceChildren(...info.class_names.map((code, i) => {
    const m = info.per_class[code];
    const row = $('cmpTpl').content.firstElementChild.cloneNode(true);
    row.querySelector('.cmp-name').textContent = names[i];
    row.querySelector('.cmp-after').style.width = (m.f1 * 100).toFixed(1) + '%';
    row.querySelector('.cmp-after-num').textContent = fmt.num(m.f1, 2);
    row.title = `${names[i]}: precision ${fmt.pct(m.precision)} · recall ${fmt.pct(m.recall)} · F1 ${fmt.num(m.f1, 4)}`;
    ['.cmp-before', '.cmp-before-num', '.cmp-arrow'].forEach(sel => show(row.querySelector(sel), false));
    return row;
  }));
  $('legendAfter').textContent = `Mô hình ${info.version} · độ chính xác ${fmt.pct(info.test_accuracy)}`;
}

async function load() {
  try {
    const info = await api.get('/api/model-info');
    // Nhãn ma trận theo đúng thứ tự class_names; loài thiếu trong CSDL thì tạm hiện mã lớp
    const names = info.class_names.map(code => info.flowers.find(f => f.code === code)?.name_vi ?? code);
    renderStats(info);
    renderArch(info.architecture);
    renderTraining(info);
    renderMatrix(info.confusion_matrix, names);
    renderCounts(info.flowers);
    renderF1(info, names);
    show($('content'), true);
  } catch (e) {
    $('loadError').lastElementChild.textContent = `Không tải được thông tin mô hình. ${e.message}`;
    show($('loadError'), true);
  } finally {
    show($('loadStatus'), false);
  }
}

$('chartSeg').querySelectorAll('button').forEach(btn => btn.addEventListener('click', () => pickChart(btn)));
load();
