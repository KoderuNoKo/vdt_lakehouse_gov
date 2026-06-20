DROP TABLE IF EXISTS clerk_notes_templates CASCADE;
DROP TABLE IF EXISTS record_statuses CASCADE;
DROP TABLE IF EXISTS service_types CASCADE;

-- =========================================================================
-- TABLE 1: Service Types (Các loại hình dịch vụ hành chính)
-- =========================================================================

CREATE TABLE service_types (
    id SERIAL PRIMARY KEY,
    service_name_vn VARCHAR(255) NOT NULL,
    service_name_en VARCHAR(255) NOT NULL
);

INSERT INTO service_types (id, service_name_vn, service_name_en) VALUES
(1, 'Cấp đổi Căn cước công dân', 'Citizen Identification Card Renewal'),
(2, 'Đăng ký khai sinh', 'Birth Registration'),
(3, 'Đăng ký kinh doanh', 'Business Registration'),
(4, 'Đăng ký kết hôn', 'Marriage Registration'),
(5, 'Cấp giấy phép xây dựng', 'Construction Permit Issuance');

-- =========================================================================
-- TABLE 2: Record Statuses (Trạng thái hồ sơ)
-- =========================================================================
CREATE TABLE record_statuses (
    id SERIAL PRIMARY KEY,
    status_en VARCHAR(50) NOT NULL,
    status_vn VARCHAR(255) NOT NULL
);

INSERT INTO record_statuses (id, status_en, status_vn) VALUES
(1, 'PENDING', 'Đang chờ tiếp nhận'),
(2, 'PROCESSING', 'Đang thẩm định/xử lý'),
(3, 'ADDITIONAL_INFO_REQUIRED', 'Yêu cầu bổ sung hồ sơ'),
(4, 'APPROVED', 'Đã duyệt/Hoàn thành'),
(5, 'REJECTED', 'Bị từ chối');

-- =========================================================================
-- TABLE 3: Clerk Notes Templates (Mẫu ghi chú của cán bộ)
-- =========================================================================
CREATE TABLE clerk_notes_templates (
    id SERIAL PRIMARY KEY,
    service_type_id INT REFERENCES service_types(id),
    status_id INT REFERENCES record_statuses(id),
    contain_pii BOOLEAN DEFAULT FALSE,
    clerk_note TEXT NOT NULL
);

-- Bơm dữ liệu (Templates kết hợp các trường hợp sạch và trường hợp chứa PII)
INSERT INTO clerk_notes_templates (service_type_id, status_id, contain_pii, clerk_note) VALUES

-- ==========================================
-- 1. Cấp đổi CCCD
-- ==========================================
(1, 1, FALSE, 'Hồ sơ công dân nộp qua cổng dịch vụ công trực tuyến, đang chờ phân công người thẩm định ban đầu.'),
(1, 2, FALSE, 'Đang kiểm tra chéo thông tin nhân trắc học trên cơ sở dữ liệu quốc gia về dân cư.'),
(1, 3, TRUE,  'Yêu cầu công dân đến cơ quan công an để chụp lại ảnh chân dung do ảnh cũ không đạt tiêu chuẩn. Cán bộ phụ trách liên hệ qua SĐT ${phone_number} để hẹn lịch.'),
(1, 4, FALSE, 'Hồ sơ cấp đổi hợp lệ. Đã tiến hành in thẻ và bàn giao cho bưu điện phát trả về địa chỉ thường trú.'),
(1, 5, TRUE,  'Hồ sơ bị từ chối do dấu vân tay cung cấp không khớp với dữ liệu gốc của số CCCD ${national_id} trên hệ thống.'),

-- ==========================================
-- 2. Đăng ký khai sinh
-- ==========================================
(2, 1, TRUE,  'Tiếp nhận hồ sơ đăng ký khai sinh bản cứng trực tiếp tại bộ phận một cửa. Người đi khai sinh: ${full_name}.'),
(2, 2, FALSE, 'Đang gửi yêu cầu xác minh thông tin giấy chứng sinh với bệnh viện phụ sản tuyến tỉnh.'),
(2, 3, TRUE,  'Thiếu bản sao công chứng CCCD của người cha. Vui lòng bổ sung bản scan qua hòm thư điện tử ${email} để tiếp tục xử lý.'),
(2, 4, FALSE, 'Đã cấp giấy khai sinh bản chính và 02 bản sao trích lục khai sinh cho gia đình.'),
(2, 5, FALSE, 'Từ chối giải quyết hồ sơ do người đi khai sinh không cung cấp được giấy chứng sinh hợp lệ hoặc văn bản xác nhận của người làm chứng.'),

-- ==========================================
-- 3. Đăng ký kinh doanh
-- ==========================================
(3, 1, FALSE, 'Tiếp nhận hồ sơ thành lập doanh nghiệp mới trên Cổng thông tin quốc gia về đăng ký doanh nghiệp.'),
(3, 2, FALSE, 'Phòng Đăng ký kinh doanh đang thẩm định tính hợp lệ của tên doanh nghiệp dự kiến và các ngành nghề kinh doanh có điều kiện.'),
(3, 3, TRUE,  'Biên bản họp hội đồng thành viên thiếu chữ ký của cổ đông sáng lập. Đã nhắn tin thông báo bổ sung hồ sơ tới số ${phone_number}.'),
(3, 4, TRUE,  'Hồ sơ hợp lệ. Đã cấp Giấy chứng nhận đăng ký doanh nghiệp. Mã số thuế cấp mới là ${national_id}.'),
(3, 5, TRUE,  'Từ chối cấp phép do trùng tên doanh nghiệp đã đăng ký trước đó. Hoàn trả lệ phí đăng ký 200,000 VND vào STK ${bank_account} tại ngân hàng Techcombank.'),

-- ==========================================
-- 4. Đăng ký kết hôn
-- ==========================================
(4, 1, FALSE, 'Hồ sơ nộp trực tiếp tại UBND phường/xã.'),
(4, 2, FALSE, 'Đang tiến hành niêm yết công khai và xác minh tình trạng hôn nhân của nam/nữ tại địa phương nơi cư trú.'),
(4, 3, TRUE,  'Yêu cầu nộp bản gốc giấy xác nhận tình trạng hôn nhân của công dân có số định danh ${national_id} để đối chiếu xác minh chéo.'),
(4, 4, FALSE, 'Đã ký và cấp Giấy chứng nhận kết hôn bản chính cho hai bên nam nữ. Hồ sơ lưu trữ theo quy định.'),
(4, 5, FALSE, 'Bị từ chối do hệ thống quản lý hộ tịch ghi nhận một trong hai bên vẫn đang trong tình trạng hôn nhân (chưa có quyết định ly hôn của tòa án).'),

-- ==========================================
-- 5. Cấp giấy phép xây dựng
-- ==========================================
(5, 1, FALSE, 'Tiếp nhận hồ sơ xin cấp phép xây dựng nhà ở riêng lẻ tại đô thị.'),
(5, 2, FALSE, 'Đang cử cán bộ quản lý trật tự đô thị xuống hiện trường để đo đạc và đối chiếu ranh giới thửa đất so với bản vẽ thiết kế.'),
(5, 3, TRUE,  'Bản vẽ thiết kế thi công chưa thể hiện rõ hệ thống xử lý nước thải. Yêu cầu chủ đầu tư nộp lại bản vẽ đã chỉnh sửa qua email ${email}.'),
(5, 4, FALSE, 'Đã cấp giấy phép xây dựng và đóng dấu bản vẽ kỹ thuật. Chủ đầu tư mang biên nhận đến bộ phận một cửa để nhận kết quả.'),
(5, 5, TRUE,  'Hồ sơ bị từ chối do diện tích xin phép xây dựng nằm hoàn toàn trong quy hoạch công viên cây xanh. Quyết định hoàn phí thẩm định vào tài khoản ${bank_account}.');