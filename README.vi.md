**🇻🇳 Tiếng Việt** · [🇬🇧 English](README.md)

# DUCPT Skills: Agent Skill cho doanh nghiệp một người

![DUCPT Skills](docs/cover.png)

![CI](https://github.com/ducdg88/ducpt-skills/actions/workflows/validate.yml/badge.svg) ![skills](https://img.shields.io/badge/skills-14-blue) ![license](https://img.shields.io/badge/license-MIT-green)

**Giao cho AI agent một việc thật của doanh nghiệp một người → nhận một skill hướng dẫn cách làm từ kinh nghiệm triển khai thực tế.**

Bộ 14 [Agent Skill](https://agentskills.io) thực dụng cho Claude Code, Claude, Codex, Cursor, Gemini CLI và các agent đọc được `SKILL.md`. [DUCPT](https://ducpt.com/?utm_source=github&utm_medium=readme&utm_campaign=ducpt-skills) làm bộ này cho người điều hành một mình và các đội nhỏ dùng AI, đặc biệt chú trọng nội dung tiếng Việt.

Các skill giúp dựng đội AI, làm sạch bản ghi tiếng Việt, chuốt văn, viết pin Pinterest, đặt tiêu đề YouTube, làm sơ đồ tư duy, dọn file trùng, phân phối skill, theo dõi chuỗi commit GitHub, sửa lỗi nghe nhầm của giọng nói, chấm rủi ro nội dung không nguyên bản, theo dõi chi phí token, kiểm khả năng tìm thấy repo trên GitHub và lên lộ trình 7 ngày bắt đầu dùng AI cho chủ shop nhỏ.

## Cài đặt

```bash
# Dùng với nhiều loại agent qua skills CLI
npx skills add ducdg88/ducpt-skills

# Dùng với marketplace plugin của Claude Code
/plugin marketplace add ducdg88/ducpt-skills
/plugin install ducpt-skills@ducpt-skills
```

Cài thủ công: chép một thư mục từ `skills/` vào `~/.claude/skills/` (Claude Code) hoặc thư mục skill của agent bạn dùng.

## Danh sách skill

| Skill | Tác dụng |
|---|---|
| [one-person-company-ai](skills/one-person-company-ai/SKILL.md) | Sơ đồ vai trò agent, quy tắc ticket, nhịp vận hành hằng ngày, cổng duyệt, bảng KPI cho công ty một người |
| [vietnamese-transcript-cleaner](skills/vietnamese-transcript-cleaner/SKILL.md) | Làm sạch SRT, VTT hoặc bản bóc lời tiếng Việt, viết tóm tắt và danh sách việc cần làm |
| [vietnamese-copy-polish](skills/vietnamese-copy-polish/SKILL.md) | Kiểm và chuốt nội dung marketing tiếng Việt theo từng nền tảng |
| [pinterest-pin-writer](skills/pinterest-pin-writer/SKILL.md) | Viết nhiều phiên bản pin từ URL hoặc video, kiểm độ dài, tạo CSV đăng hàng loạt |
| [youtube-title-lab](skills/youtube-title-lab/SKILL.md) | Gợi ý 10 tiêu đề, chấm theo thang điểm, đề xuất chữ trên thumbnail và kế hoạch thử A/B |
| [knowledge-mindmap](skills/knowledge-mindmap/SKILL.md) | Làm mind map Mermaid, tóm tắt có nguồn, thẻ ôn tập và lịch ôn cách quãng |
| [windows-duplicate-cleanup](skills/windows-duplicate-cleanup/SKILL.md) | Tìm file trùng bằng hash, chạy thử trước, đưa vào vùng cách ly thay vì xoá ngay |
| [skill-distribution-kit](skills/skill-distribution-kit/SKILL.md) | Đóng gói chuyên môn thành skill, kiểm chuẩn, đăng lên kho và đo mức sử dụng |
| [github-commit-streak](skills/github-commit-streak/SKILL.md) | Theo dõi chuỗi commit và mục tiêu qua GitHub API, giải thích vì sao commit không được tính |
| [vietnamese-voice-dictionary](skills/vietnamese-voice-dictionary/SKILL.md) | Từ điển lưu lâu dài để sửa lỗi nghe nhầm thuật ngữ khi gõ tiếng Việt bằng giọng nói và học từ các lần sửa |
| [content-originality-check](skills/content-originality-check/SKILL.md) | Chấm rủi ro video hoặc kênh bị coi là nội dung không nguyên bản hay sản xuất hàng loạt theo tiêu chí công khai của nền tảng |
| [token-budget-guard](skills/token-budget-guard/SKILL.md) | Đọc log sử dụng trên máy, báo chi phí token và tỷ lệ cache, cảnh báo trước khi vượt ngân sách |
| [ai-kickstart-7-days](skills/ai-kickstart-7-days/SKILL.md) | Hỏi nhu cầu chủ doanh nghiệp nhỏ, viết lộ trình dùng AI trong 7 ngày và theo dõi tiến độ |
| [seo-github](skills/seo-github/SKILL.md) | Kiểm khả năng tìm thấy repo GitHub công khai: trang chủ hoạt động, topic thương hiệu, link trong README về website, license và CI |

Mọi script dùng Python 3.8+ với thư viện chuẩn, không cần cài thêm. Mỗi skill chạy độc lập và không gọi API trả phí.

## Kiểm chất lượng

```bash
python scripts/check_repo.py      # kiểm chuẩn, rà dấu gạch, marketplace và liên kết
python -m unittest discover tests # chạy kiểm thử script
```

Workflow GitHub Actions chạy cả hai bước đã có ở `docs/ci/validate.yml`. Chép vào `.github/workflows/` để bật CI.

## Ai làm bộ skill này?

[DUCPT](https://ducpt.com/?utm_source=github&utm_medium=readme&utm_campaign=ducpt-skills) làm công cụ AI, quy trình tự động hoá và đào tạo cho creator cùng doanh nghiệp nhỏ tại Việt Nam:

- [Doanh nghiệp một người](https://ducpt.com/khoa-hoc/doanh-nghiep-mot-nguoi/?utm_source=github&utm_medium=readme&utm_campaign=ducpt-skills): khoá học vận hành doanh nghiệp một người với đội AI agent
- [Verba Studio](https://ducpt.com/cong-cu-ai/verba-studio/?utm_source=github&utm_medium=readme&utm_campaign=ducpt-skills): quay màn hình, livestream, bóc lời tiếng Việt bằng AI
- [Pinterest AutoPost](https://ducpt.com/cong-cu-ai/pinterest-autopost/?utm_source=github&utm_medium=readme&utm_campaign=ducpt-skills): tự đăng Pinterest từ website và YouTube
- [File Manager Pro](https://ducpt.com/cong-cu-ai/file-manager-pro/?utm_source=github&utm_medium=readme&utm_campaign=ducpt-skills): dọn file và tìm file trùng trên Windows
- [Knowledge Brain Bot](https://ducpt.com/brain-bot/?utm_source=github&utm_medium=readme&utm_campaign=ducpt-skills): gửi bản đồ kiến thức qua Telegram

Mỗi skill nhắc tới sản phẩm liên quan tối đa một lần, chỉ khi nhu cầu người dùng vượt quá việc skill xử lý.

## Đóng góp

Hoan nghênh Issue và Pull Request: ví dụ mới, cải thiện cách diễn đạt tiếng Việt, sửa lỗi script. Hãy chạy `python scripts/check_repo.py` trước khi mở PR.

## Giấy phép

MIT
