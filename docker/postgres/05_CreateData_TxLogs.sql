DROP TABLE IF EXISTS tx_message_templates CASCADE;

CREATE TABLE tx_message_templates (
    id SERIAL PRIMARY KEY,
    contain_pii BOOLEAN DEFAULT FALSE,
    template_text TEXT NOT NULL
);

INSERT INTO tx_message_templates (contain_pii, template_text) VALUES
(FALSE, 'Chuyen tien an trua nay nhe'),
(FALSE, 'Thanh toan tien nha thang 6'),
(FALSE, 'Chuyen khoản mua laptop Macbook Pro'),
(FALSE, 'Tra tien cafe hom qua'),
(FALSE, 'Vu Nguyen thanh toan tien dien nuoc'),
(FALSE, 'Chuyen tien luong thang nay'),

(TRUE, 'Tien dat coc vay tien, sdt lien he ${phone_number} nhe'),
(TRUE, 'Thanh toan don hang, xuat hoa don cho MST ${tax_id}'),
(TRUE, 'Tra tien cho STK ${bank_account} ho minh nhe, cam on'),
(TRUE, 'Gui hop dong va bien lai vao email ${email} sau khi nhan duoc tien'),
(TRUE, 'Chuyen khoan giu cho. Dung sdt ${phone_number} de goi nhan hang nhe'),
(TRUE, 'Phi dich vu thang 5. Tai khoan nhan: ${bank_account}');


DROP TABLE IF EXISTS fraud_note_templates CASCADE;

CREATE TABLE fraud_note_templates (
    id SERIAL PRIMARY KEY,
    contain_pii BOOLEAN DEFAULT FALSE,
    template_text TEXT NOT NULL
);

INSERT INTO fraud_note_templates (contain_pii, template_text) VALUES
(FALSE, 'Giao dịch bình thường, không có dấu hiệu đáng ngờ. Đã đối chiếu tự động với profile khách hàng.'),
(FALSE, 'Tài khoản nhận có lịch sử giao dịch nhận tiền liên tục trong ngày, nhưng vẫn nằm trong hạn mức cho phép.'),
(FALSE, 'Hệ thống AML (Anti-Money Laundering) cảnh báo rủi ro thấp. Bỏ qua.'),
(FALSE, 'Khách hàng gọi lên tổng đài xác nhận đây là giao dịch do chính chủ thực hiện. Đã gỡ phong tỏa.'),
(FALSE, 'Giao dịch thực hiện trên thiết bị lạ, nhưng xác thực sinh trắc học thành công. Hợp lệ.'),

(TRUE, 'Giao dịch bị AML đưa vào danh sách nghi ngờ rửa tiền. Yêu cầu ra quầy xác minh lại CCCD số ${national_id} của người nhận.'),
(TRUE, 'Phát hiện đăng nhập bất thường từ IP nước ngoài. Đã khóa tạm thời thẻ tín dụng liên kết và gửi mã mở khóa về số ${phone_number}.'),
(TRUE, 'Khách hàng khiếu nại chuyển nhầm tiền do sai 1 số cuối. Yêu cầu bộ phận thẻ tiến hành tra soát và tạm khóa STK thụ hưởng ${bank_account}.'),
(TRUE, 'Tài khoản doanh nghiệp có dấu hiệu giao dịch khống để hoàn thuế. Cần báo cáo lên cơ quan chức năng theo MST ${tax_id} và gửi cảnh báo tới ${email}.'),
(TRUE, 'Nghi ngờ lừa đảo chiếm đoạt tài sản. Số điện thoại ${phone_number} của người nhận từng bị report trên hệ thống. Số CCCD đăng ký mở tài khoản là ${national_id}. Đóng băng số dư tức thì.'),
(TRUE, 'Khách hàng cung cấp sai thông tin định danh. Email đăng ký ban đầu là ${email} không khớp với email hiện tại. Chờ xác minh lại.');