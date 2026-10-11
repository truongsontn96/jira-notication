# Jira Alert Monitor

Ứng dụng Windows giám sát Jira tickets và phát cảnh báo qua loa khi có tickets khớp với rules đã thiết lập.

## Tính năng

✅ **Kết nối Jira Cloud/Server**
- Hỗ trợ Jira Cloud và Jira Server
- Xác thực qua API Token
- Test connection trước khi lưu

✅ **Thiết lập Alert Rules**
- Tùy chỉnh rules bằng JQL (Jira Query Language)
- Bật/tắt từng rule riêng biệt
- Hỗ trợ nhiều rules chạy đồng thời

✅ **Text-to-Speech tùy chỉnh**
- Template với variables: `{ticket_key}`, `{summary}`, `{priority}`, `{status}`, `{assignee}`
- Hỗ trợ nhiều ngôn ngữ: Tiếng Việt, English, 日本語, 한국어, 中文
- Điều chỉnh tốc độ phát (50% - 300%)

✅ **Chạy background**
- Minimize to system tray
- Notifications popup khi có alert
- Activity log chi tiết

✅ **Build thành .exe**
- Portable, không cần cài Python
- Double-click là chạy

---

## Cài đặt (Development)

### Yêu cầu
- Python 3.8+
- Windows 10/11

### Bước 1: Clone/Download project

```bash
cd jira-alert-app
```

### Bước 2: Tạo virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

### Bước 3: Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### Bước 4: Chạy app

```bash
python main.py
```

---

## Build thành .exe

### Trên Windows:

```bash
# Activate venv
venv\Scripts\activate

# Build
build_exe.bat
```

File `.exe` sẽ ở: `dist/JiraAlertMonitor.exe`

### Manual build:

```bash
pyinstaller --onefile --windowed --name "JiraAlertMonitor" main.py
```

---

## Hướng dẫn sử dụng

### 1. Cấu hình Jira Connection

**Tab "Jira Connection":**

1. **Jira URL**: Nhập URL Jira của bạn
   - Ví dụ: `https://yourcompany.atlassian.net`
   
2. **Email**: Email đăng nhập Jira

3. **API Token**: 
   - Tạo tại: https://id.atlassian.com/manage-profile/security/api-tokens
   - Click "Create API token" → Copy token

4. **Check Interval**: Khoảng thời gian kiểm tra (giây)
   - Mặc định: 60 giây

5. Click **"Test Connection"** để kiểm tra kết nối

6. Click **"Save Settings"**

---

### 2. Thiết lập Alert Rules

**Tab "Alert Rules":**

Click **"Add New Rule"** để tạo rule mới:

#### Ví dụ Rules:

**Rule 1: High priority tickets chưa assign**
```
Rule Name: High Priority Unassigned
JQL: priority = High AND assignee is EMPTY AND status != Done
TTS Template: Cảnh báo: Ticket {ticket_key} chưa có người xử lý, priority {priority}
```

**Rule 2: Bugs trong project**
```
Rule Name: Critical Bugs
JQL: project = MYPROJ AND type = Bug AND priority = Critical
TTS Template: Có bug critical: {ticket_key}, {summary}
```

**Rule 3: Tickets assigned cho tôi**
```
Rule Name: My High Priority Tasks
JQL: assignee = currentUser() AND priority in (High, Critical) AND status = Open
TTS Template: Bạn có task mới: {ticket_key}, {summary}
```

**Rule 4: Tickets updated hôm nay**
```
Rule Name: Today Updates
JQL: project = MYPROJ AND updated >= startOfDay()
TTS Template: Ticket {ticket_key} vừa được cập nhật
```

#### JQL Cheatsheet:

| Filter | Syntax |
|--------|--------|
| Project | `project = PROJ` |
| Status | `status = "In Progress"` |
| Priority | `priority in (High, Critical)` |
| Assignee | `assignee = currentUser()` hoặc `assignee is EMPTY` |
| Type | `type = Bug` |
| Created | `created >= -7d` (7 ngày qua) |
| Updated | `updated >= startOfDay()` |
| Multiple | `project = PROJ AND status = Open AND assignee = currentUser()` |

Xem thêm: https://support.atlassian.com/jira-service-management-cloud/docs/use-advanced-search-with-jira-query-language-jql/

---

### 3. Cấu hình TTS

**Tab "TTS Settings":**

1. **Language**: Chọn ngôn ngữ phát
   - `vi` - Tiếng Việt
   - `en` - English
   - `ja` - 日本語
   - `ko` - 한국어
   - `zh-CN` - 中文

2. **Speed**: Tốc độ phát (50% - 300%)
   - 100% = bình thường
   - 150% = nhanh hơn 50%

3. **Template Variables**:
   - `{ticket_key}` - Ticket ID (VD: PROJ-123)
   - `{summary}` - Tóm tắt ticket
   - `{priority}` - Priority level
   - `{status}` - Trạng thái hiện tại
   - `{assignee}` - Người được assign

**Ví dụ templates:**
```
Cảnh báo: {ticket_key}, {summary}, priority {priority}
Ticket {ticket_key} đang ở trạng thái {status}
{assignee} có ticket mới: {ticket_key}
```

---

### 4. Chạy Monitor

1. Click **"Start Monitoring"**
2. App sẽ kiểm tra Jira theo interval đã cấu hình
3. Khi có ticket khớp rule → phát cảnh báo qua loa
4. Click **"Test Alert"** để test trước

---

### 5. Minimize to Tray

- Click **X** (đóng window) → app minimize to system tray
- Double-click icon tray → mở lại window
- Right-click icon tray → **Quit** để thoát hoàn toàn

---

## Troubleshooting

### 1. Không kết nối được Jira

**Lỗi 401 Unauthorized:**
- Kiểm tra email và API token
- Tạo lại API token mới

**Lỗi 404:**
- Kiểm tra Jira URL (có thể thiếu `https://`)

### 2. Không nghe thấy âm thanh

- Kiểm tra volume hệ thống
- Kiểm tra speaker/headphone đã cắm chưa
- Click **"Test Alert"** để test

### 3. JQL query không chạy

- Dùng **Test Connection** để verify connection
- Test JQL trực tiếp trong Jira UI trước:
  - Jira → **Filters** → **Advanced search**
  - Paste JQL query → Enter

### 4. Build .exe bị lỗi

```bash
# Cài lại PyInstaller
pip uninstall pyinstaller
pip install pyinstaller==6.3.0

# Build lại
build_exe.bat
```

---

## Cấu trúc thư mục

```
jira-alert-app/
├── main.py                 # Source code chính
├── requirements.txt        # Python dependencies
├── build_exe.bat          # Build script (Windows)
├── README.md              # Tài liệu này
├── config/
│   └── settings.json      # Cấu hình (auto-generated)
├── logs/
│   └── app.log           # Application logs
└── dist/
    └── JiraAlertMonitor.exe  # Executable (sau khi build)
```

---

## Config File Format

File `config/settings.json`:

```json
{
  "jira_url": "https://yourcompany.atlassian.net",
  "jira_email": "your.email@company.com",
  "jira_api_token": "YOUR_TOKEN_HERE",
  "check_interval": 60,
  "jira_enabled": false,
  "tts_lang": "vi",
  "tts_speed": 1.5,
  "rules": [
    {
      "enabled": true,
      "name": "High Priority Unassigned",
      "jql": "priority = High AND assignee is EMPTY",
      "tts_template": "Cảnh báo: {ticket_key}, {summary}"
    }
  ]
}
```

---

## Tips & Best Practices

1. **Check Interval:**
   - Không nên < 30 giây (tránh spam Jira API)
   - 60-120 giây là hợp lý

2. **JQL Rules:**
   - Test JQL trong Jira UI trước khi dùng
   - Dùng `AND` để combine conditions
   - Dùng `is EMPTY` thay vì `= null`

3. **TTS Template:**
   - Giữ ngắn gọn (< 30 từ)
   - Ưu tiên thông tin quan trọng (ticket_key, priority)

4. **System Tray:**
   - App có thể chạy background suốt ngày
   - Chỉ hiện notification khi có alert

---

## License

MIT License - Free to use and modify

## Support

Có vấn đề? Tạo issue hoặc liên hệ team.
