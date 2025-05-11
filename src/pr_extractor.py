from github import Github
from loguru import logger
import os
from typing import Dict, List, Any

class PRExtractor:
    def __init__(self, github_token: str):
        self.github = Github(github_token)

    def extract_pr_data(self, repo: str, pr_number: int) -> Dict[str, Any]:
        """PR의 변경 사항을 추출하고 구조화된 데이터로 반환합니다."""
        try:
            repo_obj = self.github.get_repo(repo)
            pr = repo_obj.get_pull(pr_number)
            
            files = pr.get_files()
            pr_data = {
                "title": pr.title,
                "description": pr.body,
                "changed_files": [],
                "base_sha": pr.base.sha,
                "head_sha": pr.head.sha,
                "number": pr_number
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

    def get_file_content(self, repo: str, file_path: str, ref: str) -> str:
        """특정 파일의 내용을 가져옵니다."""
        try:
            repo_obj = self.github.get_repo(repo)
            content = repo_obj.get_contents(file_path, ref=ref)
            return content.decoded_content.decode('utf-8')
        except Exception as e:
            logger.error(f"Error getting file content for {file_path}: {str(e)}")
            raise

    def get_file_context(self, repo: str, file_path: str, line_number: int, context_lines: int = 5) -> Dict[str, Any]:
        """특정 라인 주변의 컨텍스트를 가져옵니다."""
        try:
            repo_obj = self.github.get_repo(repo)
            pr = repo_obj.get_pull(pr_number)
            content = self.get_file_content(repo, file_path, pr.head.sha)
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

    def add_review(self, repo: str, pr_number: int, review_body: str, comments: List[Dict[str, Any]]) -> None:
        """PR에 리뷰를 추가합니다."""
        try:
            repo_obj = self.github.get_repo(repo)
            pr = repo_obj.get_pull(pr_number)
            
            # 리뷰 코멘트 생성
            review_comments = []
            for comment in comments:
                review_comments.append({
                    'path': comment['file'],
                    'position': comment['line'],
                    'body': comment['body']
                })
            
            # 리뷰 추가
            pr.create_review(
                body=review_body,
                event='COMMENT',
                comments=review_comments
            )
            
            logger.info(f"리뷰가 성공적으로 추가되었습니다: PR #{pr_number}")
            
        except Exception as e:
            logger.error(f"Error adding review: {str(e)}")
            raise 