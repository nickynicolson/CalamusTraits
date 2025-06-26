from textwrap import dedent

ZERO_SHOT_PROMPT = dedent(f"""
    ### Task ###
    Create a JSON object where the key is the "code" and its corresponding value is a numeric score derived by applying the given rules to the respective descriptions. 
    Ensure the JSON object includes all specified codes, with scores accurately matching their respective codes. 
    If a score cannot be determined for a code, assign a value of null. 
    Provide a complete and accurate JSON object without any extra text or fabricated data, and export it as a JSON object with no whitespace or trailing commas.
                        
    ### Materials ###
    A description of a species: {{subject_para}}\n
    A JSON dictionary of trait codes ("code") and sets of rules ("rules") for encoding trait values:\n
    {{appendix_2_subject_batch}}
    Carefully analyse the description and apply the rules systematically before generating the JSON response.
""")

FEW_SHOT_PROMPT = dedent(f"""
    ### Task ###
    Create a JSON object where the key is the "code" and its corresponding value is a numeric score derived by applying the given rules to the respective descriptions. 
    Ensure the JSON object includes all specified codes, with scores accurately matching their respective codes. 
    If a score cannot be determined for a code, assign a value of null. 
    Provide a complete and accurate JSON object without any extra text or fabricated data, and export it as a JSON object with no whitespace or trailing commas.

    ### Materials ###
    A description of a species: {{subject_para}}\n
    A JSON dictionary of trait codes ("code") and sets of rules ("rules") for encoding trait values:\n
    {{appendix_2_subject_batch}}
    Carefully analyse the description and apply the rules systematically before generating the JSON response.
    
    #### Example 1 ###
    description: "rachises 36.2(28.5–45.0) cm long, the  apices extended into an elongate cirrus, without reduced or vestigial pinnae, adaxially flat, abaxially with more or  less regularly arranged (at least proximally), distantly spaced clusters of dark–tipped, recurved spines, terminating  in a stub, without a shallow groove adaxially"
    rules: "Petioles and rachises with long, straight, yellowish or brownish, black-tipped, usually solitary spines abaxially and laterally (0); petioles and rachises without long, straight, spines abaxially and laterally (1)"
    code: "rachis"
    rule "0" doesn't apply here, therefore it must be rule "1". output: "{{{{"rachis": "1"}}}}"  
    
    ### Example 2 ###
    description: "seeds 1 per fruit"
    rules: "Seeds 1 per fruit (0); seeds 2-3 per fruit (1)"
    code: "seeded"
    The description clearly states that there is 1 seed per fruit, therefore assign rule "0". output: "{{{{"seeded": "0"}}}}" 
    
    ### Example 3 ###
    description: "leaf sheaths with numerous spicules borne on short, low, horizontal ridges, easily detached  and leaving the sheaths with ridges only"
    rules: "Leaf sheath spines slender to stout, triangular, concave at the base proximally, horizontally spreading or downward pointing, scattered to dense, rarely in horizontal rows, yellowish-brown to dark brown (0); leaf sheath spines short to long, triangular, concave at the base proximally, usually horizontally spreading, scattered to dense, yellowish-brown to dark brown, slightly swollen-based or with an adjacent swelling (1); leaf sheath spines not as above (2)"
    code: "dactyl"
    The description does not match rules "0" or "1", therefore we must assign rule "2". output: "{{{{"dactyl": "2"}}}}"
                        
    ### Example 4 ### 
    description: " "
    rules: "Staminate sepals as long as the petals, splitting almost to the base (0); staminate sepals usually shorter than the petals, cupular, 3-lobed at the apex (1); staminate sepals as long as petals (splitting not recorded) (2)"
    code: "sepals"
    There is no mention of sepals in the description, therefore we must assign "null". output: "{{{{"sepals": null}}}}"
                                
    ### Example 5 ### where the value is multiple numbers
    description: "Stems clustered, rarely solitary"
    rules: "Stems solitary (0); stems clustered (1)"
    code: "solclu"
    This description applied to multiple rules, therefore assign both rules. output: "{{{{"solclu": "0,1"}}}}"
""")

COT_PROMPT = dedent(f"""
    1. List the questions that you would ask to score a plant according to the "rules" in this rubric. Ensure that each question is atomic and concerns only a single character (shape, structure, etc):\n
    {{appendix_2_subject_batch}}
    2. Now apply those questions to this description:\n
    {{subject_para}}
    3. Now combine the answers to give me a rubric score. If you cannot give a score, set the value to null.
    4. Export the answers as a JSON object. Use the code as the key. Ensure no white space or trailing commas.
""")

COT_FEWSHOT_PROMPT = dedent(f"""
    ### Instructions ###
    1. list the questions that you would ask to score a plant according to the "rules" in this rubric. Ensure that each question is atomic and concerns only a single character (shape, structure etc):\n
    {{appendix_2_subject_batch}}
    2. Now apply those questions to this description:\n
    {{subject_para}}
    3. Now combine the answers to give me a rubric score. If you cannot give a score, set the value to null. 
    4. Export the answers as a JSON object. Use the code as the key. Ensure no white space or trailing commas. 

    #### Example 1 ###
    description: "rachises 36.2(28.5–45.0) cm long, the  apices extended into an elongate cirrus, without reduced or vestigial pinnae, adaxially flat, abaxially with more or  less regularly arranged (at least proximally), distantly spaced clusters of dark–tipped, recurved spines, terminating  in a stub, without a shallow groove adaxially"
    rules: "Petioles and rachises with long, straight, yellowish or brownish, black-tipped, usually solitary spines abaxially and laterally (0); petioles and rachises without long, straight, spines abaxially and laterally (1)"
    code: "rachis"
    rule "0" doesn't apply here, therefore it must be rule "1". output: "{{{{"rachis": "1"}}}}"  
    
    ### Example 2 ###
    description: "seeds 1 per fruit"
    rules: "Seeds 1 per fruit (0); seeds 2-3 per fruit (1)"
    code: "seeded"
    The description clearly states that there is 1 seed per fruit, therefore assign rule "0". output: "{{{{"seeded": "0"}}}}" 
    
    ### Example 3 ###
    description: "leaf sheaths with numerous spicules borne on short, low, horizontal ridges, easily detached  and leaving the sheaths with ridges only"
    rules: "Leaf sheath spines slender to stout, triangular, concave at the base proximally, horizontally spreading or downward pointing, scattered to dense, rarely in horizontal rows, yellowish-brown to dark brown (0); leaf sheath spines short to long, triangular, concave at the base proximally, usually horizontally spreading, scattered to dense, yellowish-brown to dark brown, slightly swollen-based or with an adjacent swelling (1); leaf sheath spines not as above (2)"
    code: "dactyl"
    The description does not match rules "0" or "1", therefore we must assign rule "2". output: "{{{{"dactyl": "2"}}}}"
                        
    ### Example 4 ### 
    description: " "
    rules: "Staminate sepals as long as the petals, splitting almost to the base (0); staminate sepals usually shorter than the petals, cupular, 3-lobed at the apex (1); staminate sepals as long as petals (splitting not recorded) (2)"
    code: "sepals"
    There is no mention of sepals in the description, therefore we must assign "null". output: "{{{{"sepals": null}}}}"
                                
    ### Example 5 ### where the value is multiple numbers
    description: "Stems clustered, rarely solitary"
    rules: "Stems solitary (0); stems clustered (1)"
    code: "solclu"
    This description applied to multiple rules, therefore assign both rules. output: "{{{{"solclu": "0,1"}}}}"
""")