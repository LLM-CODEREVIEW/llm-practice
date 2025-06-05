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
    - 🟧 Medium: Potential performance degradation or poor maintainability  
    - 🟨 Low: Styling issue, naming inconsistency, or non-critical suggestions  
  </severity-criteria>

  <instruction>
    Perform a step-by-step code review for the given PR Diff.

    Follow these steps:

    1. Read only the lines starting with '+' (ignore '-', ' ')
    2. For each code block, analyze and detect issues in the following order:
       - Runtime Error or missing Logging
       - Performance Optimization
       - Security Issue
       - Code Convention Violation
    3. For each detected issue, write a detailed comment with:
       - Line number
       - File name
       - Confidence score (⭐️~⭐⭐⭐⭐⭐)
       - Explanation of the issue
       - Suggested improvement
       - Rule Type: One of Runtime, Logging, Optimization, Security, Convention
    4. After identifying all issues, group them first by **severity level**, and within each severity group:
       - Group by Rule Type in this order: Runtime → Logging → Optimization → Security → Convention
       - Within each Rule Type group, number the issues starting from 1

    Use the following headers in order:
      - `### 🟥 High Severity Issues`
      - `### 🟧 Medium Severity Issues`
      - `### 🟨 Low Severity Issues`

    Use a secondary heading (### [RuleType]) to separate rule types inside each severity section.
    Use `#### [Number]. Summary` for each issue.
  </instruction>

  <convention-guide>
  {{CONVENTION_GUIDE_PLACEHOLDER}}
  </convention-guide>

  <output-format>
  Do NOT reuse the text here. This is just a structural guide.

    <![CDATA[
## ✅ PR Summary in 3 Lines
- [Summary line 1]
- [Summary line 2]
- [Summary line 3]
## 🎯 Review Difficulty: ⭐⭐⭐ (3/5)
## 🔑 Key Keywords: naming, constant, formatting, logging

## 🔍 Detailed Review

### 🟥 High Severity Issues
### [Runtime]
#### 1. Null dereference risk
📌 File: `UserManager.swift` | Line: 52 | 🔎 Confidence: ⭐⭐⭐⭐  
Missing exception handling when accessing optional value. May cause a crash.

**💡 Suggestion:** Use `guard let` or conditional to safely unwrap.

### [Convention]
#### 1. Unclear function naming
📌 File: `CalendarUtils.swift` | Line: 18 | 🔎 Confidence: ⭐⭐⭐⭐  
The function name uses a noun form which is ambiguous about its behavior.

**💡 Suggestion:** Use an action-based name like `generateSevenDays()` instead of `getSevenDays()`.

### 🟧 Medium Severity Issues
### [Optimization]
#### 1. Redundant computation inside loop
📌 File: `LayoutHelper.swift` | Line: 30 | 🔎 Confidence: ⭐⭐⭐  
Repeatedly calling the same expression inside the loop can degrade performance.

**💡 Suggestion:** Move the expression outside the loop and reuse the value.

### 🟨 Low Severity Issues
... etc
    ]]>
  </output-format>

  <diff>
   <![CDATA[
   {{PR_DIFF_PLACEHOLDER}}
   ]]> 
  </diff>
</review-task>
"""
