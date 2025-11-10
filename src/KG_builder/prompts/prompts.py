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
        [
            {{
                "subject": {{
                    "name": "Đỗ Văn Chiến"
                }},
                "predicate": {{
                    "name": "has_birth_date"
                }},
                "object": {{
                    "name": "17-11-1980"
                }},
                "metadata": {{
                    "page": 1,
                    "confidence": 1,
                    "source": "Ngày tháng năm sinh: 17 - 11 - 1980"
                }}
            }},
            {{
                "subject": {{
                    "name": "Đỗ Văn Chiến"
                }},
                "predicate": {{
                    "name": "was_born_in"
                }},
                "object": {{
                    "name": "Hoằng Thắng, Hoằng Hóa, Thanh Hóa"
                }},
                "metadata": {{
                    "source": "Quê quán (xã/phường, huyện/quận, tỉnh/thành phố): Hoằng Thắng, Hoằng Hóa, Thanh Hóa"
                }}
            }}
        ]
    ```
"""
    
EXTRACT_TRIPLE_PERSONAL_INFO_USER_PROMPT = """
    Extract relational triples from the following text.
    Return only the JSON array of triples, no explanation.
    
    Text:
    {context}
    """


# TODO: prompt for qua trinh cong tac + paper
EXTRACT_TRIPLE_WORKING_INFO_PROMPT = """
    You are an expert knowledge graph engineer specializing in extracting structured triples from Vietnamese personal information documents.
    ## CRITICAL RULE: SUBJECT IDENTIFICATION
    
    **FIRST STEP - IDENTIFY THE MAIN SUBJECT:**
    1. According to the main subject given, this becomes the **SUBJECT for ALL triples** in this document

    ## TASK
    Extract all personal information as triples where:
    - **Subject**: ALWAYS the main person's full name (identified in step 1)
    - **Predicate**: Standardized relationship/property name
    - **Object**: The attribute value containing personal info

    ## EXTRACTION GUIDELINES

    ### 1. Triple Construction Rules
    - **One fact per triple** → Each triple represents a single, atomic fact.
    - **Subject consistency** → All triples use the same main subject.
    - **Multiple values** → Create separate triples for multiple entities (e.g., multiple universities or awards).
    - **Date handling** → Preserve date ranges in the form “From <Month-Year> to <Month-Year>”.
    - **Keep original Vietnamese text** for all proper names (schools, hospitals, institutions, awards).

    ### 2. Focus on Capturing

    Extract only meaningful and semantically rich facts in the following categories:

    #### Education
    - Degrees, programs, majors, and issuing institutions.
    - Dates of study and countries of education.
    - Internships, residencies, and research training abroad.

    #### Professional & Academic Career
    - Job titles, positions, departments, and affiliated institutions.
    - Time spans of employment or service.
    - Current position and current workplace.
    - Academic teaching or guest lecturing roles.

    #### Research
    - Research directions, topics, or fields.
    - Supervised students or trainees.
    - Research projects or scientific works completed.

    #### Publications & Academic Output
    - Number of scientific papers, books, theses, or research projects.
    - Distinguish between domestic and international publications if mentioned.

    #### Awards & Honors
    - Awards, prizes, or recognitions (with organization name and year).
    - Include both national and international awards.

    #### Academic Titles & Credentials
    - Degrees awarded (Bachelor, PhD, etc.) with issue date, specialization, and issuing institution.
    - Registration or recognition of academic ranks (e.g., Associate Professor).

    #### Organizational Relationships
    - Relationships between institutions (e.g., “Viện Tim Mạch” thuộc “Bệnh viện TƯQĐ 108”).

    ### 3. Metadata Requirements
    For every triple, include:
    - `"source"`: the exact sentence or phrase in Vietnamese that the triple was extracted from.

    ### 4. Special Handling for Vietnamese Text
    1. **Names**: Preserve Vietnamese capitalization and diacritics (e.g., “Đỗ Văn Chiến”).
    2. **Dates & Numbers**: Keep original Vietnamese numeric formats (e.g., “tháng 9/1998”, “05 đề tài”).
    3. **No translation**: Do not translate proper nouns or institution names.
    
    ## REQUIRED OUTPUT FORMAT
    * **Input data**: "Từ tháng 9/1998 đến tháng 9/1999: Học đại học tại Trường Đại Học Y Hà Nội, ngành học: Bác sĩ đa khoa, hệ chính quy."
    ```json
    {{
        [
            {{
                "subject": {{
                    "name": "Đỗ Văn Chiến"
                }},
                "predicate": {{
                    "name": "studied_at"
                }},
                "object": {{
                    "name": "Trường Đại học Y Hà Nội (ngành Bác sĩ đa khoa, hệ chính quy)"
                }},
                "metadata": {{
                    "page": "2",
                    "confidence": "1",
                    "start_date": "9/1998",
                    "end_date": "9/1999",
                    "source": "Từ tháng 9/1998 đến tháng 9/1999: Học đại học tại Trường Đại Học Y Hà Nội, ngành học: Bác sĩ đa khoa, hệ chính quy.",
                }}
            }}
        ]
    }}
    ```
"""
EXTRACT_TRIPLE_WORKING_INFO_USER_PROMPT = """
    Extract relational triples from the following text.
    Return only the JSON array of triples, no explanation.
    
    Main subject:
    {main_subject}
    
    Text:
    {context}
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

# extract triples tu table data
EXTRACT_TRIPLE_FROM_TABLE_PROMPT = """
You are an expert Data Normalization and Knowledge Graph (KG) Agent. Your task is to process the structured JSON data provided, representing an applicant's academic and scientific portfolio, and transform it into a set of well-defined Subject-Predicate-Object (SPO) Triples.


### I. DATA CONTEXT AND INPUT STRUCTURE

You will receive a JSON dictionary containing academic/research data with the following possible sections:
- papers: Published research papers
- books: Published books or book chapters
- patents: Patents and innovations
- training_programs: Educational program development activities
- projects: Research/technology projects
- achievements: Awards and recognitions

### II. CRITICAL SUBJECT IDENTIFICATION
According to the main subject given, this becomes the **Applicant** in this document

## TASK

Extract **ALL** academic/research data as triples where:
- **Subject**: Either the Applicant or paper title, project title, etc.
- **Predicate**: Standardized, meaningful, logical relationship, **derived from JSON keys**
- **Object**: The value or related entity
    
### III. TRIPLE GENERATION GUIDELINES AND SUBJECT ASSIGNMENT GUIDELINES

#### A. Subject Assignment Rules (Priority):

* **Rule 1 (Applicant Focus):** If the Predicate describes a **relationship**, **role**, or **direct contribution** of the applicant (e.g., authorship, chief editor status, participation), the Subject MUST be the **Applicant (<ABC>)**.
These include:
- Authorship relationships (is author, is main author, is co-author)
- Editorial roles (is editor-in-chief, is editor)
- Inventor status (is inventor, is main inventor)
- Project participation (is principal investigator, is member)
- Achievements (received award, achieved recognition)

* **Rule 2 (Work Focus):** If the Predicate describes an **attribute** or **metadata** of the work itself (e.g., ranking, year, code, document ID, journal name), the Subject MUST be the **Title of the Work** (Paper Title, Project Title, Book Title, etc.).
These include:
- Publication details (journal name, publisher, ISSN)
- Metadata (ranking, volume, pages, code)
- Dates (publication date, issue date, acceptance date)
- Counts (number of authors, citation count, number of contributors)
- Classifications (type, level, rating)
- Document identifiers (verification IDs, assignment documents)

#### B. Triple Construction Rules

- **Predicate** must be meaningful, logical, and based on the context of the data key and **Subject(applicant or title)**. Focus on the json keys to extract **ALL Predicates**. 
Consider the **meaning** of the JSON key, not just its name. Use clear, descriptive verbs or verb phrases. 
- **Object** must be meaningful, if object is N/A, **PASS** it. 

### IV. REQUIRED OUTPUT FORMAT
* **Input Data:** `title`: "Thẩm định chương trình đào tạo...", `applicant_role`: "Participant", `assignment_document_id`: "301/QĐ-ĐHTG", `certifying_authority`: "Trường Đại học Tiền Giang"

Return a JSON array of triples:
```json
    [
        {{
            "subject": {{
                "name": "Đỗ Văn Chiến"
            }},
            "predicate": {{
                "name": "participated_in_program"
            }},
            "object": {{
                "name": "Thẩm định chương trình đào tạo..."
            }}
        }},
        {{
            "subject": {{
                "name": "Thẩm định chương trình đào tạo..."
            }},
            "predicate": {{
                "name": "assigned_in_doc"
            }},
            "object": {{
                "name": "Quyết định số 301/QĐ-ĐHTG ngày 30/05/2017"
            }}
        }},
        {{
            "subject": {{
                "name": "Thẩm định chương trình đào tạo..."
            }},
            "predicate": {{
                "name": "certified_by"
            }},
            "object": {{
                "name": "Trường Đại học Tiền Giang"
            }}
        }},
        {{
            "subject": {{
                "name": "Đỗ Văn Chiến"
            }},
            "predicate": {{
                "name": "is_main_author_of"
            }},
            "object": {{
                "name": "Nghiên cứu ảnh hưởng..."
            }}
        }},
        {{
            "subject": {{
                "name": ""Gia cố nền đất yếu bằng trụ đất xi măng""
            }},
            "predicate": {{
                "name": "published_by"
            }},
            "object": {{
                "name": "Nhà xuất bản Khoa học và Kỹ thuật"
            }}
        }}
    ]
```
"""

EXTRACT_TRIPLE_FROM_TABLE_USER_PROMPT = """
    Extract relational triples from the following text.
    Return only the JSON array of triples, no explanation.
    
    Main subject:
    {main_subject}
    
    Text:
    {context}
"""

EXTRACT_TRIPLE_FROM_PAPER_PROMPT = """
You are an expert Data Normalization and Knowledge Graph (KG) Agent. Your task is to process the structured JSON data provided, representing an applicant's academic and scientific portfolio, and transform it into a set of well-defined Subject-Predicate-Object (SPO) Triples.


### I. DATA CONTEXT AND INPUT STRUCTURE

You will receive a JSON dictionary containing academic/research data with the following possible sections:
- papers: Published research papers

### II. CRITICAL SUBJECT IDENTIFICATION
According to the main subject given, this becomes the **Applicant** in this document

## TASK

Extract **ALL** academic/research data as triples where:
- **Subject**: Either the Applicant or paper title.
- **Predicate**: Standardized, meaningful, logical relationship, **derived from JSON keys**
- **Object**: The value or related entity
    
### III. TRIPLE GENERATION GUIDELINES AND SUBJECT ASSIGNMENT GUIDELINES

#### A. Subject Assignment Rules (Priority):

* **Rule 1 (Applicant Focus):** If the Predicate describes a **relationship**, **role**, or **direct contribution** of the applicant (e.g., authorship, the Subject MUST be the **Applicant (<ABC>)**.
These include:
- Authorship relationships (is author, is main author, is co-author)

* **Rule 2 (Work Focus):** If the Predicate describes an **attribute** or **metadata** of the work itself (e.g., ranking, journal name), the Subject MUST be the **Title of the Work** (Paper Title).
These include:
- Publication details (journal name, ISSN)
- Metadata (ranking, volume, pages, code)
- Dates (publication date, issue date, acceptance date)
- Counts (number of authors, citation count, number of contributors)

#### B. Triple Construction Rules

- **Predicate** must be meaningful, logical, and **based** on the context of the data key and **Subject(applicant or title)**. Focus on the json keys to extract **ALL Predicates**. 
Consider the **meaning** of the JSON key, not just its name. Ask what meaning it really is. Use clear, descriptive verbs or verb phrases.
- **Object** must be meaningful, if object is N/A, **PASS** it. 

### IV. REQUIRED OUTPUT FORMAT
* **Input Data:** 
      "title": "Nghiên cứu ảnh hưởng của hàm lượng Montmorillonite đến tính chất cơ học của đất trộn xi măng",
      "num_authors": 4,
      "is_main_author": true,
      "journal_name_ISSN": "Tạp chí địa kỹ thuật-Viện địa kỹ thuật ISSN 0868-279X",
      "journal_ranking": "N/A",
      "citation_count": 0,
      "volume_issue_pages": "Tập 15, số 4, trang 11-19",
      "published_date": "4/2011"

Return a JSON array of triples:
```json
    [
        {{
            "subject": {{
                "name": "Đỗ Văn Chiến"
            }},
            "predicate": {{
                "name": "is_main_author_of"
            }},
            "object": {{
                "name": "Nghiên cứu ảnh hưởng của hàm lượng Montmorillonite đến tính chất cơ học của đất trộn xi măng"
            }}
        }},
        {{
            "subject": {{
                "name": "Nghiên cứu ảnh hưởng của hàm lượng Montmorillonite đến tính chất cơ học của đất trộn xi măng"
            }},
            "predicate": {{
                "name": "published_in_journal"
            }},
            "object": {{
                "name": "Tạp chí địa kỹ thuật-Viện địa kỹ thuật ISSN 0868-279X"
            }}
        }},
        {{
            "subject": {{
                "name": "Nghiên cứu ảnh hưởng của hàm lượng Montmorillonite đến tính chất cơ học của đất trộn xi măng"
            }},
            "predicate": {{
                "name": "has_total_citation"
            }},
            "object": {{
                "name": "0"
            }}
        }}
    ]
```
"""
EXTRACT_TRIPLE_FROM_PAPER_USER_PROMPT = """
    Extract relational triples from the following text.
    Return only the JSON array of triples, no explanation.
    
    Main subject:
    {main_subject}
    
    Text:
    {context}
"""