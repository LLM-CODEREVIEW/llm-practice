from typing import Dict, List, Any
from loguru import logger
from pr_extractor import PRExtractor
import re

class LineCommenter:
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

    def _parse_review(self, review_text: str) -> List[Dict[str, Any]]:
        """리뷰 텍스트를 파싱하여 이슈 목록을 생성합니다."""
        issues = []
        current_issue = {}
        
        # 심각도와 카테고리 추출을 위한 정규식
        severity_pattern = r"심각도:\s*(HIGH|MEDIUM|LOW)"
        category_pattern = r"카테고리:\s*(BUG|PERFORMANCE|READABILITY|SECURITY|OTHER)"
        
        for line in review_text.split('\n'):
            # 심각도 매칭
            severity_match = re.search(severity_pattern, line, re.IGNORECASE)
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
            
            # 카테고리 매칭
            category_match = re.search(category_pattern, line, re.IGNORECASE)
            if category_match:
                current_issue['category'] = category_match.group(1)
                continue
            
            # 설명과 제안 추출
            if line.startswith('설명:'):
                current_issue['description'] = line[3:].strip()
            elif line.startswith('제안:'):
                current_issue['suggestion'] = line[3:].strip()
        
        if current_issue:
            issues.append(current_issue)
        
        return issues

    def _format_comment(self, issue: Dict[str, Any], context: Dict[str, Any]) -> str:
        """이슈 정보를 기반으로 코멘트를 포맷팅합니다."""
        severity = self.severity_emoji.get(issue['severity'], "ℹ️")
        category = self.category_emoji.get(issue['category'], "ℹ️")
        
        comment = f"{severity} **{issue['severity']}** {category} **{issue['category']}**\n\n"
        comment += f"{issue['description']}\n\n"
        
        if issue['suggestion']:
            comment += "**개선 제안:**\n"
            comment += f"```\n{issue['suggestion']}\n```\n\n"
        
        if context and 'context' in context:
            comment += "**컨텍스트:**\n"
            comment += "```\n"
            for i, line in enumerate(context['context'], start=context.get('start_line', 1)):
                comment += f"  {i}: {line}\n"
            comment += "```"
        
        return comment

    def generate_comments(self, review_results: Dict[str, Any], pr_extractor: PRExtractor) -> List[Dict[str, Any]]:
        """리뷰 결과를 기반으로 라인별 코멘트를 생성합니다."""
        comments = []
        
        try:
            for review in review_results.get('reviews', []):
                file_name = review['file']
                review_text = review['review']
                
                # 리뷰 텍스트 파싱
                issues = self._parse_review(review_text)
                
                for issue in issues:
                    # 파일 컨텍스트 가져오기
                    context = pr_extractor.get_file_context(file_name, 1)  # 첫 번째 라인부터 시작
                    
                    # 코멘트 생성
                    comment = self._format_comment(issue, context)
                    
                    comments.append({
                        'file': file_name,
                        'line': 1,  # 첫 번째 라인에 코멘트 추가
                        'body': comment,
                        'severity': issue['severity'],
                        'category': issue['category']
                    })
            
            # 심각도와 카테고리별로 정렬
            comments.sort(
                key=lambda x: (
                    {"HIGH": 0, "MEDIUM": 1, "LOW": 2}[x['severity']],
                    x['category']
                )
            )
            
            return comments

        except Exception as e:
            logger.error(f"Error generating comments: {str(e)}")
            raise 