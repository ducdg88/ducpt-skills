# Working on this repo (agents and people)

Tiếng Việt ở dưới.

## Pull request flow

1. **Issue first.** Open an issue that states the real task before writing code. Skip it only for typo fixes.
2. **Own branch.** One branch per task, named after the issue or ticket (`fix-12-srt-timestamps`, `nv-82/impl`). Never commit straight to `main`.
3. **Small real commits.** Each commit is one step that works on its own: a test, the fix, the docs. Do not split one change into fake steps, do not make empty commits, do not change commit dates. CI refuses empty commits and messages with a literal `\n` (`scripts/check_commits.py`).
4. **PR closes the issue.** Write `Closes #<n>` in the PR description.
5. **Merge with rebase.** Use "Rebase and merge" so the small commits stay on `main`. No squash.
6. **Gate.** `python scripts/check_repo.py` and `python -m unittest discover -s tests` pass before the PR is opened.

Author email must be the account's verified or noreply address, or the work does not show on the contribution graph. Check with `python scripts/check_commit_emails.py <repo paths>`.

Never touched by agents without the owner's approval: pushing to `main`, merging, publishing to registries or other people's repos, changing repo settings.

---

# Làm việc trên repo này (agent và người)

## Quy trình pull request

1. **Issue trước.** Mở issue nêu việc thật trước khi code. Chỉ bỏ qua khi sửa lỗi chính tả.
2. **Nhánh riêng.** Mỗi việc một nhánh, đặt tên theo issue hoặc ticket. Không commit thẳng vào `main`.
3. **Commit nhỏ, thật.** Mỗi commit là một bước chạy được: test, phần sửa, tài liệu. Không tách một thay đổi thành nhiều bước giả, không commit rỗng, không sửa ngày commit. CI chặn commit rỗng và message có chữ `\n` thô.
4. **PR đóng issue.** Ghi `Closes #<n>` trong mô tả PR.
5. **Merge kiểu rebase.** Dùng "Rebase and merge" để các commit nhỏ còn nguyên trên `main`. Không squash.
6. **Cổng.** `python scripts/check_repo.py` và toàn bộ test phải qua trước khi mở PR.

Email tác giả phải là email đã xác minh hoặc email noreply của tài khoản, nếu không việc làm không lên ô xanh. Kiểm bằng `python scripts/check_commit_emails.py <đường dẫn repo>`.

Agent không tự làm khi chưa có chủ repo duyệt: push lên `main`, merge, đăng lên registry hay repo của người khác, đổi cài đặt repo.
