/* Trang Chi tiết loài (/flowers/<id>). Người phụ trách: Nghi */

const $ = id => document.getElementById(id);
const show = (el, on) => el.classList.toggle('d-none', !on);

// "641 ảnh TF Flowers + 412 ảnh tự thu thập"; chưa có ảnh tự thu thập thì chỉ phần đầu
function dataCountText({ tf_flowers, web }) {
  const parts = [`${fmt.num(tf_flowers)} ảnh TF Flowers`];
  if (web > 0) parts.push(`${fmt.num(web)} ảnh tự thu thập`);
  return parts.join(' + ');
}

function render(f) {
  $('dot').style.setProperty('--h', f.hue);
  $('sci').textContent = f.scientific;
  $('nameVi').textContent = f.name_vi;
  $('nameEn').textContent = f.name_en;
  $('desc').textContent = f.description;
  $('meaning').textContent = f.meaning;
  $('season').textContent = f.season;

  // Ô 1: ảnh bìa, ô 2–3: hai ảnh mẫu tiếp theo
  const boxes = $('gallery').children;
  boxes[0].querySelector('.ph-label').textContent = `[ Ảnh ${f.name_vi.toLowerCase()} ]`;
  [...boxes].forEach((box, i) => {
    box.style.setProperty('--h', f.hue);
    const img = box.querySelector('img');
    img.alt = i === 0 ? f.name_vi : `Ảnh mẫu ${f.name_vi.toLowerCase()} ${i}`;
    if (f.samples[i]) {
      img.src = f.samples[i];
      img.addEventListener('error', () => img.removeAttribute('src'));
    }
  });

  // Loài chưa có trong mô hình (hoa sen): chưa có dữ liệu huấn luyện, không mời nhận diện
  if (f.in_model) {
    $('dataCount').textContent = dataCountText(f.image_counts);
    $('btnIdentify').textContent = `Nhận diện một bông ${f.name_vi.toLowerCase()}`;
  } else {
    $('dataCount').textContent = 'Chưa có trong mô hình — sắp có';
    show($('btnIdentify'), false);
  }
}

async function load() {
  try {
    render(await api.get(`/api/flowers/${$('flowerDetail').dataset.id}`));
    show($('detail'), true);
  } catch (e) {
    $('loadError').lastElementChild.textContent = `Không tải được thông tin loài hoa. ${e.message}`;
    show($('loadError'), true);
  } finally {
    show($('loadStatus'), false);
  }
}

load();
