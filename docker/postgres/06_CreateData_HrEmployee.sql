-- ============================================================
-- CLEAN UP
-- ============================================================
-- DROP TABLE IF EXISTS hr_remarks_templates CASCADE;
-- DROP TABLE IF EXISTS departments CASCADE;

-- =========================================================================
-- TABLE: Departments (Phòng ban)
-- =========================================================================
CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    department_name VARCHAR(255) NOT NULL
);

INSERT INTO departments (department_name) VALUES
('Phòng Nhân sự'),
('Phòng Kế toán'),
('Phòng Kinh doanh'),
('Phòng Marketing'),
('Phòng IT'),
('Phòng Hành chính'),
('Phòng R&D'),
('Phòng Sản xuất'),
('Phòng Pháp chế'),
('Phòng Chăm sóc khách hàng');

-- =========================================================================
-- TABLE: HR Remarks Templates (Mẫu ghi chú nhân sự)
-- =========================================================================
CREATE TABLE hr_remarks_templates (
    id SERIAL PRIMARY KEY,
    contain_pii BOOLEAN DEFAULT FALSE,
    template_text TEXT NOT NULL
);

INSERT INTO hr_remarks_templates (contain_pii, template_text) VALUES
-- Clean remarks (no PII)
(FALSE, 'Nhân viên hoàn thành KPI quý đạt 120%. Đề xuất tăng lương.'),
(FALSE, 'Đã ký hợp đồng lao động chính thức từ ngày 01/01/2025.'),
(FALSE, 'Nhân viên xin nghỉ phép không lương 2 tuần.'),
(FALSE, 'Chuyển từ bộ phận Kinh doanh sang Marketing theo quyết định của Ban Giám đốc.'),
(FALSE, 'Đánh giá cuối năm: Xuất sắc. Được bổ nhiệm làm Team Leader.'),
(FALSE, 'Nhân viên thử việc, đánh giá sau 2 tháng.'),
(FALSE, 'Đã hoàn tất khóa đào tạo nội bộ về ATTT.'),
(FALSE, 'Nghỉ thai sản từ tháng 3 đến tháng 9.'),
(FALSE, 'Hợp đồng kết thúc ngày 31/12/2025. Chờ gia hạn.'),
(FALSE, ''),

-- PII-containing remarks
(TRUE, 'Yêu cầu cập nhật STK lương mới: ${bank_account} tại Vietcombank.'),
(TRUE, 'Liên hệ khẩn cấp: ${emergency_name} - ${phone_number}.'),
(TRUE, 'Nhân viên báo mất thẻ CCCD. Số CCCD cũ: ${national_id}. Đang chờ cấp lại.'),
(TRUE, 'Gửi phiếu lương tháng 5 qua email ${email}.'),
(TRUE, 'MST cá nhân cần cập nhật trên hệ thống: ${tax_id}.'),
(TRUE, 'Chuyển lương tháng 6 vào STK ${bank_account}. SĐT xác nhận: ${phone_number}.');
