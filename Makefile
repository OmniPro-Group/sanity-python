test:
	python -m unittest -v

coverage:
	coverage run -m unittest discover
	coverage report --skip-empty --sort=name --precision=0
