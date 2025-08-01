# Gmail Reader App

Ứng dụng Flask để đọc emails Gmail qua IMAP với hỗ trợ 2FA và App Password.

## 🚀 Tính năng

- ✅ **Đọc emails qua IMAP** - Kết nối trực tiếp với Gmail IMAP
- ✅ **Hỗ trợ 2FA** - Tự động xử lý 2-Step Verification
- ✅ **App Password** - Sử dụng App Password cho kết nối an toàn
- ✅ **Web Interface** - Giao diện web đẹp và dễ sử dụng
- ✅ **Real-time** - Auto refresh emails mỗi 30 giây
- ✅ **Multi-account** - Hỗ trợ nhiều tài khoản Gmail

## 📋 Yêu cầu

- Python 3.8+
- Gmail account với 2FA đã setup
- App Password đã tạo (khuyến nghị)

## 🛠️ Cài đặt

1. **Clone hoặc tạo thư mục:**
```bash
cd gmail_reader_app
```

2. **Cài đặt dependencies:**
```bash
pip install -r requirements.txt
```

3. **Chuẩn bị files:**
- Đảm bảo có file `../accounts.txt` với format: `email|password`
- Đảm bảo có file `../2fa_backup.json` với thông tin 2FA

## 🚀 Chạy ứng dụng

```bash
python app.py
```

Truy cập: http://localhost:5000

## 📁 Cấu trúc thư mục

```
gmail_reader_app/
├── app.py                 # Main Flask app
├── requirements.txt       # Python dependencies
├── README.md             # Hướng dẫn
└── templates/
    ├── base.html         # Base template
    ├── index.html        # Trang chủ
    ├── emails.html       # Trang emails
    └── accounts.html     # Trang quản lý accounts
```

## 🔧 Cấu hình

### File accounts.txt
```
email1@gmail.com|password1
email2@gmail.com|password2
```

### File 2fa_backup.json
```json
{
  "email@gmail.com": {
    "setup_key": "ABCDEFGHIJKLMNOP",
    "app_passwords": {
      "Mail": {
        "password": "abcd efgh ijkl mnop",
        "created_at": "2024-01-01 12:00:00"
      }
    }
  }
}
```

## 🎯 Sử dụng

1. **Đăng nhập:** Nhập email và password
2. **Xem emails:** Tự động load 20 emails mới nhất
3. **Refresh:** Click nút refresh hoặc auto refresh mỗi 30s
4. **Load more:** Click "Load More" để tải thêm emails

## 🔐 Bảo mật

- Sử dụng App Password thay vì password gốc
- Session-based authentication
- Không lưu password trong database
- Tự động logout sau khi đóng browser

## 🐛 Troubleshooting

### Lỗi kết nối IMAP
- Kiểm tra App Password đã tạo chưa
- Kiểm tra 2FA đã setup chưa
- Kiểm tra "Less secure app access" đã bật chưa

### Lỗi 2FA
- Đảm bảo setup_key trong 2fa_backup.json đúng
- Kiểm tra TOTP code được generate đúng

### Lỗi App Password
- Tạo lại App Password nếu cần
- Kiểm tra format trong 2fa_backup.json

## 📞 Hỗ trợ

Nếu gặp vấn đề, kiểm tra:
1. Logs trong console
2. File 2fa_backup.json có đúng format không
3. App Password có hoạt động không
4. 2FA setup có thành công không

## 🔄 Cập nhật

Để cập nhật:
```bash
git pull
pip install -r requirements.txt
```

## 📄 License

MIT License - Tự do sử dụng và chỉnh sửa. 