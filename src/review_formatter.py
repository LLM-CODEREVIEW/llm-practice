from typing import Dict, List, Any
from loguru import logger
from collections import defaultdict

class ReviewFormatter:
    def __init__(self):
        self.severity_emoji = {
            "HIGH": "🔴",
            "MEDIUM": "🟡",
            "LOW": "🟢"
        }
        
        self.category_emoji = {
            "BUG": "🐛",
            "PERFORMANCE": "⚡",
            "READABILITY": "📝",
            "SECURITY": "🔒",
            "OTHER": "ℹ️"
        }

    def _group_issues_by_file(self, issues: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """이슈를 파일별로 그룹화합니다."""
        grouped_issues = defaultdict(list)
        for issue in issues:
            grouped_issues[issue['file']].append(issue)
        return dict(grouped_issues)

    def _format_file_summary(self, file: str, issues: List[Dict[str, Any]]) -> str:
        """파일별 이슈 요약을 포맷팅합니다."""
        summary = f"### 📁 {file}\n\n"
        
        # 심각도별 이슈 수 계산
        severity_count = defaultdict(int)
        category_count = defaultdict(int)
        
        for issue in issues:
            severity_count[issue['severity']] += 1
            category_count[issue['category']] += 1
        
        # 심각도 요약
        summary += "**심각도별 이슈:**\n"
        for severity in ["HIGH", "MEDIUM", "LOW"]:
            count = severity_count[severity]
            if count > 0:
                emoji = self.severity_emoji[severity]
                summary += f"- {emoji} {severity}: {count}개\n"
        
        # 카테고리 요약
        summary += "\n**카테고리별 이슈:**\n"
        for category in ["BUG", "PERFORMANCE", "READABILITY", "SECURITY", "OTHER"]:
            count = category_count[category]
            if count > 0:
                emoji = self.category_emoji[category]
                summary += f"- {emoji} {category}: {count}개\n"
        
        return summary

    def format_review(self, issues: List[Dict[str, Any]], line_comments: List[Dict[str, Any]]) -> str:
        """전체 리뷰 결과를 포맷팅합니다."""
        try:
            # 이슈 통계 계산
            total_issues = len(issues)
            severity_count = defaultdict(int)
            category_count = defaultdict(int)
            
            for issue in issues:
                severity_count[issue['severity']] += 1
                category_count[issue['category']] += 1
            
            # 전체 요약 생성
            summary = "# 🔍 코드 리뷰 결과\n\n"
            summary += f"총 {total_issues}개의 이슈가 발견되었습니다.\n\n"
            
            # 심각도별 요약
            summary += "## 심각도별 이슈\n"
            for severity in ["HIGH", "MEDIUM", "LOW"]:
                count = severity_count[severity]
                if count > 0:
                    emoji = self.severity_emoji[severity]
                    summary += f"- {emoji} {severity}: {count}개\n"
            
            # 카테고리별 요약
            summary += "\n## 카테고리별 이슈\n"
            for category in ["BUG", "PERFORMANCE", "READABILITY", "SECURITY", "OTHER"]:
                count = category_count[category]
                if count > 0:
                    emoji = self.category_emoji[category]
                    summary += f"- {emoji} {category}: {count}개\n"
            
            # 파일별 요약
            summary += "\n## 파일별 요약\n"
            grouped_issues = self._group_issues_by_file(issues)
            for file, file_issues in grouped_issues.items():
                summary += self._format_file_summary(file, file_issues)
            
            return summary

        except Exception as e:
            logger.error(f"Error formatting review: {str(e)}")
            raise 