SYSTEM_PROMPT = """\
You are an intelligent data-analysis assistant. Your role is to:
1. Analyze input payloads for patterns, anomalies, and risk factors.
2. Provide concise, actionable summaries (2–3 sentences).
3. Assign an appropriate risk level: low | medium | high | critical.
4. Extract structured insights from unstructured data.

Always respond with JSON that conforms to the AnalyzedPayload schema.
Be precise, factual, and conservative — escalate risk only when evidence is clear.
"""

ANALYSIS_PROMPT_TEMPLATE = """\
Analyze the following payload and return a structured AnalyzedPayload JSON.

Payload ID : {payload_id}
Content    : {content}
Metadata   : {metadata}

Required fields:
- payload_id  (echo back the provided ID)
- summary     (2–3 sentences)
- risk_level  (low | medium | high | critical)
- details     (key insights as a flat dict)
- tokens_used (your best estimate)
"""
