import requests
from bs4 import BeautifulSoup
import json
import time
import os

BASE_URL = "https://oto360.net"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Bluehtml) Chrome/120.0.0.0 Safari/537.36"
}

session = requests.Session()
session.headers.update(HEADERS)

VALID_BRANDS = {
    # Hãng phổ thông & Xe tải/Khách
    "toyota": "TOYOTA", "vinfast": "VINFAST", "hyundai": "HYUNDAI", "honda": "HONDA",
    "kia": "KIA", "ford": "FORD", "mitsubishi": "MITSUBISHI", "mazda": "MAZDA",
    "suzuki": "SUZUKI", "isuzu": "ISUZU", "nissan": "NISSAN", "mg": "MG",
    "hino": "HINO", "jac": "JAC", "teraco": "TERACO", "thaco": "THACO",
    # Hãng xe Trung Quốc mới & các hãng khác
    "byd": "BYD", "baojun": "BAOJUN", "wuling": "WULING", "tq-wuling": "TQ-WULING",
    "dongfeng": "DONGFENG", "gac": "GAC", "geely": "GEELY", "gwm": "GWM",
    "lynkco": "LYNKCO", "jaecoo": "JAECOO", "zeekr": "ZEEKR", "chery": "CHERY",
    "omoda": "OMODA", "haima": "HAIMA", "bestune": "BESTUNE",
    # Hãng xe sang & Siêu xe
    "mercedes-benz": "MERCEDES-BENZ", "bmw": "BMW", "audi": "AUDI", "lexus": "LEXUS",
    "volvo": "VOLVO", "volkswagen": "VOLKSWAGEN", "porsche": "PORSCHE",
    "land-rover": "LAND-ROVER", "jaguar": "JAGUAR", "peugeot": "PEUGEOT",
    "skoda": "SKODA", "subaru": "SUBARU", "mini-cooper": "MINI-COOPER",
    "maserati": "MASERATI", "aston-martin": "ASTON-MARTIN", "bentley": "BENTLEY",
    "lamborghini": "LAMBORGHINI", "jeep": "JEEP", "morgan": "MORGAN", "lotus": "LOTUS",
    # Xe thương mại / Xe tải nặng đặc thù
    "chenglong": "CHENGLONG", "sinotruk": "SINOTRUK", "kamaz": "KAMAZ", "veam": "VEAM",
    "hongyan": "HONGYAN", "ud": "UD", "fuso": "FUSO", "daewoo": "DAEWOO",
    "foton": "FOTON", "vm-motors": "VM-MOTORS", "sany": "SANY", "king-long": "KING-LONG",
    "iveco": "IVECO", "gaz": "GAZ", "kim-long": "KIM-LONG", "samco": "SAMCO"
}

def parse_table_specs(soup):
    """Bóc tách thông số kỹ thuật tối ưu hóa tốc độ lặp vòng dữ liệu"""
    specs = {"so_cho": "Chưa cập nhật", "dong_co": "Chưa cập nhật", "tieu_thu": "Chưa cập nhật", "tai_trong": "Chưa cập nhật"}
    
    keywords = {
        "so_cho": ["số chỗ", "chỗ ngồi", "ghế"],
        "dong_co": ["động cơ", "loại pin", "mô tơ", "dung tích"],
        "tieu_thu": ["tiêu thụ", "năng lượng", "đường hỗn hợp", "quãng đường"],
        "tai_trong": ["tải trọng", "khối lượng hàng", "cho phép chở"]
    }

    for table in soup.find_all('table'):
        for row in table.find_all('tr'):
            cells = [cell.text.strip() for cell in row.find_all(['td', 'th'])]
            if len(cells) < 2:
                continue
                
            key = cells[0].lower()
            value = cells[1]
            
            # Tối ưu hóa: kiểm tra tuần tự và break sớm để giảm tải cho CPU
            matched = False
            for spec_key, kw_list in keywords.items():
                if any(kw in key for kw in kw_list):
                    specs[spec_key] = value
                    matched = True
                    break
            if matched:
                continue
                
    return specs

def log_error(url, error_message):
    """Ghi nhận lại các đường dẫn lỗi để kiểm tra sau"""
    with open("error_links.txt", "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {url} -> Lỗi: {error_message}\n")

def save_database(data, filename="perfect_cars_database.json"):
    """Hàm lưu dữ liệu an toàn"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def scrape_optimized_market():
    print("--- BẮT ĐẦU CHẠY SCRIPT CHUẨN HÓA VÀ TỐI ƯU TOÀN DIỆN ---")
    
    output_file = "perfect_cars_database.json"
    final_database = []
    
    # Nếu file đã tồn tại từ trước, đọc lên để chạy tiếp (chống mất dữ liệu)
    if os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                final_database = json.load(f)
            print(f"-> Đã tìm thấy file cũ. Đang có sẵn {len(final_database)} dòng xe.")
        except:
            final_database = []

    # Gom các URL đã cào thành công để tránh cào lại nếu chạy lại script
    scraped_urls = {item["url_chi_tiet"] for item in final_database}

    for b_slug, b_name in VALID_BRANDS.items():
        brand_url = f"{BASE_URL}/xe-{b_slug}"
        print(f"\n[HÃNG {b_slug}] Đang quét thương hiệu: {b_name}")
        
        try:
            response = session.get(brand_url, timeout=10)
            if response.status_code != 200:
                print(f" -> Không truy cập được trang hãng {b_name}, bỏ qua.")
                log_error(brand_url, f"Mã trạng thái HTTP {response.status_code}")
                continue
                
            soup = BeautifulSoup(response.text, 'html.parser')
            model_urls = set()
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                if f"/xe-{b_slug}/" in href and href.endswith('.html'):
                    full_url = href if href.startswith('http') else BASE_URL + href
                    # Lọc trùng ngay lập tức nếu link này đã được cào từ trước
                    if full_url not in scraped_urls:
                        model_urls.add(full_url)
            
            if not model_urls:
                print(f" -> Không có dòng xe mới nào cần cào.")
                continue
                
            print(f" -> Tìm thấy {len(model_urls)} dòng xe mới hợp lệ.")

            # Chui vào chi tiết từng xe
            for m_index, m_url in enumerate(sorted(model_urls), 1):
                print(f"    [{m_index}/{len(model_urls)}] Đang cào: {m_url}")
                try:
                    res = session.get(m_url, timeout=10)
                    if res.status_code == 200:
                        detail_soup = BeautifulSoup(res.text, 'html.parser')
                        specs = parse_table_specs(detail_soup)
                        
                        model_name = m_url.split('/')[-1].replace('.html', '').upper()
                        
                        final_database.append({
                            "hang": b_name,
                            "dong_xe": model_name,
                            "url_chi_tiet": m_url,
                            "so_cho_ngoi": specs["so_cho"],
                            "dong_co": specs["dong_co"],
                            "muc_tieu_thu": specs["tieu_thu"],
                            "tai_trong_cho_phep": specs["tai_trong"]
                        })
                        scraped_urls.add(m_url)
                    else:
                        log_error(m_url, f"Mã trạng thái dòng xe HTTP {res.status_code}")
                except Exception as e:
                    print(f"      Lỗi tại link {m_url}: {e}")
                    log_error(m_url, str(e))
                
                time.sleep(1) # Delay an toàn chống ban IP
            
            # ĐẶC BIỆT: Lưu cuốn chiếu ngay sau khi quét xong 1 Hãng để bảo vệ dữ liệu
            save_database(final_database, output_file)
            print(f" -> Đã lưu sao lưu dữ liệu cho hãng {b_name}!")
                
        except Exception as e:
            print(f" Lỗi hệ thống khi quét hãng {b_name}: {e}")
            log_error(brand_url, str(e))
            
        time.sleep(1.5)

    print(f"\n HOÀN THÀNH TỐI ƯU! Tổng cộng có {len(final_database)} dòng xe trong hệ thống.")

if __name__ == "__main__":
    scrape_optimized_market()