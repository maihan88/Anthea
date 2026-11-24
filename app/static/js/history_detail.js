const predictionId = location.pathname.split('/').pop();

function showPrediction(item) {
  const flower = item.flower;
  document.title = flower.name_vi + ' #' + item.id + ' · Anthea';

  $('imageBox').style.setProperty('--h', flower.hue);
  $('image').src = item.image_url;
  $('image').alt = 'Ảnh đã tải lên: ' + item.original_name;
  $('metaTime').textContent = formatDateTime(item.created_at);
  $('metaFile').textContent = item.original_name;
  $('metaSize').textContent = formatSize(item.file_size);
  $('metaModel').textContent = item.model_version;
  $('metaThreshold').textContent = formatPercent(item.threshold);

  $('dot').style.setProperty('--h', flower.hue);
  $('nameVi').textContent = flower.name_vi;
  if (flower.code === 'other') {
    $('nameEn').textContent = 'Không thuộc 5 loài Anthea nhận diện';
  } else {
    $('nameEn').textContent = flower.name_en + ' · ' + flower.scientific;
  }
  $('pct').textContent = formatPercent(item.confidence);
  $('top3').innerHTML = top3Html(item.top, item.uncertain);
  $('flowerLink').href = '/flowers/' + flower.id;
  if (flower.code === 'other') hide('flowerLink');

  if (item.uncertain) {
    $('pct').classList.add('low');
    $('unsureThreshold').textContent = formatPercent(item.threshold);
    show('unsure');
  }
}

async function loadPrediction() {
  try {
    const item = await callApi('/api/history/' + predictionId);
    showPrediction(item);
    show('detail');
  } catch (error) {
    if (error.status === 404) {
      show('notFound');
    } else {
      showLoadError('Không tải được mục này. ' + error.message);
    }
  }
  hide('loadStatus');
}

function deleteThis() {
  askConfirm('Xóa mục này?', 'Kết quả này và ảnh đã tải lên sẽ bị xóa. Không thể hoàn tác.', async function () {
    try {
      await callApi('/api/history/' + predictionId, 'DELETE');
    } catch (error) {
      if (error.status !== 404) {
        showLoadError('Chưa xóa được. ' + error.message);
        return;
      }
    }
    location.href = '/history';
  });
}

$('btnDelete').onclick = deleteThis;
loadPrediction();
