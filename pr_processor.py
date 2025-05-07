import github_client


def process_pull_request(repo_name, pr_number):
    """PR을 처리하고 코드 리뷰 수행"""
    try:
        # PR 정보 가져오기
        pr_info = github_client.get_pull_request_diff(repo_name, pr_number)

        # 초기 코멘트 추가
        initial_comment = (
            "🤖 **자동 코드 리뷰 시작**\n\n"
            "PR을 분석 중입니다. 곧 리뷰 코멘트가 추가될 예정입니다."
        )
        github_client.add_pr_comment(repo_name, pr_number, initial_comment)

        # TODO: 여기에 codellama 13b 모델 호출 코드 추가 예정

        # 임시로 간단한 리뷰 코멘트 생성 (codellama 구현 전)
        review_comments = []
        for change in pr_info['changes']:
            if change['status'] != 'removed' and change.get('content'):
                # 예: Python 파일만 처리
                if change['filename'].endswith('.py'):
                    # 간단한 예시 코멘트
                    comment = {
                        'path': change['filename'],
                        'position': 1,  # 나중에 실제 위치 계산 필요
                        'body': f"이 파일에 대한 자동 코드 리뷰 코멘트입니다. codellama 13b 모델 통합 후 실제 분석 결과로 대체됩니다."
                    }
                    review_comments.append(comment)
        # 리뷰 제출
        if review_comments:
            review_body = "자동 코드 리뷰 결과입니다. 이것은 임시 메시지이며, codellama 13b 모델 통합 후 실제 분석으로 대체됩니다."
            github_client.add_review_comments(repo_name, pr_number, review_comments, review_body)
        else:
            github_client.add_pr_comment(
                repo_name,
                pr_number,
                "🎉 코드를 분석했으나 현재는 테스트 단계입니다. 곧 실제 분석 결과가 제공될 예정입니다."
            )

    except Exception as e:
        # 오류 발생 시 PR에 알림
        error_message = f"🚨 자동 코드 리뷰 중 오류가 발생했습니다: {str(e)}"
        print(f"Error processing PR {pr_number} in {repo_name}: {str(e)}")

        try:
            github_client.add_pr_comment(repo_name, pr_number, error_message)
        except Exception as comment_error:
            print(f"코멘트 추가 중 오류 발생: {str(comment_error)}")
