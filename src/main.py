#!/usr/bin/env python3
import argparse
import os
import json
from loguru import logger
from dotenv import load_dotenv

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
    try:
        # 명령행 인자 파싱
        args = parse_args()
        
        # 환경 변수 확인
        github_token = os.getenv('GITHUB_TOKEN')
        if not github_token:
            raise ValueError("GITHUB_TOKEN 환경 변수가 설정되지 않았습니다.")
        
        # PR 데이터 추출
        extractor = PRExtractor(github_token)
        pr_data = extractor.extract_pr_data(args.repo, args.pr_number)
        
        # 코드 리뷰 수행
        reviewer = CodeLlamaReviewer(args.api_url)
        review_results = reviewer.review_code(pr_data)
        
        # 리뷰 결과 포맷팅
        formatter = ReviewFormatter()
        formatted_review = formatter.format_review(review_results, [])
        
        # 라인별 코멘트 생성
        commenter = LineCommenter()
        line_comments = commenter.generate_comments(review_results, extractor)
        
        # PR에 리뷰 결과 추가
        if args.dry_run:
            logger.info("Dry run 모드: PR에 리뷰를 추가하지 않습니다.")
            logger.info(f"리뷰 결과:\n{formatted_review}")
            logger.info(f"라인 코멘트:\n{json.dumps(line_comments, indent=2, ensure_ascii=False)}")
        else:
            extractor.add_review(
                args.repo,
                args.pr_number,
                formatted_review,
                line_comments
            )
            logger.info("리뷰가 성공적으로 추가되었습니다.")
        
    except Exception as e:
        logger.error(f"Error during code review: {str(e)}")
        raise

if __name__ == "__main__":
    main() 