/* Trang Chi tiết loài (/flowers/<id>). Người phụ trách: Nghi */

// Lấy id trên thanh địa chỉ: "/flowers/3" -> "3"
const flowerId = location.pathname.split('/').pop();

function showFlower(flower) {
  document.title = flower.name_vi + ' · Anthea';

  $('dot').style.setProperty('--h', flower.hue);
  $('sci').textContent = flower.scientific;
  $('nameVi').textContent = flower.name_vi;
  $('nameEn').textContent = flower.name_en;
  $('desc').textContent = flower.description;
  $('meaning').textContent = flower.meaning;
  $('season').textContent = flower.season;

  // 3 ô ảnh mẫu: ô nào chưa có ảnh thì chỉ hiện khung sọc kèm chữ
  let html = '';
  for (let i = 0; i < 3; i++) {
    const src = flower.samples[i];
    if (src) {
      html += `<div class="stripe" style="--h:${flower.hue}"><img class="cover" src="${src}" alt="${flower.name_vi}"></div>`;
    } else {
      html += `<div class="stripe" style="--h:${flower.hue}"><span class="ph-label">[ ảnh mẫu dataset ]</span></div>`;
    }
  }
  $('gallery').innerHTML = html;

  // Loài chưa có trong mô hình (hoa sen): chưa có dữ liệu huấn luyện, không mời nhận diện
  if (flower.in_model) {
    const counts = flower.image_counts;
    let text = formatNumber(counts.tf_flowers) + ' ảnh TF Flowers';
    if (counts.web > 0) text += ' + ' + formatNumber(counts.web) + ' ảnh tự thu thập';
    $('dataCount').textContent = text;
    $('btnIdentify').textContent = 'Nhận diện một bông ' + flower.name_vi.toLowerCase();
  } else {
    $('dataCount').textContent = 'Chưa có trong mô hình — sắp có';
    hide('btnIdentify');
  }
}

async function loadFlower() {
  try {
    const flower = await callApi('/api/flowers/' + flowerId);
    showFlower(flower);
    show('detail');
  } catch (error) {
    showLoadError('Không tải được thông tin loài hoa. ' + error.message);
  }
  hide('loadStatus');
}

loadFlower();
