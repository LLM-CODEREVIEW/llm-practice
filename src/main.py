#!/usr/bin/env python3
import argparse
import os
import json
import sys
from loguru import logger
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

from pr_extractor import PRExtractor
from codellama_reviewer import CodeLlamaReviewer
from line_commenter import LineCommenter
from review_formatter import ReviewFormatter
from github_commenter import GitHubCommenter

def setup_logging():
    logger.add("logs/code_review.log", rotation="1 day", retention="7 days")

def parse_args():
    parser = argparse.ArgumentParser(description="GitHub PR Code Review System")
    parser.add_argument("--repo", required=True, help="GitHub repository (owner/repo)")
    parser.add_argument("--pr-number", required=True, type=int, help="Pull request number")
    parser.add_argument("--base-sha", required=True, help="Base commit SHA")
    parser.add_argument("--head-sha", required=True, help="Head commit SHA")
    parser.add_argument("--api-url", required=True, help="Ollama API URL")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    return parser.parse_args()

def main():
    # GitHub 토큰 확인
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        logger.error("GITHUB_TOKEN 환경 변수가 설정되지 않았습니다.")
        sys.exit(1)

    # PR 데이터 추출
    pr_extractor = PRExtractor(github_token)
    repo = os.getenv("GITHUB_REPOSITORY")
    pr_number = int(os.getenv("PR_NUMBER", "0"))
    
    if not repo or pr_number == 0:
        logger.error("GITHUB_REPOSITORY 또는 PR_NUMBER 환경 변수가 설정되지 않았습니다.")
        sys.exit(1)

    try:
        pr_data = pr_extractor.extract_pr_data(repo, pr_number)
    except Exception as e:
        logger.error(f"PR 데이터 추출 중 오류 발생: {str(e)}")
        sys.exit(1)

    # 코드 리뷰 수행
    reviewer = CodeLlamaReviewer()
    review_results = reviewer.review_code(pr_data)

    # 리뷰 결과 포맷팅
    formatter = ReviewFormatter()
    formatted_review = formatter.format_review(review_results)

    # 라인 코멘트 생성
    commenter = LineCommenter()
    comments = commenter.generate_comments(review_results)

    # 리뷰 추가
    try:
        pr_extractor.add_review(repo, pr_number, formatted_review, comments)
        logger.info("코드 리뷰가 성공적으로 완료되었습니다.")
    except Exception as e:
        logger.error(f"리뷰 추가 중 오류 발생: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 