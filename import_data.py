import sqlite3
import json
import os
import sys

# Đảm bảo mã hóa UTF-8 cho stdout trên terminal Windows
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

DB_FILE = "cars.db"
SCHEMA_FILE = "init_schema.sql"
JSON_FILE = "perfect_cars_database.json"

def init_database():
    """Đọc tệp schema.sql và khởi tạo cơ cấu bảng cơ sở dữ liệu"""
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print(f"-> Đã xóa cơ sở dữ liệu cũ {DB_FILE} để khởi tạo mới.")
        
    print(f"-> Đang khởi tạo cơ sở dữ liệu {DB_FILE}...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    
    # Thực hiện chạy các câu lệnh SQL khởi tạo
    cursor.executescript(schema_sql)
    conn.commit()
    conn.close()
    print("-> Khởi tạo cơ sở dữ liệu thành công!")

def normalize_and_import():
    """Đọc dữ liệu từ file JSON, chuẩn hóa và chèn vào database"""
    if not os.path.exists(JSON_FILE):
        print(f"Lỗi: Không tìm thấy file {JSON_FILE}!")
        return
        
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        cars_data = json.load(f)
        
    # Thêm hai dòng xe mẫu do người dùng đề xuất để kiểm thử tính đa hình
    user_samples = [
        {
          "thuong_hieu": "Toyota",
          "dong_xe": "Vios 2024 (Mẫu)",
          "nam_san_xuat": 2024,
          "loai_xe": "Sedan",
          "phan_khuc": "Hạng B",
          "loai_nhien_lieu": "Xăng",
          "so_cho_ngoi": 5,
          "hop_so": "Tự động CVT",
          "dong_co": "1.5L Dual VVT-i",
          "he_dan_dong": "Cầu trước (FWD)",
          "tieu_hao_nhien_lieu_lit_100km": 5.8,
          "tinh_trang_san_xuat": "Còn sản xuất",
          "xuat_xu": "Nhật Bản (Lắp ráp tại VN)",
          "gia_niem_yet": 545000000,
          "gia_lan_banh_tam_tinh": 615000000,
          "hinh_anh_url": "https://link-anh-xe.com/vios.jpg"
        },
        {
          "thuong_hieu": "Hyundai",
          "dong_xe": "New Porter 150 (Mẫu)",
          "nam_san_xuat": 2024,
          "loai_xe": "Xe tải",
          "loai_nhien_lieu": "Dầu Diesel",
          "dong_co": "D4CB 2.5L",
          "tinh_trang_san_xuat": "Còn sản xuất",
          "gia_niem_yet": 350000000,
          "dac_tinh_xe_tai": {
            "loai_thung": "Thùng mui bạt",
            "tai_trong_cho_phep_kg": 1490,
            "tong_tai_trong_kg": 3500,
            "kich_thuoc_thung_mm": "3110 x 1630 x 1720"
          }
        }
    ]
    cars_data.extend(user_samples)
        
    print(f"-> Đang xử lý và import {len(cars_data)} bản ghi vào database...")
    
    imported_count = 0
    for idx, item in enumerate(cars_data):
        # 1. Trích xuất thông tin hãng xe
        hang = item.get("hang") or item.get("thuong_hieu")
        if not hang:
            continue
            
        hang = hang.strip().upper()
        
        # Thêm hãng xe nếu chưa tồn tại
        cursor.execute("INSERT OR IGNORE INTO hang_xe (ten_hang) VALUES (?)", (hang,))
        cursor.execute("SELECT id FROM hang_xe WHERE ten_hang = ?", (hang,))
        hang_id = cursor.fetchone()[0]
        
        # 2. Phân loại thuộc tính chung và thuộc tính động (JSON)
        dong_xe = item.get("dong_xe", "").strip()
        nam_san_xuat = item.get("nam_san_xuat")
        loai_xe = item.get("loai_xe", "Chưa xác định").strip()
        loai_nhien_lieu = item.get("loai_nhien_lieu")
        dong_co = item.get("dong_co")
        tinh_trang_san_xuat = item.get("tinh_trang_san_xuat", "Còn sản xuất")
        gia_niem_yet = item.get("gia_niem_yet")
        xuat_xu = item.get("xuat_xu")
        hinh_anh_url = item.get("hinh_anh_url")
        url_chi_tiet = item.get("url_chi_tiet")
        
        # Chuẩn hóa thuộc tính động cho JSONB/JSON column
        thong_so_chi_tiet = {}
        
        # Trường hợp cào thô từ oto360.net có cấu trúc khác:
        if "so_cho_ngoi" in item:
            thong_so_chi_tiet["so_cho_ngoi"] = item["so_cho_ngoi"]
        elif "so_cho" in item:
            thong_so_chi_tiet["so_cho_ngoi"] = item["so_cho"]
            
        if "muc_tieu_thu" in item:
            thong_so_chi_tiet["muc_tieu_thu"] = item["muc_tieu_thu"]
        if "tieu_hao_nhien_lieu_lit_100km" in item:
            thong_so_chi_tiet["tieu_hao_nhien_lieu_lit_100km"] = item["tieu_hao_nhien_lieu_lit_100km"]
            
        if "tai_trong_cho_phep" in item:
            thong_so_chi_tiet["tai_trong_cho_phep"] = item["tai_trong_cho_phep"]
            
        # Thêm các trường đặc thù của xe con nếu có
        for field in ["phan_khuc", "hop_so", "he_dan_dong", "gia_lan_banh_tam_tinh"]:
            if field in item:
                thong_so_chi_tiet[field] = item[field]
                
        # Thêm các trường đặc thù của xe tải
        if "dac_tinh_xe_tai" in item:
            thong_so_chi_tiet["dac_tinh_xe_tai"] = item["dac_tinh_xe_tai"]
            
        # Thêm các phiên bản chi tiết từ API nếu có
        if "cac_phien_ban" in item:
            thong_so_chi_tiet["cac_phien_ban"] = item["cac_phien_ban"]

        # Chuyển đổi thong_so_chi_tiet sang chuỗi JSON
        thong_so_json = json.dumps(thong_so_chi_tiet, ensure_ascii=False)
        
        # Lấy lịch sử dòng xe
        lich_su = item.get("lich_su")
        
        # Chèn bản ghi vào bảng phuong_tien
        cursor.execute("""
            INSERT INTO phuong_tien (
                hang_id, dong_xe, nam_san_xuat, loai_xe, loai_nhien_lieu, 
                dong_co, tinh_trang_san_xuat, gia_niem_yet, xuat_xu, 
                hinh_anh_url, url_chi_tiet, thong_so_chi_tiet, lich_su
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            hang_id, dong_xe, nam_san_xuat, loai_xe, loai_nhien_lieu,
            dong_co, tinh_trang_san_xuat, gia_niem_yet, xuat_xu,
            hinh_anh_url, url_chi_tiet, thong_so_json, lich_su
        ))
        imported_count += 1

    conn.commit()
    conn.close()
    print(f"-> Thành công! Đã nhập {imported_count} dòng xe vào bảng phuong_tien.")

def run_test_queries():
    """Chạy thử nghiệm truy vấn dữ liệu động bằng JSON"""
    print("\n=== CHẠY TRUY VẤN KIỂM THỬ ===")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 1. Truy vấn các hãng xe có trong DB
    print("\n--- Danh sách hãng xe ---")
    cursor.execute("SELECT id, ten_hang FROM hang_xe LIMIT 5")
    for row in cursor.fetchall():
        print(f"ID: {row[0]} | Tên hãng: {row[1]}")
        
    # 2. Tìm xe ô tô có số chỗ ngồi cụ thể (Sử dụng hàm trích xuất JSON trong SQLite)
    print("\n--- Lọc xe ô tô có số chỗ ngồi là 5 hoặc 7 (sử dụng json_extract) ---")
    cursor.execute("""
        SELECT h.ten_hang, p.dong_xe, p.loai_xe, json_extract(p.thong_so_chi_tiet, '$.so_cho_ngoi') as so_cho
        FROM phuong_tien p
        JOIN hang_xe h ON p.hang_id = h.id
        WHERE so_cho IN ('5', '7', 5, 7)
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"Hãng: {row[0]} | Dòng xe: {row[1]} | Loại: {row[2]} | Số chỗ: {row[3]}")
        
    # 3. Lọc xe tải và lấy thông tin tải trọng từ trường JSON
    print("\n--- Lọc danh sách xe tải có tải trọng cho phép ---")
    cursor.execute("""
        SELECT h.ten_hang, p.dong_xe, p.loai_xe, json_extract(p.thong_so_chi_tiet, '$.dac_tinh_xe_tai.tai_trong_cho_phep_kg') as tai_trong
        FROM phuong_tien p
        JOIN hang_xe h ON p.hang_id = h.id
        WHERE p.loai_xe LIKE '%tải%' OR json_extract(p.thong_so_chi_tiet, '$.dac_tinh_xe_tai') IS NOT NULL
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"Hãng: {row[0]} | Dòng xe: {row[1]} | Loại: {row[2]} | Tải trọng: {row[3]} kg")

    # 4. Truy vấn lịch sử dòng xe và phiên bản (Trims) mẫu từ Wikipedia/CarQuery
    print("\n--- Truy vấn lịch sử dòng xe và phiên bản mẫu ---")
    cursor.execute("""
        SELECT h.ten_hang, p.dong_xe, p.lich_su, json_extract(p.thong_so_chi_tiet, '$.cac_phien_ban') as phien_ban
        FROM phuong_tien p
        JOIN hang_xe h ON p.hang_id = h.id
        WHERE p.lich_su IS NOT NULL AND p.lich_su NOT LIKE '%chưa được cập nhật%'
        LIMIT 2
    """)
    for row in cursor.fetchall():
        pb_list = json.loads(row[3]) if row[3] else []
        pb_names = [f"{pb.get('phien_ban')} ({pb.get('nam')})" for pb in pb_list[:2]]
        print(f"Hãng: {row[0]} | Dòng xe: {row[1]}")
        print(f"  Lịch sử: {row[2][:200]}...")
        print(f"  Phiên bản mẫu: {', '.join(pb_names)}")

    conn.close()

if __name__ == "__main__":
    init_database()
    normalize_and_import()
    run_test_queries()
