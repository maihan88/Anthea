/* Trang Chi tiết lịch sử (/history/<id>). Người phụ trách: Nghi */

// Lấy id trên thanh địa chỉ: "/history/12" -> "12"
const predictionId = location.pathname.split('/').pop();

function showPrediction(item) {
  const flower = item.flower;
  document.title = flower.name_vi + ' #' + item.id + ' · Anthea';

  // Cột trái: ảnh + thông tin
  $('imageBox').style.setProperty('--h', flower.hue);
  $('image').src = item.image_url;
  $('image').alt = 'Ảnh đã tải lên: ' + item.original_name;
  $('code').textContent = '#' + item.id;
  $('metaTime').textContent = formatDateTime(item.created_at);
  $('metaFile').textContent = item.original_name;
  $('metaSize').textContent = formatSize(item.file_size);
  $('metaModel').textContent = item.model_version;       // phiên bản LÚC phân loại, không phải bản hiện tại
  $('metaThreshold').textContent = formatPercent(item.threshold);

  // Cột phải: kết quả
  $('dot').style.setProperty('--h', flower.hue);
  $('nameVi').textContent = flower.name_vi;
  $('nameEn').textContent = flower.name_en + ' · ' + flower.scientific;
  $('pct').textContent = formatPercent(item.confidence);
  $('top3').innerHTML = top3Html(item.top, item.uncertain);
  $('flowerLink').href = '/flowers/' + flower.id;

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
      show('notFound');                                  // id sai hoặc mục đã bị xóa
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
      if (error.status !== 404) {                       // 404 = đã bị xóa từ trước, coi như xong
        showLoadError('Chưa xóa được. ' + error.message);
        return;
      }
    }
    location.href = '/history';                          // xóa xong thì quay về danh sách
  });
}

$('btnDelete').onclick = deleteThis;
loadPrediction();
