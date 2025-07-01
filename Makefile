# Extract appendices data
data/appendix_1.txt: scripts/monograph_text_extraction/clean_appendix.py resources/appendix_1.txt
	mkdir -p data
	python $^ --quantitative $@

data/appendix_2.txt: scripts/monograph_text_extraction/clean_appendix.py resources/appendix_2.txt
	mkdir -p data
	python $^ $@

appendices: data/appendix_1.txt data/appendix_2.txt

# Extract treatments and sentences for ceratolobus group
data/treatments.txt: scripts/monograph_text_extraction/extract_treatments.py resources/calamus_monograph.pdf resources/ceratolobus_target_species.txt
	mkdir -p data
	python $^ $@

data/sentences.txt: scripts/monograph_text_extraction/extract_treatments.py resources/calamus_monograph.pdf resources/ceratolobus_target_species.txt
	mkdir -p data
	python $^ --sentences $@

treatments: data/treatments.txt

sentences: data/sentences.txt

monograph_data: appendices treatments sentences

# Ceratolobus description generation
ceratolobus_outputs/formatted_supp_data.csv ceratolobus_outputs/supp_data_multi.csv: resources/Ceratolobus.xlsx
	mkdir -p ceratolobus_outputs
	python -m scripts.description_generation.format_supplementary_data $< ceratolobus_outputs/supp_data_multi.csv ceratolobus_outputs/formatted_supp_data.csv

ceratolobus_outputs/app1_descriptions.csv: data/appendix_1.txt ceratolobus_outputs/formatted_supp_data.csv
	mkdir -p ceratolobus_outputs
	python -m scripts.description_generation.app1_descriptions $^ ceratolobus_outputs/app1_descriptions.csv

ceratolobus_outputs/app2_descriptions.csv: data/appendix_2.txt
	mkdir -p ceratolobus_outputs
	python -m scripts.description_generation.app2_descriptions $< trials/ceratbolobus_trial/supp_data.csv trials/ceratbolobus_trial/supp_data_multi.csv ceratolobus_outputs/app2_descriptions.csv

# Generates full species descriptions
ceratolobus_outputs/final_combined_descriptions.csv: ceratolobus_outputs/app1_descriptions.csv ceratolobus_outputs/app2_descriptions.csv
	mkdir -p ceratolobus_outputs
	python -m scripts.description_generation.combine_descriptions $^ ceratolobus_outputs/final_combined_descriptions.csv

# Use the subject_sentences option to include the subject of each sentence in the final output
ceratolobus_outputs/subject_descriptions.csv: ceratolobus_outputs/app1_descriptions.csv ceratolobus_outputs/app2_descriptions.csv
	mkdir -p ceratolobus_outputs
	python -m scripts.description_generation.combine_descriptions $^ ceratolobus_outputs/final_combined_descriptions.csv --subject_sentences

ceratolobus_descriptions: ceratolobus_outputs/final_combined_descriptions.csv

# To extract quantitative data from the monograph
ceratbolobus_outputs/quantitative_traits.csv: data/sentences.txt data/appendix_1.txt
	mkdir -p ceratolobus_outputs
	python -m scripts.trait_extraction.app1_extraction $^ ceratolobus_outputs/quantitative_traits.csv

all: data/appendix_1.txt data/appendix_2.txt data/treatments.txt data/sentences.txt ceratolobus_descriptions ceratbolobus_outputs/quantitative_traits.csv

clean:
	rm -rf data ceratolobus_outputs