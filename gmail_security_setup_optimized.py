#!/usr/bin/env python3
"""
Gmail Security Setup - Tự động setup 2FA và tạo App Password cho Gmail
FLOW TỐI ƯU:
1. Login Gmail
2. Kiểm tra 2FA status  
3. Setup 2FA (nếu cần)
4. Tạo App Password
5. Lưu kết quả
"""

import time
import os
import json
import qrcode
import base64
import pyotp
import cv2
from pyzbar import pyzbar
import re
import string
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc

class GmailSecuritySetup:
    def __init__(self):
        self.driver = None
        self.current_email = None
        self.setup_key = None
        self.app_password = None
        
    def setup_driver(self, headless=False):
        """Setup Chrome driver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")
            
            if headless:
                chrome_options.add_argument("--headless")
                print("🤖 Chạy ở chế độ headless")
            else:
                print("👁️  Chạy ở chế độ hiển thị browser")
            
            self.driver = uc.Chrome(options=chrome_options, version_main=131)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("✅ Đã setup Chrome driver")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi setup driver: {e}")
            return False
    
    def login_gmail(self, email: str, password: str) -> bool:
        """Login vào Gmail với delay tối ưu"""
        try:
            print(f"🔐 Đang login: {email}")
            
            # Mở Gmail
            self.driver.get("https://accounts.google.com/signin")
            time.sleep(2)
            
            # Nhập email
            email_input = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "identifierId"))
            )
            email_input.clear()
            time.sleep(0.5)
            email_input.send_keys(email)
            time.sleep(0.5)
            
            # Click Next
            next_button = WebDriverWait(self.driver, 8).until(
                EC.element_to_be_clickable((By.ID, "identifierNext"))
            )
            next_button.click()
            time.sleep(3)
            
            # Nhập password
            password_input = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.NAME, "Passwd"))
            )
            password_input.clear()
            time.sleep(0.5)
            password_input.send_keys(password)
            time.sleep(0.5)
            
            # Click Next
            password_next = WebDriverWait(self.driver, 8).until(
                EC.element_to_be_clickable((By.ID, "passwordNext"))
            )
            password_next.click()
            time.sleep(5)
            
            # Kiểm tra button "Tôi hiểu" nếu có
            try:
                confirm_btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "confirm"))
                )
                confirm_btn.click()
                print("⚠️  Đã bấm 'Tôi hiểu'")
                time.sleep(2)
            except:
                print("✅ Không có xác minh 'Tôi hiểu'")
            
            # Kiểm tra 2FA challenge
            if "challenge/totp" in self.driver.current_url:
                print("🔐 Phát hiện 2FA challenge, đang xử lý...")
                return self.handle_2fa_challenge(email)
            
            # Kiểm tra CAPTCHA
            try:
                captcha_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'captcha') or contains(@class, 'Captcha') or contains(@class, 'recaptcha')]")
                if captcha_elements:
                    print("⚠️  Phát hiện CAPTCHA, cần xử lý thủ công")
                    print("🔍 Vui lòng hoàn thành CAPTCHA và nhấn Enter để tiếp tục...")
                    input()
            except:
                pass
            
            # Kiểm tra login thành công
            print(f"🔍 URL sau khi login: {self.driver.current_url}")
            if "mail.google.com" in self.driver.current_url or "myaccount.google.com" in self.driver.current_url:
                print(f"✅ Đã login thành công: {email}")
                self.current_email = email
                return True
            else:
                print(f"❌ Login thất bại: {email}")
                return False
                
        except Exception as e:
            print(f"❌ Lỗi login: {e}")
            return False
    
    def handle_2fa_challenge(self, email: str) -> bool:
        """Xử lý 2FA challenge tự động"""
        try:
            print("🔐 Đang xử lý 2FA challenge...")
            
            # Load 2FA data
            backup_data = self.load_2fa_data()
            if email not in backup_data or 'setup_key' not in backup_data[email]:
                print("❌ Không tìm thấy 2FA key cho", email)
                return False
            
            setup_key = backup_data[email]['setup_key']
            print(f"✅ Tìm thấy 2FA key cho {email}")
            
            # Generate TOTP
            totp = pyotp.TOTP(setup_key)
            code = totp.now()
            print(f"🔢 Generated TOTP: {code}")
            
            # Nhập code
            code_input = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.NAME, "totpPin"))
            )
            code_input.clear()
            time.sleep(0.5)
            code_input.send_keys(code)
            time.sleep(0.5)
            
            # Click Next
            next_button = WebDriverWait(self.driver, 8).until(
                EC.element_to_be_clickable((By.ID, "totpNext"))
            )
            next_button.click()
            time.sleep(5)
            
            print(f"🔍 URL sau khi 2FA: {self.driver.current_url}")
            if "myaccount.google.com" in self.driver.current_url:
                print(f"✅ Đã login thành công với 2FA: {email}")
                self.current_email = email
                return True
            else:
                print(f"❌ 2FA thất bại: {email}")
                return False
                
        except Exception as e:
            print(f"❌ Lỗi 2FA: {e}")
            return False
    
    def go_to_2fa_settings(self):
        """Đi đến trang 2FA settings"""
        try:
            print("🔧 Đang mở 2FA settings...")
            self.driver.get("https://myaccount.google.com/signinoptions/twosv")
            time.sleep(3)
            print(f"✅ Đã mở trang: {self.driver.current_url}")
            return True
        except Exception as e:
            print(f"❌ Lỗi mở 2FA settings: {e}")
            return False
    
    def check_2fa_status(self) -> str:
        """Kiểm tra trạng thái 2FA - trả về 'turn_on', 'turn_off', 'unknown', 'error'"""
        try:
            if not self.go_to_2fa_settings():
                return "error"
            
            print("🔍 Check text Turn on/Turn off...")
            page_text = self.driver.page_source.lower()
            
            if "turn off 2-step verification" in page_text:
                print("✅ Tìm thấy: 'Turn off 2-Step Verification'")
                return "turn_off"
            elif "turn on 2-step verification" in page_text:
                print("✅ Tìm thấy: 'Turn on 2-Step Verification'")
                return "turn_on"
            else:
                print("⚠️  Không tìm thấy text Turn on/Turn off")
                return "unknown"
                
        except Exception as e:
            print(f"❌ Lỗi check 2FA status: {e}")
            return "error"
    
    def setup_google_authenticator(self) -> bool:
        """Setup Google Authenticator"""
        try:
            print("🔐 Đang setup Google Authenticator...")
            
            # Đi đến trang authenticator
            self.driver.get("https://myaccount.google.com/two-step-verification/authenticator")
            time.sleep(3)
            print(f"✅ Đã mở trang: {self.driver.current_url}")
            
            # Tìm và click "Set up authenticator"
            setup_selectors = [
                "//button[contains(text(), 'Set up authenticator')]",
                "//span[contains(text(), 'Set up authenticator')]",
                "//button[contains(text(), 'Get started')]",
                "//button[contains(text(), 'Start setup')]",
                "//button[contains(text(), 'Begin setup')]"
            ]
            
            setup_clicked = False
            for i, selector in enumerate(setup_selectors):
                try:
                    print(f"🔍 Thử tìm nút Set up authenticator với selector {i+1}: {selector}")
                    setup_buttons = self.driver.find_elements(By.XPATH, selector)
                    if setup_buttons:
                        for button in setup_buttons:
                            if button.is_displayed() and button.is_enabled():
                                self.driver.execute_script("arguments[0].click();", button)
                                time.sleep(3)
                                print(f"✅ Đã click nút Set up authenticator (selector {i+1})")
                                setup_clicked = True
                                break
                        if setup_clicked:
                            break
                except Exception as e:
                    print(f"⚠️  Không tìm thấy với selector {i+1}: {e}")
                    continue
            
            if not setup_clicked:
                print("❌ Không thể tìm thấy nút Set up authenticator")
                return False
            
            # Đợi QR code xuất hiện
            print("🔍 Đang chờ QR code xuất hiện...")
            time.sleep(5)
            
            # Tìm và đọc QR code
            qr_code = self.find_and_read_qr_code()
            if not qr_code:
                print("❌ Không thể đọc QR code")
                return False
            
            # Lưu setup key
            self.setup_key = qr_code
            print(f"🔑 Setup Key: {self.format_setup_key(qr_code)}")
            
            # Auto verify
            return self.auto_verify_setup()
            
        except Exception as e:
            print(f"❌ Lỗi setup Google Authenticator: {e}")
            return False
    
    def find_and_read_qr_code(self):
        """Tìm và đọc QR code"""
        try:
            # Tìm QR code image
            qr_selectors = [
                "//div[@jsname='Sx9Kwc']//div[@jsname='dj7gwc']//img[contains(@src, 'data:image')]",
                "//img[contains(@src, 'data:image')]",
                "//img[contains(@alt, 'QR')]"
            ]
            
            for selector in qr_selectors:
                try:
                    qr_img = self.driver.find_element(By.XPATH, selector)
                    qr_src = qr_img.get_attribute('src')
                    if qr_src and qr_src.startswith('data:image'):
                        print("✅ Đã tìm thấy QR code")
                        return self.extract_secret_from_qr(qr_src)
                except:
                    continue
            
            return None
            
        except Exception as e:
            print(f"❌ Lỗi tìm QR code: {e}")
            return None
    
    def extract_secret_from_qr(self, qr_src: str):
        """Trích xuất secret từ QR code"""
        try:
            # Tạo image từ base64
            base64_data = qr_src.split(',')[1]
            image_data = base64.b64decode(base64_data)
            
            # Lưu tạm thời
            with open('temp_qr.png', 'wb') as f:
                f.write(image_data)
            
            # Đọc QR code
            image = cv2.imread('temp_qr.png')
            qr_codes = pyzbar.decode(image)
            
            if qr_codes:
                qr_data = qr_codes[0].data.decode('utf-8')
                print(f"📱 QR Data: {qr_data}")
                
                # Trích xuất secret - cải thiện regex
                secret_match = re.search(r'secret=([A-Z2-7]+)', qr_data)
                if secret_match:
                    secret = secret_match.group(1)
                    print(f"🔑 Secret từ QR regex: {secret}")
                    return secret
                
                # Thử tìm secret bằng cách khác
                print("⚠️  Không tìm thấy secret bằng regex [A-Z2-7]+, thử cách khác...")
                # Tìm secret trong URL parameters
                if 'secret=' in qr_data:
                    secret_part = qr_data.split('secret=')[1]
                    if '&' in secret_part:
                        secret = secret_part.split('&')[0]
                    else:
                        secret = secret_part
                    print(f"🔑 Secret từ URL split: {secret}")
                    return secret
                
                # Thử tìm secret bằng cách khác nữa
                print("⚠️  Thử tìm secret bằng regex [^&]+...")
                # Tìm secret trong URL parameters với pattern khác
                if 'secret=' in qr_data:
                    # Tìm phần sau secret= và trước & hoặc kết thúc
                    secret_match = re.search(r'secret=([^&]+)', qr_data)
                    if secret_match:
                        secret = secret_match.group(1)
                        print(f"🔑 Secret từ URL pattern [^&]+: {secret}")
                        return secret
                
                print("❌ Không thể trích xuất secret từ QR code")
            
            return None
            
        except Exception as e:
            print(f"❌ Lỗi trích xuất secret: {e}")
            return None
    
    def format_setup_key(self, base32_key: str):
        """Format setup key thành nhóm 4 ký tự"""
        return ' '.join([base32_key[i:i+4] for i in range(0, len(base32_key), 4)])
    
    def auto_verify_setup(self) -> bool:
        """Tự động verify setup"""
        try:
            print("🔍 Đang click nút Next để chuyển sang màn hình nhập code...")
            
            # Tìm và click Next
            next_selectors = [
                "//button[contains(text(), 'Next')]",
                "//span[contains(text(), 'Next')]",
                "//button[@jsname='Pr7Yme']"
            ]
            
            next_clicked = False
            for selector in next_selectors:
                try:
                    next_buttons = self.driver.find_elements(By.XPATH, selector)
                    for button in next_buttons:
                        if button.is_displayed() and button.is_enabled():
                            self.driver.execute_script("arguments[0].click();", button)
                            time.sleep(3)
                            print(f"✅ Đã click nút Next")
                            next_clicked = True
                            break
                    if next_clicked:
                        break
                except:
                    continue
            
            if not next_clicked:
                print("❌ Không thể click Next")
                return False
            
            # Tự động tạo và nhập code
            print("🤖 Tự động xử lý verification...")
            totp = pyotp.TOTP(self.setup_key)
            code = totp.now()
            print(f"🔢 Tự động tạo code: {code}")
            
            # Nhập code
            code_input = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[@id='c0']"))
            )
            code_input.clear()
            time.sleep(0.5)
            code_input.send_keys(code)
            time.sleep(0.5)
            print(f"✅ Đã nhập code vào ô input")
            
            # Click Verify
            verify_selectors = [
                "//button[@data-id='dtOep']",
                "//*[@id='yDmH0d']/div[11]/div/div[2]/div[3]/div/div[2]/div[3]/button",
                "//button[contains(text(), 'Verify')]"
            ]
            
            verify_clicked = False
            for selector in verify_selectors:
                try:
                    verify_buttons = self.driver.find_elements(By.XPATH, selector)
                    for button in verify_buttons:
                        if button.is_displayed() and button.is_enabled():
                            self.driver.execute_script("arguments[0].click();", button)
                            time.sleep(3)
                            print(f"✅ Đã click nút Verify")
                            verify_clicked = True
                            break
                    if verify_clicked:
                        break
                except:
                    continue
            
            if not verify_clicked:
                print("❌ Không thể click Verify")
                return False
            
            # Kiểm tra thành công
            time.sleep(3)
            page_source = self.driver.page_source.lower()
            if "enabled" in page_source or "2-step verification" in page_source:
                print("✅ Đã setup Google Authenticator thành công!")
                return True
            else:
                print("❌ Setup không thành công")
                return False
                
        except Exception as e:
            print(f"❌ Lỗi auto verify: {e}")
            return False
    
    def turn_on_2fa(self) -> bool:
        """Bật 2-Step Verification"""
        try:
            print("🔍 Đang bật 2-Step Verification...")
            
            # Đi đến trang 2FA settings
            self.driver.get("https://myaccount.google.com/signinoptions/twosv")
            time.sleep(3)
            
            # Tìm và click "Turn on 2-Step Verification"
            turn_on_selectors = [
                "//button[@jsname='Pr7Yme' and @aria-label='Turn on 2-Step Verification']",
                "//button[contains(text(), 'Turn on 2-Step Verification')]",
                "//span[contains(text(), 'Turn on 2-Step Verification')]"
            ]
            
            turn_on_clicked = False
            for selector in turn_on_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            self.driver.execute_script("arguments[0].click();", element)
                            time.sleep(3)
                            print(f"✅ Đã click button 'Turn on 2-Step Verification'")
                            turn_on_clicked = True
                            break
                    if turn_on_clicked:
                        break
                except:
                    continue
            
            if not turn_on_clicked:
                print("❌ Không thể click Turn on 2-Step Verification")
                return False
            
            # Đợi và kiểm tra thành công
            time.sleep(5)
            page_source = self.driver.page_source.lower()
            if "turn off 2-step verification" in page_source:
                print("✅ 2-Step Verification đã được bật thành công!")
                return True
            else:
                print("❌ Không thể bật 2-Step Verification")
                return False
                
        except Exception as e:
            print(f"❌ Lỗi turn on 2FA: {e}")
            return False
    
    def create_app_password(self, app_name: str = "Mail") -> bool:
        """Tạo App Password"""
        try:
            print(f"🔐 Đang tạo App Password cho: {app_name}")
            
            # Đi đến trang App Passwords
            self.driver.get("https://myaccount.google.com/apppasswords")
            time.sleep(3)
            
            # Click "Create app password"
            create_selectors = [
                "//button[contains(@class, 'LgbsSe')]",
                "//span[contains(text(), 'Create')]",
                "//button[contains(text(), 'Create')]"
            ]
            
            create_clicked = False
            for selector in create_selectors:
                try:
                    create_buttons = self.driver.find_elements(By.XPATH, selector)
                    for button in create_buttons:
                        if button.is_displayed() and button.is_enabled():
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                            time.sleep(1)
                            self.driver.execute_script("arguments[0].click();", button)
                            time.sleep(3)
                            print(f"✅ Đã click nút Create")
                            create_clicked = True
                            break
                    if create_clicked:
                        break
                except:
                    continue
            
            if not create_clicked:
                print("❌ Không thể click Create")
                return False
            
            # Nhập tên app - CẢI THIỆN
            time.sleep(3)
            app_input = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[@id='i5']"))
            )
            
            # Clear và nhập app name với nhiều phương pháp
            app_input.clear()
            time.sleep(0.5)
            app_input.send_keys(app_name)
            time.sleep(0.5)
            
            # Verify app name đã được nhập
            actual_value = app_input.get_attribute('value')
            print(f"🔍 Giá trị thực tế trong input: '{actual_value}'")
            
            if actual_value != app_name:
                # Thử phương pháp khác
                print("⚠️  App name chưa được nhập đúng, thử phương pháp khác...")
                app_input.clear()
                time.sleep(0.5)
                app_input.click()
                time.sleep(0.5)
                app_input.send_keys(app_name)
                time.sleep(0.5)
                
                # Verify lại
                actual_value = app_input.get_attribute('value')
                print(f"🔍 Giá trị sau khi thử lại: '{actual_value}'")
                
                if actual_value != app_name:
                    # Thử JavaScript
                    print("⚠️  Thử JavaScript...")
                    self.driver.execute_script(f"arguments[0].value = '{app_name}';", app_input)
                    time.sleep(0.5)
                    
                    # Verify cuối cùng
                    actual_value = app_input.get_attribute('value')
                    print(f"🔍 Giá trị sau JavaScript: '{actual_value}'")
            
            print(f"✅ Đã nhập tên app: {app_name}")
            
            # Đợi button Create xuất hiện sau khi nhập app name
            time.sleep(2)
            
            # Click Create để tạo app password
            create_app_selectors = [
                "//*[@id='yDmH0d']/c-wiz/div/div[2]/div[2]/c-wiz/div/div[4]/div/div[3]/div/div[2]/div/div/div/button/span[5]",
                "//button[contains(text(), 'Create')]",
                "//button[@jsname='Pr7Yme']"
            ]
            
            create_app_clicked = False
            for selector in create_app_selectors:
                try:
                    create_app_buttons = self.driver.find_elements(By.XPATH, selector)
                    for button in create_app_buttons:
                        if button.is_displayed() and button.is_enabled():
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                            time.sleep(1)
                            self.driver.execute_script("arguments[0].click();", button)
                            time.sleep(5)
                            print(f"✅ Đã click nút Create App")
                            create_app_clicked = True
                            break
                    if create_app_clicked:
                        break
                except:
                    continue
            
            if not create_app_clicked:
                print("❌ Không thể click Create App")
                return False
            
            # Lấy app password từ popup
            time.sleep(5)
            popup_selectors = [
                "//*[@id='yDmH0d']/div[16]/div[2]/div",
                "//article[contains(@class, 'VuF2Pd')]",
                "//div[contains(@class, 'lY6Rwe')]"
            ]
            
            app_password_found = False
            for selector in popup_selectors:
                try:
                    popups = self.driver.find_elements(By.XPATH, selector)
                    for popup in popups:
                        if popup.is_displayed():
                            # Tìm app password trong spans
                            spans = popup.find_elements(By.TAG_NAME, "span")
                            password_chars = []
                            for span in spans:
                                char = span.text.strip()
                                if char and len(char) == 1:
                                    password_chars.append(char)
                            
                            if len(password_chars) == 16:
                                self.app_password = ''.join(password_chars)
                                print(f"✅ Đã tìm thấy app password: {self.app_password}")
                                app_password_found = True
                                break
                    if app_password_found:
                        break
                except:
                    continue
            
            if app_password_found:
                self.save_app_password(app_name)
                return True
            else:
                print("❌ Không tìm thấy app password")
                return False
                
        except Exception as e:
            print(f"❌ Lỗi tạo app password: {e}")
            return False
    
    def save_2fa_info(self):
        """Lưu thông tin 2FA"""
        try:
            backup_file = "2fa_backup.json"  # Lưu vào thư mục hiện tại
            backup_data = {}
            
            if os.path.exists(backup_file):
                with open(backup_file, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
            
            if self.current_email not in backup_data:
                backup_data[self.current_email] = {}
            
            backup_data[self.current_email]['setup_key'] = self.setup_key
            backup_data[self.current_email]['created_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Đã lưu thông tin 2FA cho: {self.current_email}")
            
        except Exception as e:
            print(f"⚠️  Lỗi lưu 2FA info: {e}")
    
    def save_app_password(self, app_name: str):
        """Lưu app password"""
        try:
            backup_file = "2fa_backup.json"  # Lưu vào thư mục hiện tại
            backup_data = {}
            
            if os.path.exists(backup_file):
                with open(backup_file, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
            
            if self.current_email not in backup_data:
                backup_data[self.current_email] = {
                    'setup_key': '',
                    'backup_codes': [],
                    'app_passwords': {}
                }
            
            if 'app_passwords' not in backup_data[self.current_email]:
                backup_data[self.current_email]['app_passwords'] = {}
            
            backup_data[self.current_email]['app_passwords'][app_name] = {
                'password': self.app_password,
                'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Đã lưu app password cho {self.current_email} - {app_name}")
            print(f"🔑 App Password: {self.app_password}")
            print(f"📁 Đã lưu vào file: {backup_file}")
            
        except Exception as e:
            print(f"⚠️  Lỗi lưu app password: {e}")
    
    def load_2fa_data(self):
        """Load 2FA data từ file"""
        try:
            backup_file = "2fa_backup.json"  # Đọc từ thư mục hiện tại
            if os.path.exists(backup_file):
                with open(backup_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"⚠️  Lỗi load 2FA data: {e}")
            return {}
    
    def run_complete_setup(self, email: str, password: str) -> bool:
        """Chạy setup hoàn chỉnh"""
        try:
            print(f"🔐 Bắt đầu setup security cho: {email}")
            print("=" * 60)
            
            # 1. Login Gmail
            print("🔐 Bước 1: Login Gmail...")
            if not self.login_gmail(email, password):
                return False
            
            # 2. Kiểm tra 2FA status
            print("\n🔍 Bước 2: Kiểm tra 2FA status...")
            status = self.check_2fa_status()
            
            if status == "turn_off":
                print("✅ 2FA đã được bật")
            elif status == "turn_on":
                print("⚠️  2FA chưa được bật, đang setup...")
                if not self.setup_google_authenticator():
                    return False
                if not self.turn_on_2fa():
                    return False
                self.save_2fa_info()
            elif status == "unknown":
                print("⚠️  Không xác định được trạng thái 2FA")
                return False
            else:
                print("❌ Lỗi kiểm tra 2FA status")
                return False
            
            # 3. Tạo App Password
            print("\n🔐 Bước 3: Tạo App Password...")
            if not self.create_app_password("Mail"):
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Lỗi setup: {e}")
            return False
    
    def close(self):
        """Đóng browser"""
        if self.driver:
            try:
                self.driver.quit()
                print("✅ Đã đóng browser")
            except Exception as e:
                # Bỏ qua lỗi cleanup Chrome driver
                if "handle is invalid" in str(e) or "OSError" in str(e):
                    print("✅ Browser đã được đóng")
                else:
                    print(f"⚠️  Lỗi đóng browser: {e}")
    
    def keep_open(self):
        """Giữ browser mở để debug"""
        print("🔍 Browser vẫn mở để debug...")
        print("💡 Nhấn Ctrl+C để đóng browser khi xong")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Đóng browser...")
            self.close()

def load_accounts_from_file(filename: str = "accounts.txt") -> list:
    """Load danh sách accounts từ file"""
    accounts = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            if line:
                if '|' in line:
                    parts = line.split('|', 1)
                    if len(parts) == 2:
                        email, password = parts
                        accounts.append({
                            'email': email.strip(),
                            'password': password.strip()
                        })
        
        print(f"✅ Đã load {len(accounts)} accounts từ {filename}")
        return accounts
        
    except Exception as e:
        print(f"❌ Lỗi load file: {e}")
        return []

def main():
    """Main function"""
    print("🔐 Gmail Security Setup - Tự động setup 2FA và App Password")
    print("=" * 70)
    
    # Load accounts
    accounts = load_accounts_from_file()
    if not accounts:
        print("❌ Không có accounts nào")
        return
    
    # Hiển thị danh sách accounts
    print("\n📧 Danh sách Accounts:")
    print("-" * 50)
    for i, account in enumerate(accounts, 1):
        print(f"{i:2d}. {account['email']}")
    print("-" * 50)
    
    # Chọn account
    try:
        choice = int(input("\nChọn account (1-{}): ".format(len(accounts))))
        if choice < 1 or choice > len(accounts):
            print("❌ Lựa chọn không hợp lệ")
            return
    except ValueError:
        print("❌ Vui lòng nhập số")
        return
    
    selected_account = accounts[choice - 1]
    
    # Hỏi headless mode
    try:
        headless_choice = input("\n🤖 Bạn có muốn chạy headless không? (y/n): ").strip().lower()
        headless_mode = headless_choice in ['y', 'yes', 'có', 'co']
    except:
        headless_mode = True
    
    # Tạo setup instance
    setup = GmailSecuritySetup()
    
    try:
        # Setup driver
        if not setup.setup_driver(headless=headless_mode):
            return
        
        # Chạy setup hoàn chỉnh
        if setup.run_complete_setup(selected_account['email'], selected_account['password']):
            print("\n🎉 HOÀN THÀNH!")
            print("✅ Setup hoàn thành thành công!")
        else:
            print("\n❌ Setup thất bại")
            print("🔍 Giữ browser mở để debug...")
            setup.keep_open()
        
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        print("🔍 Giữ browser mở để debug...")
        setup.keep_open()
    
    finally:
        # Đảm bảo đóng browser an toàn
        try:
            setup.close()
        except Exception as e:
            # Bỏ qua lỗi cleanup Chrome driver
            if "handle is invalid" not in str(e):
                print(f"⚠️  Lỗi cleanup: {e}")

if __name__ == "__main__":
    main() 