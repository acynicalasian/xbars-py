from google.cloud import language_v2
import re

class EntityList:
    """
    Initialize an object that holds entities detected in a string.

    Entities include people, organizations, locations, etc. Check 
    https://cloud.google.com/natural-language/docs/reference/rest/v2/Entity#type for entity types.
    """    
    def __init__(self, text):
        self.__parse(text)

    # Parse input text, find entities, and replace any spaces in multi-word entites with _'s
    def __parse(self, text):
        output = text
        
        client = language_v2.LanguageServiceClient()
        # Default to inputs being English for now, we don't know enough PSRs for other
        # languages
        doc = {
            "content": text,
            "type_": language_v2.Document.Type.PLAIN_TEXT,
            "language_code": "en"
            }
        response = client.analyze_entities(
            request = {"document": doc, "encoding_type": language_v2.EncodingType.UTF8}
            )

        # Store proper nouns that are or aren't preceded by "the". This automatically assumes that
        # the user-provided input was semantically valid in the first place (i.e. "I saw *the* Mona
        # Lisa" as opposed to "I saw Mona Lisa")
        #
        # Gather addresses separately, as they seem primarily used in prepositional phrases
        self.PN_NULL_DET = []
        self.PN_DET = []
        self.PN_ADDR = []
        
        self.__ENTS_TO_CHECK = {}

        last_pn_poss = None
        for entity in response.entities:
            # People and addresses are almost always used without articles/determiners in English
            ent_type = language_v2.Entity.Type(entity.type_).name
            mention_type = language_v2.EntityMention.Type(mention.type_).name
            if ent_type == "PERSON" and mention_type == "PROPER":
                self.PN_NULL_DET.append(entity.name)
            elif ent_type == "ADDRESS":
                self.PN_ADDR.append(entity.name)
            elif ent_type in ["LOCATION", "ORGANIZATION"] and mention_type == "PROPER":
                pn_det_pattern = "the " + entity.name
                pn_poss_pattern = entity.name + "'s"
                # Handle stuff like "the Titanic"
                if re.search(pn_det_pattern, output):
                    underscore_name = entity.name.replace(' ', '_')
                    output = output.replace(pn_det_pattern, underscore_name)
                    self.PN_DET.append(underscore_name)
                    
                
                
                
                
