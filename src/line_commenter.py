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

        # LLM 응답이 리스트인 경우 문자열로 변환
        if isinstance(review_text, list):
            review_text = '\n'.join(review_text)

        # 정규식 패턴 개선 (영어/한글 모두 robust하게)
        line_pattern = r"(?:Line|라인):\s*([\d,\- ]+)"
        severity_pattern = r"(?:Severity|심각도):\s*(HIGH|MEDIUM|LOW)"
        category_pattern = r"(?:Category|카테고리):\s*(BUG|PERFORMANCE|READABILITY|SECURITY|OTHER)"
        description_pattern = r"(?:Description|설명):\s*(.*?)(?=\n(?:Line|라인):|\Z)"
        suggestion_pattern = r"(?:Proposed Solution|Proposal|Proposed solution|제안):\s*(.*?)(?=\n(?:Line|라인):|\Z)"

        # 각 이슈 블록 추출
        issue_blocks = re.split(r"(?=^라인:|^Line:)", review_text, flags=re.MULTILINE)

        for block in issue_blocks:
            if not block.strip():
                continue
            line_match = re.search(line_pattern, block)
            if not line_match:
                logger.warning(f"[DEBUG] block에서 라인 파싱 실패: {block}")
                continue
            line_field = line_match.group(1)
            line_nums = []
            for part in line_field.split(','):
                part = part.strip()
                m = re.match(r'^(\d+)-(\d+)$', part)
                if m:
                    start, end = int(m.group(1)), int(m.group(2))
                    line_nums.extend(range(start, end + 1))
                else:
                    m = re.match(r'^(\d+)$', part)
                    if m:
                        line_nums.append(int(m.group(1)))
            severity_match = re.search(severity_pattern, block)
            category_match = re.search(category_pattern, block)
            description_match = re.search(description_pattern, block, re.DOTALL)
            suggestion_match = re.search(suggestion_pattern, block, re.DOTALL)
            if severity_match and category_match and description_match:
                for line_num in line_nums:
                    issue = {
                        'line': line_num,
                        'severity': severity_match.group(1),
                        'category': category_match.group(1),
                        'description': description_match.group(1).strip(),
                        'suggestion': suggestion_match.group(1).strip() if suggestion_match else ""
                    }
                    issues.append(issue)

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
        logger.debug(f"[DEBUG] review_results: {review_results}")
        comments = []
        
        try:
            # review_results에서 reviews 리스트 가져오기
            reviews = review_results.get('reviews', [])
            
            for review in reviews:
                file_name = review.get('file')
                review_text = review.get('review')
                logger.debug(f"[DEBUG] file_name: {file_name}, review_text: {review_text}")
                
                if not file_name or not review_text:
                    continue
                
                # 리뷰 텍스트 파싱
                issues = self._parse_review(review_text)
                logger.debug(f"[DEBUG] 파싱된 issues: {issues}")
                
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
            
            logger.debug(f"[DEBUG] 최종 생성된 comments: {comments}")
            return comments

        except Exception as e:
            logger.error(f"Error generating comments: {str(e)}")
            raise

def make_llm_prompt_with_patch(patch: str) -> str:
    return f"""
아래는 GitHub Pull Request의 diff patch입니다.

- patch의 각 줄에서 +로 시작하는 줄(즉, 실제로 변경/추가된 코드)에만 코멘트를 달아주세요.
- 전체 코드를 이해하고, 변경된 줄(+)에만 코멘트가 필요하다고 판단되는 경우에만 코멘트를 작성하세요.
- 각 코멘트는 아래 형식으로 작성하세요:

Line: [patch에서 +로 시작하는 줄의 실제 라인 번호]
Severity: [HIGH|MEDIUM|LOW]
Category: [BUG|PERFORMANCE|READABILITY|SECURITY|OTHER]
Description: [문제 설명]
Proposed Solution: [개선 방안]

아래는 diff patch입니다:
{patch}

리뷰 결과:
""" 