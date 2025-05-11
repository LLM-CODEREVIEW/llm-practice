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
        
        # review_text가 리스트인 경우 문자열로 변환
        if isinstance(review_text, list):
            review_text = '\n'.join(review_text)
        
        current_issue = {}
        for line in review_text.split('\n'):
            line = line.strip()
            if not line:
                continue

            if line.startswith('라인:'):
                if current_issue:
                    issues.append(current_issue)
                current_issue = {'line': int(line.split(':')[1].strip())}
            elif line.startswith('심각도:'):
                current_issue['severity'] = line.split(':')[1].strip()
            elif line.startswith('카테고리:'):
                current_issue['category'] = line.split(':')[1].strip()
            elif line.startswith('설명:'):
                current_issue['description'] = line.split(':')[1].strip()
            elif line.startswith('제안:'):
                current_issue['suggestion'] = line.split(':')[1].strip()

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
            # review_results에서 reviews 리스트 가져오기
            reviews = review_results.get('reviews', [])
            
            for review in reviews:
                file_name = review.get('file')
                review_text = review.get('review')
                
                if not file_name or not review_text:
                    continue
                
                # 리뷰 텍스트 파싱
                issues = self._parse_review(review_text)
                
                for issue in issues:
                    # 라인 번호가 없는 경우 건너뛰기
                    if not issue.get('line'):
                        continue
                    
                    # 파일 컨텍스트 가져오기
                    context = pr_extractor.get_file_context(file_name, issue['line'])
                    
                    # 코멘트 생성
                    comment = self._format_comment(issue, context)
                    
                    comments.append({
                        'file': file_name,
                        'line': issue['line'],
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