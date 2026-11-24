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

  let html = '';
  for (let i = 0; i < 3; i++) {
    const src = flower.samples[i];
    html += `<div class="stripe" style="--h:${flower.hue}"><img class="cover" src="${src}" alt="${flower.name_vi}"></div>`;
  }
  $('gallery').innerHTML = html;

  $('btnIdentify').textContent = 'Nhận diện một bông ' + flower.name_vi.toLowerCase();
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
