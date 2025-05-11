from typing import Dict, List, Any
from loguru import logger
from pr_extractor import PRExtractor

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

    def _format_comment(self, issue: Dict[str, Any], context: Dict[str, Any]) -> str:
        """이슈 정보를 기반으로 코멘트를 포맷팅합니다."""
        severity = self.severity_emoji.get(issue['severity'], "ℹ️")
        category = self.category_emoji.get(issue['category'], "ℹ️")
        
        comment = f"{severity} **{issue['severity']}** {category} **{issue['category']}**\n\n"
        comment += f"{issue['description']}\n\n"
        
        if issue['suggestion']:
            comment += "**개선 제안:**\n"
            comment += f"```\n{issue['suggestion']}\n```\n\n"
        
        comment += "**컨텍스트:**\n"
        comment += "```\n"
        for i, line in enumerate(context['context'], start=context['start_line']):
            if i == issue['line_number']:
                comment += f"> {i}: {line}\n"
            else:
                comment += f"  {i}: {line}\n"
        comment += "```"
        
        return comment

    def generate_comments(self, issues: List[Dict[str, Any]], pr_extractor: PRExtractor) -> List[Dict[str, Any]]:
        """이슈 목록을 기반으로 라인별 코멘트를 생성합니다."""
        comments = []
        
        try:
            for issue in issues:
                # 파일 컨텍스트 가져오기
                context = pr_extractor.get_file_context(
                    issue['file'],
                    issue['line_number']
                )
                
                # 코멘트 생성
                comment = self._format_comment(issue, context)
                
                comments.append({
                    'file': issue['file'],
                    'line': issue['line_number'],
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