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
            
            # PR 정보
            pr_title = review_results.get('title', '')
            if pr_title:
                report += f"**PR 제목:** {pr_title}\n\n"

            # 파일별 리뷰 결과 처리
            file_summaries = review_results.get('file_summaries', [])
            
            if not file_summaries:
                report += "리뷰할 변경사항이 없습니다.\n"
                return report

            total_files = len(file_summaries)
            report += f"**총 {total_files}개 파일을 리뷰했습니다.**\n\n"

            # 각 파일별 리뷰 결과 - LLM 출력 그대로 사용
            for file_summary in file_summaries:
                file_name = file_summary.get('file', 'Unknown')
                summary_text = file_summary.get('summary', '')
                
                report += f"## 📄 {file_name}\n\n"
                
                # LLM 결과를 거의 그대로 사용
                if summary_text.strip() == "NO ISSUE":
                    report += "✅ 특별한 이슈가 발견되지 않았습니다.\n\n"

            # 리포트 푸터
            report += "---\n"
            report += "🤖 *이 리뷰는 AI에 의해 자동 생성되었습니다.*\n"
            
            logger.info("통합 리포트 생성 완료")
            return report

        except Exception as e:
            logger.error(f"Error creating unified report: {str(e)}")
            raise 