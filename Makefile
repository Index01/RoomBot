frontend_build:
	docker build -t roombaht:latest frontend/
	docker run -u node \
		-v $(shell pwd)/frontend:/src \
		-v $(shell pwd)/build:/build \
		roombaht:latest build

frontend_dev:
	docker run -ti \
		-p 3000:3000 \
		-u node \
		-v $(shell pwd)/frontend/:/app roombaht:latest

backend_dev:
	test -d backend/.env || \
		( mkdir backend/.env && \
			virtualenv -p python3 backend/.env) && \
		backend/.env/bin/python3 -m pip install --upgrade pip
	backend/.env/bin/pip install -r requirements.txt --upgrade	
	cd backend && \
		python manage.py makemigrations && \
		python manage.py migrate && \
		python manage.py runserver 0.0.0.0:8080
