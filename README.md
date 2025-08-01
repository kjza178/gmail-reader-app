# Gmail Reader App

Ứng dụng Flask để đọc mail Gmail với hỗ trợ 2FA và App Password.

## 🚀 Features

- ✅ Đọc mail Gmail qua IMAP
- ✅ Hỗ trợ 2FA (Two-Factor Authentication)
- ✅ Tự động setup 2FA cho Gmail accounts
- ✅ Tạo App Password tự động
- ✅ Web interface đơn giản
- ✅ Logging chi tiết

## 📦 Installation

### Local Development
```bash
pip install -r requirements.txt
python app_simple.py
```

### Server Deployment

#### Railway.app
1. Fork/Clone repository này
2. Đăng ký tại [railway.app](https://railway.app)
3. Connect GitHub repository
4. Deploy tự động

#### Render.com
1. Fork/Clone repository này  
2. Đăng ký tại [render.com](https://render.com)
3. Tạo Web Service
4. Connect GitHub repository
5. Deploy

## 🔧 Configuration

### Environment Variables
- `PORT`: Port để chạy app (mặc định: 5000)
- `SECRET_KEY`: Flask secret key

### Files cần thiết
- `accounts.txt`: Danh sách email|password
- `2fa_backup.json`: Backup 2FA keys (tự động tạo)

## 📱 Usage

1. Truy cập web app
2. Chọn account từ danh sách
3. Login với App Password
4. Đọc mail hoặc setup 2FA

## 🛠️ Development

### Structure
```
gmail_reader_app/
├── app_simple.py              # Main Flask app
├── gmail_security_setup_optimized.py  # 2FA setup automation
├── requirements.txt           # Python dependencies
├── templates/                # HTML templates
├── Procfile                 # Railway deployment
└── runtime.txt              # Python version
```

### Key Components
- **GmailReader**: Class xử lý IMAP và 2FA
- **GmailSecuritySetup**: Class tự động setup 2FA
- **Flask Routes**: Web interface endpoints

## 🔒 Security

- App Password được lưu local
- 2FA keys được backup
- Session management
- Input validation

## 📝 License

MIT License 