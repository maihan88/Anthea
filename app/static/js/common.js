/* Các hàm dùng chung cho mọi trang. Nạp TRƯỚC file JS riêng của từng trang. Người phụ trách: Nghi */

// ---------------- Lấy phần tử, ẩn / hiện ----------------

// $('abc') là viết tắt của document.getElementById('abc')
function $(id) {
  return document.getElementById(id);
}

// Bootstrap có sẵn class "d-none" (display: none). Thêm class thì ẩn, bỏ class thì hiện.
function show(id) {
  $(id).classList.remove('d-none');
}

function hide(id) {
  $(id).classList.add('d-none');
}

// ---------------- Gọi API của Flask ----------------

// Ví dụ:  const flowers = await callApi('/api/flowers');
//         await callApi('/api/history/5', 'DELETE');
// Thành công: trả về dữ liệu JSON.
// Thất bại: ném lỗi (Error) có message là câu báo lỗi tiếng Việt do Flask gửi về trong trường "error",
//           và error.status là mã HTTP (ví dụ 404) để trang biết "không tìm thấy" hay lỗi khác.
async function callApi(url, method = 'GET', body = null) {
  let response;
  try {
    response = await fetch(url, { method: method, body: body });
  } catch (error) {
    throw new Error('Không kết nối được tới máy chủ.');
  }

  let data;
  try {
    data = await response.json();
  } catch (error) {
    data = { error: 'Máy chủ gặp lỗi, vui lòng thử lại.' };   // máy chủ không trả JSON
  }

  if (!response.ok) {
    const error = new Error(data.error);
    error.status = response.status;
    throw error;
  }
  return data;
}

// Hiện câu báo lỗi trong khối lỗi của trang (khối có id="loadError" và phần chữ id="loadErrorText")
function showLoadError(message) {
  $('loadErrorText').textContent = message;
  show('loadError');
}

// ---------------- Định dạng số, ngày giờ ----------------

// 0.873 -> "87%";  formatPercent(0.873, 1) -> "87,3%"
function formatPercent(value, digits = 0) {
  return (value * 100).toFixed(digits).replace('.', ',') + '%';
}

// 6842 -> "6.842"
function formatNumber(value) {
  return value.toLocaleString('vi-VN');
}

// 54451 -> "53 KB";  2202009 -> "2,1 MB"
function formatSize(bytes) {
  const MB = 1024 * 1024;
  if (bytes >= MB) {
    return (bytes / MB).toFixed(1).replace('.', ',') + ' MB';
  }
  return Math.round(bytes / 1024) + ' KB';
}

// "2026-10-21T22:38:05" -> "21/10/2026 22:38"
function formatDateTime(isoText) {
  const d = new Date(isoText);
  const day = String(d.getDate()).padStart(2, '0');           // 5 -> "05"
  const month = String(d.getMonth() + 1).padStart(2, '0');    // getMonth() đếm từ 0
  const hour = String(d.getHours()).padStart(2, '0');
  const minute = String(d.getMinutes()).padStart(2, '0');
  return `${day}/${month}/${d.getFullYear()} ${hour}:${minute}`;
}

// Tên file do người dùng tự đặt có thể chứa ký tự < > &. Đổi chúng thành dạng an toàn
// trước khi ghép vào innerHTML, để trình duyệt không hiểu nhầm thành thẻ HTML.
function escapeHtml(text) {
  return text.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
}

// ---------------- Phần dùng chung của nhiều trang ----------------

// HTML 3 thanh top 3 (trang Nhận diện và Chi tiết lịch sử).
// top: [{ name_vi: 'Hoa hồng', confidence: 0.87 }, ...];  uncertain: true khi độ tin cậy dưới ngưỡng
function top3Html(top, uncertain) {
  let html = '';
  for (let i = 0; i < top.length; i++) {
    const flower = top[i];
    const width = flower.confidence * 100;

    let barClass = 'bar-fill';
    let nameStyle = '';
    if (i === 0) {                                  // loài đứng đầu: thanh đậm, chữ đậm
      barClass = 'bar-fill main';
      nameStyle = 'font-weight:600';
      if (uncertain) barClass = 'bar-fill main low';
    }

    html += `
      <div class="top3-row">
        <span class="top3-rank">0${i + 1}</span>
        <span style="${nameStyle}">${flower.name_vi}</span>
        <div class="bar-track"><div class="${barClass}" style="width:${width}%"></div></div>
        <span class="top3-pct">${formatPercent(flower.confidence)}</span>
      </div>`;
  }
  return html;
}

// Hộp xác nhận xóa (cần có khối #confirmModal trong trang và thư viện Bootstrap JS).
// Bấm "Xóa" thì gọi hàm onConfirm; bấm "Hủy" thì không làm gì.
function askConfirm(title, text, onConfirm) {
  const modal = bootstrap.Modal.getOrCreateInstance($('confirmModal'));
  $('confirmTitle').textContent = title;
  $('confirmText').textContent = text;
  $('btnConfirm').onclick = function () {
    modal.hide();
    onConfirm();
  };
  modal.show();
}
