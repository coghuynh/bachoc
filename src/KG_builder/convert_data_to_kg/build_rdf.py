from rdflib import Graph, Namespace, XSD, Literal, URIRef, RDF, FOAF, DC
import json, re

BASE_URI = Namespace("http://duncan.org/academy/")
BASE_SCHEMA = Namespace("http://duncan.org/schema/academic#")

def create_uri(entity_type: str, identifier: str) -> URIRef:
    return URIRef(f"{BASE_URI}{entity_type}/{identifier}")

def add_person(g: Graph, person_data: dict[str, any]) -> URIRef:
    """Add person information to graph"""
    person_id = person_data.get("id") or person_data.get("name").replace(" ", "_")
    person_uri = create_uri("person", person_id)
    
    g.add((person_uri, RDF.type, FOAF.Person))
    g.add((person_uri, FOAF.name, Literal(person_data["name"])))
    
    if person_data.get("gender"):
        g.add((person_uri, FOAF.gender, Literal(person_data["gender"])))
    
    if person_data.get("date_of_birth"):
        g.add((person_uri, BASE_SCHEMA.dateOfBirth, Literal(person_data["date_of_birth"], datatype=XSD.date)))
    
    if person_data.get("nationality"):
        g.add((person_uri, BASE_SCHEMA.nationality, Literal(person_data["nationality"])))
    
    if person_data.get("ethnicity"):
        g.add((person_uri, BASE_SCHEMA.ethnicity, Literal(person_data["ethnicity"])))
    
    if person_data.get("religion"):
        g.add((person_uri, BASE_SCHEMA.religion, Literal(person_data["religion"])))
        
    if person_data.get("is_party_member"):
        g.add((person_uri, BASE_SCHEMA.is_party_member, Literal(person_data["is_party_member"], datatype=XSD.boolean)))
    
    if person_data.get("citizenship_id"):
        g.add((person_uri, BASE_SCHEMA.citizenship_id, Literal(person_data["citizenship_id"])))    
    
    # Aliases
    for alias in person_data.get('aliases', []):
        g.add((person_uri, BASE_SCHEMA.alias, Literal(alias)))
        
    return person_uri


def add_contacts(g: Graph, person_uri: URIRef, contacts: dict[str, any]):
    """Add contacts information"""
    if not contacts:
        return
    
    for key, value in contacts.items():
        if value:
            if key == "email":
                g.add((person_uri, FOAF.mbox, URIRef(f"mailto:{value}")))
            elif key == "phone_mobile":
                g.add((person_uri, FOAF.phone, Literal(value)))
            elif key == "permanent_address":
                g.add((person_uri, BASE_SCHEMA.permanent_address, Literal(value)))
            elif key == "hometown":
                g.add((person_uri, BASE_SCHEMA.hometown, Literal(value)))
            elif key == "mailing_address":
                g.add((person_uri, BASE_SCHEMA.mailing_address, Literal(value)))
            elif key == "work_address":
                g.add((person_uri, BASE_SCHEMA.word_address, Literal(value)))
            elif key == "phone_home":
                g.add((person_uri, BASE_SCHEMA.phone_home, Literal(value)))
    

def add_current_affiliation(g: Graph, person_uri: URIRef, affiliation: dict[str, any]):
    """Add current affiliation"""
    if not affiliation:
        return
    
    aff_uri = URIRef(f"{person_uri}/current_affiliation")
    g.add((aff_uri, RDF.type, BASE_SCHEMA.Affiliation))
    g.add((person_uri, BASE_SCHEMA.currentAffiliation, aff_uri))
    
    if affiliation.get('institution_name'):
        g.add((aff_uri, BASE_SCHEMA.institutionName, 
                    Literal(affiliation['institution_name'])))
    
    if affiliation.get('institution_id'):
        g.add((aff_uri, BASE_SCHEMA.institutionId, 
                    Literal(affiliation['institution_id'])))
    
    if affiliation.get('faculty_or_department'):
        g.add((aff_uri, BASE_SCHEMA.department, 
                    Literal(affiliation['faculty_or_department'])))
    
    if affiliation.get('unit'):
        g.add((aff_uri, BASE_SCHEMA.unit, Literal(affiliation['unit'])))
    
    if affiliation.get('position'):
        g.add((aff_uri, BASE_SCHEMA.position, 
                    Literal(affiliation['position'])))
        
    add_provenance(g, aff_uri, affiliation.get("provenance", {}))


def add_employment_history(g: Graph, person_uri: URIRef, employment_list: list[dict[str, any]]):
    """Add employment history"""
    for idx, emp in enumerate(employment_list):
        emp_uri = URIRef(f"{person_uri}/employment/{idx}")
        g.add((emp_uri, RDF.type, BASE_SCHEMA.Employment))
        g.add((person_uri, BASE_SCHEMA.hasEmployment, emp_uri))
        
        if emp.get("position_title"):
            g.add((emp_uri, BASE_SCHEMA.position_title, Literal(emp["position_title"])))
        
        if emp.get("institution_name"):
            g.add((emp_uri, BASE_SCHEMA.institution_name, Literal(emp["institution_name"])))
        
        if emp.get("unit"):
            g.add((emp_uri, BASE_SCHEMA.unit, Literal(emp["unit"])))
            
        if emp.get("country"):
            g.add((emp_uri, BASE_SCHEMA.country, Literal(emp["country"])))
        
        if emp.get("from"):
            g.add((emp_uri, BASE_SCHEMA.startDate, normalize_date(emp["from"])))
        
        if emp.get("to"):
            g.add((emp_uri, BASE_SCHEMA.endDate, normalize_date(emp["to"])))
            
        add_provenance(g, emp_uri, emp.get("provenance", {}))
            
            
def add_visiting_appointments(g: Graph, person_uri: URIRef, visiting_appointments: list[dict[str, any]]):
    """Add visiting appointments"""
    for idx, app in enumerate(visiting_appointments):
        app_uri = URIRef(f"{person_uri}/appointment/{idx}")
        g.add((app_uri, RDF.type, BASE_SCHEMA.APPOINTMENT))
        g.add((person_uri, BASE_SCHEMA.hasAppointment, app_uri))
        
        if app.get("role"):
            g.add((app_uri, BASE_SCHEMA.role, Literal(app["role"])))
            
        if app.get("institution_name"):
            g.add((app_uri, BASE_SCHEMA.institution_name, Literal(app["institution_name"])))
        
        if app.get("institution_id"):
            g.add((app_uri, BASE_SCHEMA.institution_id, Literal(app["institution_id"])))
        
        if app.get("from"):
            g.add((app_uri, BASE_SCHEMA.startDate, Literal(app["from"])))
        
        if app.get("to"):
            g.add((app_uri, BASE_SCHEMA.endDate, Literal(app["to"])))

        add_provenance(g, app_uri, app.get("provenance", {}))


def add_education(g: Graph, person_uri: URIRef, education: list[dict[str, any]]):
    """Add education information"""
    for idx, edu in enumerate(education):
        edu_uri = URIRef(f"{person_uri}/education/{idx}")
        g.add((edu_uri, RDF.type, BASE_SCHEMA.EDUCATION))
        g.add((person_uri, BASE_SCHEMA.hasEducation, edu_uri))
        
        g.add((edu_uri, BASE_SCHEMA.degree, Literal(edu["degree"])))
        
        if edu.get('field'):
            g.add((edu_uri, BASE_SCHEMA.field, Literal(edu['field'])))
            
        if edu.get('specialization'):
            g.add((edu_uri, BASE_SCHEMA.specialization, 
                        Literal(edu['specialization'])))
        
        if edu.get('institution_name'):
            g.add((edu_uri, BASE_SCHEMA.institutionName, 
                        Literal(edu['institution_name'])))
        
        if edu.get('country'):
            g.add((edu_uri, BASE_SCHEMA.country, Literal(edu['country'])))
        
        if edu.get('date_awarded'):
            g.add((edu_uri, BASE_SCHEMA.dateAwarded, 
                        normalize_date(edu["date_awarded"])))
            
        add_provenance(g, edu_uri, edu.get("provenance", {}))
            
            
def add_discipline(g: Graph, person_uri: URIRef, discipline: dict[str, any]):
    if not discipline:
        return
    
    discipline_uri = URIRef(f"{person_uri}/discipline")
    g.add((discipline_uri, RDF.type, BASE_SCHEMA.DISCIPLINE))
    g.add((person_uri, BASE_SCHEMA.hasDiscipline, discipline_uri))
    
    if discipline.get("sector"):
        g.add((discipline_uri, BASE_SCHEMA.sector, Literal(discipline["sector"])))
    
    if discipline.get("field"):
        g.add((discipline_uri, BASE_SCHEMA.field, Literal(discipline["field"])))
    
    if discipline.get("subfield"):
        g.add((discipline_uri, BASE_SCHEMA.subfield, Literal(discipline["subfield"])))
    
    
def add_application(g: Graph, person_uri: URIRef, application: dict[str, any]):
    if not application:
        return
    
    application_uri = URIRef(f"{person_uri}/application")
    g.add((application_uri, RDF.type, BASE_SCHEMA.APPLICATION))
    g.add((person_uri, BASE_SCHEMA.hasApplication, application_uri))
    
    if application.get("dossier_code"):
        g.add((application_uri, BASE_SCHEMA.dossier_code, Literal(application["dossier_code"])))
        
    if application.get("rank_applied"):
        g.add((application_uri, BASE_SCHEMA.rank_applied, Literal(application["rank_applied"])))
        
    if application.get("host_institution"):
        g.add((application_uri, BASE_SCHEMA.host_institution, Literal(application["host_institution"])))
        
    if application.get("field_council"):
        g.add((application_uri, BASE_SCHEMA.field_council, Literal(application["field_council"])))
        
    if application.get("date_submitted"):
        g.add((application_uri, BASE_SCHEMA.date_submitted, Literal(application["date_submitted"])))
        
    if application.get("lecturer_type"):
        g.add((application_uri, BASE_SCHEMA.lecturer_type, Literal(application["lecturer_type"])))


def add_research_interests(g: Graph, person_uri: URIRef, research_interests: list):
    if not research_interests:
        return
    
    research_interests_uri = URIRef(f"{person_uri}/research_interests")
    g.add((research_interests_uri, RDF.type, BASE_SCHEMA.RESEARCH_INTERESTS))
    g.add((person_uri, BASE_SCHEMA.hasResearchInterests, research_interests_uri))
    
    for interests in research_interests:
        g.add((research_interests_uri, BASE_SCHEMA.interests, Literal(interests)))
        

def add_supervision(g: Graph, person_uri: URIRef, supervision: dict[str, any]):
    """Add student supervision information"""
    if not supervision:
            return
        
    if supervision.get('phd_completed'):
        g.add((person_uri, BASE_SCHEMA.phdSupervised, 
                    Literal(supervision['phd_completed'], datatype=XSD.integer)))
    
    if supervision.get('masters_completed'):
        g.add((person_uri, BASE_SCHEMA.mastersSupervised, 
                    Literal(supervision['masters_completed'], datatype=XSD.integer)))
    
    for idx, detail in enumerate(supervision.get('details', [])):
        sup_uri = URIRef(f"{person_uri}/supervision/{idx}")
        g.add((sup_uri, RDF.type, BASE_SCHEMA.Supervision))
        g.add((person_uri, BASE_SCHEMA.hasSupervision, sup_uri))
        
        if detail.get('candidate_name'):
            g.add((sup_uri, BASE_SCHEMA.candidateName, 
                        Literal(detail['candidate_name'])))
        
        if detail.get('level'):
            g.add((sup_uri, BASE_SCHEMA.level, Literal(detail['level'])))
        
        if detail.get('role'):
            g.add((sup_uri, BASE_SCHEMA.supervisorRole, 
                        Literal(detail['role'])))
        
        if detail.get('institution_name'):
            g.add((sup_uri, BASE_SCHEMA.institutionName, 
                        Literal(detail['institution_name'])))
        
        if detail.get('from'):
            g.add((sup_uri, BASE_SCHEMA.startDate, 
                        normalize_date(detail["from"])))
        
        if detail.get('to'):
            g.add((sup_uri, BASE_SCHEMA.endDate, 
                        normalize_date(detail["to"])))
        
        if detail.get('date_awarded'):
            g.add((sup_uri, BASE_SCHEMA.dateAwarded, 
                        normalize_date(detail["date_awarded"])))
            
        add_provenance(g, sup_uri, detail.get("provenance", {}))


def add_projects(g: Graph, person_uri: URIRef, projects: list[dict[str, any]]):
    """Add research projects"""
    for idx, proj in enumerate(projects):
        proj_uri = URIRef(f"{person_uri}/project/{idx}")
        g.add((proj_uri, RDF.type, BASE_SCHEMA.Project))
        g.add((person_uri, BASE_SCHEMA.hasProject, proj_uri))
        
        if proj.get('title'):
            g.add((proj_uri, DC.title, Literal(proj['title'])))
        
        if proj.get('code'):
            g.add((proj_uri, BASE_SCHEMA.projectCode, 
                        Literal(proj['code'])))
        
        if proj.get('level'):
            g.add((proj_uri, BASE_SCHEMA.projectLevel, 
                        Literal(proj['level'])))
        
        if proj.get('role'):
            g.add((proj_uri, BASE_SCHEMA.role, Literal(proj['role'])))
        
        if proj.get('from'):
            g.add((proj_uri, BASE_SCHEMA.startDate, 
                        normalize_date(proj["from"])))
        
        if proj.get('to'):
            g.add((proj_uri, BASE_SCHEMA.endDate, 
                        normalize_date(proj["to"])))
        
        if proj.get('result'):
            g.add((proj_uri, BASE_SCHEMA.result, Literal(proj['result'])))
            
        add_provenance(g, proj_uri, proj.get("provenance", {}))


def add_publications(g: Graph, person_uri: URIRef, 
                        publications: list[dict[str, any]]):
    """Add publications"""
    for idx, pub in enumerate(publications):
        pub_uri = URIRef(f"{person_uri}/publication/{idx}")
        g.add((pub_uri, RDF.type, BASE_SCHEMA.Publication))
        g.add((person_uri, BASE_SCHEMA.hasPublication, pub_uri))
        
        if pub.get('title'):
            g.add((pub_uri, DC.title, Literal(pub['title'])))
        
        if pub.get('venue'):
            g.add((pub_uri, BASE_SCHEMA.venue, Literal(pub['venue'])))
        
        if pub.get('type'):
            g.add((pub_uri, BASE_SCHEMA.publicationType, 
                        Literal(pub['type'])))
        
        if pub.get('year'):
            g.add((pub_uri, DC.date, 
                        Literal(pub['year'], datatype=XSD.gYear)))
        
        if pub.get('indexing'):
            g.add((pub_uri, BASE_SCHEMA.indexing, 
                        Literal(pub['indexing'])))
        
        if pub.get('quartile'):
            g.add((pub_uri, BASE_SCHEMA.quartile, 
                        Literal(pub['quartile'])))
        
        if pub.get('impact_factor'):
            g.add((pub_uri, BASE_SCHEMA.impactFactor, 
                        Literal(pub['impact_factor'], datatype=XSD.float)))
        
        if pub.get('is_lead_author') is not None:
            g.add((pub_uri, BASE_SCHEMA.isLeadAuthor, 
                        Literal(pub['is_lead_author'], datatype=XSD.boolean)))
        
        if pub.get('citations'):
            g.add((pub_uri, BASE_SCHEMA.citations, 
                        Literal(pub['citations'], datatype=XSD.integer)))
            
        add_provenance(g, pub_uri, pub.get("provenance", {}))
            
            
def add_books(g: Graph, person_uri: URIRef, books: list[dict[str, any]]):
    """Add books"""
    for idx, book in enumerate(books):
        book_uri = URIRef(f"{person_uri}/books/{idx}")
        g.add((book_uri, RDF.type, BASE_SCHEMA.Book))
        g.add((person_uri, BASE_SCHEMA.hasBook, book_uri))
        
        if book.get('title'):
            g.add((book_uri, DC.title, Literal(book['title'])))
        
        if book.get('type'):
            g.add((book_uri, BASE_SCHEMA.bookType, Literal(book['type'])))
        
        if book.get('publisher'):
            g.add((book_uri, BASE_SCHEMA.publisher, 
                        Literal(book['publisher'])))
        
        if book.get('year'):
            g.add((book_uri, DC.date, 
                        Literal(book['year'], datatype=XSD.gYear)))
        
        if book.get('is_reputable_publisher'):
            g.add((book_uri, BASE_SCHEMA.is_reputable_publisher, 
                        Literal(book['is_reputable_publisher'], datatype=XSD.boolean)))
        
        if book.get('chapter_pages'):
            g.add((book_uri, BASE_SCHEMA.chapter_pages, 
                        Literal(book['chapter_pages'])))
            
        add_provenance(g, book_uri, book.get("provenance", {}))
        
        
def add_awards(g: Graph, person_uri: URIRef, awards: list[dict[str, any]]):
    if not awards:
        return
    
    for idx, award in enumerate(awards):
        award_uri = URIRef(f"{person_uri}/awards/{idx}")
        g.add((award_uri, RDF.type, BASE_SCHEMA.Award))
        g.add((person_uri, BASE_SCHEMA.hasAward, award_uri))
        
        if award.get("name"):
            g.add((award_uri, BASE_SCHEMA.awardName, Literal(award["name"])))
            
        if award.get("issuer"):
            g.add((award_uri, BASE_SCHEMA.awardIssuer, Literal(award["issuer"])))
            
        if award.get("year"):
            g.add((award_uri, DC.date, Literal(award["year"], datatype=XSD.gYear)))
        
        add_provenance(g, award_uri, award.get("provenance", {}))
            

def add_discipline_actions(g: Graph, person_uri: URIRef, discipline_actions: list[dict[str, any]]):
    if not discipline_actions:
        return
    
    for idx, disc in enumerate(discipline_actions):
        disc_uri = URIRef(f"{person_uri}/discipline_actions/{idx}")
        g.add((disc_uri, RDF.type, BASE_SCHEMA.DisciplineAction))
        g.add((person_uri, BASE_SCHEMA.hasDisciplineAction, disc_uri))
        
        if disc.get("name"):
            g.add((disc_uri, BASE_SCHEMA.discActionName, Literal(disc["name"])))
            
        if disc.get("issuer"):
            g.add((disc_uri, BASE_SCHEMA.discActionIssuer, Literal(disc["issuer"])))
            
        if disc.get("decision_no"):
            g.add((disc_uri, BASE_SCHEMA.discDecision, Literal(disc["decision_no"])))
        
        if disc.get("effective_period"):
            g.add((disc_uri, BASE_SCHEMA.discEffectivePeriod, Literal(disc["effective_period"])))
        
        add_provenance(g, disc_uri, disc.get("provenance", {}))
            

def add_teaching_loads(g: Graph, person_uri: URIRef, teaching_loads: list[dict[str, any]]):
    if not teaching_loads:
        return
    
    for idx, load in enumerate(teaching_loads):
        teach_uri = URIRef(f"{person_uri}/teaching_loads/{idx}")
        g.add((teach_uri, RDF.type, BASE_SCHEMA.TeachingLoads))
        g.add((person_uri, BASE_SCHEMA.hasTeachingLoads, teach_uri))
        
        if load.get("hours_direct"):
            g.add((teach_uri, BASE_SCHEMA.hours_direct, Literal(load["hours_direct"])))
        
        if load.get("hours_converted"):
            g.add((teach_uri, BASE_SCHEMA.hours_converted, Literal(load["hours_converted"])))
            
        if load.get("hours_required"):
            g.add((teach_uri, BASE_SCHEMA.hours_required, Literal(load["hours_required"])))
        
        add_provenance(g, teach_uri, load.get("provenance", {}))
        

def add_languages(g: Graph, person_uri: URIRef, languages: list[dict[str, any]]):
    if not languages:
        return
    
    for idx, lang in enumerate(languages):
        language_uri = URIRef(f"{person_uri}/languages/{idx}")
        g.add((language_uri, RDF.type, BASE_SCHEMA.Language))
        g.add((person_uri, BASE_SCHEMA.hasLanguage, language_uri))
        
        if lang.get("language"):
            g.add((language_uri, BASE_SCHEMA.language, Literal(lang["language"])))
        
        if lang.get("level"):
            g.add((language_uri, BASE_SCHEMA.level, Literal(lang["level"])))
        
        if lang.get("evidence"):
            g.add((language_uri, BASE_SCHEMA.evidence, Literal(lang["evidence"])))
            
        add_provenance(g, language_uri, lang.get("provenance", {}))


def add_checkboxes(g: Graph, person_uri: URIRef, checkboxes: dict[str, any]):
    if not checkboxes:
        return
    
    checkbox_uri = URIRef(f"{person_uri}/checkbox")
    g.add((checkbox_uri, RDF.type, BASE_SCHEMA.Checkbox))
    g.add((person_uri, BASE_SCHEMA.hasCheckbox, checkbox_uri))
    
    if checkboxes.get("is_giang_vien"):
        g.add((checkbox_uri, BASE_SCHEMA.is_giang_vien, Literal(checkboxes["is_giang_vien"], datatype=XSD.boolean)))
    
    if checkboxes.get("is_giang_vien_thinh_giang"):
        g.add((checkbox_uri, BASE_SCHEMA.is_giang_vien_thinh_giang, Literal(checkboxes["is_giang_vien_thinh_giang"], datatype=XSD.boolean)))
        

def add_provenance(g: Graph, entity_uri: URIRef, provenance: dict[str, any]):
    """Add provenance information"""
    if not provenance:
        return
    
    prov_uri = URIRef(f"{entity_uri}/provenance")
    g.add((prov_uri, RDF.type, BASE_SCHEMA.Provenance))
    g.add((entity_uri, BASE_SCHEMA.provenance, prov_uri))
    
    if provenance.get("doc_id"):
        g.add((prov_uri, BASE_SCHEMA.documentId, Literal(provenance["doc_id"])))
        
    if provenance.get("page"):
        g.add((prov_uri, BASE_SCHEMA.page, Literal(provenance["page"], datatype=XSD.integer)))
        
    
def normalize_date(date_str: str):
    if not date_str:
        return None
    if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return Literal(date_str, datatype=XSD.date)
    elif re.match(r"^\d{4}-\d{2}$", date_str):
        return Literal(date_str, datatype=XSD.gYearMonth)
    elif re.match(r"^\d{4}$", date_str):
        return Literal(date_str, datatype=XSD.gYear)
    else:
        return Literal(date_str)  # fallback, treat as plain string
    
    
def export_turtle(g: Graph, filename: str):
    """Export graph to Turtle format"""
    g.serialize(destination=filename, format='turtle')
    

def export_jsonld(g: Graph, filename: str):
    """Export graph to JSON-LD format"""
    g.serialize(destination=filename, format='json-ld')
    
    
def build_graph(g: Graph, profile_data: dict[str, any]) -> Graph:
    person_uri = add_person(g, profile_data.get("person", {}))
    
    add_contacts(g, person_uri, profile_data.get("contacts", {}))
    
    add_current_affiliation(g, person_uri, profile_data.get("current_affiliation", {}))
    
    add_employment_history(g, person_uri, profile_data.get("employment_history", []))
    
    add_visiting_appointments(g, person_uri, profile_data.get("visiting_appointments", []))
    
    add_education(g, person_uri, profile_data.get("education", []))
    
    add_discipline(g, person_uri, profile_data.get("discipline", {}))
    
    add_application(g, person_uri, profile_data.get("application", {}))
    
    add_research_interests(g, person_uri, profile_data.get("research_interests", []))
    
    add_supervision(g, person_uri, profile_data.get("supervision", {}))
    
    add_projects(g, person_uri, profile_data.get("projects", []))
    
    add_publications(g, person_uri, profile_data.get("publications", []))
    
    add_books(g, person_uri, profile_data.get("book", []))
    
    add_awards(g, person_uri, profile_data.get("awards", []))
    
    add_discipline_actions(g, person_uri, profile_data.get("discipline_actions", []))
    
    add_teaching_loads(g, person_uri, profile_data.get("teaching_loads", []))
    
    add_languages(g, person_uri, profile_data.get("languages", []))
    
    add_checkboxes(g, person_uri, profile_data.get("checkboxes", {}))
    

if __name__ == "__main__":
    json_file = "sample_data.json"
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"Succesfully reads file: {json_file}")
        profiles = data
        print(f"Found {len(profiles)} profiles")
    
        g = Graph()
        for idx, profile in enumerate(profiles):
            try:
                build_graph(g, profile)
                person_name = profile.get("person", {}).get("name", f"Unknown_{idx}")
                print(f"[{idx+1}] Completed: {person_name}")
            except Exception as e:
                print(f"Error handling profile {idx+1}: {e}")
                continue
            
        output_prefix = "academic_profiles"
        export_turtle(g, f"{output_prefix}.ttl")
        export_jsonld(g, f"{output_prefix}.jsonld")
        
        print(f"\n{'='*60}")
        print(f"✓ Hoàn thành!")
        print(f"  Total triples: {len(g)}")
        print(f"  Exported files:")
        print(f"    - {output_prefix}.ttl (Turtle)")
        print(f"    - {output_prefix}.jsonld (JSON-LD)")
        print(f"{'='*60}")
    
    except FileNotFoundError:
        print(f"File not found: {json_file}")