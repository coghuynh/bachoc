from pydantic import BaseModel, Field
import os
import pathlib
import json
from google.genai import types
from KG_builder.prompts.prompts import (
    EXTRACT_TABLE_PAPER_INFO,
    EXTRACT_TRIPLE_FROM_TABLE_PROMPT,
    EXTRACT_TRIPLE_FROM_TABLE_USER_PROMPT,
    EXTRACT_TRIPLE_FROM_PAPER_PROMPT,
    EXTRACT_TRIPLE_FROM_PAPER_USER_PROMPT
)
from KG_builder.llm.cost.cost_model import GeminiModel
from KG_builder.utils.llm_utils import load_model
from KG_builder.extract.extract_triples import extract_triples
from KG_builder.triple_models import TripleList

class Paper(BaseModel):
    """Represents a row in Paper/Article table"""
    title: str = Field(
        ...,
        description="The full title of the scientific paper, report, or conference proceeding."
    )
    num_authors: int = Field(
        ..., 
        description="The total number of authors associated with the publication. Must be an integer."
    )
    is_main_author: bool = Field(
        ...,
        description="A boolean indicating whether the applicant is the main author (e.g., first or corresponding author). True for Yes, False for No."
    )
    journal_name_ISSN: str = Field(
        ..., 
        description="The name of the scientific journal or proceeding where the paper was published, including its ISSN or ISBN."
    )
    journal_ranking: str = Field(
        ..., 
        description="The international prestige index of the journal, such as 'ISI Q1', 'Scopus Q2', 'ISI-ranked', or similar categorization."
    )
    citation_count: int = Field(
        ..., 
        description="The total number of times the article has been cited, excluding self-citations. Must be an integer."
    )
    volume_issue_pages: str = Field(
        ..., 
        description="The full publication reference details, including Volume (Tập), Issue (Số), and Page range (Trang)."
    )
    published_date: str = Field(
        ..., 
        description="The month and year when the paper was officially published (e.g., 'May, 2022' or '05/2022')."
    )
    
    
class Project(BaseModel):
    title: str = Field(
        ...,
        description="The full name of the scientific or technological task (e.g., Program, Project)."
    )
    role: str = Field(
        ...,
        description="The applicant's role in the project (e.g., CN for Principal Investigator, PCN for Co-Investigator, TVC for Key Member, TK for Assistant)."
    )
    project_code: str = Field(
        ...,
        description="The official code of the project."
    )
    management_level: str = Field(
        ...,
        description="The management level of the project by organization(e.g., Trường Đại học Tiền Giang)"
    )
    period: str = Field(
        ...,
        description="The full duration of the project's execution (e.g., 2020-2022 or Start Date - End Date)."
    )
    acceptance_date: str = Field(
        ...,
        description="The date of final acceptance."
    )
    rating: str = Field(
        ...,
        description="The rating/classification result of the project"
    )


class Book(BaseModel):
    title: str = Field(
        ...,
        description="The full name of the published book"
    )
    type: str = Field(
        ...,
        description="The classification of the book (e.g., CK: Monograph, GT: Textbook, TK: Reference, HD: Guide)."
    )
    publisher: str = Field(
        ...,
        description="The name of the publisher"
    )
    publish_year: str = Field(
        ...,
        description="The year the book was published"
    )
    num_authors: int = Field(
        ...,
        description="The total number of authors/contributors listed for the book."
    )
    is_editor_in_chief: bool = Field(
        ...,
        description="A boolean indicating if the applicant served as the editor-in-chief (Chủ biên). True for Yes, False for No"
    )
    compiled_pages: str = Field(
        ...,
        description="The specific section or page range contributed/compiled by the applicant (e.g., 'p. 10 to p. 50')."
    )
    verification_document_id: str = Field(
        ...,
        description="The ID or reference number of the official document from the Higher Education Institution verifying the use of the book."
    )
    
    
class Patent(BaseModel):
    title: str = Field(
        ...,
        description="The full title of the patent or utility solution certificate."
    )
    issuing_authority: str = Field(
        ...,
        description="The name of the organization or agency that issued the certificate (e.g., NOIP)."
    )
    issue_date: str = Field(
        ...,
        description="The exact date (day, month, year) the patent/certificate was granted."
    )
    is_main_inventor: bool = Field(
        ...,
        description="A boolean indicating whether the applicant is the main inventor (Tác giả chính). True for Yes, False for No."
    )
    num_inventors: int = Field(
        ...,
        description="The total number of inventors/authors listed on the certificate."
    )
    

class Achievement(BaseModel):
    """Represents a row detailing an artistic work or sports achievement."""
    title: str = Field(
        ...,
        description="The title of the artwork, training achievement, or sports competition result."
    )
    certifying_organization: str = Field(
        ...,
        description="The name of the agency or organization that officially recognized the achievement/work."
    )
    certificate_document_id: str = Field(
        ...,
        description="The number and date (day, month, year) of the official recognition document."
    )
    award: str = Field(
        ...,
        description="The national prize or international prize received"
    )
    num_contributors: int = Field(
        ...,
        description="The total number of authors/contributors/team members associated with the work or achievement."
    )
    
    
class TrainingResearchProgram(BaseModel):
    """Represents a row detailing a training program or applied S&T research program."""
    title: str = Field(
        ...,
        description="The full title of the training program or the applied S&T research program."
    )
    applicant_role: str = Field(
        ...,
        description="The applicant's role in the program (e.g., 'Chủ trì' for Lead/Coordinator, 'Tham gia' for Participant/Member)."
    )
    assignment_document_id: str = Field(
        ...,
        description="The number and date (day, month, year) of the official document assigning the task/program."
    )
    certifying_authority: str = Field(
        ...,
        description="The name of the agency/authority that evaluated and authorized the program for use."
    )
    implementation_document_id: str = Field(
        ...,
        description="The number and date of the official document confirming the practical application of the program."
    )
    notes: str = Field(
        ...,
        description="Any additional comments or notes related to the program."
    )
    
class AllTablesSchema(BaseModel):
    papers: list[Paper] | None = None
    projects: list[Project] | None = None
    books: list[Book] | None = None
    patents: list[Patent] | None = None
    achievements: list[Achievement] | None = None
    training_programs: list[TrainingResearchProgram] | None = None
    

def extract_table_from_pdf(pdf_path: str, genai: GeminiModel):
    """Extract tables from pdf and return JSON based on schema"""
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found: {pdf_path}")
        return
    
    print(f"Uploading PDF file '{os.path.basename(pdf_path)}' on Gemini File API")
    filepath = pathlib.Path(pdf_path)
    response_format = {
        "type": "json_object",
        "response_mime_type": "application/json",
        "response_schema": AllTablesSchema
    }
    
    contents = [types.Part.from_bytes(data=filepath.read_bytes(), mime_type="application/pdf"), EXTRACT_TABLE_PAPER_INFO.format()]
    
    return genai.generate_response(
        contents,
        response_format=response_format
    )
    
# table_data = extract_table_from_pdf("D:/fico/DỰ_ÁN/pdf_data/(16842975053804_29_06_2024_09_24)nguyen-ngoc-thang-1979-08-13-1719627885.pdf", llm)
# parsed = json.loads(table_data)  # chuyển sang dict
# with open('table_data_1.json', 'w', encoding='utf-8') as f:
#     json.dump(parsed, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    llm = load_model("gemini-2.0-flash")
    response_format = {
        "type": "json_object",
        "response_mime_type": "application/json",
        "response_schema": TripleList
    }
    
    folder_path = "D:/fico/DỰ_ÁN/test_table_data"

    for idx, filename in enumerate(os.listdir(folder_path)):
        if "paper" in filename:
            filepath = os.path.join(folder_path, filename)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                extracted_data = json.load(f)
                json_string = json.dumps(extracted_data, indent=2, ensure_ascii=False)
                
                messages = {
                    "system_instruction": EXTRACT_TRIPLE_FROM_PAPER_PROMPT.format(),
                    "context": EXTRACT_TRIPLE_FROM_PAPER_USER_PROMPT.format(
                        main_subject="TRAN HONG DANG",
                        context=json_string
                    )
                }
                response = extract_triples(messages, llm, response_format=response_format)
                
                with open(f"test_triple_data_{idx}.json", 'w', encoding='utf-8') as f:
                    json.dump(response, f, ensure_ascii=False, indent=4)