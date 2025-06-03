#!/usr/bin/env python3
import argparse
import os
from loguru import logger
from dotenv import load_dotenv

from pr_extractor import PRExtractor
from codellama_reviewer import CodeLlamaReviewer
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
    return parser.parse_args()

def main():
    load_dotenv()
    setup_logging()
    args = parse_args()

    try:
        # PR 정보 추출
        extractor = PRExtractor(args.repo, args.pr_number)
        pr_data = extractor.extract_pr_data()
        logger.info(f"[DEBUG] pr_data: {pr_data}")

        # CodeLlama 모델을 사용한 코드 리뷰
        reviewer = CodeLlamaReviewer(api_url=args.api_url)
        review_results = reviewer.review_code(pr_data)
        logger.info(f"[DEBUG] review_results: {review_results}")

        # 통합 리포트 생성
        formatter = ReviewFormatter()
        final_report = formatter.create_unified_report(review_results)
        logger.info(f"[DEBUG] final_report: {final_report}")

        # GitHub에 통합 리포트 게시
        github_commenter = GitHubCommenter(args.repo, args.pr_number)
        github_commenter.post_unified_report(final_report)

        logger.info("Code review completed successfully")

    except Exception as e:
        logger.error(f"Error during code review: {str(e)}")
        raise

if __name__ == "__main__":
    main() 