FROM python:3.9-slim

COPY --chmod=555 ./bin/* /usr/local/bin/

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

WORKDIR /app

COPY brefv-spec/ brefv-spec/
RUN mkdir brefv && \
    datamodel-codegen --input brefv-spec/envelope.json --input-file-type jsonschema --output brefv/envelope.py && \
    datamodel-codegen --input brefv-spec/messages --input-file-type jsonschema  --reuse-model --output brefv/messages


COPY main.py main.py

CMD ["python3", "main.py"]