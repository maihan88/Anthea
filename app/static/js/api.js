/* Phần dùng chung cho mọi trang (nạp trong base.html, trước script riêng của từng trang). Người phụ trách: Nghi
   - api:  gọi /api/..., lỗi thì ném Error mang câu tiếng Việt của máy chủ (trường "error")
   - fmt:  định dạng số, phần trăm, dung lượng, ngày giờ kiểu Việt Nam
   - confirmDialog, renderTop3: hộp xác nhận xóa và 3 thanh top 3 mà nhiều trang cùng dùng
   Không khai báo $ ở đây: identify.js và các trang tự có $ riêng. */

const api = (() => {
  async function request(url, options) {
    let res;
    try {
      res = await fetch(url, options);
    } catch {
      throw new Error('Không kết nối được tới máy chủ.');
    }
    const data = await res.json().catch(() => null);
    if (!res.ok || data === null) {
      const err = new Error(data?.error || 'Máy chủ gặp lỗi, vui lòng thử lại.');
      err.status = res.status;                        // trang cần phân biệt 404 (đã bị xóa) với lỗi khác
      throw err;
    }
    return data;
  }
  return {
    get: url => request(url),
    post: (url, body) => request(url, { method: 'POST', body }),
    del: url => request(url, { method: 'DELETE' }),
  };
})();

const fmt = {
  // 0.873 → "87,3%"; digits: số chữ số sau dấu phẩy
  pct: (p, digits = 1) => new Intl.NumberFormat('vi-VN', {
    style: 'percent', minimumFractionDigits: digits, maximumFractionDigits: digits,
  }).format(p),
  // 1222 → "1.222"; fmt.num(0.8, 2) → "0,80" (luôn đủ digits chữ số sau dấu phẩy)
  num: (n, digits = 0) => new Intl.NumberFormat('vi-VN', {
    minimumFractionDigits: digits, maximumFractionDigits: digits,
  }).format(n),
  // 54451 → "53 KB", 2202009 → "2,1 MB"
  size: bytes => bytes >= 1024 * 1024
    ? fmt.num(bytes / 1024 / 1024, 1) + ' MB'
    : fmt.num(Math.max(1, Math.round(bytes / 1024))) + ' KB',
  // "2026-10-21T22:38:05" (giờ máy chủ, không kèm múi giờ nên trình duyệt hiểu là giờ địa phương)
  // → { date: "21/10/2026", time: "22:38" }. Tự ghép vì toLocaleString('vi-VN') đặt giờ trước ngày.
  parts: iso => {
    const d = new Date(iso);
    const two = n => String(n).padStart(2, '0');
    return { date: `${two(d.getDate())}/${two(d.getMonth() + 1)}/${d.getFullYear()}`, time: `${two(d.getHours())}:${two(d.getMinutes())}` };
  },
  // → "21/10/2026 22:38"
  datetime: iso => {
    const { date, time } = fmt.parts(iso);
    return `${date} ${time}`;
  },
};

// Hộp xác nhận trong _confirm_modal.html. Trả Promise: true khi bấm Xóa, false khi Hủy hoặc đóng hộp.
function confirmDialog(title, text) {
  const el = document.getElementById('confirmModal');
  const modal = bootstrap.Modal.getOrCreateInstance(el);
  const ok = document.getElementById('btnConfirm');
  const opener = document.activeElement;
  document.getElementById('confirmTitle').textContent = title;
  document.getElementById('confirmText').textContent = text;
  return new Promise(resolve => {
    const onOk = () => {
      resolve(true);
      modal.hide();
    };
    ok.addEventListener('click', onOk);
    el.addEventListener('hidden.bs.modal', () => {
      ok.removeEventListener('click', onOk);
      if (opener?.isConnected) opener.focus();       // Hủy thì trả con trỏ về nút vừa bấm
      resolve(false);                                 // đã resolve(true) rồi thì lệnh này không có tác dụng
    }, { once: true });
    modal.show();
  });
}

// Vẽ 3 thanh top 3 vào box (trang Nhận diện và Chi tiết lịch sử). top: [{name_vi, confidence}, …]
// Chỉ thay các .top3-row cũ, giữ nguyên phần khác trong box (ví dụ nhãn "Top 3 dự đoán").
function renderTop3(box, top, uncertain) {
  box.querySelectorAll('.top3-row').forEach(row => row.remove());
  top.forEach((f, i) => {
    const row = document.createElement('div');
    row.className = 'top3-row';
    row.innerHTML = '<span class="top3-rank"></span><span></span><div class="bar-track"><div class="bar-fill"></div></div><span class="top3-pct"></span>';
    const [rank, name, track, pct] = row.children;
    rank.textContent = '0' + (i + 1);
    name.textContent = f.name_vi;
    if (i === 0) name.style.fontWeight = 600;
    const fill = track.firstElementChild;
    fill.classList.toggle('main', i === 0);
    fill.classList.toggle('low', i === 0 && uncertain);
    fill.style.width = (f.confidence * 100).toFixed(1) + '%';
    pct.textContent = fmt.pct(f.confidence, 0);
    box.append(row);
  });
}
