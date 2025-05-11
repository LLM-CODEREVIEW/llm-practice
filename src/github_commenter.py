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

    def post_review(self, summary: str, line_comments: List[Dict[str, Any]]) -> None:
        """리뷰 요약과 라인별 코멘트를 GitHub에 게시합니다."""
        try:
            # 라인별 코멘트 생성
            review_comments = []
            for comment in line_comments:
                try:
                    # 필수 필드 확인
                    if 'line' not in comment or 'file' not in comment:
                        logger.warning(f"Skipping comment with missing fields: {comment}")
                        continue

                    body = f"""**심각도**: {comment.get('severity', 'N/A')}
                                **카테고리**: {comment.get('category', 'N/A')}
                                **설명**: {comment.get('description', 'N/A')}
                                **제안**: {comment.get('proposal', 'N/A')}"""

                    review_comment = {
                        "body": body,
                        "path": comment['file'],
                        "position": comment['line']
                    }
                    logger.debug(f"[DEBUG] 코멘트 생성: {review_comment}")
                    review_comments.append(review_comment)
                except Exception as e:
                    logger.warning(f"Error creating comment: {str(e)}")
                    continue

            logger.debug(f"[DEBUG] review_comments 전체: {review_comments}")
            logger.info(f"[DEBUG] create_review 파라미터: summary={summary}, comments={review_comments}")

            if not review_comments:
                # 코멘트가 없으면 요약만 게시
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
