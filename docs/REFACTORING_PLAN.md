# Refactoring Plan: Remove Mock Mode from Production Code

**Created:** 2025-12-30  
**Status:** Planned  
**Priority:** High (Technical Debt Elimination)

---

## 🎯 Objectives

1. **Remove all `mock_mode` logic from production code** (Adapters, Services)
2. **Migrate to standard Python mocking** using `unittest.mock` and `pytest`
3. **Improve code maintainability** by eliminating dual implementation paths
4. **Align with industry best practices** as documented in `@docs/TECH_RULES.md`
5. **Maintain 99% test coverage** throughout refactoring

---

## 📊 Current State Analysis

### Impacted Files (Complete List)

#### Production Code

| File                                      | Lines of Mock Code | Mock Methods/Config                                                           | Impact     |
| ----------------------------------------- | ------------------ | ----------------------------------------------------------------------------- | ---------- |
| `app/adapters/s3/s3_adapter.py`           | ~70 lines          | `_mock_upload_file`, `_mock_list_files`, `_mock_delete_file`, `_mock_storage` | **High**   |
| `app/adapters/bedrock/bedrock_adapter.py` | ~40 lines          | `_mock_retrieve_and_generate`, `_mock_start_ingestion_job`                    | **High**   |
| `app/utils/config.py`                     | ~5 lines           | `MOCK_MODE`, `is_mock_enabled()`                                              | **Medium** |

#### Test Files

| File                                                | Occurrences | Usage Pattern                             | Impact     |
| --------------------------------------------------- | ----------- | ----------------------------------------- | ---------- |
| `app/adapters/bedrock/test_bedrock_adapter.py`      | 6           | `mock_mode=True/False` in fixture & tests | Medium     |
| `app/adapters/s3/test_s3_adapter.py`                | 6           | `mock_mode=True/False` in fixture & tests | Medium     |
| `app/services/rag/test_rag_service.py`              | 1           | `config.MOCK_MODE = True` in fixture      | Low        |
| `app/services/ingestion/test_ingestion_service.py`  | 1           | `config.MOCK_MODE = True` in fixture      | Low        |
| `app/tests/integration/test_service_integration.py` | 1           | `assert config.MOCK_MODE == ...`          | Low        |
| `conftest.py`                                       | 2           | Force `MOCK_MODE=true` globally           | **Medium** |

#### Configuration & Documentation

| File                 | Occurrences | Content                                    | Impact |
| -------------------- | ----------- | ------------------------------------------ | ------ |
| `.env.example`       | 1           | `MOCK_MODE=true`                           | Low    |
| `README.md`          | 1           | Setup instructions mentioning MOCK_MODE    | Low    |
| `ARCHITECTURE.md`    | 2           | Config example & environment setup         | Low    |
| `docs/GLOSSARY.md`   | 2           | MOCK_MODE term definition                  | Low    |
| `docs/TECH_RULES.md` | 5           | Anti-pattern examples (already updated ✅) | None   |

**Total Impact:** 11 production code changes + 6 test file updates + 5 documentation updates = **22 files**

### Dependencies

```
Config.MOCK_MODE
    ↓
BedrockAdapter.__init__(mock_mode)
    ↓
BedrockAdapter._mock_* methods
    ↓
Tests using mock_mode=True
```

---

## 🔄 Refactoring Strategy

### Phase 1: Adapter Layer Refactoring

#### Step 1.1: Refactor `S3Adapter`

**Actions:**

1. Remove `mock_mode` parameter from `__init__`
2. Remove `self.mock_mode` attribute
3. Delete all `_mock_*` methods (~70 lines)
4. Remove `self._mock_storage` dictionary
5. Simplify all public methods (remove `if self.mock_mode:` branches)

**Before:**

```python
class S3Adapter:
    def __init__(self, mock_mode: Optional[bool] = None):
        self.mock_mode = mock_mode if mock_mode is not None else config.is_mock_enabled()
        if not self.mock_mode:
            self.client = boto3.client('s3', ...)
        else:
            self.client = None
            self._mock_storage = {}

    def upload_file(self, ...):
        if self.mock_mode:
            return self._mock_upload_file(...)
        # Real implementation
```

**After:**

```python
class S3Adapter:
    def __init__(self):
        config = get_config()
        self.client = boto3.client('s3', region_name=config.AWS_REGION)

    def upload_file(self, ...):
        # Only real implementation
        try:
            response = self.client.put_object(...)
            ...
```

**Estimated Impact:**

- Lines removed: ~70
- Methods simplified: 3 (`upload_file`, `list_files`, `delete_file`)
- Test updates needed: ~10 test files

---

#### Step 1.2: Refactor `BedrockAdapter`

**Actions:**

1. Remove `mock_mode` parameter from `__init__`
2. Remove `self.mock_mode` attribute
3. Delete `_mock_retrieve_and_generate` and `_mock_start_ingestion_job` (~40 lines)
4. Simplify public methods

**Before:**

```python
class BedrockAdapter:
    def __init__(self, mock_mode: Optional[bool] = None):
        self.mock_mode = mock_mode if mock_mode is not None else config.is_mock_enabled()
        if not self.mock_mode:
            self.client = boto3.client('bedrock-agent-runtime', ...)
        else:
            self.client = None
```

**After:**

```python
class BedrockAdapter:
    def __init__(self):
        config = get_config()
        self.client = boto3.client(
            'bedrock-agent-runtime',
            region_name=config.AWS_REGION
        )
```

**Estimated Impact:**

- Lines removed: ~40
- Methods simplified: 2 (`retrieve_and_generate`, `start_ingestion_job`)
- Test updates needed: ~8 test files

---

### Phase 2: Test Migration

#### Step 2.1: Update `test_bedrock_adapter.py` (6 changes)

**Lines to Update:**

- Line 16: `return BedrockAdapter(mock_mode=True)` → `return BedrockAdapter()`
- Line 18: `def test_initialization_mock_mode` → `def test_initialization`
- Line 20: `assert adapter.mock_mode is True` → Remove assertion
- Line 138: `adapter = BedrockAdapter(mock_mode=False)` → Add `@patch('boto3.client')`
- Line 148: `adapter = BedrockAdapter(mock_mode=False)` → Add `@patch('boto3.client')`
- Line 150: `assert adapter.mock_mode is False` → Remove assertion

**Current Pattern (Wrong):**

```python
# app/adapters/bedrock/test_bedrock_adapter.py
@pytest.fixture
def adapter():
    return BedrockAdapter(mock_mode=True)  # Uses built-in mock

def test_retrieve(adapter):
    result = adapter.retrieve_and_generate(...)  # Calls _mock_* method
```

**New Pattern (Correct):**

```python
# app/adapters/bedrock/test_bedrock_adapter.py
@pytest.fixture
def mock_bedrock_client():
    with patch('boto3.client') as mock_boto3:
        client = Mock()
        mock_boto3.return_value = client
        yield client

@pytest.fixture
def adapter(mock_bedrock_client):
    return BedrockAdapter()

def test_retrieve_and_generate(adapter, mock_bedrock_client):
    # Setup mock response
    mock_bedrock_client.retrieve_and_generate.return_value = {
        'output': {'text': 'answer'},
        'sessionId': 'session-123',
        'citations': [
            {
                'retrievedReferences': [
                    {
                        'content': {'text': 'reference content'},
                        'location': {'s3Location': {'uri': 's3://bucket/key'}},
                        'metadata': {'score': 0.95}
                    }
                ]
            }
        ]
    }

    # Test real code with mocked boto3
    result = adapter.retrieve_and_generate("query", "kb-id")

    # Verify
    assert result["success"] is True
    assert result["data"].answer == "answer"
    mock_bedrock_client.retrieve_and_generate.assert_called_once()
```

---

#### Step 2.2: Update `test_s3_adapter.py` (6 changes)

**Lines to Update:**

- Line 17: `return S3Adapter(mock_mode=True)` → `return S3Adapter()`
- Line 19: `def test_initialization_mock_mode` → `def test_initialization`
- Line 21: `assert adapter.mock_mode is True` → Remove assertion
- Line 193: `adapter = S3Adapter(mock_mode=False)` → Add `@patch('boto3.client')`
- Line 203: `adapter = S3Adapter(mock_mode=False)` → Add `@patch('boto3.client')`
- Line 205: `assert adapter.mock_mode is False` → Remove assertion

**New Pattern (Correct):**

```python
# app/adapters/s3/test_s3_adapter.py
@pytest.fixture
def mock_s3_client():
    with patch('boto3.client') as mock_boto3:
        client = Mock()
        mock_boto3.return_value = client
        yield client

@pytest.fixture
def adapter(mock_s3_client):
    return S3Adapter()

def test_upload_file(adapter, mock_s3_client):
    # Setup mock
    mock_s3_client.put_object.return_value = {
        'ETag': '"mock-etag"',
        'VersionId': 'v1'
    }

    # Test
    result = adapter.upload_file(b"test", "bucket", "key")

    # Verify
    assert result["success"] is True
    assert result["data"].etag == '"mock-etag"'
    mock_s3_client.put_object.assert_called_once_with(
        Bucket="bucket",
        Key="key",
        Body=b"test"
    )
```

---

#### Step 2.3: Update Service Tests (2 files)

**Files:**

- `app/services/rag/test_rag_service.py` (Line 26)
- `app/services/ingestion/test_ingestion_service.py` (Line 28)

**Current Pattern:**

```python
@pytest.fixture
def mock_config(self):
    config = Mock(spec=Config)
    config.BEDROCK_KB_ID = "test-kb-id"
    config.MOCK_MODE = True  # Remove this line
    return config
```

**Action:**

- Remove `config.MOCK_MODE = True` line
- Service tests already use `@patch` correctly for adapters
- No other changes needed

---

#### Step 2.4: Update Integration Tests (1 file)

**File:** `app/tests/integration/test_service_integration.py`

**Line 140:** Remove or update assertion

```python
# Before
assert config1.MOCK_MODE == config2.MOCK_MODE

# After - Option 1: Remove entirely
# (assertion no longer needed)

# After - Option 2: Test different config property
assert config1.AWS_REGION == config2.AWS_REGION
```

---

#### Step 2.5: Update `conftest.py` (2 lines)

**Current Code (Lines 12-17):**

```python
@pytest.fixture(scope="session", autouse=True)
def force_mock_mode():
    """
    Force MOCK_MODE=true for all test runs.
    This prevents accidental real AWS calls during testing.
    """
    os.environ["MOCK_MODE"] = "true"
```

**Action:**

- **Option 1 (Recommended):** Remove entire fixture

  - Tests will use `@patch` instead of relying on MOCK_MODE
  - More explicit and follows best practices

- **Option 2 (Conservative):** Keep but modify to prevent real AWS calls
  ```python
  @pytest.fixture(scope="session", autouse=True)
  def prevent_real_aws_calls():
      """
      Prevent accidental real AWS calls during testing.
      Tests should explicitly use @patch('boto3.client').
      """
      # Could add environment checks or warnings here
      pass
  ```

**Recommendation:** Use Option 1 (remove fixture entirely)

---

### Phase 3: Configuration Cleanup

#### Step 3.1: Update `Config` Class

**Remove:**

```python
# app/utils/config.py
MOCK_MODE: bool = os.getenv("MOCK_MODE", "true").lower() == "true"

@classmethod
def is_mock_enabled(cls) -> bool:
    return cls.MOCK_MODE
```

**Impact:**

- `.env.example`: Remove `MOCK_MODE=true`
- Documentation: Update configuration docs
- CI/CD: No impact (tests will use mocks automatically)

---

### Phase 4: Documentation Updates

#### Files to Update:

1. **`README.md`** (1 occurrence)

   - Line 117: Remove `MOCK_MODE=true` from setup instructions
   - Update: Change to "Edit .env with your AWS credentials"

2. **`ARCHITECTURE.md`** (2 occurrences)

   - Line 337: Remove `MOCK_MODE` from config example
   - Line 354: Remove from environment variables section

3. **`docs/GLOSSARY.md`** (2 occurrences)

   - Line 236: Remove "Mock Mode" term definition
   - Line 441: Remove `MOCK_MODE` from environment variables table

4. **`docs/TECH_RULES.md`** ✅ Already updated (v1.1)

5. **`.env.example`** (1 occurrence)

   - Line 19: Remove `MOCK_MODE=true`

6. **`conftest.py`** (2 occurrences)
   - Line 12-17: Remove `autouse` fixture that forces `MOCK_MODE=true`
   - **Note:** This may impact test setup - verify all tests still run correctly

---

## 📋 Execution Checklist (Detailed)

### Pre-Refactoring ✅

- [x] Document current state analysis
- [x] Update `TECH_RULES.md` with mock guidelines (v1.1)
- [x] Create comprehensive refactoring plan
- [ ] Review plan with team/stakeholder
- [ ] Create feature branch: `git checkout -b refactor/remove-mock-mode`
- [ ] Verify all tests pass: `make test` → 234 tests ✅
- [ ] Record baseline coverage: 99%
- [ ] Commit current clean state

### Phase 1: Adapter Refactoring (2 tasks)

#### Task 1.1: Refactor `S3Adapter` (~70 lines removed)

- [ ] Backup file: `cp app/adapters/s3/s3_adapter.py app/adapters/s3/s3_adapter.py.bak`
- [ ] Remove `mock_mode` parameter from `__init__` (Line 18)
- [ ] Remove `self.mock_mode` attribute (Line 26)
- [ ] Remove `if not self.mock_mode:` branch (Lines 29-31)
- [ ] Remove `else:` block with `self._mock_storage` (Lines 32-34)
- [ ] Remove `if self.mock_mode:` check in `upload_file()` (Lines 58-59)
- [ ] Remove `if self.mock_mode:` check in `list_files()` (Lines 99-100)
- [ ] Remove `if self.mock_mode:` check in `delete_file()` (Lines 150-151)
- [ ] Delete entire section "# Mock implementations" (Lines 167-237)
  - `_mock_upload_file()` method
  - `_mock_list_files()` method
  - `_mock_delete_file()` method
- [ ] Update class docstring (remove mock mode mention)
- [ ] Update `__init__` docstring (remove mock_mode param)
- [ ] Simplify `__init__`: Always create `boto3.client('s3')`
- [ ] Run `make test` (expect failures in test_s3_adapter.py)
- [ ] Git commit: `git commit -m "refactor: remove mock mode from S3Adapter"`

**Validation:**

- [ ] File size reduced by ~70 lines
- [ ] No `mock_mode` references in `s3_adapter.py`
- [ ] `__init__` only has real boto3 client creation

#### Task 1.2: Refactor `BedrockAdapter` (~40 lines removed)

- [ ] Backup file: `cp app/adapters/bedrock/bedrock_adapter.py app/adapters/bedrock/bedrock_adapter.py.bak`
- [ ] Remove `mock_mode` parameter from `__init__` (Line 19)
- [ ] Remove `self.mock_mode` attribute (Line 27)
- [ ] Remove `if not self.mock_mode:` branch (Lines 31-36)
- [ ] Remove `else:` block with `self.client = None` (Lines 37-38)
- [ ] Remove `if self.mock_mode:` check in `retrieve_and_generate()` (Lines 61-62)
- [ ] Remove `if self.mock_mode:` check in `start_ingestion_job()` (Lines 130-131)
- [ ] Delete `_mock_retrieve_and_generate()` method (~20 lines)
- [ ] Delete `_mock_start_ingestion_job()` method (~10 lines)
- [ ] Update class and method docstrings
- [ ] Simplify `__init__`: Always create boto3 clients
- [ ] Run `make test` (expect failures in test_bedrock_adapter.py)
- [ ] Git commit: `git commit -m "refactor: remove mock mode from BedrockAdapter"`

**Validation:**

- [ ] File size reduced by ~40 lines
- [ ] No `mock_mode` references in `bedrock_adapter.py`
- [ ] Both boto3 clients always initialized

---

### Phase 2: Test Migration (5 tasks - HIGH PRIORITY)

#### Task 2.1: Update `test_bedrock_adapter.py` (6 changes)

- [ ] Add import: `from unittest.mock import Mock, patch, MagicMock`
- [ ] Create fixture `mock_bedrock_runtime_client()`
- [ ] Create fixture `mock_bedrock_agent_client()`
- [ ] Update `adapter` fixture: Remove `mock_mode=True`, add client fixtures
- [ ] Rename `test_initialization_mock_mode` → `test_initialization`
- [ ] Remove `assert adapter.mock_mode is True` (Line 20)
- [ ] Update `test_retrieve_and_generate_basic`:
  - Add `@patch('boto3.client')`
  - Setup `mock_client.retrieve_and_generate.return_value = {...}`
  - Verify with `assert_called_once()`
- [ ] Update `test_start_ingestion_job`:
  - Add `@patch('boto3.client')`
  - Setup `mock_client.start_ingestion_job.return_value = {...}`
- [ ] Update Real Mode tests (Lines 138-150):
  - Replace `mock_mode=False` with `@patch('boto3.client')`
  - Mock boto3 responses instead of asserting mock_mode
- [ ] Run: `PYTHONPATH=. pytest app/adapters/bedrock/test_bedrock_adapter.py -v`
- [ ] Verify coverage: `pytest app/adapters/bedrock/ --cov=app/adapters/bedrock --cov-report=term-missing`
- [ ] Target: Maintain 100% coverage ✅
- [ ] Git commit: `git commit -m "test: migrate bedrock adapter tests to use @patch"`

**Key Changes Example:**

```python
# Before
@pytest.fixture
def adapter():
    return BedrockAdapter(mock_mode=True)

# After
@pytest.fixture
def mock_bedrock_client():
    with patch('boto3.client') as mock:
        client = Mock()
        mock.return_value = client
        yield client

@pytest.fixture
def adapter(mock_bedrock_client):
    return BedrockAdapter()
```

---

#### Task 2.2: Update `test_s3_adapter.py` (6 changes)

- [ ] Add import: `from unittest.mock import Mock, patch`
- [ ] Create fixture `mock_s3_client()`
- [ ] Update `adapter` fixture: Remove `mock_mode=True`, add client fixture
- [ ] Rename `test_initialization_mock_mode` → `test_initialization`
- [ ] Remove `assert adapter.mock_mode is True` (Line 21)
- [ ] Update `test_upload_file`:
  - Setup `mock_s3_client.put_object.return_value = {...}`
- [ ] Update `test_list_files`:
  - Setup `mock_s3_client.list_objects_v2.return_value = {...}`
- [ ] Update `test_delete_file`:
  - Setup `mock_s3_client.delete_object.return_value = {...}`
- [ ] Update Real Mode tests (Lines 193-205):
  - Replace with proper `@patch('boto3.client')` mocking
- [ ] Run: `PYTHONPATH=. pytest app/adapters/s3/test_s3_adapter.py -v`
- [ ] Verify coverage: `pytest app/adapters/s3/ --cov=app/adapters/s3 --cov-report=term-missing`
- [ ] Target: Maintain 94%+ coverage ✅
- [ ] Git commit: `git commit -m "test: migrate s3 adapter tests to use @patch"`

---

#### Task 2.3: Update Service Tests (2 files)

- [ ] File: `app/services/rag/test_rag_service.py`
  - [ ] Remove Line 26: `config.MOCK_MODE = True`
  - [ ] Verify existing `@patch('app.services.rag.rag_service.BedrockAdapter')` still works
  - [ ] Run: `PYTHONPATH=. pytest app/services/rag/test_rag_service.py -v`
- [ ] File: `app/services/ingestion/test_ingestion_service.py`
  - [ ] Remove Line 28: `config.MOCK_MODE = True`
  - [ ] Verify existing patches still work
  - [ ] Run: `PYTHONPATH=. pytest app/services/ingestion/test_ingestion_service.py -v`
- [ ] Run full service test suite: `make test`
- [ ] Verify no test failures
- [ ] Git commit: `git commit -m "test: remove MOCK_MODE from service test configs"`

---

#### Task 2.4: Update Integration Tests

- [ ] File: `app/tests/integration/test_service_integration.py`
  - [ ] Line 140: Remove `assert config1.MOCK_MODE == config2.MOCK_MODE`
  - [ ] Or replace with: `assert config1.AWS_REGION == config2.AWS_REGION`
- [ ] File: `app/tests/integration/test_api_integration.py`
  - [ ] Search for "mock mode" comments
  - [ ] Update or remove comments as needed
- [ ] Run: `PYTHONPATH=. pytest app/tests/integration/ -v`
- [ ] Verify all integration tests pass
- [ ] Git commit: `git commit -m "test: update integration tests to remove MOCK_MODE refs"`

---

#### Task 2.5: Update `conftest.py`

- [ ] Review Lines 12-17: `force_mock_mode` fixture
- [ ] **Option 1 (Recommended):** Delete entire fixture
  ```python
  # Remove this:
  @pytest.fixture(scope="session", autouse=True)
  def force_mock_mode():
      os.environ["MOCK_MODE"] = "true"
  ```
- [ ] **Option 2 (Conservative):** Rename and simplify
  ```python
  @pytest.fixture(scope="session", autouse=True)
  def test_environment_setup():
      """Ensure test environment is properly configured."""
      # Add any necessary test environment setup
      pass
  ```
- [ ] Run full test suite: `make test`
- [ ] Verify 234 tests still pass
- [ ] Git commit: `git commit -m "test: remove force_mock_mode fixture from conftest"`

**Validation:**

- [ ] All 234 tests passing ✅
- [ ] No test uses `mock_mode` parameter
- [ ] All adapter tests use `@patch('boto3.client')`
- [ ] Coverage maintained at 99%

---

### Phase 3: Configuration Cleanup (2 tasks)

#### Task 3.1: Update `Config` Class

- [ ] File: `app/utils/config.py`
  - [ ] Remove Line 35: `MOCK_MODE: bool = os.getenv(...)`
  - [ ] Remove Lines 42-44: `is_mock_enabled()` method
  - [ ] Update class docstring (remove MOCK_MODE mention)
- [ ] Search for imports: `grep -r "is_mock_enabled" app/`
  - [ ] Verify no remaining imports
- [ ] Run: `PYTHONPATH=. pytest app/utils/ -v` (if tests exist)
- [ ] Run full test suite: `make test`
- [ ] Git commit: `git commit -m "refactor: remove MOCK_MODE from Config class"`

#### Task 3.2: Update Environment Files

- [ ] File: `.env.example`
  - [ ] Remove Line 19: `MOCK_MODE=true`
  - [ ] Add comment: `# All configuration is for AWS services`
- [ ] File: `.env` (if exists locally)
  - [ ] Remove `MOCK_MODE=true` line
- [ ] Verify: `grep -r "MOCK_MODE" .env*`
- [ ] Git commit: `git commit -m "chore: remove MOCK_MODE from environment files"`

---

### Phase 4: Documentation (6 tasks)

#### Task 4.1: Update `README.md`

- [ ] Line 117: Change from:
  ```
  # Edit .env with your configuration (use MOCK_MODE=true for local development)
  ```
  To:
  ```
  # Edit .env with your AWS configuration
  ```
- [ ] Search for other "MOCK_MODE" or "mock mode" mentions
- [ ] Update testing section if needed
- [ ] Git commit: `git commit -m "docs: remove MOCK_MODE from README"`

#### Task 4.2: Update `ARCHITECTURE.md`

- [ ] Line 337: Remove `MOCK_MODE: bool = False` from config example
- [ ] Line 354: Remove `MOCK_MODE=true` from environment section
- [ ] Update "Adapter Layer" section:
  - Remove mentions of mock implementations
  - Clarify that adapters only handle real AWS calls
  - Testing is done via mocked boto3 clients
- [ ] Git commit: `git commit -m "docs: update ARCHITECTURE.md to remove mock mode"`

#### Task 4.3: Update `docs/GLOSSARY.md`

- [ ] Line 236: Remove "Mock Mode" term definition entirely
- [ ] Line 441: Remove `MOCK_MODE` row from environment variables table
- [ ] Verify no other mock mode references
- [ ] Git commit: `git commit -m "docs: remove Mock Mode from GLOSSARY"`

#### Task 4.4: Update `PROJECT_STATUS.md`

- [ ] Add new entry in changelog/recent achievements:
  ```markdown
  **Recent Refactoring (2025-12-30):** ✅ Removed mock mode from production code

  - Eliminated 110 lines of mock implementations from adapters
  - Migrated all tests to use standard Python mocking (@patch, Mock)
  - Improved code maintainability and aligned with Python best practices
  - Maintained 99% test coverage and 234 passing tests
  ```
- [ ] Update Phase 4 or add new "Technical Debt Elimination" section
- [ ] Git commit: `git commit -m "docs: update PROJECT_STATUS with refactoring completion"`

#### Task 4.5: Verify `docs/TECH_RULES.md`

- [ ] Confirm Section 10 is correctly updated ✅ (already done)
- [ ] Verify version history shows v1.1
- [ ] No action needed (already completed)

#### Task 4.6: Update/Archive `docs/REFACTORING_PLAN.md`

- [ ] Add completion date at top
- [ ] Mark all tasks as complete
- [ ] Add "Completed" badge
- [ ] Git commit: `git commit -m "docs: mark refactoring plan as completed"`

---

### Validation (Critical - Do NOT skip)

- [ ] **Code Quality Checks:**

  - [ ] Run: `grep -r "mock_mode" app/ --include="*.py" | grep -v test` → Should return NOTHING
  - [ ] Run: `grep -r "_mock_" app/ --include="*.py" | grep -v test` → Should return NOTHING
  - [ ] Run: `grep -r "MOCK_MODE" app/ --include="*.py"` → Should only appear in tests (if at all)
  - [ ] Run: `grep -r "is_mock_enabled" app/ --include="*.py"` → Should return NOTHING

- [ ] **Test Suite Validation:**

  - [ ] Run: `make test` → **All 234 tests pass** ✅
  - [ ] Run: `PYTHONPATH=. pytest --cov=app --cov-report=term-missing` → **Coverage ≥99%** ✅
  - [ ] Verify no warnings about missing coverage in adapters
  - [ ] Check for any test deprecation warnings

- [ ] **Adapter Verification:**

  - [ ] `app/adapters/bedrock/bedrock_adapter.py`: ~188 lines → ~148 lines (40 removed)
  - [ ] `app/adapters/s3/s3_adapter.py`: ~237 lines → ~167 lines (70 removed)
  - [ ] Both adapters only have real AWS implementation
  - [ ] No conditional `if mock_mode:` branches

- [ ] **Test File Verification:**

  - [ ] All adapter tests use `@patch('boto3.client')`
  - [ ] No test file instantiates adapters with `mock_mode=True/False`
  - [ ] Service tests don't set `config.MOCK_MODE`
  - [ ] Integration tests don't assert on `MOCK_MODE`

- [ ] **Documentation Verification:**

  - [ ] `grep -r "MOCK_MODE\|mock mode\|Mock Mode" docs/` → Only in TECH_RULES.md (as anti-pattern)
  - [ ] `grep "MOCK_MODE" .env.example` → Should return nothing
  - [ ] README.md updated
  - [ ] ARCHITECTURE.md updated
  - [ ] GLOSSARY.md updated

- [ ] **Git Status:**
  - [ ] Run: `git status` → Working directory clean
  - [ ] Run: `git log --oneline -10` → See all refactoring commits
  - [ ] Verify commit messages follow convention: `refactor:`, `test:`, `docs:`, `chore:`

---

### Finalization

- [ ] **Final Test Run:**

  - [ ] `make test` → 234 tests ✅
  - [ ] `make lint` (if exists)
  - [ ] Manual spot-check: Start app, verify no mock mode warnings

- [ ] **Code Review:**

  - [ ] Self-review all changes using `git diff main...refactor/remove-mock-mode`
  - [ ] Verify no accidental deletions
  - [ ] Check all docstrings updated
  - [ ] Request peer review (if applicable)

- [ ] **Merge Preparation:**

  - [ ] Rebase on main: `git rebase main`
  - [ ] Squash commits (optional): `git rebase -i main`
  - [ ] Final test: `make test`
  - [ ] Push branch: `git push origin refactor/remove-mock-mode`

- [ ] **Merge to Main:**

  - [ ] Create Pull Request
  - [ ] Wait for CI/CD pipeline (if exists)
  - [ ] Merge PR
  - [ ] Delete branch: `git branch -d refactor/remove-mock-mode`

- [ ] **Post-Merge:**
  - [ ] Update `PROJECT_STATUS.md` on main branch
  - [ ] Archive this refactoring plan (move to `docs/archived/` or add "Completed" tag)
  - [ ] Close related technical debt issue/ticket
  - [ ] Notify team of completion

---

## 🎯 Success Criteria

1. ✅ **Zero `mock_mode` references** in production code (`app/adapters/`, `app/services/`)
2. ✅ **All tests use standard mocking** (`@patch`, `Mock()`)
3. ✅ **Test coverage ≥99%** maintained
4. ✅ **234+ tests passing**
5. ✅ **Code complexity reduced** (fewer lines, fewer branches)
6. ✅ **Adapter classes are pure** (single responsibility)

---

## 📊 Estimated Effort

| Phase                        | Tasks        | Estimated Time | Complexity      |
| ---------------------------- | ------------ | -------------- | --------------- |
| Phase 1: Adapter Refactoring | 2            | 2-3 hours      | Medium          |
| Phase 2: Test Migration      | 4            | 4-5 hours      | High            |
| Phase 3: Config Cleanup      | 2            | 1 hour         | Low             |
| Phase 4: Documentation       | 4            | 1-2 hours      | Low             |
| **Total**                    | **12 tasks** | **8-11 hours** | **Medium-High** |

---

## 🚨 Risks & Mitigation

### Risk 1: Test Coverage Drop

**Mitigation:**

- Run coverage after each adapter refactoring
- Target: Keep coverage ≥99%
- If coverage drops, add missing test cases immediately

### Risk 2: Breaking Integration Tests

**Mitigation:**

- Update integration tests in Phase 2.4
- Consider creating separate "real AWS" test suite for manual E2E testing
- Use `@pytest.mark.integration` to separate unit vs integration

### Risk 3: Unexpected Dependencies

**Mitigation:**

- Search codebase for all `mock_mode` references before starting
- Use `git grep -n "mock_mode"` to find all occurrences
- Review all imports of `Config` class

---

## 📈 Benefits

### Code Quality

- **-110 lines** of production code (mock implementations)
- **Simpler code paths** (no `if mock_mode:` branches)
- **Single responsibility** for adapters

### Maintainability

- **Fewer methods** to maintain per adapter
- **Standard testing patterns** (easier for new developers)
- **Aligned with Python best practices**

### Testing

- **Better isolation** (tests control mocking, not production code)
- **More realistic tests** (mocking at boto3 boundary, not adapter boundary)
- **Easier to add new tests** (standard pytest patterns)

### Security

- **Reduced attack surface** (no test code in production)
- **Clearer production code** (only real AWS logic)

---

## 🔗 Related Documents

- [`@docs/TECH_RULES.md`](TECH_RULES.md) - Section 10: Mock Usage & Testing Strategy
- [`@ARCHITECTURE.md`](../ARCHITECTURE.md) - Adapter Layer
- [`@PROJECT_STATUS.md`](../PROJECT_STATUS.md) - Current progress tracking

---

## 📝 Notes

- This refactoring aligns with the **Atomic Loop** development workflow
- Each task should be completed, tested, and committed independently
- Update `PROJECT_STATUS.md` after completing each phase
- Consider creating a new Phase in `PROJECT_STATUS.md` for this refactoring work

---

**Next Action:** Review this plan with the team and get approval before starting Phase 1.
