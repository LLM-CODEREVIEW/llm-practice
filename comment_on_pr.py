from github import Github

# 토큰은 이미 노출되었으니 새로 발급받아 사용하세요
token = "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"

g = Github(token)

repo_name = "coals0115/llm-practice"
pr_number = 1

# 리포지토리 가져오기
repo = g.get_repo(repo_name)
pr = repo.get_pull(pr_number)

# PR에 일반 댓글 남기기
pr.create_issue_comment("ㅎㅏ이하이")
print("PR에 일반 댓글 추가 완료!")

# PR의 특정 파일 특정 라인에 코멘트 남기기
commit_id = pr.get_commits().reversed[0].sha  # 최신 커밋 ID 가져오기
print("commit_id: " + commit_id)

# 커밋 객체 가져오기 - 이 부분이 중요합니다!
commit = repo.get_commit(commit_id)

# 특정 파일 경로와 라인에 코멘트 남기기
file_path = "example.py"  # 코멘트를 달 파일 경로
line_number = 10  # 코멘트를 달 라인 번호

pr.create_review_comment(
    body="이 라인에 문제가 있습니다. 변수 이름을 더 명확하게 지정하는 것이 좋겠습니다.",
    commit=commit,  # 문자열이 아닌 커밋 객체 사용
    path=file_path,
    line=line_number
)

print(f"{file_path} 파일의 {line_number}번 라인에 코멘트 추가 완료!")