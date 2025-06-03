
template = """
<review-task>
  <confidence-score-criteria>
    - ⭐️: Code is unclear or incomplete. Low confidence in the review judgment  
    - ⭐⭐: Possible issues, but lacking clear evidence. Suggestions are speculative  
    - ⭐⭐⭐: General-level suggestion with moderate confidence  
    - ⭐⭐⭐⭐: Clear problem identification with practical recommendation  
    - ⭐⭐⭐⭐⭐: Highly confident suggestion based on explicit and observable issue  
  </confidence-score-criteria>

  <review-difficulty-criteria>
    - ⭐️: Very simple change. No code analysis needed  
    - ⭐⭐: Simple logic, but understanding the flow is required  
    - ⭐⭐⭐: Requires analyzing function- or block-level logic  
    - ⭐⭐⭐⭐: Multiple conditions, exceptions, or structure must be understood  
    - ⭐⭐⭐⭐⭐: Complex state handling or multi-module dependency analysis required  
  </review-difficulty-criteria>

  <severity-criteria>
    - 🔥 High: May cause runtime error, security breach, or data corruption  
    - 🔥 Medium: Potential performance degradation or poor maintainability  
    - 🔥 Low: Styling issue, naming inconsistency, or non-critical suggestions  
  </severity-criteria>

  <instruction>
    Perform a step-by-step code review for the given PR Diff.

    Follow these steps:
    1. Read only the lines starting with '+' (ignore '-', ' ')
    2. Understand what the code is trying to do
    3. For each code block, think in the following order:
       - Check for runtime errors or missing logging
       - Consider performance optimization
       - Evaluate security risks
       - Verify code convention compliance
       Only write comments when you detect an issue in each step.
    4. Summarize your findings using the format in &lt;output-format&gt;.
  </instruction>

  <convention-guide>
  {{CONVENTION_GUIDE_PLACEHOLDER}}
  </convention-guide>

  <output-format>
    <![CDATA[
### ✅ PR Summary in 3 Lines
- [Summary line 1]
- [Summary line 2]
- [Summary line 3]

---

| Category            | Description                            |
|---------------------|-----------------------------------------|
| 🎯 Review Difficulty | ⭐⭐⭐ (3/5)                               |
| 🔎 Confidence Score  | ⭐⭐⭐⭐ (4/5)                              |
| 🔑 Key Keywords      | 네이밍, 상수, 포맷팅, 로그 등            |

---

### 🔍 Detailed Review

- ❗ Issue: 상수 'MaximumNumberOfLines'는 Swift 컨벤션(lowerCamelCase)을 따르지 않습니다.  
  📌 Line: 3, 🔥 Severity: Low  
- 💡 Suggestion: 'maximumNumberOfLines'로 변경하세요.  

  ```swift
  let maximumNumberOfLines = 3
````

* ❗ Issue: 'get' 접두사는 Swift 함수명에서 권장되지 않습니다.
  📌 Line: 8, 🔥 Severity: Medium
* 💡 Suggestion: 아래처럼 함수명을 개선하세요.

  ```swift
  func userName(for user: User) -> String?
  ```

  ]]>
  </output-format>

  <diff>
   <![CDATA[
   {{PR_DIFF_PLACEHOLDER}}
   ]]> 
  </diff>
</review-task>
"""
