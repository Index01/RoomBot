.PHONY = frontend_build frontend_dev frontend_archive backend_dev backend_archive archive
ifdef DEV
	API_ENDPOINT := "http://localhost:8000/"
else
	API_ENDPOINT := $(shell ./scripts/secrets show REACT_APP_API_ENDPOINT)
endif

frontend_build:
	docker build -t roombaht:latest frontend/
	docker run -u node \
		-e REACT_APP_API_ENDPOINT=$(API_ENDPOINT) \
		-v $(shell pwd)/frontend:/src \
		-v $(shell pwd)/build:/build \
		roombaht:latest build

frontend_dev: frontend_build
	docker run -ti \
		-p 3000:3000 \
		-u node \
		-v $(shell pwd)/frontend/:/app roombaht:latest

backend_dev:
	test -d backend/venv || \
		( mkdir backend/venv && \
			virtualenv -p python3.8 backend/venv) && \
		backend/venv/bin/python3 -m pip install --upgrade pip
	backend/venv/bin/pip install -r backend/requirements.txt --upgrade	

	test -f dev.env || \
		(scripts/secrets decrypt)
	./scripts/start_backend_dev.sh

archive: backend_archive frontend_archive

backend_archive:
	mkdir -p build && \
		tar -cvz \
			--exclude "__pycache__" \
			--exclude ".env" \
			--exclude "venv" \
			--exclude "db.sqlite3" \
			--transform 's,^backend,roombaht-backend,' \
			backend > build/roombaht-backend.tgz

frontend_archive: frontend_build
	mkdir -p build && \
		tar -cvz \
			-C frontend \
			--transform 's,^build,roombaht-frontend,' \
			build > build/roombaht-frontend.tgz
