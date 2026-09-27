# Nhật ký cải tiến skill seo-github

Đọc file này ở ĐẦU mỗi lần chạy skill. Ghi vào CUỐI file mỗi khi Founder chỉ ra một chỗ thiếu
hoặc một yêu cầu mới, để không phải nhắc lại lần hai. Đây là bộ nhớ sống của skill, không phải
nhật ký để đọc rồi bỏ.

## Yêu cầu của Founder (áp cho mọi lần chạy)

- 27/09/2026: Từ nay, **mọi dự án tải lên GitHub đều phải qua checklist skill `seo-github`**
  trước khi coi là xong, không chỉ khi Founder hỏi. Đây là một hướng đi duy nhất, không có
  ngoại lệ ngầm.
- 27/09/2026: Không được chỉ phát hiện thiếu rồi để đó. Founder nói "bổ sung" là phải bổ sung
  ngay, chạy lại script xác nhận xanh thật, rồi mới báo xong.
- 27/09/2026: Repo đang có nội dung thật đang chạy (không phải 0 byte, không phải vừa tạo trong
  vài phút) thì áp checklist ngay, không viện lý do "có thể ai đó đang làm dở" để hoãn. Chỉ hoãn
  khi repo thật sự trống (size 0, mới tạo trong vòng vài phút) và nói rõ lý do hoãn.
- 27/09/2026: Bất kể domain riêng của sản phẩm là gì (ví dụ verbar.io khác ducpt.com), homepage
  của repo GitHub đặt về đúng trang sống của repo đó; README vẫn phải có một liên kết về
  ducpt.com hoặc trang sản phẩm tương ứng trên ducpt.com kèm `utm_source=github`.

## Bài học khi tham khảo repo khác để học SEO

- 27/09/2026: Trước khi coi một repo là "top" đáng học theo, kiểm tỉ lệ sao/watcher/follower.
  Tìm theo `topic:architecture-diagram` trên GitHub ra repo `tt-a1i/archify` 72.618 sao nhưng
  chỉ 209 watcher và chủ tài khoản 1.730 follower, tỉ lệ lệch bất thường, dấu hiệu bơm sao ảo.
  Không copy pattern từ repo này.
- 27/09/2026: `aws-solutions/workload-discovery-on-aws` (831 sao, repo chính thức AWS) đã ngừng
  phát triển (thông báo discontinued ngay đầu README). Sao cao không có nghĩa còn giá trị tham
  khảo hôm nay; luôn kiểm `pushed_at` và có thông báo ngừng không trước khi học theo.
- 27/09/2026: `sverweij/dependency-cruiser` (7.224 sao, dự án lâu năm, đáng tin) chèn ảnh chụp
  kết quả thật ngay dưới heading đầu tiên, trước cả phần cài đặt. Không bắt buộc thành FAIL/WARN
  cho moi repo (Founder da co OG image rieng tren website cho cac trang san pham), chi ghi lai
  lam goi y: repo la cong cu/CLI thuc su nen chen anh chup man hinh hoac dien luu do that trong
  README, cang som cang tot.

## Bài học kỹ thuật

- 27/09/2026: `subprocess.run(..., text=True)` trên Windows dùng bảng mã cp1252 mặc định, vỡ
  chữ tiếng Việt UTF-8 từ `gh`. Luôn `capture_output=True` (không `text=True`) rồi tự
  `.decode("utf-8")`.
- 27/09/2026: Repo chưa có commit nào (`repository is empty`) và repo không có README
  (`Not Found`) là hai lỗi 404 khác câu chữ nhau; phải bắt cả hai để không crash.
- 27/09/2026: Repo chưa clone local thì tạo/sửa file qua GitHub Contents API
  (`gh api -X PUT .../contents/<file> --input -`), không cần clone.

## Phản hồi sau từng lần chạy

<!-- YYYY-MM-DD · repo · điều Founder sửa hoặc yêu cầu thêm -->
- 27/09/2026 · toàn bộ 20 repo công khai · nâng "topics phải có brand ducpt" từ cảnh báo thành
  bắt buộc theo yêu cầu Founder; thêm nhận diện repo Build to Own (`bto-*`) để không ép quảng bá
  vào bài nộp học.
- 27/09/2026 · verbar.io · Founder chỉ ra repo có nội dung thật (trang verbar.io đang sống) mà
  bị bỏ qua vì tưởng đang tạo dở; đã bổ sung homepage, topics, mô tả, README.
- 27/09/2026 · dg-ops-skills · Founder chấm "tên sai, sơ sài, thiếu checklist": chính repo chứa
  skill này cũng fail 3/3; đã sửa mô tả, homepage, topics, viết lại README, thêm mục license và
  scan-secrets vào script.
- 27/09/2026 · so sánh thêm 8 repo của sonpiaz (github.com/sonpiaz) để tìm mục còn thiếu, không
  chỉ nhìn 1 repo: 6/8 có LICENSE (2 ngoại lệ là repo thử nghiệm và kênh phát hành), 4/8 có CI
  thật. Thêm 2 mục WARN: license (FAIL nếu public mà thiếu, trừ repo private/kênh phát hành),
  CI workflow thật trong `.github/workflows/`.
