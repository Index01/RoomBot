.PHONY = frontend_build frontend_dev frontend_archive frontend_clean \
	backend_dev backend_archive backend_clean backend_env \
	archive

ifdef API_ENV
ifeq ($(API_ENV), dev)
	API_ENDPOINT := "http://localhost:8000/"
else
	API_ENDPOINT := $(shell ./scripts/secrets show $(API_ENV) REACT_APP_API_ENDPOINT)
endif
else
	API_ENDPOINT := $(shell ./scripts/secrets show prod REACT_APP_API_ENDPOINT)
endif


frontend_build:
	test -d frontend/public/layouts || ./scripts/fetch-images
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

frontend_clean:
	rm -rf build/roombaht-frontend.tgz frontend/public/layouts

backend_env:
	test -d backend/venv || \
		( mkdir backend/venv && \
			virtualenv -p python3.8 backend/venv) && \
		backend/venv/bin/python3 -m pip install --upgrade pip
	backend/venv/bin/pip install \
		-r backend/requirements.txt \
		-r backend/requirements-dev.txt \
		--upgrade

backend_dev: backend_env
	./scripts/start_backend_dev.sh

backend_clean:
	rm -rf backend/db.sqlite3 build/roombaht-backend.tgz

archive: backend_archive frontend_archive

backend_archive:
	mkdir -p build && \
	cp -r backend build/roombaht-backend && \
	tar -cvz \
		-C build \
		--exclude "__pycache__" \
		--exclude ".env" \
		--exclude "venv" \
		--exclude "db.sqlite3" \
		roombaht-backend > build/roombaht-backend.tgz && \
	rm -rf build/roombaht-backend

frontend_archive: frontend_build
	mkdir -p build && \
	cp -r frontend/build build/roombaht-frontend && \
	tar -cvz \
		-C build \
		roombaht-frontend > build/roombaht-frontend.tgz && \
	rm -rf build/roombaht-frontend
