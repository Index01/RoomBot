.PHONY = frontend_build frontend_dev frontend_archive frontend_clean \
	backend_dev backend_archive backend_clean backend_migrations backend_env \
	archive sample_data

frontend_build:
	test -d frontend/public/layouts || ./scripts/fetch-images
	docker build -t roombaht:latest frontend/
	docker run -u node \
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

backend_migrations: backend_env
	backend/venv/bin/python3 backend/manage.py makemigrations

sample_data:
	backend/venv/bin/python3 backend/manage.py create_rooms samples/exampleBallysRoomList.csv --force
	backend/venv/bin/python3 backend/manage.py create_rooms samples/exampleHardrockRoomList.csv --force --preserve --hotel-name=hardrock
	backend/venv/bin/python3 backend/manage.py create_staff samples/exampleMainStaffList.csv

archive: backend_archive frontend_archive

backend_archive:
	mkdir -p build && \
	cp -r backend build/roombaht-backend && \
	./scripts/version > build/roombaht-backend/reservations/version && \
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
