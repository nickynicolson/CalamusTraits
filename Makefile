data/appendix_1.txt: clean_appendix.py resources/appendix_1.txt
	mkdir -p data
	python $^ --quantitative $@

data/appendix_2.txt: clean_appendix.py resources/appendix_2.txt
	mkdir -p data
	python $^ $@

appendices: data/appendix_1.txt data/appendix_2.txt

data/treatments.txt: extract_treatments.py resources/calamus_monograph.pdf resources/target_species.txt
	mkdir -p data
	python $^ $@

data/sentences.txt: extract_treatments.py resources/calamus_monograph.pdf resources/target_species.txt
	mkdir -p data
	python $^ --sentences $@

data/formatted_supp_data.csv: format_supplementary_data.py resources/Ceratolobus.xlsx
	mkdir -p data
	python $^ $@

treatments: data/treatments.txt

sentences: data/sentences.txt

supp: data/formatted_supp_data.csv

all: data/appendix_1.txt data/appendix_2.txt data/treatments.txt data/sentences.txt data/formatted_supp_data.csv

clean:
	rm -rf data