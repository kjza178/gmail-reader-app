#!/usr/bin/env python3
"""
Filter Setup Accounts - Lọc ra accounts đã setup và chỉ setup những accounts chưa có 2FA
"""

import json
import os

def load_backup_data():
    """Load dữ liệu từ file backup"""
    backup_file = "../2fa_backup.json"
    try:
        if os.path.exists(backup_file):
            with open(backup_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"❌ Lỗi load backup data: {e}")
        return {}

def load_accounts():
    """Load danh sách accounts"""
    accounts = []
    accounts_file = "../accounts.txt"
    try:
        if os.path.exists(accounts_file):
            with open(accounts_file, 'r', encoding='utf-8') as f:
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
            
            print(f"✅ Đã load {len(accounts)} accounts từ {accounts_file}")
            return accounts
        else:
            print(f"❌ Không tìm thấy file: {accounts_file}")
            return []
            
    except Exception as e:
        print(f"❌ Lỗi load accounts: {e}")
        return []

def check_2fa_status(email, backup_data):
    """Kiểm tra trạng thái 2FA của account"""
    if email in backup_data:
        account_data = backup_data[email]
        if 'setup_key' in account_data and 'app_passwords' in account_data:
            return True, "Đã có 2FA + App Password"
        elif 'setup_key' in account_data:
            return True, "Có 2FA nhưng chưa có App Password"
    
    return False, "Chưa setup 2FA"

def filter_accounts():
    """Lọc accounts theo trạng thái 2FA"""
    print("🔍 Đang lọc accounts theo trạng thái 2FA...")
    print("=" * 60)
    
    # Load data
    backup_data = load_backup_data()
    all_accounts = load_accounts()
    
    if not all_accounts:
        print("❌ Không có accounts nào")
        return
    
    # Phân loại accounts
    setup_complete = []  # Đã có 2FA + App Password
    setup_partial = []   # Có 2FA nhưng chưa có App Password
    not_setup = []       # Chưa setup 2FA
    
    print("📊 Phân loại accounts:")
    print("-" * 60)
    
    for account in all_accounts:
        email = account['email']
        has_2fa, status = check_2fa_status(email, backup_data)
        
        if has_2fa:
            if "App Password" in status:
                setup_complete.append(account)
                print(f"✅ {email}: {status}")
            else:
                setup_partial.append(account)
                print(f"⚠️  {email}: {status}")
        else:
            not_setup.append(account)
            print(f"❌ {email}: {status}")
    
    print("-" * 60)
    print(f"📊 KẾT QUẢ PHÂN LOẠI:")
    print(f"✅ Hoàn thành (2FA + App Password): {len(setup_complete)}")
    print(f"⚠️  Chưa hoàn thành (chỉ có 2FA): {len(setup_partial)}")
    print(f"❌ Chưa setup: {len(not_setup)}")
    print(f"📊 Tổng cộng: {len(all_accounts)}")
    print("=" * 60)
    
    # Tạo file accounts chỉ chứa những accounts chưa setup
    if not_setup:
        not_setup_file = "accounts_not_setup.txt"  # Lưu vào thư mục hiện tại
        try:
            with open(not_setup_file, 'w', encoding='utf-8') as f:
                for account in not_setup:
                    f.write(f"{account['email']}|{account['password']}\n")
            
            print(f"💾 Đã lưu {len(not_setup)} accounts chưa setup vào: {not_setup_file}")
            print("📝 Danh sách accounts chưa setup:")
            for i, account in enumerate(not_setup, 1):
                print(f"{i:2d}. {account['email']}")
        except Exception as e:
            print(f"❌ Lỗi lưu file: {e}")
    else:
        print("🎉 Tất cả accounts đã được setup!")
    
    # Tạo file accounts chỉ chứa những accounts cần App Password
    if setup_partial:
        partial_file = "accounts_need_app_password.txt"  # Lưu vào thư mục hiện tại
        try:
            with open(partial_file, 'w', encoding='utf-8') as f:
                for account in setup_partial:
                    f.write(f"{account['email']}|{account['password']}\n")
            
            print(f"💾 Đã lưu {len(setup_partial)} accounts cần App Password vào: {partial_file}")
            print("📝 Danh sách accounts cần App Password:")
            for i, account in enumerate(setup_partial, 1):
                print(f"{i:2d}. {account['email']}")
        except Exception as e:
            print(f"❌ Lỗi lưu file: {e}")
    
    # Tạo file accounts đã hoàn thành
    if setup_complete:
        complete_file = "accounts_complete.txt"  # Lưu vào thư mục hiện tại
        try:
            with open(complete_file, 'w', encoding='utf-8') as f:
                for account in setup_complete:
                    f.write(f"{account['email']}|{account['password']}\n")
            
            print(f"💾 Đã lưu {len(setup_complete)} accounts hoàn thành vào: {complete_file}")
        except Exception as e:
            print(f"❌ Lỗi lưu file: {e}")
    
    print("=" * 60)
    print("🎯 KHUYẾN NGHỊ:")
    if not_setup:
        print(f"🚀 Chạy setup cho {len(not_setup)} accounts chưa setup:")
        print(f"   python multi_setup_2fa.py --accounts accounts_not_setup.txt")
    if setup_partial:
        print(f"🔑 Tạo App Password cho {len(setup_partial)} accounts:")
        print(f"   python create_app_passwords.py --accounts accounts_need_app_password.txt")
    if setup_complete:
        print(f"✅ {len(setup_complete)} accounts đã hoàn thành, có thể sử dụng ngay!")

def main():
    """Main function"""
    print("🔍 Filter Setup Accounts")
    print("=" * 50)
    
    filter_accounts()

if __name__ == "__main__":
    main() 