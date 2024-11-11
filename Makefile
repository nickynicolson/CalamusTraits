data/appendix_1.txt: clean_appendix.py resources/appendix_1.txt
	mkdir -p data
	python $^ $@

data/appendix_2.txt: clean_appendix.py resources/appendix_2.txt
	mkdir -p data
	python $^ $@

data/calamus_monograph_treatments.txt: extract_treatments.py resources/calamus_monograph.pdf resources/target_species.txt
	mkdir -p data
	python $^ $@

treatments: data/calamus_monograph_treatments.txt

all: data/appendix_1.txt data/appendix_2.txt data/calamus_monograph_treatments.txt

clean:
	rm -rf data