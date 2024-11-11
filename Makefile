data/appendix_1.txt: clean_appendix.py resources/appendix_1.txt
	mkdir -p data
	python $^ $@

data/appendix_2.txt: clean_appendix.py resources/appendix_2.txt
	mkdir -p data
	python $^ $@
