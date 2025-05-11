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
            # 기존 리뷰 코멘트 삭제
            reviews = self.pr.get_reviews()
            for review in reviews:
                if review.user.login == self.github.get_user().login:
                    review.dismiss()

            # 새로운 리뷰 생성
            review_comments = []
            for comment in line_comments:
                try:
                    if 'line' not in comment:
                        logger.warning(f"Skipping comment without line number: {comment}")
                        continue
                    # diff 기준 position 대신 line/side 사용
                    review_comments.append({
                        "body": comment['body'],
                        "path": comment['file'],
                        "line": comment['line'],
                        "side": "RIGHT"
                    })
                except Exception as e:
                    logger.warning(f"Error creating comment for line {comment.get('line')}: {str(e)}")
                    continue

            if not review_comments:
                logger.warning("No valid comments to post")

            # 리뷰 제출
            self.pr.create_review(
                body=summary,
                event="COMMENT",
                comments=review_comments
            )

            logger.info(f"Successfully posted review for PR #{self.pr_number}")

        except Exception as e:
            logger.error(f"Error posting review: {str(e)}")
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