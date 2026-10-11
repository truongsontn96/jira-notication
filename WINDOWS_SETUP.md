# QUICK START GUIDE - Windows
# ===========================

## Bạn đang gặp lỗi PowerShell Execution Policy

### Giải pháp 1: Chạy lệnh đơn giản (KHUYẾN NGHỊ)

Mở PowerShell trong thư mục `jira-alert-app`, chạy từng lệnh:

```powershell
# 1. Tạo virtual environment
python -m venv venv

# 2. Cài đặt packages
.\venv\Scripts\python.exe -m pip install -r requirements.txt

# 3. Chạy app
.\venv\Scripts\python.exe main.py
```

### Giải pháp 2: Dùng setup script

```powershell
# Chạy PowerShell as Administrator, rồi chạy:
powershell -ExecutionPolicy Bypass -File setup.ps1

# Sau đó chạy app:
.\venv\Scripts\python.exe main.py
```

### Giải pháp 3: Bật ExecutionPolicy vĩnh viễn (cần Admin)

```powershell
# Run PowerShell as Administrator
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

# Sau đó chạy bình thường
.\setup.ps1
.\run.ps1
```

---

## Nếu không có Python trên Windows

Download và cài Python: https://www.python.org/downloads/

✅ Tick: "Add Python to PATH"

---

## Build .exe (sau khi setup xong)

```powershell
# Activate venv
.\venv\Scripts\activate

# Build
pyinstaller --onefile --windowed --name "JiraAlertMonitor" main.py

# File .exe sẽ ở: dist\JiraAlertMonitor.exe
```

---

## Troubleshooting

### Lỗi: python không được nhận diện
- Cài Python và tick "Add to PATH"
- Hoặc dùng `py` thay vì `python`:
  ```powershell
  py -m venv venv
  ```

### Lỗi: pip install failed
```powershell
# Upgrade pip trước
.\venv\Scripts\python.exe -m pip install --upgrade pip

# Rồi cài lại
.\venv\Scripts\pip.exe install -r requirements.txt
```

### Lỗi: PyQt5 không cài được
```powershell
# Cài từng package riêng
.\venv\Scripts\pip.exe install PyQt5
.\venv\Scripts\pip.exe install requests gTTS pygame
```
