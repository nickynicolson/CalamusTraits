data/appendix_1.txt: clean_appendix.py resources/appendix_1.txt resources/appendix_1_subjects.txt
	mkdir -p data
	python $^ --quantitative $@

data/appendix_2.txt: clean_appendix.py resources/appendix_2.txt resources/appendix_2_subjects.txt
	mkdir -p data
	python $^ $@

data/treatments.txt: extract_treatments.py resources/calamus_monograph.pdf resources/target_species.txt
	mkdir -p data
	python $^ $@

data/sentences.txt: extract_treatments.py resources/calamus_monograph.pdf resources/target_species.txt
	mkdir -p data
	python $^ --sentences $@

treatments: data/treatments.txt

sentences: data/sentences.txt

data/sentences_cat.txt: cat_sentences.py data/sentences.txt resources/appendix_2_subjects.txt
	mkdir -p data
	python $^ $@

cat: data/sentences_cat.txt

all: data/appendix_1.txt data/appendix_2.txt data/treatments.txt data/sentences.txt data/sentences_cat.txt

clean:
	rm -rf data