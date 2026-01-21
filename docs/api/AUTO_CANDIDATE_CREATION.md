# Automatic Candidate Creation from CV

## Overview

The CV upload API now supports automatic candidate creation. When uploading a CV, you can set `auto_create_candidate=true` to automatically extract candidate information from the CV file and create a new candidate record.

## API Endpoint

```
POST /api/cv/upload/
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File | Yes | The CV file to upload (PDF, DOCX, etc.) |
| `candidate_id` | UUID | No | Existing candidate ID (if known) |
| `candidate_email` | String | No | Existing candidate email (if known) |
| `auto_create_candidate` | Boolean | No | If `true`, automatically creates candidate from CV data. Default: `false` |
| `timeout_seconds` | Integer | No | Text extraction timeout. Default: `30` |
| `save_to_file` | Boolean | No | Save extracted text to file. Default: `true` |

## Usage Examples

### Option 1: Auto-create candidate (NEW!)

Upload a CV and let the system automatically create the candidate:

```bash
curl -X POST http://localhost:8000/api/cv/upload/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@john_doe_cv.pdf" \
  -F "auto_create_candidate=true"
```

**How it works:**
1. Extracts text from the CV
2. Uses entity extraction to find email, phone, and name
3. Creates a new candidate with extracted information
4. If a candidate with the same email exists, uses that instead

### Option 2: Upload for existing candidate (ID)

```bash
curl -X POST http://localhost:8000/api/cv/upload/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@cv.pdf" \
  -F "candidate_id=123e4567-e89b-12d3-a456-426614174000"
```

### Option 3: Upload for existing candidate (Email)

```bash
curl -X POST http://localhost:8000/api/cv/upload/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@cv.pdf" \
  -F "candidate_email=john@example.com"
```

### Option 4: Fallback to auto-create if not found

If you specify a candidate email but it doesn't exist, you can still auto-create:

```bash
curl -X POST http://localhost:8000/api/cv/upload/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@cv.pdf" \
  -F "candidate_email=newcandidate@example.com" \
  -F "auto_create_candidate=true"
```

## Response

Successful response includes:

```json
{
  "id": "uuid",
  "candidate_created": true,
  "candidate_id": "candidate-uuid",
  "candidate_name": "John Doe",
  "original_filename": "john_doe_cv.pdf",
  "storage_path": "org-id/candidate-id/john_doe_cv.pdf",
  "success": true,
  "extracted_text": "...",
  "entities": {
    "email": ["john@example.com"],
    "phone": ["+1234567890"],
    "programming_languages": ["Python", "Java"],
    ...
  }
}
```

## Field Extraction

The system attempts to extract the following from the CV:

- **Email** (required): First email found in the CV
- **Phone** (optional): First phone number found
- **Name** (heuristic): Attempts to extract from first few lines of CV
  - First name: First word of detected name
  - Last name: Remaining words

### Name Extraction Heuristic

The system looks for a name in the first 5 lines of the CV text:
- Skips empty lines
- Looks for lines with 2-4 words
- Excludes lines with special characters (@, http, +)
- Takes first word as first name, rest as last name

**Note**: Name extraction is basic. For better results, consider:
1. Improving the CV format (name on first line)
2. Using structured CV templates
3. Manually specifying candidate if name extraction fails

## Error Handling

If extraction fails:

```json
{
  "error": "Failed to extract candidate info: No email found in CV"
}
```

Common errors:
- `No email found in CV`: CV must contain at least one email address
- `Failed to extract text from CV`: File might be corrupted or unsupported format
- `No candidate specified`: Must provide candidate_id, candidate_email, or auto_create_candidate=true

## Best Practices

1. **Use auto-create for bulk imports**: Great for importing many CVs at once
2. **Email is key**: Ensure CVs contain email addresses
3. **Check candidate_created flag**: Know when new candidates are created
4. **Validate extracted data**: Review candidate information after creation
5. **Handle duplicates**: System uses email to detect existing candidates

## Frontend Integration

Example JavaScript/TypeScript:

```typescript
const uploadCV = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('auto_create_candidate', 'true');
  
  const response = await fetch('/api/cv/upload/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });
  
  const data = await response.json();
  
  if (data.candidate_created) {
    console.log(`New candidate created: ${data.candidate_name}`);
  } else {
    console.log(`CV uploaded for existing candidate: ${data.candidate_name}`);
  }
  
  return data;
};
```

## Migration Path

For existing workflows:

1. **No changes required**: Old behavior still works (requires candidate_id or candidate_email)
2. **Gradual adoption**: Add auto_create_candidate=true to new uploads
3. **Bulk import**: Use auto_create for importing historical CVs

## Limitations

1. **Name extraction is basic**: May not work well for non-standard CV formats
2. **Single language**: Currently optimized for standard CV formats
3. **Email required**: CVs without emails will fail
4. **No validation**: Extracted data is not validated (e.g., email format)

## Future Improvements

- [ ] Better name extraction using NER (Named Entity Recognition)
- [ ] Support for multiple CVs per candidate in one request
- [ ] Validation of extracted email addresses
- [ ] Location extraction from CV
- [ ] LinkedIn profile extraction
- [ ] Multi-language name extraction
