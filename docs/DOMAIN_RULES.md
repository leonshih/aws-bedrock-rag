# Domain Rules (Business Logic & Integrity)

This document defines the **Business Logic Rules** and **Data Consistency Patterns** that the AI must follow.
Unlike `TECH_RULES.md` (which focuses on code style and architecture), this document focuses on **Correctness and Data Integrity**.

---

## 📂 1. Core Domains

### [INGEST] Document Ingestion

#### Rule 1.1: Logical Tenant Isolation (Metadata Enforcement)

Physical path isolation (e.g., S3 Service Paths) is **insufficient** for data security.
**ALL** Bedrock Knowledge Base Ingestion operations MUST include explicit tenant metadata.

- **Requirement:** Every document uploaded to S3 MUST have a corresponding `.metadata.json` sidecar.
- **Mandatory Field:** `{ "tenant_id": "<UUID>" }`
- **Reason:** Bedrock Knowledge Base uses vector filters, not file paths, for retrieval isolation.
- **Enforcement:** `IngestionService` must force-inject `tenant_id` into the metadata dictionary before S3 upload.

#### Rule 1.2: System vs. User Metadata

Metadata is divided into two categories:

1.  **System Metadata (Read-Only/System-Managed):** `tenant_id`, `upload_timestamp`, `source_system`.
2.  **User Metadata (Mutable):** `category`, `tags`, `description`.

**Implementation Pattern:**

```python
final_metadata = {
    **user_provided_metadata,  # User input
    "tenant_id": str(tenant_id),  # System override (FORCE)
    "uploaded_at": datetime.now(UTC).isoformat()
}
```

### [RAG] Retrieval & Generation

#### Rule 2.1: Strict Tenant Filtering

- **ALL** RAG queries to Bedrock MUST include a `filter` for `tenant_id`.
- **NEVER** rely solely on the prompt instruction (e.g., "Only answer for tenant X") for security.
- **Pattern:** `rag_service.py` must inject the filter at the _lowest possible level_ before calling the adapter.

---

## 🛡️ 2. Cross-Cutting Concerns

### [DATA] Data Consistency & Integrity

#### Rule X.1: Transactional Integrity (All or Nothing)

Any Service method that performs multiple external write operations (e.g., "Upload File" + "Upload Metadata" + "Sync KB") MUST implement **Compensating Transactions** (Saga Pattern Lite).

**Scenario:**
If `Step 2 (Metadata Upload)` fails after `Step 1 (File Upload)` succeeds, the system is in an invalid state.

**Required Pattern:**

```python
try:
    # Step 1
    s3.upload_file(...)

    # Step 2
    s3.upload_metadata(...)

    # Step 3
    bedrock.sync(...)
except Exception as e:
    # ROLLBACK
    logger.error("Transaction failed, rolling back...")
    s3.delete_file(...)  # Compensate Step 1
    s3.delete_metadata(...) # Compensate Step 2
    raise DomainTransactionError(e)
```
