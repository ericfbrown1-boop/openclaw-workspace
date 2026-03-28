---
name: ragflow-search
description: >
  Query RAGFlow knowledge bases on PowerSpec for citation-backed answers.
  Supports contract analysis, competitive intel, and general document Q&A.
  Accessible via Tailscale at remote-coder-main:9380.
---

# RAGFlow Knowledge Base Search

## When to Use

- Eric asks a question that could be answered by uploaded documents
- Contract analysis needs reference to prior contracts, CUAD taxonomy, or legal templates
- Competitive intel queries against uploaded earnings transcripts, analyst reports
- Any "search my documents" or "find in my files" type request
- Cross-referencing information across multiple uploaded knowledge bases

## Prerequisites

- RAGFlow running on PowerSpec (`remote-coder-main:8880` for UI, `:9380` for API)
- Valid RAGFlow API key (get from RAGFlow UI: Profile > API Keys)
- At least one knowledge base populated with documents

## Configuration

| Setting | Value |
|---------|-------|
| RAGFlow API | `http://remote-coder-main:9380` |
| RAGFlow UI | `http://remote-coder-main:8880` |
| RAGFlow MCP | `http://remote-coder-main:9382` |
| Auth | Bearer token (API key from RAGFlow UI) |

## API Reference

### List Knowledge Bases

```bash
curl -s -H "Authorization: Bearer <API_KEY>" \
  http://remote-coder-main:9380/api/v1/datasets | jq
```

### Direct Retrieval (No LLM)

Returns raw chunks with similarity scores. Use this when you want to feed
results into your own analysis pipeline.

```bash
curl -s -X POST http://remote-coder-main:9380/api/v1/retrieval \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the termination clauses?",
    "dataset_ids": ["<dataset_id>"],
    "top_k": 5,
    "similarity_threshold": 0.2
  }' | jq
```

### Chat Completion (With LLM)

Queries a chat assistant that combines retrieval with LLM generation.
Returns an answer with source citations.

```bash
# Step 1: Create a session
SESSION=$(curl -s -X POST \
  "http://remote-coder-main:9380/api/v1/chats/<chat_id>/sessions" \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"name": "jarvis-session"}' | jq -r '.data.id')

# Step 2: Ask a question
curl -s -X POST \
  "http://remote-coder-main:9380/api/v1/chats/<chat_id>/completions" \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json" \
  -d "{
    \"question\": \"What are Rubrik's key competitive advantages?\",
    \"session_id\": \"$SESSION\",
    \"stream\": false
  }" | jq '.data.answer'
```

## Workflow

1. **Identify the right knowledge base**: List datasets to find the relevant one
2. **Choose retrieval mode**:
   - **Direct retrieval** (`/api/v1/retrieval`): When you need raw chunks for further processing
   - **Chat completion** (`/api/v1/chats/{id}/completions`): When you need a synthesized answer with citations
3. **Parse citations**: Chat completions include `reference.chunks[]` with source document names, page numbers, and relevance scores
4. **Format for user**: Include source attribution in the response

## Knowledge Bases (Update as Created)

| Name | Dataset ID | Contents | Use Case |
|------|-----------|----------|----------|
| Contracts | TBD | Reference contracts, CUAD taxonomy, legal templates | Contract analysis |
| Competitive Intel | TBD | Earnings transcripts, analyst reports, press releases | Competitor research |
| Farm Docs | TBD | Property records, agricultural documents | Personal reference |

## Integration Points

- **ContractAnalyzer** (`http://remote-coder-main:8000`): Has its own RAGFlow integration at `/api/ragflow/*`
- **competitive-intel skill**: Can query the Competitive Intel knowledge base for historical data
- **earnings-analyzer skill**: Can search earnings transcript knowledge base
- **Telegram**: Format RAGFlow answers as Telegram messages with source citations

## Telegram Response Format

When returning RAGFlow results via Telegram, use this format:

```
[Answer text here]

Sources:
- document_name.pdf (p. 12, relevance: 0.85)
- other_doc.docx (p. 3, relevance: 0.72)
```

## Error Handling

| Condition | Action |
|-----------|--------|
| RAGFlow unreachable | Check if PowerSpec is on and Docker is running. Try `curl http://remote-coder-main:9380/api/v1/datasets` |
| 401 Unauthorized | API key is wrong or expired. Get new key from RAGFlow UI |
| No results found | Lower similarity_threshold (try 0.1), increase top_k, or rephrase query |
| Timeout | RAGFlow may be processing. Default timeout is 120s. Retry once. |
| Empty knowledge base | No documents uploaded yet. Direct user to RAGFlow UI to upload. |
