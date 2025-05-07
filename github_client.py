from github import Github
from config import GITHUB_TOKEN

def setup_github_client():
    """GitHub API 클라이언트 설정"""
    return Github(GITHUB_TOKEN)

def get_repo(repo_name):
    """저장소 객체 가져오기"""
    client = setup_github_client()
    return client.get_repo(repo_name)

def get_pull_request(repo_name, pr_number):
    """PR 객체 가져오기"""
    repo = get_repo(repo_name)
    return repo.get_pull(pr_number)

def get_pull_request_diff(repo_name, pr_number):
    """PR의 변경사항(diff) 가져오기"""

    repo = get_repo(repo_name)
    pull_request = repo.get_pull(pr_number)

    # 변경된 파일 목록 가져오기
    files = pull_request.get_files()

    changes = []
    for file in files:
        change = {
            'filename': file.filename,
            'status': file.status,
            'patch': file.patch # todo 이게뭐지
        }

        # 파일이 추가되거나 수정된 경우 내용 가져오기
        if file.status in ['added', 'modified']:
            try:
                content = repo.get_contents(file.filename, ref=pull_request.head.sha).decoded_content.decode('utf-8')
                change['content'] = content
            except Exception as e:
                print(f"파일 내용 가져오기 오류 ({file.filename}): {str(e)}")
                change['content'] = None

        changes.append(change)

    pr_info = {
        'title': pull_request.title,
        'body': pull_request.body,
        'base_branch': pull_request.base.ref,
        'head_branch': pull_request.head.ref,
        'head_sha': pull_request.head.sha,
        'user': pull_request.user.login,
        'changes': changes
    }

    return pr_info

def add_pr_comment(repo_name, pr_number, comment_body):
    """PR에 일반 코멘트 추가"""
    pull_request = get_pull_request(repo_name, pr_number)
    pull_request.create_issue_comment(comment_body)
    print(f"PR #{pr_number}에 코멘트 추가됨")

def add_review_comments(repo_name, pr_number, comments, review_body="코드 리뷰 결과", event="COMMENT"):
    """PR에 리뷰 코멘트 추가"""
    pull_request = get_pull_request(repo_name, pr_number)

    # 이벤트 타입: 'APPROVE', 'REQUEST_CHANGES', 'COMMENT'
    review = pull_request.create_review(
        commit=pull_request.head.sha,
        body=review_body,
        event=event,
        comments=comments
    )
    print(f"PR #{pr_number}에 리뷰 추가됨")
    return review
