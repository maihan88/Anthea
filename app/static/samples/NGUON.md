# Ảnh mẫu

Mỗi loài 4 ảnh, Hân tự tải trên mạng (thay bộ ảnh TF Flowers cũ ngày 13/11/2026). Ảnh `(1)` làm ảnh bìa trong
Thư viện hoa; nút "Thử với ảnh mẫu" ở trang Nhận diện chọn ngẫu nhiên một ảnh ở đây (kiểm thử mức L1).
Trang chủ dùng `sunflowers/sunflower(3).jpg`, `tulips/tulip(1).jpg`, `daisy/daisy(1).jpg`.

Người phụ trách: Hân

## Kết quả mô hình v1-khac (đo ngày 13/11/2026)

Đúng **12/20** ảnh. Các ảnh `(1)` là ảnh trang trí (vẽ thêm tim, sao, viền trắng), khác xa ảnh chụp thật dùng để
train, nên mô hình hay nhận sai.

| File | Kết quả | Đúng? |
| --- | --- | --- |
| daisy/daisy(1).jpg | Cúc họa mi 97,3% | ✓ |
| daisy/daisy(2).jpg | Cúc họa mi 98,9% | ✓ |
| daisy/daisy(3).jpg | Cúc họa mi 99,6% | ✓ |
| daisy/daisy(4).jpg | Tulip 52,5% | ✗ |
| dandelion/dandelion(1).jpg | Tulip 41,2% | ✗ |
| dandelion/dandelion(2).jpg | Bồ công anh 98,7% | ✓ |
| dandelion/dandelion(3).jpg | Khác 57,4% | ✗ |
| dandelion/dandelion(4).jpg | Bồ công anh 80,8% | ✓ |
| roses/roses(1).jpg | Hướng dương 70,8% | ✗ |
| roses/roses(2).jpg | Hoa hồng 74,6% | ✓ |
| roses/roses(3).jpg | Tulip 87,3% | ✗ |
| roses/roses(4).jpg | Khác 39,1% | ✗ |
| sunflowers/sunflower(1).jpg | Tulip 59,1% | ✗ |
| sunflowers/sunflower(2).jpg | Hướng dương 46,5% (dưới ngưỡng 0,5) | ✓ |
| sunflowers/sunflower(3).jpg | Hướng dương 100% | ✓ |
| sunflowers/sunflower(4).jpg | Hướng dương 100% | ✓ |
| tulips/tulip(1).jpg | Khác 61,7% | ✗ |
| tulips/tulip(2).jpg | Tulip 97,1% | ✓ |
| tulips/tulip(3).jpg | Tulip 99,9% | ✓ |
| tulips/tulip(4).jpg | Tulip 76,3% | ✓ |

## Nguồn ảnh

TODO (Hân): điền link gốc và giấy phép của từng ảnh.

| File | Ảnh gốc | Giấy phép |
| --- | --- | --- |
| daisy/daisy(1).jpg | | |
| daisy/daisy(2).jpg | | |
| daisy/daisy(3).jpg | | |
| daisy/daisy(4).jpg | | |
| dandelion/dandelion(1).jpg | | |
| dandelion/dandelion(2).jpg | | |
| dandelion/dandelion(3).jpg | | |
| dandelion/dandelion(4).jpg | | |
| roses/roses(1).jpg | | |
| roses/roses(2).jpg | | |
| roses/roses(3).jpg | | |
| roses/roses(4).jpg | | |
| sunflowers/sunflower(1).jpg | | |
| sunflowers/sunflower(2).jpg | | |
| sunflowers/sunflower(3).jpg | | |
| sunflowers/sunflower(4).jpg | | |
| tulips/tulip(1).jpg | | |
| tulips/tulip(2).jpg | | |
| tulips/tulip(3).jpg | | |
| tulips/tulip(4).jpg | | |
