
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
### 🎯 Review Difficulty: ⭐⭐⭐ (3/5)
### 🔑 Key Keyword: 네이밍, 상수, 포맷팅, 로그 등
### 🔍 Detailed Review

#### 1. **Function name uses discouraged 'get' prefix**  
📌 Line 33 | 🔥 Severity: Medium | 🔎 Confidence: ⭐⭐⭐⭐ (4/5)  
The `getSevenDays()` function name violates Swift naming conventions.

**💡 Suggestion:** Rename the function to improve clarity and follow naming standards.

```swift
func generateSevenDays() -> [ScheduleDate]
```

#### 2. **Mixing Calendar.current and .gregorian**

📌 Line 21 | 🔥 Severity: Medium | 🔎 Confidence: ⭐⭐ (2/5)
Using both `Calendar.current` and `Calendar(identifier: .gregorian)` may introduce inconsistencies.

**💡 Suggestion:** Declare a single calendar instance and reuse it consistently.

```swift
let calendar = Calendar(identifier: .gregorian)
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
