from typing import Dict, List, Any, Union
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

    def _parse_review_text(self, review_text: Union[str, List[str], Dict[str, Any]]) -> List[Dict[str, Any]]:
        """리뷰 텍스트를 파싱하여 이슈 목록을 생성합니다."""
        issues = []
        current_issue = None
        
        # 이슈 패턴
        severity_pattern = r"심각도:\s*(HIGH|MEDIUM|LOW)"
        category_pattern = r"카테고리:\s*(BUG|PERFORMANCE|READABILITY|SECURITY|OTHER)"
        description_pattern = r"설명:\s*(.*?)(?=\n\n|$)"
        suggestion_pattern = r"제안:\s*(.*?)(?=\n\n|$)"
        
        # 딕셔너리인 경우 처리
        if isinstance(review_text, dict):
            if 'severity' in review_text and 'category' in review_text:
                return [review_text]
            return []
            
        # 리스트인 경우 문자열로 변환
        if isinstance(review_text, list):
            if all(isinstance(item, dict) for item in review_text):
                return review_text
            review_text = '\n'.join(review_text)
        
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

    def _group_issues_by_file(self, review_results: Union[Dict[str, str], Dict[str, List[str]], Dict[str, Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
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
            severity = issue.get('severity', 'OTHER')
            category = issue.get('category', 'OTHER')
            severity_count[severity] += 1
            category_count[category] += 1
        
        # 심각도 요약
        summary += "**심각도별 이슈:**\n"
        for severity in ["HIGH", "MEDIUM", "LOW"]:
            count = severity_count[severity]
            if count > 0:
                emoji = self.severity_emoji.get(severity, "ℹ️")
                summary += f"- {emoji} {severity}: {count}개\n"
        
        # 카테고리 요약
        summary += "\n**카테고리별 이슈:**\n"
        for category in ["BUG", "PERFORMANCE", "READABILITY", "SECURITY", "OTHER"]:
            count = category_count[category]
            if count > 0:
                emoji = self.category_emoji.get(category, "ℹ️")
                summary += f"- {emoji} {category}: {count}개\n"
        
        # 상세 이슈
        summary += "\n**상세 이슈:**\n"
        for issue in issues:
            severity = issue.get('severity', 'OTHER')
            category = issue.get('category', 'OTHER')
            severity_emoji = self.severity_emoji.get(severity, "ℹ️")
            category_emoji = self.category_emoji.get(category, "ℹ️")
            description = issue.get('description', '설명 없음')
            summary += f"- {severity_emoji} {category_emoji} {description}\n"
            suggestion = issue.get('suggestion')
            if suggestion:
                summary += f"  - 💡 제안: {suggestion}\n"
        
        return summary

    def format_review(self, review_results: Union[Dict[str, str], Dict[str, List[str]], Dict[str, Dict[str, Any]]], line_comments: List[Dict[str, Any]]) -> str:
        """전체 리뷰 결과를 포맷팅합니다."""
        try:
            # 모든 이슈 수집
            all_issues = []
            
            # review_results가 reviews 리스트를 포함하는 경우
            if isinstance(review_results, dict) and 'reviews' in review_results:
                for review in review_results['reviews']:
                    file = review.get('file')
                    review_text = review.get('review')
                    if file and review_text:
                        issues = self._parse_review_text(review_text)
                        for issue in issues:
                            issue['file'] = file
                            all_issues.append(issue)
            else:
                # 기존 구조 처리
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
                severity = issue.get('severity', 'OTHER')
                category = issue.get('category', 'OTHER')
                severity_count[severity] += 1
                category_count[category] += 1
            
            # 전체 요약 생성
            summary = "# 🔍 코드 리뷰 결과\n\n"
            summary += f"총 {total_issues}개의 이슈가 발견되었습니다.\n\n"
            
            # 심각도별 요약
            summary += "## 심각도별 이슈\n"
            for severity in ["HIGH", "MEDIUM", "LOW"]:
                count = severity_count[severity]
                if count > 0:
                    emoji = self.severity_emoji.get(severity, "ℹ️")
                    summary += f"- {emoji} {severity}: {count}개\n"
            
            # 카테고리별 요약
            summary += "\n## 카테고리별 이슈\n"
            for category in ["BUG", "PERFORMANCE", "READABILITY", "SECURITY", "OTHER"]:
                count = category_count[category]
                if count > 0:
                    emoji = self.category_emoji.get(category, "ℹ️")
                    summary += f"- {emoji} {category}: {count}개\n"
            
            # 파일별 요약
            summary += "\n## 파일별 요약\n"
            grouped_issues = defaultdict(list)
            for issue in all_issues:
                grouped_issues[issue['file']].append(issue)
            
            for file, file_issues in grouped_issues.items():
                summary += self._format_file_summary(file, file_issues)
            
            # 라인별 코멘트 추가
            if line_comments:
                summary += "\n## 📝 라인별 코멘트\n\n"
                for comment in line_comments:
                    file = comment.get('file', '알 수 없음')
                    line = comment.get('line', '알 수 없음')
                    body = comment.get('body', '')
                    summary += f"### 📄 {file} (라인 {line})\n\n{body}\n\n"
            
            return summary

        except Exception as e:
            logger.error(f"Error formatting review: {str(e)}")
            raise 