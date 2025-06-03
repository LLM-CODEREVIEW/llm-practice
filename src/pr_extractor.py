from github import Github
from loguru import logger
import os
from typing import Dict, List, Any

class PRExtractor:
    def __init__(self, repo: str, pr_number: int):
        self.repo = repo
        self.pr_number = pr_number
        self.github = Github(os.getenv("GITHUB_TOKEN"))
        self.repo_obj = self.github.get_repo(repo)
        self.pr = self.repo_obj.get_pull(pr_number)

    def extract_pr_data(self) -> str:
        """PR의 변경 사항을 추출하고 하나의 문자열로 반환합니다."""
        try:
            files = self.pr.get_files()
            pr_text = f"PR Title: {self.pr.title}\n"
            pr_text += f"PR Description: {self.pr.body}\n\n"
            pr_text += "Changed Files:\n"

            for file in files:
                pr_text += f"\n=== File: {file.filename} ===\n"
                pr_text += f"Status: {file.status}\n"
                pr_text += f"Changes: +{file.additions} -{file.deletions}\n"
                if file.patch:
                    pr_text += f"\nPatch:\n{file.patch}\n"
                pr_text += "=" * 50 + "\n"

            logger.info(f"[DEBUG] extract_pr_data 결과 길이: {len(pr_text)} characters")
            return pr_text

        except Exception as e:
            logger.error(f"PR 데이터 추출 중 오류 발생: {str(e)}")
            raise