/* Trang Thư viện hoa: mỗi loài trong bảng flowers một thẻ. Người phụ trách: Nghi */

const $ = id => document.getElementById(id);
const show = (el, on) => el.classList.toggle('d-none', !on);

function renderCard(f) {
  const col = $('flowerTpl').content.firstElementChild.cloneNode(true);
  const card = col.querySelector('.flower-card');
  const img = col.querySelector('img');
  const total = f.image_counts.tf_flowers + f.image_counts.web;

  col.querySelector('.flower-thumb').style.setProperty('--h', f.hue);
  col.querySelector('.dot').style.setProperty('--h', f.hue);
  col.querySelector('.ph-label').textContent = `[ Ảnh ${f.name_vi.toLowerCase()} ]`;
  col.querySelector('.flower-vi').textContent = f.name_vi;
  col.querySelector('.flower-en').textContent = f.name_en;
  if (f.cover) {
    img.src = f.cover;
    img.addEventListener('error', () => img.removeAttribute('src'));   // ảnh hỏng thì quay về khung sọc
  }

  if (f.in_model) {
    card.href = `/flowers/${f.id}`;
    col.querySelector('.flower-badge').textContent = `${fmt.num(total)} ảnh`;
  } else {
    card.removeAttribute('href');
    card.classList.add('soon');
    card.setAttribute('aria-disabled', 'true');
    col.querySelector('.flower-badge').textContent = 'Sắp có';
  }
  return col;
}

async function load() {
  try {
    const flowers = await api.get('/api/flowers');
    $('flowerGrid').replaceChildren(...flowers.map(renderCard));
  } catch (e) {
    $('loadError').lastElementChild.textContent = `Không tải được danh sách loài hoa. ${e.message}`;
    show($('loadError'), true);
  } finally {
    show($('loadStatus'), false);
  }
}

load();
