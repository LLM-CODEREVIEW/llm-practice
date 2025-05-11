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

    def extract_pr_data(self) -> Dict[str, Any]:
        """PR의 변경 사항을 추출하고 구조화된 데이터로 반환합니다."""
        try:
            files = self.pr.get_files()
            pr_data = {
                "title": self.pr.title,
                "description": self.pr.body,
                "changed_files": [],
                "base_sha": self.pr.base.sha,
                "head_sha": self.pr.head.sha
            }

            for file in files:
                file_data = {
                    "filename": file.filename,
                    "status": file.status,
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "changes": file.changes,
                    "patch": file.patch,
                    "raw_url": file.raw_url
                }
                pr_data["changed_files"].append(file_data)

            return pr_data

        except Exception as e:
            logger.error(f"Error extracting PR data: {str(e)}")
            raise

    def get_file_content(self, file_path: str, ref: str) -> str:
        """특정 파일의 내용을 가져옵니다."""
        try:
            content = self.repo_obj.get_contents(file_path, ref=ref)
            return content.decoded_content.decode('utf-8')
        except Exception as e:
            logger.error(f"Error getting file content for {file_path}: {str(e)}")
            raise

    def get_file_context(self, file_path: str, line_number: int, context_lines: int = 5) -> Dict[str, Any]:
        """특정 라인 주변의 컨텍스트를 가져옵니다."""
        try:
            content = self.get_file_content(file_path, self.pr.head.sha)
            lines = content.split('\n')
            
            start_line = max(0, line_number - context_lines - 1)
            end_line = min(len(lines), line_number + context_lines)
            
            return {
                "file_path": file_path,
                "line_number": line_number,
                "context": lines[start_line:end_line],
                "start_line": start_line + 1,
                "end_line": end_line
            }
        except Exception as e:
            logger.error(f"Error getting file context for {file_path}: {str(e)}")
            raise 