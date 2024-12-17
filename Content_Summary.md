# Summary of the Content in this Repo

## Workflow

**Mermaid diagram made using the [Makefile](https://github.com/KewBridge/CalamusTraits/blob/main/Makefile). Shows dependencies for each file / script.**

```mermaid
graph TD
    %% Input files
    A[resources/appendix_1.txt]
    B[resources/appendix_1_subjects.txt]
    C[resources/appendix_2.txt]
    D[resources/appendix_2_subjects.txt]
    E[resources/calamus_monograph.pdf]
    F[resources/target_species.txt]
    
    %% Scripts
    G[clean_appendix.py]
    H[extract_treatments.py]
    I[cat_sentences.py]

    %% Output files
    J[data/appendix_1.txt]
    K[data/appendix_2.txt]
    L[data/treatments.txt]
    M[data/sentences.txt]
    N[data/sentences_cat.txt]

    %% Dependencies for appendix 1
    A --> G
    B --> G
    G --> J

    %% Dependencies for appendix 2
    C --> G
    D --> G
    G --> K

    %% Dependencies for treatments
    E --> H
    F --> H
    H --> L

    %% Dependencies for sentences
    E --> H
    F --> H
    H --> M

    %% Dependencies for categorised sentences
    M --> I
    D --> I
    I --> N
```

## What Does Each Script do?

| File Name | Description |
| --------- | ----------- |
| [clean_appendix.py](https://github.com/KewBridge/CalamusTraits/blob/main/clean_appendix.py) | Processes the appendices, combines them with the subject metadata, and converts them to csv files.   |
| [extract_treatments.py](https://github.com/KewBridge/CalamusTraits/blob/main/extract_treatments.py) | Identifies relevant sections of the monograph, extracts them, and outputs a csv of the taxonomic treatments. |
| [sentences_cat.py](https://github.com/KewBridge/CalamusTraits/blob/main/sentences_cat.py) | Uses an LLM to categorise each sentences in the species descriptions, and outputs a csv of sentences followed by their category. |
| [trait_extraction_app1.py](https://github.com/KewBridge/CalamusTraits/blob/main/trait_extraction_app1.py) |  |
| [trait_extraction_app2.py](https://github.com/KewBridge/CalamusTraits/blob/main/trait_extraction_app2.py) | |
