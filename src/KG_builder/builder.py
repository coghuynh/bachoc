import logging
from typing import Dict, List
from KG_builder.utils.clean_data import read_schema, chunk_corpus, write_schema
from KG_builder.embedding.ops import CostEmbeddingModel, cosine_similarity
from KG_builder.extract.extract_triples import extract_triples
from KG_builder.extract.definition import collect_definition
from KG_builder.prompts.prompts import DEFINITION_PROMPT, EXTRACT_TRIPLE_PROMPT
from KG_builder.utils.llm_utils import load_model
from dotenv import load_dotenv
import asyncio

load_dotenv()

class KG_builder:
    
    def __init__(self, **args):
        self.entities_schema = read_schema(args["entities_schema"])
        self.relations_schema = read_schema(args["relation_schema"])
        self.extract_triples_model = load_model(args["triples_model"])
        self.definition_model = load_model(args["definition_model"])
    
        embed_config = {
            "model_name" : "gemini-embedding-001",
            "similarity" : "cosine"
        }
        self.embed_model = CostEmbeddingModel(
            **embed_config
        )
        
        self.threshold = args["threshold"]
    
    def get_entities_schema(self):
        return self.entities_schema
    
    def get_relation_schema(self):
        return self.relations_schema
    
    def preprocess_embed(self):
        try:
            # Entities
            ent_defs = [v for _, v in self.entities_schema.items()]
            ent_embeds = self.embed_model.encode(ent_defs)
            self.entities_embed_schema = {
                k: ent_embeds[i] for i, (k, _) in enumerate(self.entities_schema.items())
            }

            # Relations
            rel_defs = [v for _, v in self.relations_schema.items()]
            rel_embeds = self.embed_model.encode(rel_defs)
            self.relations_embed_schema = {
                k: rel_embeds[i] for i, (k, _) in enumerate(self.relations_schema.items())
            }
        except Exception as e:
            logging.exception(f"Message: {e}")
            
    
    def standardize_triples(self, triples: Dict[str, str]) -> Dict[str, str]:
        
        return 
    
    def standardize_entities(self, entity_type: str) -> str:
        
        if entity_type in self.entities_embed_schema.keys():
            return entity_type
        
        try:
            entity_embed = self.embed_model.encode([entity_type])[0]
        except Exception as e:
            logging.exception(f"Message: {e}")
            return entity_type
        mxCor = 0.0
        new_type = ""
        for type_name, embed in self.entities_embed_schema.items():
            correlation = cosine_similarity(entity_embed, embed) 
            if correlation > mxCor:
                mxCor = correlation
                new_type = type_name
                
        if mxCor >= self.threshold:
            return new_type
        else:
            self.entities_embed_schema[entity_type]  = entity_embed
            return entity_type
    
    def standardize_relations(self, relation: Dict[str, str]) -> str:
        
        relation_type = relation["type"]
        definition = relation["definition"]
        if relation_type in self.relations_embed_schema.keys():
            return relation_type
        relation_embed = None
        
        try:
            relation_embed = self.embed_model.encode([definition])[0]
        except Exception as e:
            logging.exception(f"Message: {e}")
            relation_embed = None
        if relation_embed is None:
            return relation_type
        mxCor = 0.0
        new_type = ""
    
        for type_name, embed in self.relations_embed_schema.items():
            correlation = cosine_similarity(relation_embed, embed) 
            if correlation > mxCor:
                mxCor = correlation
                new_type = type_name
                
        if mxCor >= self.threshold:
            return new_type
        else:
            self.relations_embed_schema[relation_type] = relation_embed
            self.relations_schema[relation_type] = definition
            return relation_type
            
    
    def run(self, context: str, chunk_config=None):
        self.preprocess_embed()

        if not context or not context.strip():
            logging.warning("Empty context received; skipping triple extraction.")
            return []

        chunk_kwargs = chunk_config or {}
        try:
            contexts = chunk_corpus(context, **chunk_kwargs)
        except TypeError:
            logging.exception("Invalid chunk configuration provided; falling back to defaults.")
            contexts = chunk_corpus(context)

        if not contexts:
            contexts = [context]

        aggregated_triples: List[Dict[str, str]] = []
        seen_triples = set()

        for idx, chunk in enumerate(contexts):
            # print(idx, chunk)
            try:
                partial_result = extract_triples(chunk, self.extract_triples_model, **EXTRACT_TRIPLE_PROMPT)
            except Exception as e:
                logging.exception(f"Triple extraction failed for chunk {idx}: {e}")
                continue

            if not isinstance(partial_result, list):
                logging.warning("Unexpected triple extraction output type for chunk %s", idx)
                continue

            for triple in partial_result:
                if not isinstance(triple, dict):
                    continue
                key = (
                    triple.get("subject", "").strip(),
                    triple.get("predicate", "").strip(),
                    triple.get("object", "").strip()
                )
                if not all(key):
                    continue
                if key in seen_triples:
                    continue
                seen_triples.add(key)
                aggregated_triples.append(triple)

        if not aggregated_triples:
            logging.warning("No triples extracted from provided context.")
            return []

        result = aggregated_triples

        
        set_relation_type = set()
        
        for triple in result:
            set_relation_type.add(triple["predicate"])

        if not set_relation_type:
            return result

        new_predicate_definition = collect_definition(
            set_relation_type, self.definition_model, **DEFINITION_PROMPT
        )
        
        map_new_relation = {}
        
        for predicate in new_predicate_definition:
            map_new_relation[predicate["type"]] = self.standardize_relations(predicate)
        
        for triple in result:
            predicate_name = triple["predicate"]
            triple["predicate"] = map_new_relation.get(predicate_name, predicate_name)
        
        return result
    
    def write_schema(self, path):
        write_schema(self.relations_schema, path)
    
    
    
if __name__ == "__main__":
    

    
    
    text = """
        Albert Einstein was born in Ulm, Germany in 1879. He developed the theory of relativity, which changed how scientists understand space and time. In 1921, he received the Nobel Prize in Physics for his explanation of the photoelectric effect. Later, Einstein worked at Princeton University in the United States. His contributions influenced modern physics and inspired generations of scientists.
    """
    
    args = {
        "entities_schema" : "/Users/huynhnguyen/WorkDir/bachoc_1/entities.csv",
        "relation_schema" : "/Users/huynhnguyen/WorkDir/bachoc_1/relationships.csv",
        "threshold" : 0.6
    }
    
    builder = KG_builder(**args)
    
    chunks_config = {
        "max_chunk_chars": 4800,
        "min_chunk_chars": 1200,
        "sentence_overlap": 1
    }
    
    print(builder.run(text, chunks_config))
    
    builder.write_schema("new_relationship_v1.1.csv")
        
        
            
            
            
            
        
        
        
        
        
        
        
