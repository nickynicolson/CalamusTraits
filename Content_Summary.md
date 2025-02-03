# Summary of the Content in this Repo

## Workflow

**Mermaid diagram made using the [Makefile](https://github.com/KewBridge/CalamusTraits/blob/main/Makefile). Shows dependencies and outputs for each file / script.**

```mermaid
graph TD
    %% Input files
    A[resources/appendix_1.txt]:::input --> E
    B[resources/appendix_2.txt]:::input --> E
    C[resources/calamus_monograph.pdf]:::input --> F
    D[resources/target_species.txt]:::input --> F

    %% Scripts
    E[clean_appendix.py]:::script
    F[extract_treatments.py]:::script

    %% Output files
    G[data/appendix_1.txt]:::output
    H[data/appendix_2.txt]:::output
    I[data/sentences.txt]:::output
    J[data/treatments.txt]:::output

    %% Dependencies for appendix 1
    E --> G

    %% Dependencies for appendix 2
    E --> H

    %% Dependencies for treatments
    F --> J

    %% Dependencies for sentences
    F --> I

    %% Styling
    classDef input fill:#fff3cd,stroke:#333,stroke-width:2px,rx:15px,ry:15px;
    classDef script fill:#cce5ff,stroke:#333,stroke-width:2px,rx:15px,ry:15px;
    classDef output fill:#d4edda,stroke:#333,stroke-width:2px,rx:15px,ry:15px;
```

```mermaid
    block-beta
    a("Input Files") b("Scripts") c("Output Files")

    style a fill:#fff3cd,stroke:#333,stroke-width:2px,rx:15px,ry:15px;
    style b fill:#cce5ff,stroke:#333,stroke-width:2px,rx:15px,ry:15px;
    style c fill:#d4edda,stroke:#333,stroke-width:2px,rx:15px,ry:15px;
```

## What Does Each Script do?

| File Name | Description |
| --------- | ----------- |
| [clean_appendix.py](https://github.com/KewBridge/CalamusTraits/blob/main/clean_appendix.py) | Processes the appendices, combines them with the subject metadata, and converts them to csv files.   |
| [extract_treatments.py](https://github.com/KewBridge/CalamusTraits/blob/main/extract_treatments.py) | Identifies relevant sections of the monograph, extracts them, and outputs a csv of the taxonomic treatments. |
| [app1_extraction.py](https://github.com/KewBridge/CalamusTraits/blob/main/app1_extraction.py) | Extracts quantitative traits from species descriptions in the monograph. |
| [trait_extraction_app2.py](https://github.com/KewBridge/CalamusTraits/blob/main/trait_extraction_app2.py) | |
| [term_mapper.py](https://github.com/KewBridge/CalamusTraits/blob/main/term_mapper.py) | Used in [extract_treatments.py](https://github.com/KewBridge/CalamusTraits/blob/main/extract_treatments.py) and [clean_appendix.py](https://github.com/KewBridge/CalamusTraits/blob/main/clean_appendix.py). Standardises the subject names. |
