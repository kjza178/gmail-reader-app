#!/usr/bin/env python3
"""
Multi-Thread 2FA Setup - Setup 2FA cho nhiều accounts cùng lúc
Sử dụng threading để tăng tốc độ setup
"""

import threading
import time
import os
import sys
import json
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
import logging

# Import trực tiếp từ cùng thư mục
try:
    from gmail_security_setup_optimized import GmailSecuritySetup
except ImportError:
    print("❌ Không tìm thấy gmail_security_setup_optimized.py")
    print(f"📁 Thư mục hiện tại: {os.getcwd()}")
    print(f"📁 Thư mục script: {os.path.dirname(os.path.abspath(__file__))}")
    sys.exit(1)

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('multi_setup_2fa.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MultiSetup2FA:
    def __init__(self, max_workers=3, accounts_file=None):
        self.max_workers = max_workers
        self.results = {}
        self.lock = threading.Lock()
        self.backup_file = "../2fa_backup.json"
        self.accounts_file = accounts_file or "../accounts.txt"  # Mặc định đọc từ thư mục cha
        
    def load_accounts(self):
        """Load accounts từ file"""
        accounts = []
        
        try:
            if os.path.exists(self.accounts_file):
                with open(self.accounts_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                for line in lines:
                    line = line.strip()
                    if line and '|' in line:
                        parts = line.split('|', 1)
                        if len(parts) == 2:
                            email, password = parts
                            accounts.append({
                                'email': email.strip(),
                                'password': password.strip()
                            })
                
                logger.info(f"✅ Đã load {len(accounts)} accounts từ {self.accounts_file}")
                return accounts
            else:
                logger.error(f"❌ Không tìm thấy file: {self.accounts_file}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Lỗi load accounts: {e}")
            return []
    
    def check_existing_2fa(self, email):
        """Kiểm tra xem account đã có 2FA chưa"""
        try:
            if os.path.exists(self.backup_file):
                with open(self.backup_file, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
                
                if email in backup_data:
                    account_data = backup_data[email]
                    if 'setup_key' in account_data and 'app_passwords' in account_data:
                        return True, "Đã có 2FA + App Password"
                    elif 'setup_key' in account_data:
                        return True, "Có 2FA nhưng chưa có App Password"
            
            return False, "Chưa setup 2FA"
            
        except Exception as e:
            logger.error(f"❌ Lỗi check 2FA cho {email}: {e}")
            return False, "Lỗi kiểm tra"
    
    def setup_single_account(self, account):
        """Setup 2FA cho 1 account"""
        email = account['email']
        password = account['password']
        
        try:
            logger.info(f"🔐 Bắt đầu setup cho: {email}")
            
            # Kiểm tra xem đã có 2FA chưa
            has_2fa, status = self.check_existing_2fa(email)
            if has_2fa:
                logger.info(f"✅ {email}: {status}")
                with self.lock:
                    self.results[email] = {
                        'status': 'skipped',
                        'message': status,
                        'timestamp': time.strftime('%H:%M:%S')
                    }
                return
            
            # Tạo setup instance
            setup = GmailSecuritySetup()
            
            try:
                # Setup driver (headless)
                if not setup.setup_driver(headless=True):
                    logger.error(f"❌ Không thể khởi tạo browser cho {email}")
                    with self.lock:
                        self.results[email] = {
                            'status': 'error',
                            'message': 'Browser initialization failed',
                            'timestamp': time.strftime('%H:%M:%S')
                        }
                    return
                
                # Chạy setup hoàn chỉnh
                if setup.run_complete_setup(email, password):
                    logger.info(f"✅ Setup thành công: {email}")
                    with self.lock:
                        self.results[email] = {
                            'status': 'success',
                            'message': 'Setup thành công',
                            'timestamp': time.strftime('%H:%M:%S')
                        }
                else:
                    logger.error(f"❌ Setup thất bại: {email}")
                    with self.lock:
                        self.results[email] = {
                            'status': 'error',
                            'message': 'Setup thất bại',
                            'timestamp': time.strftime('%H:%M:%S')
                        }
                
            finally:
                # Đóng browser
                try:
                    setup.close()
                except:
                    pass
                
        except Exception as e:
            logger.error(f"❌ Lỗi setup {email}: {e}")
            with self.lock:
                self.results[email] = {
                    'status': 'error',
                    'message': str(e),
                    'timestamp': time.strftime('%H:%M:%S')
                }
    
    def run_multi_setup(self):
        """Chạy setup multi-thread"""
        accounts = self.load_accounts()
        if not accounts:
            logger.error("❌ Không có accounts nào để setup")
            return
        
        logger.info(f"🚀 Bắt đầu setup 2FA cho {len(accounts)} accounts với {self.max_workers} threads")
        logger.info("=" * 60)
        
        # Hiển thị danh sách accounts
        for i, account in enumerate(accounts, 1):
            has_2fa, status = self.check_existing_2fa(account['email'])
            status_icon = "✅" if has_2fa else "❌"
            logger.info(f"{i:2d}. {status_icon} {account['email']} - {status}")
        
        logger.info("=" * 60)
        
        # Chạy setup với ThreadPoolExecutor
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit tất cả tasks
            future_to_account = {
                executor.submit(self.setup_single_account, account): account 
                for account in accounts
            }
            
            # Theo dõi progress
            completed = 0
            for future in as_completed(future_to_account):
                account = future_to_account[future]
                completed += 1
                
                try:
                    # Kết quả đã được lưu trong setup_single_account
                    logger.info(f"📊 Progress: {completed}/{len(accounts)} - {account['email']}")
                except Exception as e:
                    logger.error(f"❌ Lỗi xử lý {account['email']}: {e}")
        
        # Hiển thị kết quả
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info("=" * 60)
        logger.info("📊 KẾT QUẢ SETUP:")
        logger.info("=" * 60)
        
        success_count = 0
        error_count = 0
        skipped_count = 0
        
        for email, result in self.results.items():
            status_icon = {
                'success': '✅',
                'error': '❌',
                'skipped': '⏭️'
            }.get(result['status'], '❓')
            
            logger.info(f"{status_icon} {email}: {result['message']} ({result['timestamp']})")
            
            if result['status'] == 'success':
                success_count += 1
            elif result['status'] == 'error':
                error_count += 1
            elif result['status'] == 'skipped':
                skipped_count += 1
        
        logger.info("=" * 60)
        logger.info(f"⏱️  Thời gian: {duration:.2f} giây")
        logger.info(f"✅ Thành công: {success_count}")
        logger.info(f"❌ Thất bại: {error_count}")
        logger.info(f"⏭️  Bỏ qua: {skipped_count}")
        logger.info(f"📊 Tổng cộng: {len(accounts)} accounts")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Multi-Thread 2FA Setup')
    parser.add_argument('--threads', type=int, default=3, help='Số threads (mặc định 3)')
    parser.add_argument('--accounts', type=str, help='File accounts tùy chỉnh')
    parser.add_argument('--filter', action='store_true', help='Chỉ setup accounts chưa có 2FA')
    
    args = parser.parse_args()
    
    print("🚀 Multi-Thread 2FA Setup")
    print("=" * 50)
    
    # Nếu có flag --filter, chạy filter trước
    if args.filter:
        print("🔍 Đang lọc accounts chưa setup...")
        try:
            from filter_setup_accounts import filter_accounts # type: ignore
            filter_accounts()
            print("✅ Đã lọc xong, sử dụng file accounts_not_setup.txt")
            args.accounts = "accounts_not_setup.txt"  # Sử dụng file local
        except ImportError:
            print("❌ Không tìm thấy filter_setup_accounts.py")
            return
    
    # Tạo và chạy multi setup
    multi_setup = MultiSetup2FA(
        max_workers=args.threads,
        accounts_file=args.accounts
    )
    multi_setup.run_multi_setup()

if __name__ == "__main__":
    main() 