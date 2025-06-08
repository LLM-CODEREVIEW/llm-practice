template = """
<review-task>
  <instruction>
    Follow the process below to perform a step-by-step code review:

	1. Review only the lines starting with '+' (added/modified code), but use the entire file context to understand
	   - Lines starting with '-' or unchanged lines serve as context only - do not review them unless they directly affect the '+' lines.
    2. For each code block, detect issues in the following priority order:
       - Runtime Error Check: Inspect code for potential runtime errors and identify other latent risks + recommend logging implementation points
       - Optimization: Examine optimization opportunities in code patches, recommend optimized code when performance degradation is detected
       - Security Issue: Check whether code uses modules with serious security flaws or contains security vulnerabilities
       - Code Convention Compliance: Verify adherence to team-defined coding conventions (e.g., function/variable naming rules, comment styles, file/class organization order, etc.)

    3. For each identified issue, document the following:
       - File name, method/function name, and line number
       - Code snippet of the problematic lines
       - Confidence score (⭐️ to ⭐⭐⭐⭐⭐)
       - Explanation of the issue
       - Suggested improvement with code example
       - Rule Type: one of {Runtime, Logging, Optimization, Security, Convention}

    4. After detecting all issues, organize them as follows:
       - First group by severity level: 🟥 High → 🟧 Medium → 🟨 Low
       - Within each severity level, group by rule type: Runtime → Logging → Optimization → Security → Convention
       - Number the issues in each group (e.g., 1, 2, 3...)
       - Do not repeat same issues.

    ❗️Important: The <output-format> section is for structural guidance only. Never copy any of its content directly.
  </instruction>

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

  <convention-guide>
  {{CONVENTION_GUIDE_PLACEHOLDER}}
  </convention-guide>

  <output-format>
    <![CDATA[
    # ✅ PR Summary in 3 Lines
    - [Summary line 1]
    - [Summary line 2]
    - [Summary line 3]

    # 🎯 Review Difficulty: ⭐⭐⭐ (1 to 5 stars)
    # 🔑 Key Keywords: [e.g., optional unwrapping, loop optimization, naming, logging missing, etc.]

    # 🔍 Detailed Review

    ## 🟥 High Severity Issues
    ### [Runtime]
    #### 1. [Issue Title]
    📌 File: `filename.swift` | Line: XX | 🔎 Confidence: ⭐⭐⭐⭐  
    Explanation of the problem...

    💡 **Suggestion:** Suggested fix or improvement...

    ## 🟧 Medium Severity Issues
    ### [Optimization]
    #### 1. [Issue Title]
    📌 File: ...  
    ...

    ## 🟨 Low Severity Issues
    ### [Convention]
    #### 1. [Issue Title]
    ...
    ]]>
  </output-format>

  <diff>
    <![CDATA[
    {{PR_DIFF_PLACEHOLDER}}
    ]]>
  </diff>
</review-task>
"""