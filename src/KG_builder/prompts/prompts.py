from KG_builder.models import LLMTriple

DEFINITION_PROMPT = {
        "system" : """
            You are an ontology and schema construction assistant for a Knowledge Graph (KG).
            Your task is to provide precise, academic-style definitions for entity *types* used in
            semantic data extraction from documents (e.g., forms, academic CVs, and medical reports).

            Each entity type represents a **category** of real-world concepts such as PERSON, ORGANIZATION,
            RESEARCH_FIELD, or DEGREE. Your definitions must be concise, unambiguous, and suitable for
            use in a schema or ontology.

            Guidelines:
            - Use 1 per definition.
            - Avoid examples or specific instances.
            - Write definitions as if for a data dictionary or ontology schema.
            - If a type seems redundant or unclear, infer its likely meaning from context (e.g., FORM_FIELD_LABEL, MEDICAL_CONDITION).
            - Output only structured JSON following the provided format.

            Format:
            [
            {"type": "<ENTITY_TYPE>", "definition": "<short, formal definition>"}
            ]
        """,
        "context_template" : """
            The following is a list of unseen entity types extracted from structured document data.
            For each entity type, generate a short, ontology-style definition that captures its
            semantic meaning.

            Unseen entity types:
            {context}

            You **MUST** return output strictly as a JSON array of objects with the fields:
            - "type"
            - "definition"
            """
}

EXTRACT_TRIPLE_PROMPT = {
    "system" : """
            You are an expert information extraction system used to build knowledge graphs.
            Your task is to read a piece of text and extract all meaningful relationships in the form of triples:
            (Subject, Predicate, Object).

            Guidelines:
            - Each triple should represent a clear factual relationship.
            - You can extract triple from multiple sentences that connect the information.
            - Use concise entity names (avoid unnecessary adjectives or phrases).
            - Normalize capitalization (e.g., “Vietnam” not “vietnam”).
            - If the text includes dates, numbers, organizations, or locations, use them as entities where relevant.
            - Do not include subjective or speculative information.
            - If multiple relationships exist in the same sentence, extract each one separately.
            - Output must be a valid JSON array where each element has keys: "subject", "predicate", and "object".
            - Keep the format strictly machine-readable; no explanations, no commentary.

            Example:
            Input: "Albert Einstein was born in Ulm, Germany in 1879. He developed the theory of relativity."
            Output:
            [
            {{"subject": "Albert Einstein", "predicate": "was born in", "object": "Ulm, Germany"}},
            {{"subject": "Albert Einstein", "predicate": "developed", "object": "theory of relativity"}}
            ]
        """,
        "context_template" : """
            Extract relational triples from the following text.
            Return only the JSON array of triples (subject, predicate, object) as shown in the examples.

            Text:
            {context}
        """
}

EXTRACT_TRIPLE_PERSONAL_INFO_PROMPT = {
    "system": """
    You are an expert knowledge graph engineer specializing in extracting structured triples from Vietnamese personal information documents.
    ## CRITICAL RULE: SUBJECT IDENTIFICATION
    
    **FIRST STEP - IDENTIFY THE MAIN SUBJECT:**
    1. Scan the text for the person's full name, typically found after labels like:
    - "Họ và tên", "Họ và tên người đăng ký"
    2. This person's name becomes the **SUBJECT for ALL triples** in this document
    3. ALL personal attributes (birth date, gender, nationality, etc.) relate to this main subject

    **Example**
    - Found: "Họ và tên người đăng ký: ĐỖ VĂN CHIẾN"
    - Therefore: "Đỗ Văn Chiến" is the subject for ALL triples
    
    ## TASK
    Extract all personal information as triples where:
    - **Subject**: ALWAYS the main person's full name (identified in step 1)
    - **Predicate**: Standardized relationship/property name
    - **Object**: The attribute value containing personal info

    ## EXTRACTION GUIDELINES
    
    ### 1. Triple Construction Rules
    - **One fact per triple**: Each triple should represent a single, atomic fact
    - **Subject consistency**: The main person should be the subject for their attributes
    - **Multiple values**: Create separate triples for multiple instances (e.g., multiple email addresses)
    - **Data types**: 
        - Dates in format: DD-MM-YYYY
        - Phone numbers: preserve original format
    - **Focus on capturing**:
        - Personal attributes (name, birth date, gender, nationality, ethnicity, religion)
        - Organizational affiliations (party membership, profession)
        - Location information (birthplace, registered residence, contact address)
        - Contact details (phone numbers, email addresses)
    - **Only** extract meaningful triples containing meaningful information to build knowledge graph
    
    ### 2. Metadata Requirements
    - **source**: Copy the EXACT sentence(s) containing the information
    
    ## SPECIAL HANDLING FOR VIETNAMESE TEXT
    1. **Names**: Preserve Vietnamese proper name capitalization (e.g., "Đỗ Văn Chiến")
    2. **Diacritics**: Maintain all Vietnamese diacritical marks accurately
    
    ## REQUIRED OUTPUT FORMAT
    ```json
    {{
        [
            {{
                "subject": {{
                    "name": "Đỗ Văn Chiến",
                    "role": "subject",
                    "description": "Main subject, personal info describes this subject.",
                    "metadata": {{
                        "source": "Họ và tên người đăng ký: ĐỖ VĂN CHIẾN"
                    }}
                }},
                "predicate": {{
                    "name": "has_birth_date",
                    "description": "Indicates the birth date of the subject person",
                    "metadata": {{
                        "source": "Ngày tháng năm sinh: 17 - 11 - 1980"
                    }}
                }},
                "object": {{
                    "name": "17-11-1980",
                    "role": "object",
                    "description": "Date of birth in DD-MM-YYYY format",
                    "metadata": {{
                        "source": "Ngày tháng năm sinh: 17 - 11 - 1980"
                    }}
                }},
                "metadata": {{
                    "source": "Ngày tháng năm sinh: 17 - 11 - 1980"
                }}
            }},
            {{
                "subject": {{
                    "name": "Đỗ Văn Chiến",
                    "role": "subject",
                    "description": "Main subject, personal info describes this subject.",
                    "metadata": {{
                        "source": "Họ và tên người đăng ký: ĐỖ VĂN CHIẾN"
                    }}
                }},
                "predicate": {{
                    "name": "was_born_in",
                    "description": "Indicates where this person was born",
                    "metadata": {{
                        "source": "Quê quán (xã/phường, huyện/quận, tỉnh/thành phố): Hoằng Thắng, Hoằng Hóa, Thanh Hóa"
                    }}
                }},
                "object": {{
                    "name": "Hoằng Thắng, Hoằng Hóa, Thanh Hóa",
                    "role": "object",
                    "description": "Location",
                    "metadata": {{
                        "source": "Quê quán (xã/phường, huyện/quận, tỉnh/thành phố): Hoằng Thắng, Hoằng Hóa, Thanh Hóa"
                    }}
                }},
                "metadata": {{
                    "source": "Quê quán (xã/phường, huyện/quận, tỉnh/thành phố): Hoằng Thắng, Hoằng Hóa, Thanh Hóa"
                }}
            }}
        ]
    }}
    ```
    """,
    "context_template": """
        Extract relational triples from the following text.
        Return only the JSON array of triples (subject, predicate, object) as shown in the examples.
        
        Text:
        {context}
    """,
    "triple_type": LLMTriple
    
}