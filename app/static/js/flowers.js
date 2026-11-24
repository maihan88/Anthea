function flowerCardHtml(flower) {
  return `
    <div class="col-sm-6 col-lg-4 col-xl-3">
      <a class="flower-card" href="/flowers/${flower.id}">
        <span class="flower-thumb stripe" style="--h:${flower.hue}">
          <img class="cover" src="${flower.samples[0]}" alt="" loading="lazy">
          <span class="flower-badge">${formatNumber(flower.image_count)} ảnh</span>
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
