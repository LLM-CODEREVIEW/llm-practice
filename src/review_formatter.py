from typing import Dict, List, Any, Union
from loguru import logger

class ReviewFormatter:
    def __init__(self):
        pass

    def create_unified_report(self, review_results: Dict[str, Any]) -> str:
        """리뷰 결과를 하나의 통합된 리포트로 생성합니다."""
        try:
            logger.info("=== 통합 리포트 생성 시작 ===")
            logger.debug(f"[DEBUG] review_results: {review_results}")

            # 리포트 헤더
            report = "# 🔍 코드 리뷰 결과\n\n"
            report += review_results
            # 리포트 푸터
            report += "\n\n---\n"
            report += "🤖 *이 리뷰는 AI에 의해 자동 생성되었습니다.*\n"
            
            logger.info("통합 리포트 생성 완료")
            return report

        except Exception as e:
            logger.error(f"Error creating unified report: {str(e)}")
            raise 