# Requirements Document: Testcase Comparison Feature
## Introduction

The Testcase Comparison Feature enables users to select and compare multiple testcases (2-10) to analyze differences in bot responses, response times, and overall quality. The system validates that selected testcases share common criteria (same question OR same bot URL), performs visual diff highlighting using Myers algorithm, calculates semantic similarity using OpenAI embeddings, provides LLM-powered comprehensive analysis with actionable suggestions, displays metrics in an interactive dashboard with charts, offers smart suggestions for which testcases to compare, maintains comparison history in localStorage, supports exporting comparison results to Excel, and presents results in a side-by-side view with interactive filters.

## Glossary

- **Testcase**: A test scenario containing code, name, group, turns (question-expected pairs), criteria, and bot_url
- **Turn**: A single question-expected-actual response triplet within a testcase
- **Comparison_System**: The frontend and backend components that handle testcase comparison
- **Selection_Manager**: Frontend component managing checkbox selection state
- **Validation_Engine**: Component that validates comparison criteria (same question OR same bot URL)
- **Diff_Engine**: Component that performs Myers algorithm visual diff on actual responses
- **Similarity_Engine**: Component that calculates semantic similarity using OpenAI embeddings
- **LLM_Analyzer**: Backend component using GPT-4o-mini to provide comprehensive analysis
- **Metrics_Dashboard**: Frontend component displaying comparison metrics with charts
- **Suggestion_Engine**: Component that recommends which testcases to compare
- **History_Manager**: Component managing comparison history in localStorage
- **Export_Engine**: Component that exports comparison results to Excel format
- **Filter_Manager**: Component managing interactive filters on comparison results
- **Comparison_Mode**: One of three modes: bot_url (same question, different bot URLs), time (same question and bot URL), or free (no common criteria)
- **Myers_Algorithm**: Standard diff algorithm for computing minimal edit distance
- **Semantic_Similarity_Score**: Cosine similarity score (0.0-1.0) between response embeddings
- **Comparison_Record**: A saved comparison session with metadata and results

## Requirements

### Requirement 1: Testcase Selection

**User Story:** As a tester, I want to select 2-10 testcases using checkboxes, so that I can compare their results.

#### Acceptance Criteria

1. WHEN a user clicks a testcase checkbox, THE Selection_Manager SHALL toggle the selection state
2. WHEN selection count is less than 2 OR greater than 10, THE Selection_Manager SHALL disable the compare button
3. WHEN selection count is between 2 and 10 inclusive, THE Selection_Manager SHALL enable the compare button
4. THE Selection_Manager SHALL display the current selection count in real-time
5. WHEN a user clicks "clear selection", THE Selection_Manager SHALL deselect all testcases

**Property-Based Testing:**
- **Invariant**: Selection count SHALL always equal the number of checked checkboxes
- **Invariant**: Compare button enabled state SHALL equal (2 <= selection_count <= 10)
- **Metamorphic**: Adding then removing a selection SHALL return to original state

---

### Requirement 2: Comparison Validation

**User Story:** As a tester, I want the system to validate that selected testcases can be compared, so that I only compare meaningful combinations.

#### Acceptance Criteria

1. WHEN all selected testcases have at least one turn with the same question AND different bot_urls, THE Validation_Engine SHALL set comparison_mode to "bot_url"
2. WHEN all selected testcases have the same question AND the same bot_url, THE Validation_Engine SHALL set comparison_mode to "time"
3. WHEN selected testcases have neither same question NOR same bot_url, THE Validation_Engine SHALL set comparison_mode to "free"
4. WHEN user clicks compare button, THE Validation_Engine SHALL validate selection before proceeding
5. IF validation fails, THEN THE Comparison_System SHALL display an error message explaining the validation failure

**Property-Based Testing:**
- **Invariant**: Every valid comparison SHALL have exactly one comparison_mode
- **Model-Based**: Validation logic SHALL match the decision tree: (same_question AND NOT same_bot_url) → bot_url; (same_question AND same_bot_url) → time; (NOT same_question AND NOT same_bot_url) → free
- **Error Conditions**: Invalid selections (count < 2 or count > 10) SHALL return validation error

---

### Requirement 3: Visual Diff Highlighting

**User Story:** As a tester, I want to see visual differences between actual responses, so that I can quickly identify what changed.

#### Acceptance Criteria

1. WHEN comparison modal opens, THE Diff_Engine SHALL compute Myers algorithm diff for all actual response pairs
2. THE Diff_Engine SHALL highlight added text in green background
3. THE Diff_Engine SHALL highlight removed text in red background with strikethrough
4. THE Diff_Engine SHALL display unchanged text in normal style
5. WHEN actual responses are identical, THE Diff_Engine SHALL display "No differences" message

**Property-Based Testing:**
- **Round-Trip**: Applying diff operations (additions and deletions) SHALL reconstruct the target response
- **Invariant**: Total character count of (unchanged + added) SHALL equal target response length
- **Idempotence**: Computing diff twice on same inputs SHALL produce identical results
- **Metamorphic**: diff(A, B) additions SHALL equal diff(B, A) deletions

---

### Requirement 4: Semantic Similarity Scoring

**User Story:** As a tester, I want to see semantic similarity scores between responses, so that I can understand how similar responses are in meaning.

#### Acceptance Criteria

1. WHEN comparison modal opens, THE Similarity_Engine SHALL generate OpenAI embeddings for all actual responses
2. THE Similarity_Engine SHALL compute cosine similarity between all response pairs
3. THE Similarity_Engine SHALL display similarity scores as percentages (0-100%)
4. WHEN similarity score is >= 90%, THE Similarity_Engine SHALL display score in green
5. WHEN similarity score is >= 70% AND < 90%, THE Similarity_Engine SHALL display score in yellow
6. WHEN similarity score is < 70%, THE Similarity_Engine SHALL display score in red

**Property-Based Testing:**
- **Invariant**: Similarity score SHALL always be between 0.0 and 1.0 inclusive
- **Invariant**: Similarity of a response with itself SHALL equal 1.0
- **Metamorphic**: similarity(A, B) SHALL equal similarity(B, A) (symmetry)
- **Error Conditions**: Empty responses SHALL return similarity score of 0.0

---

### Requirement 5: LLM Comprehensive Analysis

**User Story:** As a tester, I want LLM to analyze comparison results and provide actionable suggestions, so that I can improve bot responses.

#### Acceptance Criteria

1. WHEN comparison modal opens, THE LLM_Analyzer SHALL analyze all selected testcases using GPT-4o-mini
2. THE LLM_Analyzer SHALL identify common patterns across responses
3. THE LLM_Analyzer SHALL identify outliers and anomalies
4. THE LLM_Analyzer SHALL provide specific, actionable improvement suggestions
5. THE LLM_Analyzer SHALL rank suggestions by priority (Critical, Major, Minor)
6. WHEN LLM analysis fails, THE LLM_Analyzer SHALL display error message and allow retry

**Property-Based Testing:**
- **Error Conditions**: Network failures SHALL return graceful error with retry option
- **Error Conditions**: Invalid API responses SHALL be caught and logged
- **Invariant**: Analysis SHALL always include at least one of: patterns, outliers, or suggestions

---

### Requirement 6: Metrics Dashboard

**User Story:** As a tester, I want to see comparison metrics in a visual dashboard, so that I can quickly understand performance differences.

#### Acceptance Criteria

1. THE Metrics_Dashboard SHALL display fastest response time with testcase code
2. THE Metrics_Dashboard SHALL display slowest response time with testcase code
3. THE Metrics_Dashboard SHALL display average response time across all selected testcases
4. THE Metrics_Dashboard SHALL display pass rate as percentage
5. THE Metrics_Dashboard SHALL render a bar chart showing response times for all testcases
6. WHEN user hovers over a bar, THE Metrics_Dashboard SHALL display detailed tooltip with testcase info

**Property-Based Testing:**
- **Invariant**: Fastest time SHALL be <= all other times
- **Invariant**: Slowest time SHALL be >= all other times
- **Invariant**: Average time SHALL be between fastest and slowest (inclusive)
- **Invariant**: Pass rate SHALL equal (passed_count / total_count) * 100
- **Metamorphic**: Adding a testcase with time T SHALL update average according to formula: new_avg = (old_avg * old_count + T) / (old_count + 1)

---

### Requirement 7: Smart Comparison Suggestions

**User Story:** As a tester, I want the system to suggest which testcases to compare, so that I can discover meaningful comparisons.

#### Acceptance Criteria

1. THE Suggestion_Engine SHALL identify testcases with same question but different bot_urls
2. THE Suggestion_Engine SHALL identify testcases with same bot_url but significantly different response times (>500ms difference)
3. THE Suggestion_Engine SHALL identify testcases with same question where one passed and one failed
4. THE Suggestion_Engine SHALL display suggestions as clickable cards
5. WHEN user clicks a suggestion card, THE Suggestion_Engine SHALL auto-select the suggested testcases and open comparison modal

**Property-Based Testing:**
- **Invariant**: All suggested testcase sets SHALL pass validation criteria
- **Invariant**: Suggested set size SHALL be between 2 and 10 inclusive
- **Metamorphic**: Filtering testcases SHALL reduce or maintain suggestion count (never increase)

---

### Requirement 8: Comparison History

**User Story:** As a tester, I want to view my comparison history, so that I can revisit previous comparisons.

#### Acceptance Criteria

1. WHEN a comparison completes, THE History_Manager SHALL save comparison record to localStorage
2. THE History_Manager SHALL store testcase codes, comparison_mode, timestamp, and summary metrics
3. THE History_Manager SHALL display history as a list with most recent first
4. WHEN user clicks a history record, THE History_Manager SHALL restore and display that comparison
5. THE History_Manager SHALL limit history to 50 most recent records
6. WHEN history exceeds 50 records, THE History_Manager SHALL remove oldest records

**Property-Based Testing:**
- **Invariant**: History count SHALL never exceed 50
- **Invariant**: History records SHALL be sorted by timestamp descending
- **Round-Trip**: Saving then loading a comparison SHALL restore all comparison data
- **Idempotence**: Saving the same comparison twice SHALL not create duplicate records

---

### Requirement 9: Export to Excel

**User Story:** As a tester, I want to export comparison results to Excel, so that I can share results with stakeholders.

#### Acceptance Criteria

1. THE Export_Engine SHALL create an Excel file with multiple sheets: Summary, Details, Diff, Similarity, LLM_Analysis
2. THE Summary sheet SHALL contain comparison metadata, metrics, and pass rate
3. THE Details sheet SHALL contain all testcase data in tabular format
4. THE Diff sheet SHALL contain visual diff results with color coding
5. THE Similarity sheet SHALL contain similarity matrix with scores
6. THE LLM_Analysis sheet SHALL contain full LLM analysis text
7. WHEN user clicks export button, THE Export_Engine SHALL download the Excel file with filename format: "comparison_YYYYMMDD_HHMMSS.xlsx"

**Property-Based Testing:**
- **Invariant**: Exported file SHALL contain exactly 6 sheets
- **Invariant**: Details sheet row count SHALL equal selected testcase count + 1 (header)
- **Round-Trip**: Exporting then importing SHALL preserve all comparison data
- **Error Conditions**: Export failures SHALL display error message without crashing

---

### Requirement 10: Side-by-Side View

**User Story:** As a tester, I want to view testcases side-by-side, so that I can easily compare responses visually.

#### Acceptance Criteria

1. THE Comparison_System SHALL display testcases in a horizontal scrollable table
2. THE Comparison_System SHALL fix the first column (testcase code) during horizontal scroll
3. THE Comparison_System SHALL display each testcase as a column with: code, name, bot_url, question, actual response, time, verdict
4. WHEN user scrolls horizontally, THE Comparison_System SHALL maintain header alignment
5. THE Comparison_System SHALL highlight the currently focused column

**Property-Based Testing:**
- **Invariant**: Column count SHALL equal selected testcase count + 1 (fixed column)
- **Invariant**: Fixed column SHALL remain visible during all scroll positions
- **Metamorphic**: Reordering columns SHALL not change data content

---

### Requirement 11: Interactive Filters

**User Story:** As a tester, I want to filter comparison results, so that I can focus on specific aspects.

#### Acceptance Criteria

1. THE Filter_Manager SHALL provide filters for: verdict (PASSED/FAILED), response time range, bot_url, group
2. WHEN user applies a filter, THE Filter_Manager SHALL update the comparison view to show only matching testcases
3. THE Filter_Manager SHALL display active filter count
4. WHEN user clears filters, THE Filter_Manager SHALL restore all testcases to view
5. THE Filter_Manager SHALL persist filter state during tab switching

**Property-Based Testing:**
- **Invariant**: Filtered testcase count SHALL be <= original testcase count
- **Metamorphic**: Applying then removing a filter SHALL restore original view
- **Confluence**: Order of applying multiple filters SHALL not affect final result
- **Idempotence**: Applying the same filter twice SHALL produce identical results

---

### Requirement 12: Comparison API Endpoint

**User Story:** As a developer, I want a backend API endpoint for comparison, so that the frontend can request LLM analysis and similarity scores.

#### Acceptance Criteria

1. THE Comparison_System SHALL expose POST /api/compare endpoint
2. THE endpoint SHALL accept request body with: testcase_codes array, comparison_mode
3. THE endpoint SHALL return response with: llm_analysis, similarity_matrix, diff_results, metrics
4. WHEN LLM analysis fails, THE endpoint SHALL return partial results with error flag
5. THE endpoint SHALL complete within 30 seconds or return timeout error

**Property-Based Testing:**
- **Error Conditions**: Invalid testcase codes SHALL return 400 Bad Request
- **Error Conditions**: Empty testcase array SHALL return 400 Bad Request
- **Error Conditions**: Testcase count < 2 or > 10 SHALL return 400 Bad Request
- **Invariant**: Response similarity_matrix SHALL be symmetric (matrix[i][j] == matrix[j][i])

---

### Requirement 13: Embedding Generation and Caching

**User Story:** As a developer, I want to cache embeddings, so that repeated comparisons are faster.

#### Acceptance Criteria

1. THE Similarity_Engine SHALL generate embeddings using OpenAI text-embedding-3-small model
2. THE Similarity_Engine SHALL cache embeddings in memory with key: hash(actual_response)
3. WHEN an embedding exists in cache, THE Similarity_Engine SHALL reuse it instead of calling OpenAI API
4. THE Similarity_Engine SHALL limit cache size to 1000 entries
5. WHEN cache exceeds 1000 entries, THE Similarity_Engine SHALL evict least recently used entries

**Property-Based Testing:**
- **Invariant**: Cache size SHALL never exceed 1000
- **Round-Trip**: Storing then retrieving an embedding SHALL return identical vector
- **Idempotence**: Generating embedding for same text twice SHALL produce identical results (when not using cache)
- **Metamorphic**: Cache hit rate SHALL increase with repeated comparisons of same testcases

---

### Requirement 14: Comparison Modal Tabs

**User Story:** As a tester, I want to switch between different comparison views, so that I can analyze results from multiple perspectives.

#### Acceptance Criteria

1. THE Comparison_System SHALL display three tabs: "Bảng so sánh" (Table), "Chỉ số" (Metrics), "Phân tích LLM" (LLM Analysis)
2. WHEN user clicks a tab, THE Comparison_System SHALL display the corresponding content
3. THE Comparison_System SHALL maintain active tab state during modal lifetime
4. THE Comparison_System SHALL load LLM analysis asynchronously without blocking other tabs
5. WHEN LLM analysis is loading, THE Comparison_System SHALL display loading spinner

**Property-Based Testing:**
- **Invariant**: Exactly one tab SHALL be active at any time
- **Idempotence**: Clicking the same tab twice SHALL not change view
- **Metamorphic**: Switching tabs SHALL not modify comparison data

---

### Requirement 15: Response Time Classification

**User Story:** As a tester, I want response times to be classified, so that I can quickly identify performance issues.

#### Acceptance Criteria

1. WHEN response_time_ms <= 2000, THE Comparison_System SHALL classify as "Nhanh" (Fast) with green indicator
2. WHEN response_time_ms > 2000 AND <= 3000, THE Comparison_System SHALL classify as "Chấp nhận được" (Acceptable) with yellow indicator
3. WHEN response_time_ms > 3000, THE Comparison_System SHALL classify as "Chậm" (Slow) with red indicator
4. THE Comparison_System SHALL display time classification in metrics dashboard
5. THE Comparison_System SHALL use time classification in LLM analysis context

**Property-Based Testing:**
- **Invariant**: Every response time SHALL map to exactly one classification
- **Metamorphic**: Classification boundaries SHALL be consistent across all components
- **Model-Based**: Classification logic SHALL match: (t <= 2000) → Fast; (2000 < t <= 3000) → Acceptable; (t > 3000) → Slow

