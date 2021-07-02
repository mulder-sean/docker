LABEL description="Execute gradlew"
COPY code code
WORKDIR /code/@FOLDER@
RUN . /etc/environment && @EXEC@ --no-build-cache @OPTS@
