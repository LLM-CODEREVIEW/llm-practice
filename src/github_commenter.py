from github import Github
from loguru import logger
import os
from typing import Dict, List, Any


class GitHubCommenter:
    def __init__(self, repo: str, pr_number: int):
        self.repo = repo
        self.pr_number = pr_number
        self.github = Github(os.getenv("GITHUB_TOKEN"))
        self.repo_obj = self.github.get_repo(repo)
        self.pr = self.repo_obj.get_pull(pr_number)

    def _create_review_comment(self, comment: Dict[str, Any]) -> Dict[str, Any]:
        """리뷰 코멘트를 생성합니다."""
        return {
            "body": comment['body'],
            "commit_id": self.pr.head.sha,
            "path": comment['file'],
            "position": comment['line']
        }

    def _build_line_to_position_map(self, patch: str) -> dict:
        """
        patch(diff) 문자열을 받아 실제 파일 라인 번호 → diff position 매핑을 반환
        """
        line_to_position = {}
        if not patch:
            return line_to_position

        import re
        lines = patch.split('\n')
        position = 0
        file_line = None
        for line in lines:
            position += 1
            if line.startswith('@@'):
                # 예: @@ -1,7 +1,9 @@
                m = re.match(r'@@ -\d+(?:,\d+)? \+(\d+)', line)
                if m:
                    file_line = int(m.group(1)) - 1  # 다음 +라인부터 시작
                continue
            if file_line is None:
                continue
            if line.startswith('+') and not line.startswith('+++'):
                file_line += 1
                line_to_position[file_line] = position
            elif line.startswith('-') and not line.startswith('---'):
                continue  # 삭제된 라인, 파일 라인 증가 없음
            else:
                file_line += 1  # context 라인
        return line_to_position

    def _parse_line_field(self, line_field):
        """
        '2-3, 5-6' → [2,3,5,6], '7-8' → [7,8], '9' → [9], int → [int]
        """
        import re
        result = []
        if isinstance(line_field, int):
            return [line_field]
        if isinstance(line_field, str):
            for part in line_field.split(','):
                part = part.strip()
                m = re.match(r'^(\d+)-(\d+)$', part)
                if m:
                    start, end = int(m.group(1)), int(m.group(2))
                    result.extend(range(start, end + 1))
                else:
                    m = re.match(r'^(\d+)$', part)
                    if m:
                        result.append(int(m.group(1)))
        return result

    def post_review(self, summary: str, line_comments: List[Dict[str, Any]]) -> None:
        logger.debug(f"[DEBUG] post_review 진입: summary={summary}")
        """리뷰 요약과 라인별 코멘트를 GitHub에 게시합니다."""
        try:
            review_comments = []
            logger.debug(f"[DEBUG] 전체 line_comments: {line_comments}")
            file_patches = {f.filename: f.patch for f in self.pr.get_files() if hasattr(f, 'patch') and f.patch}
            for comment in line_comments:
                try:
                    if 'line' not in comment or 'file' not in comment:
                        logger.warning(f"Skipping comment with missing fields: {comment}")
                        continue

                    logger.debug(f"[DEBUG] 원본 comment['line']: {comment.get('line')}")
                    logger.debug(f"[DEBUG] comment['file']: {comment.get('file')}")
                    patch = file_patches.get(comment['file'])
                    if not patch:
                        logger.warning(f"[DEBUG] Patch not found for file: {comment['file']}. file_patches keys: {list(file_patches.keys())}")
                        continue
                    logger.debug(f"[DEBUG] patch 내용 (앞 20줄):\n" + '\n'.join(patch.split('\n')[:20]))
                    line_to_position = self._build_line_to_position_map(patch)
                    logger.debug(f"[DEBUG] line_to_position 매핑: {line_to_position}")
                    line_nums = self._parse_line_field(comment['line'])
                    logger.debug(f"[DEBUG] 파싱된 라인 리스트: {line_nums}")
                    if not line_nums:
                        logger.warning(f"라인 정보 파싱 실패: {comment['line']}")
                        continue
                    for line_num in line_nums:
                        position = line_to_position.get(line_num)
                        logger.debug(f"[DEBUG] 파일: {comment['file']}, 라인: {line_num}, position: {position}")
                        if not position:
                            logger.warning(f"라인 {line_num} (파일 {comment['file']})은 diff에서 position을 찾을 수 없습니다.")
                            continue
                        review_comment = {
                            "body": comment['body'],
                            "path": comment['file'],
                            "position": position
                        }
                        logger.debug(f"[DEBUG] 코멘트 생성: {review_comment}")
                        review_comments.append(review_comment)
                except Exception as e:
                    logger.warning(f"Error creating comment: {str(e)}")
                    continue

            logger.debug(f"[DEBUG] 최종 review_comments 전체: {review_comments}")
            logger.info(f"[DEBUG] create_review 파라미터: summary={summary}, comments={review_comments}")

            if not review_comments:
                self.pr.create_issue_comment(summary)
                logger.info("Posted summary comment only (no line comments)")
            else:
                try:
                    self.pr.create_review(
                        body=summary,
                        event="COMMENT",
                        comments=review_comments
                    )
                    logger.info(f"[DEBUG] create_review 성공! {len(review_comments)}개 코멘트 제출됨")
                except Exception as e:
                    logger.error("[DEBUG] create_review 실패: {}", str(e), exc_info=True)
                    raise

        except Exception as e:
            logger.error("Error posting review: {}", str(e), exc_info=True)
            raise

    def update_review(self, summary: str, line_comments: List[Dict[str, Any]]) -> None:
        """기존 리뷰를 업데이트합니다."""
        try:
            # 기존 리뷰 찾기
            reviews = self.pr.get_reviews()
            existing_review = None
            for review in reviews:
                if review.user.login == self.github.get_user().login:
                    existing_review = review
                    break

            if existing_review:
                # 기존 리뷰 업데이트
                existing_review.dismiss()
                self.post_review(summary, line_comments)
            else:
                # 새 리뷰 생성
                self.post_review(summary, line_comments)

            logger.info(f"Successfully updated review for PR #{self.pr_number}")

        except Exception as e:
            logger.error(f"Error updating review: {str(e)}")
            raise
