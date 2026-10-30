/* Trang chủ: mục "Nhận diện gần đây" = 4 lần phân loại mới nhất. Người phụ trách: Nghi
   Hero và khối "Ba bước" là phần minh họa, viết sẵn trong index.html. */

// HTML một thẻ "gần đây". item là một mục của GET /api/history
function recentCardHtml(item) {
  let pctClass = 'recent-pct';
  if (item.uncertain) pctClass = 'recent-pct low';     // dưới ngưỡng: số màu cam

  return `
    <div class="col-md-6 col-lg-4 col-xl-3">
      <a class="recent-card" href="/history/${item.id}">
        <span class="recent-thumb stripe" style="--h:${item.flower.hue}">
          <img class="cover" src="${item.image_url}" alt="" loading="lazy">
        </span>
        <span class="recent-meta">
          <span class="d-flex flex-column gap-1" style="min-width:0">
            <span class="recent-name">${item.flower.name_vi}</span>
            <span class="recent-time">${formatDateTime(item.created_at)}</span>
          </span>
          <span class="${pctClass}">${formatPercent(item.confidence)}</span>
        </span>
      </a>
    </div>`;
}

async function loadRecent() {
  try {
    const data = await callApi('/api/history?limit=4');
    if (data.items.length === 0) return;                // chưa có lịch sử: giữ mục này ẩn

    let html = '';
    for (const item of data.items) {
      html += recentCardHtml(item);
    }
    $('recentList').innerHTML = html;
    show('recentSection');
  } catch (error) {
    // Đây chỉ là mục phụ: lỗi thì cứ để ẩn, ghi lỗi ra Console (F12) để xem
    console.warn('Không tải được nhận diện gần đây:', error.message);
  }
}

loadRecent();
