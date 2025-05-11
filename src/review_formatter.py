from typing import Dict, List, Any
from loguru import logger
from collections import defaultdict
import re

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

    def _parse_review_text(self, review_text: str) -> List[Dict[str, Any]]:
        """리뷰 텍스트를 파싱하여 이슈 목록을 생성합니다."""
        issues = []
        current_issue = None
        
        # 이슈 패턴
        severity_pattern = r"심각도:\s*(HIGH|MEDIUM|LOW)"
        category_pattern = r"카테고리:\s*(BUG|PERFORMANCE|READABILITY|SECURITY|OTHER)"
        description_pattern = r"설명:\s*(.*?)(?=\n\n|$)"
        suggestion_pattern = r"제안:\s*(.*?)(?=\n\n|$)"
        
        for line in review_text.split('\n'):
            severity_match = re.search(severity_pattern, line)
            if severity_match:
                if current_issue:
                    issues.append(current_issue)
                current_issue = {
                    'severity': severity_match.group(1),
                    'category': 'OTHER',
                    'description': '',
                    'suggestion': ''
                }
                continue
                
            if current_issue:
                category_match = re.search(category_pattern, line)
                if category_match:
                    current_issue['category'] = category_match.group(1)
                    continue
                    
                description_match = re.search(description_pattern, line)
                if description_match:
                    current_issue['description'] = description_match.group(1)
                    continue
                    
                suggestion_match = re.search(suggestion_pattern, line)
                if suggestion_match:
                    current_issue['suggestion'] = suggestion_match.group(1)
                    continue
        
        if current_issue:
            issues.append(current_issue)
            
        return issues

    def _group_issues_by_file(self, review_results: Dict[str, str]) -> Dict[str, List[Dict[str, Any]]]:
        """이슈를 파일별로 그룹화합니다."""
        grouped_issues = defaultdict(list)
        
        for file, review_text in review_results.items():
            issues = self._parse_review_text(review_text)
            for issue in issues:
                issue['file'] = file
                grouped_issues[file].append(issue)
                
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
        
        # 상세 이슈
        summary += "\n**상세 이슈:**\n"
        for issue in issues:
            severity_emoji = self.severity_emoji[issue['severity']]
            category_emoji = self.category_emoji[issue['category']]
            summary += f"- {severity_emoji} {category_emoji} {issue['description']}\n"
            if issue['suggestion']:
                summary += f"  - 💡 제안: {issue['suggestion']}\n"
        
        return summary

    def format_review(self, review_results: Dict[str, str], line_comments: List[Dict[str, Any]]) -> str:
        """전체 리뷰 결과를 포맷팅합니다."""
        try:
            # 모든 이슈 수집
            all_issues = []
            for file, review_text in review_results.items():
                issues = self._parse_review_text(review_text)
                for issue in issues:
                    issue['file'] = file
                    all_issues.append(issue)
            
            # 이슈 통계 계산
            total_issues = len(all_issues)
            severity_count = defaultdict(int)
            category_count = defaultdict(int)
            
            for issue in all_issues:
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
            grouped_issues = self._group_issues_by_file(review_results)
            for file, file_issues in grouped_issues.items():
                summary += self._format_file_summary(file, file_issues)
            
            return summary

        except Exception as e:
            logger.error(f"Error formatting review: {str(e)}")
            raise 