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

    def post_unified_report(self, report: str) -> None:
        """통합 리포트를 GitHub PR에 코멘트로 게시합니다."""
        try:
            logger.info(f"=== 통합 리포트 게시 시작: PR #{self.pr_number} ===")
            logger.debug(f"[DEBUG] 리포트 내용: {report}")

            # 기존 봇 코멘트가 있는지 확인
            existing_comment = self._find_existing_bot_comment()
            
            if existing_comment:
                # 기존 코멘트 업데이트
                existing_comment.edit(report)
                logger.info("기존 리뷰 코멘트를 업데이트했습니다.")
            else:
                # 새 코멘트 생성
                self.pr.create_issue_comment(report)
                logger.info("새로운 리뷰 코멘트를 생성했습니다.")

        except Exception as e:
            logger.error(f"Error posting unified report: {str(e)}")
            raise

    def _find_existing_bot_comment(self):
        """기존 봇 코멘트를 찾습니다."""
        try:
            comments = self.pr.get_issue_comments()
            bot_login = self.github.get_user().login
            
            for comment in comments:
                if (comment.user.login == bot_login and 
                    "🔍 코드 리뷰 결과" in comment.body):
                    return comment
            return None
            
        except Exception as e:
            logger.warning(f"기존 코멘트 검색 중 오류: {str(e)}")
            return None
