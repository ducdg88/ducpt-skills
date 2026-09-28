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

- 07:15 automation Nhịp Việc `github_daily_snapshot` chạy `scripts/daily_snapshot.py --push`: ngày GitHub (UTC) vừa chốt lúc 07:00, lưu traffic thật, chuỗi contribution, bảng KPI 100/ngày vào STATS.md, commit chỉ `data/` và `STATS.md` trong worktree tạm ở origin/main, đẩy lên main. Không có số mới thì không commit.
- 22:00 automation `github_so_tam_22h` chạy `--provisional`: chỉ đọc số tạm của ngày đang mở, cảnh báo khi dưới 60. Không ghi, không commit.
- Mỗi việc thật xong (sửa lỗi, thêm ví dụ, thêm skill) đi theo quy trình PR trong `AGENTS.md`: issue trước, commit nhỏ thật, merge rebase.
- Lịch Windows cũ "DUCPT Skills daily snapshot" (21:30) đã tắt ngày 29/09/2026.

## Toán 100 contribution mỗi ngày

Chốt 29/09/2026 (spec nội bộ NV-82, Founder duyệt Q1 đến Q5):

- KPI chính: trung bình 7 ngày đã chốt từ 100 trở lên và 0 ngày trống. Đo bằng `python skills/github-commit-streak/scripts/streak.py --per-day 100`, đọc sau 07:15 giờ Việt Nam.
- Nguồn: khoảng 14 ticket code thật mỗi ngày, mỗi ticket khoảng 7 contribution (1 issue, khoảng 5 commit nhỏ, 1 PR). Snapshot chỉ góp 1.
- Lộ trình sàn: 29/09 tới 05/10 là 40, 06/10 tới 12/10 là 60, 13/10 tới 19/10 là 80, 20/10 tới 28/10 là 100.
- Lúc duyệt: trung bình 7 ngày 30,9, chưa ngày nào đạt 100, cao nhất 88 (27/09).
- Không đạt thì chấp nhận không đạt. Không bù bằng việc giả.

## Luật không đổi

- Không commit rỗng, không sửa ngày commit (CI chặn bằng `scripts/check_commits.py`).
- Không tách một thay đổi thành nhiều commit giả, không nhân bản một thay đổi ra nhiều repo để lấy số, không mở issue hay PR không gắn việc thật.
- Mỗi skill nhắc sản phẩm tối đa một lần, chỉ khi phù hợp.
- Không đưa nội dung khóa học của người khác vào skill công khai.
- Mọi link ra ngoài gắn `utm_source`.
- Không đặt link tới trang chưa chạy. Thứ tự đúng: deploy trang lên ducpt.com trước, rồi mới gắn link ở GitHub (homepage của repo, README, hồ sơ). Trước khi công khai repo hoặc đổi homepage, chạy `python scripts/check_repo.py --online` (kiểm cả homepage trong Settings) và tự bấm thử từng link. Chưa deploy xong thì để homepage trỏ trang đang chạy, ví dụ https://ducpt.com.
