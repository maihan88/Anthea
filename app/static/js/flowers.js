/* Trang Thư viện hoa: mỗi loài trong bảng flowers một thẻ. Người phụ trách: Nghi */

// HTML một thẻ hoa. flower là một phần tử của GET /api/flowers
function flowerCardHtml(flower) {
  // Ảnh bìa = ảnh mẫu đầu tiên; chưa có ảnh mẫu thì để trống, chỉ hiện khung sọc
  let image = '';
  if (flower.samples.length > 0) {
    image = `<img class="cover" src="${flower.samples[0]}" alt="" loading="lazy">`;
  }

  // Loài đã có trong mô hình: bấm vào xem chi tiết.
  // Loài chưa có (hoa sen, in_model = false): thẻ mờ "Sắp có", không bấm được.
  let cardClass = 'flower-card';
  let link = `href="/flowers/${flower.id}"`;
  let badge = formatNumber(flower.image_counts.tf_flowers + flower.image_counts.web) + ' ảnh';
  if (!flower.in_model) {
    cardClass = 'flower-card soon';
    link = '';
    badge = 'Sắp có';
  }

  return `
    <div class="col-sm-6 col-lg-4 col-xl-3">
      <a class="${cardClass}" ${link}>
        <span class="flower-thumb stripe" style="--h:${flower.hue}">
          ${image}
          <span class="ph-label">[ Ảnh ${flower.name_vi.toLowerCase()} ]</span>
          <span class="flower-badge">${badge}</span>
        </span>
        <span class="flower-meta">
          <span class="d-flex flex-column gap-1">
            <span class="flower-vi">${flower.name_vi}</span>
            <span class="flower-en">${flower.name_en}</span>
          </span>
          <span class="dot" style="--h:${flower.hue}"></span>
        </span>
      </a>
    </div>`;
}

async function loadFlowers() {
  try {
    const flowers = await callApi('/api/flowers');
    let html = '';
    for (const flower of flowers) {
      html += flowerCardHtml(flower);
    }
    $('flowerGrid').innerHTML = html;
  } catch (error) {
    showLoadError('Không tải được danh sách loài hoa. ' + error.message);
  }
  hide('loadStatus');
}

loadFlowers();
