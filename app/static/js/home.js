/* Trang chủ: mục "Nhận diện gần đây" = 3 lần phân loại mới nhất. Người phụ trách: Nghi
   Hero và khối "Ba bước" là phần minh họa, giữ nguyên trong index.html. */

const $ = id => document.getElementById(id);
const show = (el, on) => el.classList.toggle('d-none', !on);

function renderCard(item) {
  const col = $('recentTpl').content.firstElementChild.cloneNode(true);
  const img = col.querySelector('img');
  const pct = col.querySelector('.recent-pct');
  const { date, time } = fmt.parts(item.created_at);

  col.querySelector('.recent-card').href = `/history/${item.id}`;
  col.querySelector('.recent-thumb').style.setProperty('--h', item.flower.hue);
  img.src = item.image_url;
  img.addEventListener('error', () => img.removeAttribute('src'));   // file ảnh đã mất thì hiện khung sọc
  col.querySelector('.recent-name').textContent = item.flower.name_vi;
  col.querySelector('.recent-time').textContent = `${date.slice(0, 5)} · ${time}`;   // "21/10 · 22:38"
  pct.textContent = fmt.pct(item.confidence, 0);
  pct.classList.toggle('low', item.uncertain);
  return col;
}

async function loadRecent() {
  try {
    const { items } = await api.get('/api/history?limit=3');
    $('recentList').replaceChildren(...items.map(renderCard));
    show($('recentSection'), items.length > 0);
  } catch (e) {
    // Mục phụ của Trang chủ: lỗi thì cứ để ẩn, không chiếm chỗ bằng thông báo lỗi
    show($('recentSection'), false);
    console.warn('Không tải được nhận diện gần đây:', e.message);
  }
}

// Bấm Back quay về Trang chủ sau khi xóa lịch sử: tải lại để không hiện mục đã xóa
window.addEventListener('pageshow', e => { if (e.persisted) loadRecent(); });
loadRecent();
