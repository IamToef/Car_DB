import requests
import json
import time
import os
import re
import urllib3
import sys

# Đảm bảo mã hóa UTF-8 cho stdout trên Windows nếu có thể
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Tắt cảnh báo SSL không an toàn do dùng verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CARQUERY_BASE_URL = "https://www.carqueryapi.com/api/0.3/"
WIKI_BASE_URL = "https://vi.wikipedia.org/api/rest_v1/page/summary/"
WIKI_EN_BASE_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

# Các hãng xe phổ biến toàn cầu để ưu tiên cào trước
POPULAR_MAKES = [
    "toyota", "honda", "ford", "hyundai", "kia", "mazda", "nissan", 
    "mitsubishi", "chevrolet", "subaru", "volkswagen", "bmw", 
    "mercedes-benz", "audi", "lexus", "porsche", "volvo", "land-rover"
]

session = requests.Session()
session.headers.update(HEADERS)

def log_error(msg):
    with open("crawl_global_errors.log", "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")

def get_jsonp(url, params=None):
    """Gọi API CarQuery (trả về JSONP) và chuyển đổi thành JSON"""
    for attempt in range(3):
        try:
            response = session.get(url, params=params, verify=False, timeout=15)
            if response.status_code == 200:
                text = response.text.strip()
                # CarQuery trả về định dạng ?({...}) hoặc callback({...})
                if text.startswith("?") and text.endswith(")"):
                    text = text[2:-1]
                elif text.startswith("callback(") and text.endswith(")"):
                    text = text[9:-1]
                
                return json.loads(text)
            elif response.status_code == 403:
                print(f"    [Warning] 403 Forbidden. Waiting 5s before retrying...")
                time.sleep(5)
            else:
                log_error(f"HTTP {response.status_code} at URL: {url}")
        except Exception as e:
            log_error(f"Connection error ({e}) at URL: {url}. Retrying {attempt+1}...")
            time.sleep(2)
    return None

def get_wiki_summary(make, model):
    """Lấy tóm tắt lịch sử của dòng xe từ Wikipedia (ưu tiên tiếng Việt, sau đó đến tiếng Anh)"""
    title_candidates = [
        f"{make}_{model}",
        f"{model}",
        f"{make} {model}"
    ]
    
    # Chuẩn hóa tên viết hoa chữ cái đầu cho Wikipedia
    title_candidates = [t.replace(" ", "_").title() for t in title_candidates]
    
    # 1. Thử Wikipedia Tiếng Việt trước
    for title in title_candidates:
        url = f"{WIKI_BASE_URL}{title}"
        try:
            res = session.get(url, timeout=10)
            if res.status_code == 200:
                data = res.json()
                if "extract" in data:
                    return data["extract"]
        except Exception:
            pass

    # 2. Thử Wikipedia Tiếng Anh nếu tiếng Việt không có
    for title in title_candidates:
        url = f"{WIKI_EN_BASE_URL}{title}"
        try:
            res = session.get(url, timeout=10)
            if res.status_code == 200:
                data = res.json()
                if "extract" in data:
                    return data["extract"]
        except Exception:
            pass
            
    return "Lich su dong xe nay chua duoc cap nhat."

# Dữ liệu fallback chuẩn hóa của các dòng xe nổi tiếng toàn cầu
FALLBACK_DATA = [
    {
        "hang": "TOYOTA",
        "dong_xe": "86",
        "nam_san_xuat": 2012,
        "loai_xe": "Coupe",
        "loai_nhien_lieu": "Gasoline",
        "dong_co": "1998cc Boxer 4-cylinder",
        "tinh_trang_san_xuat": "Còn sản xuất",
        "gia_niem_yet": None,
        "xuat_xu": "Japan",
        "hinh_anh_url": None,
        "url_chi_tiet": "https://www.carqueryapi.com/api/0.3/?cmd=getTrims&make=toyota&model=86",
        "so_cho_ngoi": 4,
        "muc_tieu_thu": "7.8 L/100km",
        "tai_trong_cho_phep": "1275 kg",
        "lich_su": "The Toyota 86 and the Subaru BRZ are 2+2 sports cars jointly developed by Toyota and Subaru, manufactured at Subaru's Gunma assembly plant from 2012.",
        "cac_phien_ban": [
            {"phien_ban": "Base", "nam": "2017", "dong_co_cc": "1998", "hop_so": "6-speed Manual", "he_dan_dong": "Rear-wheel drive", "trong_luong_kg": "1275", "kich_thuoc_mm": "4240x1775x1320"},
            {"phien_ban": "GT", "nam": "2017", "dong_co_cc": "1998", "hop_so": "6-speed Automatic", "he_dan_dong": "Rear-wheel drive", "trong_luong_kg": "1290", "kich_thuoc_mm": "4240x1775x1320"}
        ]
    },
    {
        "hang": "TOYOTA",
        "dong_xe": "4RUNNER",
        "nam_san_xuat": 1984,
        "loai_xe": "SUV",
        "loai_nhien_lieu": "Gasoline",
        "dong_co": "3956cc V6",
        "tinh_trang_san_xuat": "Còn sản xuất",
        "gia_niem_yet": None,
        "xuat_xu": "Japan",
        "hinh_anh_url": None,
        "url_chi_tiet": "https://www.carqueryapi.com/api/0.3/?cmd=getTrims&make=toyota&model=4runner",
        "so_cho_ngoi": 5,
        "muc_tieu_thu": "12.4 L/100km",
        "tai_trong_cho_phep": "2120 kg",
        "lich_su": "Toyota 4Runner là một mẫu xe thể thao đa dụng cỡ trung được sản xuất bởi nhà sản xuất ô tô Nhật Bản Toyota và được bán trên toàn thế giới từ năm 1984 đến nay, trải qua sáu thế hệ.",
        "cac_phien_ban": [
            {"phien_ban": "SR5", "nam": "2020", "dong_co_cc": "3956", "hop_so": "5-speed Automatic", "he_dan_dong": "Four-wheel drive", "trong_luong_kg": "2120", "kich_thuoc_mm": "4820x1925x1780"},
            {"phien_ban": "Limited", "nam": "2020", "dong_co_cc": "3956", "hop_so": "5-speed Automatic", "he_dan_dong": "Four-wheel drive", "trong_luong_kg": "2155", "kich_thuoc_mm": "4820x1925x1780"}
        ]
    },
    {
        "hang": "TOYOTA",
        "dong_xe": "CAMRY",
        "nam_san_xuat": 1982,
        "loai_xe": "Sedan",
        "loai_nhien_lieu": "Gasoline",
        "dong_co": "2487cc In-line 4",
        "tinh_trang_san_xuat": "Còn sản xuất",
        "gia_niem_yet": None,
        "xuat_xu": "Japan",
        "hinh_anh_url": None,
        "url_chi_tiet": "https://www.carqueryapi.com/api/0.3/?cmd=getTrims&make=toyota&model=camry",
        "so_cho_ngoi": 5,
        "muc_tieu_thu": "6.9 L/100km",
        "tai_trong_cho_phep": "1470 kg",
        "lich_su": "Toyota Camry là một chiếc xe ô tô cỡ trung được sản xuất bởi nhà sản xuất ô tô Nhật Bản Toyota từ năm 1982, trải qua nhiều thế hệ. Tên 'Camry' được bắt nguồn từ tiếng Nhật mang ý nghĩa vương miện.",
        "cac_phien_ban": [
            {"phien_ban": "LE", "nam": "2020", "dong_co_cc": "2487", "hop_so": "8-speed Automatic", "he_dan_dong": "Front-wheel drive", "trong_luong_kg": "1470", "kich_thuoc_mm": "4884x1839x1445"},
            {"phien_ban": "SE", "nam": "2020", "dong_co_cc": "2487", "hop_so": "8-speed Automatic", "he_dan_dong": "Front-wheel drive", "trong_luong_kg": "1500", "kich_thuoc_mm": "4884x1839x1445"}
        ]
    },
    {
        "hang": "HONDA",
        "dong_xe": "ACCORD",
        "nam_san_xuat": 1976,
        "loai_xe": "Sedan",
        "loai_nhien_lieu": "Gasoline",
        "dong_co": "1498cc Turbocharged 4",
        "tinh_trang_san_xuat": "Còn sản xuất",
        "gia_niem_yet": None,
        "xuat_xu": "Japan",
        "hinh_anh_url": None,
        "url_chi_tiet": "https://www.carqueryapi.com/api/0.3/?cmd=getTrims&make=honda&model=accord",
        "so_cho_ngoi": 5,
        "muc_tieu_thu": "7.2 L/100km",
        "tai_trong_cho_phep": "1430 kg",
        "lich_su": "Honda Accord là dòng xe sedan hạng D cỡ trung được sản xuất bởi nhà sản xuất ô tô Nhật Bản Honda từ năm 1976. Đây là một trong những mẫu xe bán chạy nhất thế giới trong nhiều thập kỷ qua.",
        "cac_phien_ban": [
            {"phien_ban": "LX", "nam": "2020", "dong_co_cc": "1498", "hop_so": "CVT", "he_dan_dong": "Front-wheel drive", "trong_luong_kg": "1430", "kich_thuoc_mm": "4882x1862x1450"},
            {"phien_ban": "Sport", "nam": "2020", "dong_co_cc": "1996", "hop_so": "10-speed Automatic", "he_dan_dong": "Front-wheel drive", "trong_luong_kg": "1480", "kich_thuoc_mm": "4882x1862x1450"}
        ]
    }
]

def crawl_car_database():
    output_file = "perfect_cars_database.json"
    database = []
    
    # Đọc dữ liệu cũ nếu có để tránh cào lại (Resume capability)
    if os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                database = json.load(f)
            print(f"-> Loaded {len(database)} models from old file.")
        except Exception as e:
            print(f"-> Error reading old file: {e}. Creating new database.")
            database = []
            
    crawled_models = {f"{item['hang'].lower()}:{item['dong_xe'].lower()}" for item in database}
    
    print("\n--- START GLOBAL CAR DATABASE CRAWLER ---")
    
    # Bước 1: Lấy danh sách các hãng xe
    print("-> Fetching makes list from CarQuery...")
    makes_data = get_jsonp(CARQUERY_BASE_URL, {"cmd": "getMakes"})
    if not makes_data or "Makes" not in makes_data:
        print("    [Warning] CarQuery API request failed or rate limited. Activating intelligent local fallback database...")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(FALLBACK_DATA, f, ensure_ascii=False, indent=4)
        print("    Done! Saved fallback database.")
        return
        
    makes_list = makes_data["Makes"]
    print(f"-> Found {len(makes_list)} makes in total.")
    
    # Lọc danh sách hãng xe để ưu tiên hãng lớn
    target_makes = [m for m in makes_list if m["make_id"] in POPULAR_MAKES]
    
    print(f"-> Will crawl {len(target_makes)} popular makes.")
    
    for idx, make_info in enumerate(target_makes, 1):
        make_id = make_info["make_id"]
        make_display = make_info["make_display"]
        print(f"\n[{idx}/{len(target_makes)}] Make: {make_display.upper()} (ID: {make_id})")
        
        # Bước 2: Lấy danh sách các models của hãng đó
        models_data = get_jsonp(CARQUERY_BASE_URL, {"cmd": "getModels", "make": make_id})
        if not models_data or "Models" not in models_data:
            print(f"  -> Could not get models list for {make_display}")
            continue
            
        models_list = models_data["Models"]
        print(f"  -> Found {len(models_list)} models.")
        
        for m_idx, model_info in enumerate(models_list, 1):
            model_name = model_info["model_name"]
            model_key = f"{make_id}:{model_name.lower()}"
            
            if model_key in crawled_models:
                # Đã cào dòng xe này rồi, bỏ qua
                continue
                
            print(f"    [{m_idx}/{len(models_list)}] Crawling model: {model_name}...")
            
            # Bước 3: Lấy tất cả Trims (phiên bản) của dòng xe này
            trims_data = get_jsonp(CARQUERY_BASE_URL, {"cmd": "getTrims", "make": make_id, "model": model_name})
            if not trims_data or "Trims" not in trims_data or not trims_data["Trims"]:
                print(f"      [Warning] Could not get specs for model {model_name}")
                continue
                
            trims = trims_data["Trims"]
            
            # Trích xuất thông tin tổng hợp sạch từ các trims
            years = [int(t["model_year"]) for t in trims if t.get("model_year") and t["model_year"].isdigit()]
            min_year = min(years) if years else "Chua cap nhat"
            max_year = max(years) if years else "Chua cap nhat"
            
            seats_list = [t["model_seats"] for t in trims if t.get("model_seats")]
            so_cho_ngoi = seats_list[0] if seats_list else "Chua cap nhat"
            
            if so_cho_ngoi != "Chua cap nhat":
                so_cho_ngoi = re.sub(r"\D", "", so_cho_ngoi)
                so_cho_ngoi = int(so_cho_ngoi) if so_cho_ngoi.isdigit() else "Chua cap nhat"
            
            engine_list = [f"{t['model_engine_cc']}cc {t['model_engine_type']}" for t in trims if t.get("model_engine_cc")]
            dong_co = engine_list[0] if engine_list else "Chua cap nhat"
            
            fuel_list = [t["model_engine_fuel"] for t in trims if t.get("model_engine_fuel")]
            loai_nhien_lieu = fuel_list[0] if fuel_list else "Xang"
            
            body_list = [t["model_body"] for t in trims if t.get("model_body")]
            loai_xe = body_list[0] if body_list else "Sedan"
            
            lkm_list = [float(t["model_lkm_mixed"]) for t in trims if t.get("model_lkm_mixed") and t["model_lkm_mixed"] != "None"]
            muc_tieu_thu = f"{round(sum(lkm_list)/len(lkm_list), 2)} L/100km" if lkm_list else "Chua cap nhat"
            
            weight_list = [t["model_weight_kg"] for t in trims if t.get("model_weight_kg")]
            tai_trong = f"{weight_list[0]} kg" if weight_list else "Chua cap nhat"
            
            # Bước 4: Lấy tóm tắt lịch sử dòng xe từ Wikipedia
            lich_su = get_wiki_summary(make_display, model_name)
            
            # Tạo bản ghi dòng xe chuẩn hóa
            car_entry = {
                "hang": make_display.upper(),
                "dong_xe": model_name.upper(),
                "nam_san_xuat": min_year if isinstance(min_year, int) else None,
                "loai_xe": loai_xe,
                "loai_nhien_lieu": loai_nhien_lieu,
                "dong_co": dong_co,
                "tinh_trang_san_xuat": "Còn sản xuất" if max_year == 2024 or max_year == 2025 else "Đã dừng sản xuất",
                "gia_niem_yet": None,
                "xuat_xu": make_info.get("make_country", "Chua cap nhat"),
                "hinh_anh_url": None,
                "url_chi_tiet": f"https://www.carqueryapi.com/api/0.3/?cmd=getTrims&make={make_id}&model={model_name}",
                "so_cho_ngoi": so_cho_ngoi,
                "muc_tieu_thu": muc_tieu_thu,
                "tai_trong_cho_phep": tai_trong,
                "lich_su": lich_su,
                "cac_phien_ban": [
                    {
                        "phien_ban": t.get("model_trim"),
                        "nam": t.get("model_year"),
                        "dong_co_cc": t.get("model_engine_cc"),
                        "hop_so": t.get("model_engine_transmission"),
                        "he_dan_dong": t.get("model_drive"),
                        "trong_luong_kg": t.get("model_weight_kg"),
                        "kich_thuoc_mm": f"{t.get('model_length_mm', '')}x{t.get('model_width_mm', '')}x{t.get('model_height_mm', '')}"
                    } for t in trims[:15]
                ]
            }
            
            database.append(car_entry)
            crawled_models.add(model_key)
            
            # Ghi cuốn chiếu để bảo vệ dữ liệu
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(database, f, ensure_ascii=False, indent=4)
                
            time.sleep(0.5)
            
        print(f" -> Completed crawling for make {make_display.upper()}")
        time.sleep(1)

    print(f"\n--- CRAWLING COMPLETED ---")
    print(f"Total models crawled successfully: {len(database)}")

if __name__ == "__main__":
    crawl_car_database()
