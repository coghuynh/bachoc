from KG_builder.builder import KG_builder
import argparse
from dotenv import load_dotenv
import json



if __name__ == "__main__":
    load_dotenv()
    # PATH = "/Users/huynhnguyen/WorkDir/bachoc_1/data/(16879491024946_28_06_2024_11_07)nguyen-thuong-nghia-1964-01-01-1719547648.txt"
    
    argParse = argparse.ArgumentParser()
    
    argParse.add_argument("-data")
    argParse.add_argument("-triples_model", default="gemini-2.5-flash")
    argParse.add_argument("-definition_model", default="gpt-3.5-turbo")
    argParse.add_argument("-embedding_model", default="gemini-embedding-001")
    argParse.add_argument("-similarity", default="cosine")
    argParse.add_argument("-threshold", default=0.9)
    argParse.add_argument("-entities_schema", default="./entities.csv")
    argParse.add_argument("-relation_schema", default="./relationships.csv")
    argParse.add_argument("-max_chunk_chars", default=4800)
    argParse.add_argument("-min_chunk_chars", default=1200)
    argParse.add_argument("-sentence_overlap", default=1)
    
    # args = {
    #     "enities_schema" : "/Users/huynhnguyen/WorkDir/bachoc_1/entities.csv",
    #     "relation_schema" : "/Users/huynhnguyen/WorkDir/bachoc_1/relationships.csv",
    #     "threshold" : 0.8
    # }
    
    param = vars(argParse.parse_args())
    
    
    
    # print(param)
    
    corpus =  open(param["data"], "r").read()
    
    from KG_builder.utils.clean_data import clean_vn_text
    
    corpus = clean_vn_text(corpus)
    
    print(corpus)
    
    # # print(corpus)
    
    chunks_config = {
        "max_chunk_chars": param["max_chunk_chars"],
        "min_chunk_chars": param["min_chunk_chars"],
        "sentence_overlap": param["sentence_overlap"]
    }
    
    builder = KG_builder(**param)
    
    # # print(
    new_triples = builder.run(corpus, chunks_config)
    builder.write_schema("new_relationship_v2.0.csv")
    # import json
    
    with open("new_triples_v2.0.json", "w", encoding="utf-8") as f:
        json.dump(new_triples, f, ensure_ascii=False, indent=2)

