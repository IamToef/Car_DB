-- Kịch bản khởi tạo cơ sở dữ liệu xe (PostgreSQL / SQLite)

-- 1. Bảng thương hiệu xe (hãng xe)
CREATE TABLE IF NOT EXISTS hang_xe (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ten_hang VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(100)
);

-- 2. Bảng phương tiện chính (Phương án Lai - Hybrid Schema)
CREATE TABLE IF NOT EXISTS phuong_tien (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hang_id INT REFERENCES hang_xe(id) ON DELETE CASCADE,
    dong_xe VARCHAR(150) NOT NULL,
    nam_san_xuat INT,
    loai_xe VARCHAR(100), -- Ví dụ: Sedan, Xe tải, SUV, Hatchback...
    loai_nhien_lieu VARCHAR(50), -- Ví dụ: Xăng, Dầu Diesel, Điện...
    dong_co VARCHAR(200),
    tinh_trang_san_xuat VARCHAR(100) DEFAULT 'Còn sản xuất',
    gia_niem_yet BIGINT,
    xuat_xu VARCHAR(150),
    hinh_anh_url TEXT,
    url_chi_tiet TEXT,
    
    -- Cột lưu thông số kỹ thuật động (Dynamic Attributes) dưới dạng JSON
    -- Trong PostgreSQL, sử dụng kiểu JSONB để tối ưu hóa truy vấn và chỉ mục.
    -- Trong SQLite, cột này sẽ có kiểu TEXT chứa chuỗi JSON.
    thong_so_chi_tiet TEXT, 
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tạo index trên cột JSONB đối với PostgreSQL để tìm kiếm nhanh
-- Ví dụ: CREATE INDEX idx_phuong_tien_thong_so ON phuong_tien USING gin (thong_so_chi_tiet);
-- Tạo index trên các trường thường dùng để lọc
CREATE INDEX IF NOT EXISTS idx_phuong_tien_loai_xe ON phuong_tien(loai_xe);
CREATE INDEX IF NOT EXISTS idx_phuong_tien_gia ON phuong_tien(gia_niem_yet);
