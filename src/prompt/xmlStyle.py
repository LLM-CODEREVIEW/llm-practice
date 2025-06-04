
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
    - 🟥 High: May cause runtime error, security breach, or data corruption  
    - 🟧 Mediu: Potential performance degradation or poor maintainability  
    - 🟨 Low: Styling issue, naming inconsistency, or non-critical suggestions  
  </severity-criteria>

  <instruction>
    Perform a step-by-step code review for the given PR Diff.

    Follow these steps:

    1. Read only the lines starting with '+' (ignore '-', ' ')
    2. For each code block, analyze and detect issues in the following order:
       - Check for runtime errors or missing logging
       - Consider performance bottlenecks
       - Evaluate security risks
       - Verify code convention/style compliance
    3. For every detected issue, write a detailed comment with:
       - Line number
       - Confidence score (⭐️~⭐⭐⭐⭐⭐)
       - Explanation of the issue
       - Suggested improvement
    4. After identifying all issues, group them by **severity level** in the final output.
       Use the following headers in order:
         - `### 🟥 High Severity Issues`
         - `### 🟧 Medium Severity Issues`
         - `### 🟨 Low Severity Issues`

    Do not include severity labels in each comment. Severity will be reflected in grouping only.
  </instruction>

  <convention-guide>
  {{CONVENTION_GUIDE_PLACEHOLDER}}
  </convention-guide>

  <output-format>
    <![CDATA[
## ✅ PR Summary in 3 Lines
- [Summary line 1]
- [Summary line 2]
- [Summary line 3]
## 🎯 Review Difficulty: ⭐⭐⭐ (3/5)
## 🔑 Key Keyword: 네이밍, 상수, 포맷팅, 로그 등

## 🔍 Detailed Review

### 🟥 High Severity Issues
#### 1. Null dereference risk
📌 Line 52 | 🔎 Confidence: ⭐⭐⭐⭐  
Exception handling is missing when accessing `data!`.

**💡 Suggestion:** Add optional binding or guard statement.

```swift
guard let value = data else { return }
```

### 🟧 Medium Severity Issues
#### 2. Inefficient calendar usage
📌 Line 21 | 🔎 Confidence: ⭐⭐  
Mixed usage of `Calendar.current` and `.gregorian` may cause inconsistencies.

**💡 Suggestion:** Use a single calendar reference.

```swift
let calendar = Calendar(identifier: .gregorian)
```

### 🟨 Low Severity Issues
#### 3. Function naming clarity
📌 Line 33 | 🔎 Confidence: ⭐⭐⭐⭐  
`getSevenDays()` is not aligned with Swift's naming guidelines.

**💡 Suggestion:** Use a verb-based name like `generateSevenDays()`.

  ]]>
  </output-format>

  <diff>
   <![CDATA[
   {{PR_DIFF_PLACEHOLDER}}
   ]]> 
  </diff>
</review-task>
"""