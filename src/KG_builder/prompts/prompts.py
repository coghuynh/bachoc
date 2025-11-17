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

EXTRACT_TRIPLE_PERSONAL_INFO_PROMPT = """
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
    - **Predicate**: Choose EXACTLY ONE from the predefined list of relations provided. Do not create new relation.
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
    3. **Preserve**: Preserve all predicates, objects in Vietnamese.
    
    ## REQUIRED OUTPUT FORMAT
    ```json
        "main_subject": "Đỗ Văn Chiến",
        "triples": 
        [
            {{
                "subject": "Đỗ Văn Chiến",
                "predicate": "sinh ngày",
                "object": "17-11-1980",
                "metadata": {{
                    "source": "Ngày tháng năm sinh: 17 - 11 - 1980"
                }}
            }},
            {{
                "subject": "Đỗ Văn Chiến",
                "predicate": "quê quán",
                "object": "Hoằng Thắng, Hoằng Hóa, Thanh Hóa",
                "metadata": {{
                    "source": "Quê quán (xã/phường, huyện/quận, tỉnh/thành phố): Hoằng Thắng, Hoằng Hóa, Thanh Hóa"
                }}
            }}
        ]
    ```
"""
    
EXTRACT_TRIPLE_USER_PROMPT = """
    Extract relational triples from the following text.
    Return only the JSON array of triples, no explanation.
    
    Main subject:
    {main_subject}
    
    List predicates:
    {predicates}
    Text:
    {text}
    """


# TODO: prompt for qua trinh cong tac + paper
EXTRACT_TRIPLE_WORKING_INFO_PROMPT = """
    You are an expert knowledge graph engineer specializing in extracting structured triples from Vietnamese personal information documents.
    ## CRITICAL RULE: SUBJECT IDENTIFICATION
    
    **FIRST STEP - IDENTIFY THE MAIN SUBJECT:**
        1. According to the main subject given, this becomes the **DEFAULT SUBJECT** for triples where the subject is not explicitly named in the source text.
        2. The Subject should be **flexibly chosen** to make the triple semantically meaningful. The Main Subject's full name is preferred only when the fact clearly relates to their personal attributes (e.g., career, education, demographics) **OR when the fact describes a high-level personal achievement (e.g., received degree, was appointed)**.

    ## TASK
    Extract all personal information as triples where:
    - **Subject**: 
      - Should be the **most appropriate entity** based on the context of the sentence (e.g., an institution, a degree, or the Main Subject).
      - Use the Main Subject's full name only when the predicate describes a personal relationship (e.g., "công tác tại," "được cấp") or when the subject is not mentioned.
    - **Predicate**: 
      - Prefer predicates from the predefined list when applicable
      - Use meaningful Vietnamese predicates for other relationships, **Must** base on the word from the text.
    - **Object**: The attribute value or related entity

    ## EXTRACTION GUIDELINES

    ### 1. Triple Construction Rules
    - **One fact per triple** → Each triple represents a single, atomic fact.
    - **Multiple values** → Create separate triples for multiple entities (e.g., multiple universities or awards).
    - **Date handling** → Preserve date ranges in the form “From <Month-Year> to <Month-Year>”.
    - **Keep original Vietnamese text** for all proper names (schools, hospitals, institutions, awards).
    - **Avoid Trivial Classification**: Do not extract triples where the predicate is simply a general classifier like "là" (is/is a) and the object is a category already implied by the subject's name (e.g., "Trường Đại học X" is "cơ sở giáo dục đại học"). Focus on relational facts.
    - **Quantity Handling**: When the Object is a countable number, the Object MUST include the unit of count or the type of item (e.g., "05 luận văn ThS", "02 đề tài cấp cơ sở", "55 bài báo khoa học")

    ### 2. Focus on Capturing

    Extract only meaningful and semantically rich facts in the following categories:

    #### Education
    - Degrees, programs, majors, and issuing institutions.
    - Dates of study and countries of education.
    - Internships, residencies, and research training abroad.

    #### Professional & Academic Career
    - Job titles, positions, departments, and affiliated institutions.
    - Current position and current workplace.

    #### Research
    - Research directions, topics, or fields.
    - **Supervision & Mentoring:** Triples related to advising students or trainees.
        - **CRITICAL RULE for Supervision:** The **Object** must include **both the quantity and the type/level of the thesis/trainee** (e.g., "05 luận văn ThS (của HVCH)", "01 luận văn BSCK cấp 2 (của học viên chuyên khoa 2)").
        - Predicate for supervision must be specific (e.g., "đã hướng dẫn bảo vệ thành công luận văn").
    - Research projects or scientific works completed.

    #### Publications & Academic Output
    - Number of scientific papers, books, theses, or research projects.
    - Distinguish between domestic and international publications if mentioned.

    #### Awards & Honors
    - Awards, prizes, or recognitions (with organization name and year).
    - Include both national and international awards.

    #### Academic Titles & Credentials
    - Degrees awarded (Bachelor, PhD, etc.).
    - Registration or recognition of academic ranks (e.g., Associate Professor).
    - Degrees and Registration or recognition of academic ranks with issue date, specialization(chuyên ngành), and issuing institution, certificate number(số hiệu bằng), major(ngành).
    These triples **must** use the exact word, phrase in the text as predicates. (e.g., "số hiệu bằng" -> "có số hiệu") 

    #### Organizational Relationships
    - Relationships between institutions (e.g., “Viện Tim Mạch” thuộc “Bệnh viện TƯQĐ 108”).
    - Relationships between institutions and locations. (e.g., "Trường Đại học Y Sydney, Úc -> "Trường Đại học Y Sydney" ở "Úc"). **For location details, prefer "tọa lạc ở" (located in) for city/country and "có địa chỉ" (has address) for specific street address.**
    - Consider the meaning of institutions, organizations to construct relationships. (e.g., "Viện NCKH y dược lâm sàng 108" does not belong to any universities)

    ### 3. Metadata Requirements
    For every triple, include:
    - `"source"`: the exact sentence or phrase in Vietnamese that the triple was extracted from.

    ### 4. Special Handling for Vietnamese Text
    1. **Names**: Preserve Vietnamese capitalization and diacritics (e.g., “Đỗ Văn Chiến”).
    2. **Dates & Numbers**: Keep original Vietnamese numeric formats (e.g., “tháng 9/1998”, “05 đề tài”).
    3. **No translation**: Do not translate proper nouns or institution names.
    
    ## REQUIRED OUTPUT FORMAT
    * **Input data**: "Từ tháng 9/2006 đến tháng 5/2008: Bác sĩ khoa Nội Tim mạch, Viện Tim Mạch, Bệnh Viện TƯQĐ 108. Được cấp bằng Tiến Sĩ ngày 1 tháng 11 năm 2018; số hiệu bằng: 000003; ngành: Y học;
chuyên ngành: Nội Tim Mạch; Nơi cấp bằng TS (trường, nước): Viện nghiên cứu khoa học y dược lâm sàng 108."
    ```json
    {{
        [
            {{
                "subject": "Đỗ Văn Chiến",
                "predicate": "công tác vị trí",
                "object": "Bác sĩ",
                "metadata": {{
                    "source": "Từ tháng 9/2006 đến tháng 5/2008: Bác sĩ khoa Nội Tim mạch, Viện Tim Mạch, Bệnh Viện TƯQĐ 108."
                }}
            }},
            {{
                "subject": "Đỗ Văn Chiến",
                "predicate": "công tác tại",
                "object": "khoa Nội Tim mạch",
                "metadata": {{
                    "source": "Từ tháng 9/2006 đến tháng 5/2008: Bác sĩ khoa Nội Tim mạch, Viện Tim Mạch, Bệnh Viện TƯQĐ 108."
                }}
            }},
            {{
                "subject": "khoa Nội Tim mạch",
                "predicate": "thuộc",
                "object": "Viện Tim Mạch",
                "metadata": {{
                    "source": "Từ tháng 9/2006 đến tháng 5/2008: Bác sĩ khoa Nội Tim mạch, Viện Tim Mạch, Bệnh Viện TƯQĐ 108."
                }}
            }},
            {{
                "subject": "Viện Tim Mạch",
                "predicate": "thuộc",
                "object": "Bệnh Viện TƯQĐ 108",
                "metadata": {{
                    "source": "Từ tháng 9/2006 đến tháng 5/2008: Bác sĩ khoa Nội Tim mạch, Viện Tim Mạch, Bệnh Viện TƯQĐ 108.",
                }}
            }},
            {{
                "subject": "Đỗ Văn Chiến",
                "predicate": "được cấp",
                "object": "bằng Tiến sĩ",
                "metadata": {{
                    "source": "Được cấp bằng Tiến Sĩ ngày 1 tháng 11 năm 2018.",
                }}
            }},
            {{
                "subject": "bằng Tiến sĩ",
                "predicate": "có số hiệu",
                "object": "000003",
                "metadata": {{
                    "source": "Được cấp bằng Tiến Sĩ ngày 1 tháng 11 năm 2018; số hiệu bằng: 000003.",
                }}
            }},
            {{
                "subject": "bằng Tiến sĩ",
                "predicate": "ngành",
                "object": "Y",
                "metadata": {{
                    "source": "Được cấp bằng Tiến Sĩ ngày 1 tháng 11 năm 2018; số hiệu bằng: 000003; ngành: Y học.",
                }}
            }},
        ]
    }}
    ```
"""

# TODO: them prompt cho extract table tu pdf.
EXTRACT_TABLE_PAPER_INFO = """
    You are an expert data extraction and normalization agent specialized in academic and scientific records. Your task is to process the uploaded PDF document, identify all tables corresponding to the provided Pydantic Schemas (Paper, Project, Book, Patent, Achievement, TrainingResearchProgram), and extract all available data.

    You MUST STRICTLY adhere to the JSON Schema provided in the configuration for the final output.

    CRITICAL INSTRUCTIONS FOR DATA TRANSFORMATION:

    1.  **Boolean Conversion:** For any fields designated as boolean (`is_main_author`, `is_editor_in_chief`, etc.), interpret the presence of the character **'X'** (or similar checkmark) in the source column as **`True`**, and the absence of any indicator (blank cell) as **`False`**.

    2.  **Field Separation & Normalization:** Source data columns must be accurately separated into the corresponding distinct fields in the Pydantic Schemas:
        * **Project Table (Code & Level):** The source content (e.g., "Mã số: 166/HĐ-ĐHTG \n Cấp quản lý: Trường Đại học Tiền Giang") must be split into **`project_code`** ("166/HĐ-ĐHTG") and **`management_level`** ("Trường Đại học Tiền Giang").
        * **Project Table (Date & Rating):** Separate the source content into **`acceptance_date`** and **`rating`**.
        * **Book Table (Publisher & Year):** Separate the source content into **`publisher`** and **`publish_year`**.

    3.  **Decode Vietnamese Abbreviations to English:** You must translate and use the full English phrase for the following Vietnamese abbreviations for the **`role`** and **`type`** fields:

        * **Project Roles:**
            * CN: **Principal Investigator**
            * PCN: **Co-Investigator**
            * TK: **Assistant**
            * TVC: **Key Member**
        * **Book Types:**
            * CK: **Monograph**
            * GT: **Textbook**
            * TK: **Reference Book**
            * HD: **Guide Book**

    4.  **Completeness & Strict Typing:** Extract every discernible row and ensure all values strictly conform to the expected Pydantic data types (e.g., integers for counts, strings for names).

    5. Ensure you specifically locate and extract the data contained in the section titled/subtitled "Bằng độc quyền sáng chế, giải pháp hữu ích" and map it to the Patent schema.
    6. **Ensure Book Extraction:** You must specifically locate and extract the data contained in the section related to "Biên soạn sách phục vụ đào tạo từ trình độ đại học trở lên"
    Begin the extraction process now.
"""