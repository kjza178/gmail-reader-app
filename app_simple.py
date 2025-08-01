#!/usr/bin/env python3
"""
Gmail Reader App - Ứng dụng Flask đơn giản để đọc mail IMAP
Tương tự như file index.html hiện có
"""

import os
import json
import time
import pyotp
import imaplib
import email
import re
import sys
import traceback
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import logging

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'gmail_reader_simple_2024'

# Error handling
@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return "Internal server error", 500

@app.errorhandler(404)
def not_found_error(error):
    logger.error(f"Page not found: {error}")
    return "Page not found", 404

class GmailReader:
    def __init__(self):
        self.backup_file = "2fa_backup.json"  # Đọc từ thư mục hiện tại
        self.logs = []
        
    def add_log(self, message):
        """Thêm log message"""
        timestamp = time.strftime('%H:%M:%S')
        self.logs.append(f"[{timestamp}] {message}")
        if len(self.logs) > 50:  # Giữ tối đa 50 logs
            self.logs.pop(0)
        logger.info(message)
        
    def load_2fa_data(self):
        """Load 2FA data từ file backup"""
        try:
            if os.path.exists(self.backup_file):
                with open(self.backup_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.add_log(f"❌ Lỗi load 2FA data: {e}")
            return {}
    
    def get_app_password(self, email_address):
        """Lấy App Password cho email"""
        try:
            backup_data = self.load_2fa_data()
            if email_address in backup_data and 'app_passwords' in backup_data[email_address]:
                app_passwords = backup_data[email_address]['app_passwords']
                if 'Mail' in app_passwords:
                    return app_passwords['Mail']['password']
            return None
        except Exception as e:
            self.add_log(f"❌ Lỗi lấy app password: {e}")
            return None
    
    def get_2fa_key(self, email_address):
        """Lấy 2FA key cho email"""
        try:
            backup_data = self.load_2fa_data()
            if email_address in backup_data and 'setup_key' in backup_data[email_address]:
                return backup_data[email_address]['setup_key']
            return None
        except Exception as e:
            self.add_log(f"❌ Lỗi lấy 2FA key: {e}")
            return None
    
    def generate_totp(self, setup_key):
        """Tạo TOTP code"""
        try:
            totp = pyotp.TOTP(setup_key)
            return totp.now()
        except Exception as e:
            self.add_log(f"❌ Lỗi tạo TOTP: {e}")
            return None
    
    def extract_email_content(self, email_message):
        """Trích xuất nội dung email"""
        content = ""
        
        # Thử lấy text content
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        content = part.get_payload(decode=True).decode()
                        break
                    except:
                        continue
        else:
            try:
                content = email_message.get_payload(decode=True).decode()
            except:
                content = str(email_message.get_payload())
        
        return content
    
    def extract_otp_from_content(self, content):
        """Trích xuất OTP từ nội dung email"""
        if not content:
            return None
            
        # Tìm các pattern OTP phổ biến - CẢI THIỆN
        patterns = [
            # OTP patterns chính xác hơn
            r'\b(\d{6})\b',  # 6 số liên tiếp
            r'\b(\d{4})\b',  # 4 số liên tiếp  
            r'\b(\d{8})\b',  # 8 số liên tiếp
            r'verification code[:\s]*(\d{4,8})',
            r'OTP[:\s]*(\d{4,8})',
            r'code[:\s]*(\d{4,8})',
            r'(\d{4,8})',  # Bất kỳ 4-8 số nào
        ]
        
        # Loại bỏ các số không phải OTP (như năm, ngày tháng)
        exclude_patterns = [
            r'\b(19|20)\d{2}\b',  # Năm 19xx, 20xx
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # Ngày tháng
            r'\b\d{1,2}:\d{2}\b',  # Giờ phút
        ]
        
        # Kiểm tra và loại bỏ các pattern không phải OTP
        for exclude_pattern in exclude_patterns:
            content = re.sub(exclude_pattern, '', content)
        
        # Tìm OTP
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                # Lọc kết quả - chỉ lấy những số có vẻ hợp lý
                for match in matches:
                    otp = str(match)
                    # Kiểm tra xem có phải OTP hợp lệ không
                    if len(otp) >= 4 and len(otp) <= 8:
                        # Loại bỏ các số quá dễ đoán
                        if not (otp.startswith('0000') or otp.startswith('1111') or 
                               otp.startswith('1234') or otp.startswith('9999')):
                            return otp
        
        return None
    
    def clear_logs(self):
        """Clear tất cả logs"""
        self.logs.clear()
        self.add_log("🧹 Đã clear logs")
    
    def read_emails_imap(self, email_address, password, max_emails=10, unread_only=False, clear_logs=True):
        """Đọc emails qua IMAP"""
        try:
            # Clear logs nếu cần
            if clear_logs:
                self.clear_logs()
            
            self.add_log(f"📧 Bắt đầu đọc emails cho: {email_address}")
            if unread_only:
                self.add_log("📬 Chỉ lấy emails chưa đọc")
            
            # Lấy 2FA key và tạo TOTP
            setup_key = self.get_2fa_key(email_address)
            totp_code = None
            if setup_key:
                totp_code = self.generate_totp(setup_key)
                self.add_log(f"🔢 Generated TOTP: {totp_code}")
            
            # Tạo app password nếu cần
            app_password = self.get_app_password(email_address)
            if app_password:
                password = app_password
                self.add_log(f"🔑 Sử dụng App Password cho {email_address}")
            
            # Kết nối IMAP
            imap_server = "imap.gmail.com"
            imap_port = 993
            
            # Tạo connection
            imap_connection = imaplib.IMAP4_SSL(imap_server, imap_port)
            
            # Login
            if app_password:
                imap_connection.login(email_address, password)
                self.add_log(f"✅ Đăng nhập thành công với App Password: {email_address}")
            else:
                # Thử login với password gốc + TOTP
                if totp_code:
                    combined_password = password + totp_code
                    imap_connection.login(email_address, combined_password)
                    self.add_log(f"✅ Đăng nhập thành công với TOTP: {email_address}")
                else:
                    imap_connection.login(email_address, password)
                    self.add_log(f"✅ Đăng nhập thành công: {email_address}")
            
            try:
                # Chọn mailbox INBOX
                imap_connection.select('INBOX')
                
                # Tìm emails - CHỈ LẤY UNREAD NẾU CẦN
                if unread_only:
                    status, messages = imap_connection.search(None, 'UNSEEN')
                    self.add_log("📬 Tìm emails chưa đọc...")
                else:
                    status, messages = imap_connection.search(None, 'ALL')
                    self.add_log("📬 Tìm tất cả emails...")
                
                if status != 'OK':
                    self.add_log("❌ Không thể tìm emails")
                    return
                
                # Lấy danh sách email IDs
                email_ids = messages[0].split()
                if not email_ids:
                    if unread_only:
                        self.add_log("📭 Không có emails chưa đọc")
                    else:
                        self.add_log("📭 Không có emails nào")
                    return
                
                # Lấy emails mới nhất
                latest_emails = email_ids[-max_emails:] if len(email_ids) > max_emails else email_ids
                latest_emails.reverse()  # Mới nhất trước
                
                self.add_log(f"📬 Tìm thấy {len(latest_emails)} emails")
                
                for i, email_id in enumerate(latest_emails, 1):
                    try:
                        # Fetch email
                        status, msg_data = imap_connection.fetch(email_id, '(RFC822)')
                        if status != 'OK':
                            continue
                        
                        # Parse email
                        raw_email = msg_data[0][1]
                        email_message = email.message_from_bytes(raw_email)
                        
                        # Extract thông tin cơ bản
                        subject = decode_header(email_message["subject"])[0][0]
                        if isinstance(subject, bytes):
                            subject = subject.decode()
                        
                        from_addr = decode_header(email_message["from"])[0][0]
                        if isinstance(from_addr, bytes):
                            from_addr = from_addr.decode()
                        
                        date = email_message["date"]
                        
                        # Extract nội dung email
                        content = self.extract_email_content(email_message)
                        
                        # Tìm OTP trong nội dung
                        otp_code = self.extract_otp_from_content(content)
                        
                        # Hiển thị email với phân cách rõ ràng
                        self.add_log("=" * 60)  # Phân cách
                        self.add_log(f"📧 EMAIL {i}: {subject}")
                        self.add_log(f"👤 From: {from_addr}")
                        self.add_log(f"📅 Date: {date}")
                        
                        # Nếu có OTP, highlight
                        if otp_code:
                            self.add_log(f"🔢 OTP FOUND: {otp_code}")
                        
                        # Log nội dung nếu là email quan trọng
                        if any(keyword in subject.lower() for keyword in ['otp', 'verification', 'code', 'security', 'google']):
                            # Cắt nội dung để hiển thị đẹp hơn
                            preview = content[:300].replace('\n', ' ').strip()
                            if len(content) > 300:
                                preview += "..."
                            self.add_log(f"📝 Content: {preview}")
                        
                        self.add_log("=" * 60)  # Phân cách
                        
                    except Exception as e:
                        self.add_log(f"⚠️ Lỗi parse email {email_id}: {e}")
                        continue
                
                self.add_log(f"✅ Hoàn thành đọc {len(latest_emails)} emails")
                
            finally:
                imap_connection.logout()
                
        except Exception as e:
            self.add_log(f"❌ Lỗi đọc emails: {e}")

# Khởi tạo GmailReader
gmail_reader = GmailReader()

def load_accounts():
    """Load danh sách accounts từ file"""
    try:
        accounts = []
        accounts_file = "../accounts.txt"
        if os.path.exists(accounts_file):
            with open(accounts_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            for line in lines:
                line = line.strip()
                if line and '|' in line:
                    parts = line.split('|', 1)
                    if len(parts) == 2:
                        email, password = parts
                        accounts.append([email.strip(), password.strip()])
        
        return accounts
    except Exception as e:
        gmail_reader.add_log(f"❌ Lỗi load accounts: {e}")
        return []

@app.route("/", methods=["GET", "POST"])
def index():
    """Trang chủ"""
    if request.method == "POST" and "action" in request.form:
        if request.form["action"] == "upload":
            # Xử lý upload file
            if "file" in request.files:
                file = request.files["file"]
                if file.filename:
                    gmail_reader.add_log(f"📁 Upload file: {file.filename}")
                    
                    try:
                        # Đọc nội dung file
                        content = file.read().decode('utf-8')
                        lines = content.strip().split('\n')
                        
                        # Parse accounts từ file
                        accounts = []
                        for line in lines:
                            line = line.strip()
                            if line and '|' in line:
                                parts = line.split('|', 1)
                                if len(parts) == 2:
                                    email, password = parts
                                    accounts.append((email.strip(), password.strip()))
                        
                        if accounts:
                            # Lưu vào file accounts.txt
                            accounts_file = "../accounts.txt"
                            with open(accounts_file, 'w', encoding='utf-8') as f:
                                for email, password in accounts:
                                    f.write(f"{email}|{password}\n")
                            
                            gmail_reader.add_log(f"✅ Đã upload {len(accounts)} accounts từ file {file.filename}")
                            gmail_reader.add_log(f"📁 Đã lưu vào: {accounts_file}")
                        else:
                            gmail_reader.add_log("❌ Không tìm thấy accounts hợp lệ trong file")
                            
                    except Exception as e:
                        gmail_reader.add_log(f"❌ Lỗi xử lý file: {e}")
                else:
                    gmail_reader.add_log("❌ Không có file được chọn")
    
    accounts = load_accounts()
    return render_template('index.html', accounts=accounts)

@app.route("/login", methods=["POST"])
def login():
    """Login với account"""
    try:
        account_idx = int(request.form.get("account", 0))
        accounts = load_accounts()
        
        if 0 <= account_idx < len(accounts):
            email, password = accounts[account_idx]
            gmail_reader.add_log(f"🔐 Login với account: {email}")
            
            # Đọc emails (tất cả) - clear logs
            gmail_reader.read_emails_imap(email, password, max_emails=5, unread_only=False, clear_logs=True)
            
            return jsonify({"status": "success"})
        else:
            gmail_reader.add_log("❌ Account index không hợp lệ")
            return jsonify({"status": "error", "message": "Invalid account index"})
            
    except Exception as e:
        gmail_reader.add_log(f"❌ Lỗi login: {e}")
        return jsonify({"status": "error", "message": str(e)})

@app.route("/refresh-unread", methods=["POST"])
def refresh_unread_emails():
    """Refresh unread emails cho account được chọn"""
    try:
        account_idx = int(request.form.get("account", 0))
        accounts = load_accounts()
        
        if 0 <= account_idx < len(accounts):
            email, password = accounts[account_idx]
            gmail_reader.add_log(f"📧 Refresh unread emails cho: {email}")
            
            # Đọc emails chưa đọc cho account này - clear logs
            gmail_reader.read_emails_imap(email, password, max_emails=5, unread_only=True, clear_logs=True)
            
            return jsonify({"status": "success"})
        else:
            gmail_reader.add_log("❌ Account index không hợp lệ")
            return jsonify({"status": "error", "message": "Invalid account index"})
            
    except Exception as e:
        gmail_reader.add_log(f"❌ Lỗi refresh unread: {e}")
        return jsonify({"status": "error", "message": str(e)})

@app.route("/refresh-balanced", methods=["POST"])
def refresh_emails_balanced():
    """Refresh emails cho tất cả accounts - CHỈ LẤY UNREAD"""
    try:
        accounts = load_accounts()
        gmail_reader.add_log(f"🔄 Refresh emails chưa đọc cho {len(accounts)} accounts")
        
        for i, (email, password) in enumerate(accounts):
            gmail_reader.add_log(f"📧 Đang xử lý account {i+1}: {email}")
            # Không clear logs khi refresh tất cả accounts
            gmail_reader.read_emails_imap(email, password, max_emails=5, unread_only=True, clear_logs=False)
            time.sleep(1)  # Delay giữa các accounts
        
        gmail_reader.add_log("✅ Hoàn thành refresh tất cả accounts")
        return jsonify({"status": "success"})
        
    except Exception as e:
        gmail_reader.add_log(f"❌ Lỗi refresh: {e}")
        return jsonify({"status": "error", "message": str(e)})

@app.route("/logout", methods=["POST"])
def logout():
    """Logout"""
    gmail_reader.add_log("👋 Logout")
    return jsonify({"status": "success"})

@app.route("/log")
def get_log():
    """Lấy logs"""
    return jsonify({"logs": gmail_reader.logs})

@app.route("/setup-2fa", methods=["POST"])
def setup_single_2fa():
    """Setup 2FA cho account được chọn - DISABLED ON SERVER"""
    try:
        account_idx = int(request.form.get("account", 0))
        accounts = load_accounts()
        
        if 0 <= account_idx < len(accounts):
            email, password = accounts[account_idx]
            gmail_reader.add_log(f"🔐 Setup 2FA cho: {email}")
            gmail_reader.add_log("⚠️ Browser automation bị disable trên server")
            gmail_reader.add_log("💡 Vui lòng chạy setup 2FA trên local machine")
            
            return jsonify({"status": "error", "message": "Browser automation not available on server"})
        else:
            gmail_reader.add_log("❌ Account index không hợp lệ")
            return jsonify({"status": "error", "message": "Invalid account index"})
            
    except Exception as e:
        gmail_reader.add_log(f"❌ Lỗi setup 2FA: {e}")
        return jsonify({"status": "error", "message": str(e)})

@app.route("/setup-all-2fa", methods=["POST"])
def setup_all_2fa():
    """Setup 2FA cho tất cả accounts - DISABLED ON SERVER"""
    try:
        accounts = load_accounts()
        gmail_reader.add_log(f"🔐 Setup 2FA cho {len(accounts)} accounts")
        gmail_reader.add_log("⚠️ Browser automation bị disable trên server")
        gmail_reader.add_log("💡 Vui lòng chạy setup 2FA trên local machine")
        
        return jsonify({"status": "error", "message": "Browser automation not available on server"})
        
    except Exception as e:
        gmail_reader.add_log(f"❌ Lỗi setup all 2FA: {e}")
        return jsonify({"status": "error", "message": str(e)})

@app.route("/check-2fa-status", methods=["POST"])
def check_2fa_status():
    """Kiểm tra trạng thái 2FA của tất cả accounts"""
    try:
        accounts = load_accounts()
        backup_data = gmail_reader.load_2fa_data()
        
        gmail_reader.add_log("📊 Kiểm tra trạng thái 2FA...")
        
        for i, (email, password) in enumerate(accounts):
            if email in backup_data:
                account_data = backup_data[email]
                if 'setup_key' in account_data and 'app_passwords' in account_data:
                    gmail_reader.add_log(f"✅ {email}: Đã setup 2FA + App Password")
                elif 'setup_key' in account_data:
                    gmail_reader.add_log(f"⚠️ {email}: Có 2FA nhưng chưa có App Password")
                else:
                    gmail_reader.add_log(f"❌ {email}: Chưa setup 2FA")
            else:
                gmail_reader.add_log(f"❌ {email}: Chưa setup 2FA")
        
        gmail_reader.add_log("📊 Hoàn thành kiểm tra trạng thái")
        return jsonify({"status": "success"})
        
    except Exception as e:
        gmail_reader.add_log(f"❌ Lỗi check 2FA status: {e}")
        return jsonify({"status": "error", "message": str(e)})

@app.route("/get-2fa-status")
def get_2fa_status():
    """Lấy trạng thái 2FA cho tất cả accounts để cập nhật UI"""
    try:
        accounts = load_accounts()
        backup_data = gmail_reader.load_2fa_data()
        
        status_data = {}
        for i, (email, password) in enumerate(accounts):
            if email in backup_data:
                account_data = backup_data[email]
                if 'setup_key' in account_data and 'app_passwords' in account_data:
                    status_data[i] = {
                        'status': 'success',
                        'text': '✅ Đã setup',
                        'class': 'status-2fa'
                    }
                elif 'setup_key' in account_data:
                    status_data[i] = {
                        'status': 'warning',
                        'text': '⚠️ Chưa có App Password',
                        'class': 'status-warning'
                    }
                else:
                    status_data[i] = {
                        'status': 'none',
                        'text': '❌ Chưa setup',
                        'class': 'status-none'
                    }
            else:
                status_data[i] = {
                    'status': 'none',
                    'text': '❌ Chưa setup',
                    'class': 'status-none'
                }
        
        return jsonify({"status_data": status_data})
        
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/setup-multi-2fa", methods=["POST"])
def setup_multi_2fa():
    """Setup 2FA cho tất cả accounts với multi-thread - DISABLED ON SERVER"""
    try:
        gmail_reader.add_log("🚀 Setup 2FA multi-thread")
        gmail_reader.add_log("⚠️ Browser automation bị disable trên server")
        gmail_reader.add_log("💡 Vui lòng chạy setup 2FA trên local machine")
        
        return jsonify({"status": "error", "message": "Browser automation not available on server"})
        
    except Exception as e:
        gmail_reader.add_log(f"❌ Lỗi setup multi-thread: {e}")
        return jsonify({"status": "error", "message": str(e)})

@app.route("/check-multi-status")
def check_multi_status():
    """Kiểm tra trạng thái setup multi-thread"""
    try:
        # Đọc log file
        log_file = "multi_setup_2fa.log"
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Lấy 20 dòng cuối
                recent_lines = lines[-20:] if len(lines) > 20 else lines
                return jsonify({
                    "status": "success",
                    "log": recent_lines
                })
        else:
            return jsonify({
                "status": "success", 
                "log": ["Chưa có log file"]
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False) 