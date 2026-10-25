# Anthea

*Gọi đúng tên từng loài hoa.*

Website phân loại 5 loài hoa (cúc họa mi, bồ công anh, hồng, hướng dương, tulip) bằng mạng CNN tự xây với TensorFlow/Keras, giao diện Flask + MySQL.

Đồ án Lập trình ứng dụng 2 – Nhóm 19: Nguyễn Ngọc Mai Hân, Hoàng Ngọc Gia Nghi.

## Cài đặt

Hướng dẫn cho Windows. Gõ lệnh trong PowerShell hoặc terminal của VS Code.

### 1. Cài Python, Git, VS Code

- **Python 3.13 (64-bit)** từ [python.org](https://www.python.org/downloads/windows/). Ở màn hình cài đầu tiên, tick ô **"Add python.exe to PATH"**. Hoặc cài bằng lệnh:
  ```powershell
  winget install Python.Python.3.13 --source winget
  ```
  - Dùng được Python 3.10 – 3.13. **Không dùng 3.14**: TensorFlow 2.21.0 chưa có bản cho 3.14.
  - Kiểm tra: `py --list` phải có dòng `3.13`.
- **Git**, rồi chạy một lần (đổi thành tên và email GitHub của bạn):
  ```powershell
  git config --global user.name "Tên của bạn"
  git config --global user.email "email-github-cua-ban@example.com"
  ```
- **VS Code** và tiện ích **Python** (khuyên dùng).

### 2. Lấy mã nguồn

Đặt dự án ở đường dẫn **không dấu, không dấu cách, không nằm trong OneDrive**, ví dụ `D:\anthea`. Đường dẫn có dấu hoặc thư mục đồng bộ OneDrive dễ gây lỗi khi cài và chạy TensorFlow.

```powershell
cd D:\
git clone https://github.com/maihan88/Anthea.git
cd Anthea
```

### 3. Tạo và bật môi trường ảo (venv)

```powershell
py -3.13 -m venv venv
.\venv\Scripts\Activate.ps1
```

Bật thành công thì đầu dòng lệnh có chữ `(venv)`, ví dụ `(venv) PS D:\anthea>`. Kiểm tra: `python --version` phải ra `Python 3.13.x`.

**Mỗi lần mở terminal mới đều phải bật lại venv** bằng lệnh `Activate.ps1` ở trên. Trong VS Code có thể cho tự bật: `Ctrl+Shift+P` → **Python: Select Interpreter** → chọn `.\venv\Scripts\python.exe`.

### 4. Cài thư viện

```powershell
pip install -r requirements.txt
```

TensorFlow nặng vài trăm MB, nên dùng mạng ổn định. `requirements.txt` ghi đúng phiên bản TensorFlow đang chạy trên Colab (`2.21.0`), không tự đổi: lệch phiên bản thì file mô hình `.keras` train trên Colab có thể không nạp được. Dòng `[notice] A new release of pip is available` chỉ là gợi ý, bỏ qua được.

### 5. Tạo file `.env`

```powershell
Copy-Item .env.example .env
```

Mở `.env`, điền `DB_USER` và `DB_PASSWORD` là tài khoản MySQL tạo ở mục **Chạy web** bước 1 (không dùng `root`). Giữ `USE_FAKE_MODEL=0` để web dùng mô hình thật `models/flower_cnn.keras`.

File `.env` chứa mật khẩu nên **không bao giờ đẩy lên GitHub** (đã có trong `.gitignore`).

### 6. Kiểm tra `model_service`

Chép một ảnh hoa bất kỳ (`.jpg`) vào thư mục gốc dự án, đặt tên `anh_thu.jpg`. Đứng ở thư mục gốc, venv đang bật, chạy:

```powershell
python -c "import sys; sys.path.insert(0,'app'); import model_service as m; print(m.predict(open('anh_thu.jpg','rb').read()))"
```

Cài đặt xong khi lệnh in ra 3 loài kèm độ tin cậy, ví dụ:

```
[{'code': 'tulips', 'confidence': 0.4167}, {'code': 'roses', 'confidence': 0.1687}, {'code': 'dandelion', 'confidence': 0.1522}]
```

Lần chạy đầu mất vài giây để nạp mô hình. Thử xong thì xóa `anh_thu.jpg`, không commit.

### Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách sửa |
| --- | --- | --- |
| `No matching distribution found for tensorflow==2.21.0` (chỉ thấy bản `2.22.0rc0`) | venv tạo bằng Python 3.14, hoặc venv chưa bật nên lệnh `pip` là của Python cài chung | Bật venv rồi chạy `python --version`, phải là 3.10 – 3.13. Sai thì cài Python 3.13, xóa venv cũ (`Remove-Item -Recurse -Force venv`), tạo lại bằng `py -3.13 -m venv venv` |
| `ModuleNotFoundError: No module named 'PIL'` (hoặc `tensorflow`, `dotenv`) | venv chưa bật: đầu dòng lệnh không có `(venv)` | Chạy `.\venv\Scripts\Activate.ps1`, hoặc gọi thẳng `.\venv\Scripts\python.exe` thay cho `python` |
| `running scripts is disabled on this system` khi bật venv | Windows chặn chạy script PowerShell | Chạy một lần `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, chọn `Y` |
| `FileNotFoundError: [Errno 2] No such file or directory: 'anh_thu.jpg'` | Ảnh không nằm trong thư mục đang đứng | Chép ảnh vào thư mục gốc dự án, hoặc ghi đường dẫn đầy đủ bằng dấu `/`, ví dụ `'D:/hinh/hoa.jpg'` (không dùng `\`) |
| `winget` hỏi đồng ý điều khoản của nguồn `msstore` | winget tìm cả trên Microsoft Store | Bấm `N`, chạy lại lệnh cài kèm `--source winget` như ở bước 1 |

## Chạy web

Cần MySQL 8.4 đang chạy (dịch vụ `MySQL84`) và file `.env` đã điền.

### 1. Tạo database và tài khoản cho app (mỗi máy làm một lần)

Mở MySQL Workbench bằng tài khoản `root`, chạy (đổi mật khẩu):

```sql
CREATE DATABASE flower_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'anthea'@'localhost' IDENTIFIED BY 'doi_mat_khau_nay';
GRANT ALL PRIVILEGES ON flower_db.* TO 'anthea'@'localhost';
```

Điền `DB_USER=anthea` và mật khẩu vừa đặt vào `.env`.

### 2. Tạo bảng và dữ liệu loài hoa

```powershell
python app/seed.py
```

Chạy lại bao nhiêu lần cũng được. Mỗi máy một CSDL riêng: lịch sử phân loại không đồng bộ giữa hai máy.

### 3. Chạy web

```powershell
python app/app.py
```

Mở http://127.0.0.1:5000.
