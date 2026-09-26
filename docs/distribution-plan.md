# Kế hoạch phân phối DUCPT Skills

Mục tiêu: skill mở mã nguồn trở thành kênh phân phối tự chạy, kéo người dùng và AI về ducpt.com, đồng thời mỗi ngày có đóng góp thật trên GitHub.

## Đầu việc theo tuần

| Tuần | Việc | Ai làm | Bằng chứng xong |
|---|---|---|---|
| 1 | Bật repo công khai, gắn topics, ảnh social preview | Founder bấm, agent chuẩn bị | Repo public, 12 topics |
| 1 | Deploy trang ducpt.com/skills/ (nhánh feat/skills-hub) | Founder duyệt merge | 10 URL trả 200 |
| 1 | Search Console: gửi lại sitemap | Founder | Sitemap đọc được 28 URL |
| 1 | Thử `npx skills add ducdg88/ducpt-skills` trên máy sạch | Agent | Ảnh chụp terminal |
| 1 | Nộp ClawHub, claude-plugins-community | Founder đăng nhập, agent soạn nội dung | Link listing |
| 2 | PR vào 3 đến 5 awesome-list | Agent soạn PR, Founder duyệt gửi | Link PR |
| 2 | Mỗi skill 1 bài blog tiếng Việt trên ducpt.com/bai-viet | Agent viết, Founder duyệt | 9 URL 200 |
| 3 | Bài FB, nhóm Claude AI Việt Nam, Viblo: kể chuyện gốc kèm số thật | Agent soạn, Founder đăng | Link bài |
| 3 | Thêm 3 skill mới từ quy trình thật của Founder | Agent | check_repo PASS |
| 4 | Đọc STATS.md: kênh nào ra clone thì làm mạnh kênh đó | Agent báo cáo | Báo cáo tuần |

## Nhịp hằng ngày

- 21:30 máy tự chạy `scripts/daily_snapshot.py --push`: lưu traffic thật, chuỗi contribution, cập nhật STATS.md, commit và đẩy lên. Không có số mới thì không commit.
- Mỗi việc thật xong (sửa lỗi, thêm ví dụ, thêm skill) là một commit nhỏ, email đã gắn tài khoản.

## Toán 10.000 contribution

Tính đến 26/09/2026: 101 contribution trong 365 ngày, chuỗi hiện tại 3 ngày. Muốn đủ 10.000 trong 12 tháng cần khoảng 27 mỗi ngày. Nhịp snapshot tự động chỉ góp 1 mỗi ngày; phần còn lại phải đến từ việc thật được commit nhỏ, đúng email.

## Luật không đổi

- Không commit rỗng, không sửa ngày commit.
- Mỗi skill nhắc sản phẩm tối đa một lần, chỉ khi phù hợp.
- Không đưa nội dung khóa học của người khác vào skill công khai.
- Mọi link ra ngoài gắn `utm_source`.
