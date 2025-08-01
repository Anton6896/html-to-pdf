# soffice

## docker

```bash
docker buildx build -f Dockerfile --platform linux/amd64 -t unoserver-worker:my .
docker run --platform linux/amd64 --rm -it -u 0  -v "$(pwd)/src":/src -w / unoserver-worker:my bash

docker tag unoserver-worker:my hub.cellosign.com/cellosign/unoserver-worker:local && \
docker push hub.cellosign.com/cellosign/unoserver-worker:local

```

## legacy api

```sh
curl -L -m 60 "http://localhost:8022/api/convert/xhtml/" \
-H "x-cellosign-request-id: ant-123-abcd" \
-F "file=@\"/Users/antonr/Documents/work/test_data/testing.xlsx\"" \
-o my.html
```

- has 2 options here
  - `http://localhost:8022/api/convert/?conformance=pdf/a`
  - `http://localhost:8022/api/convert/?conformance=pdf`
  
```sh
curl -L -m 60 'http://localhost:8022/api/convert/?conformance=pdf/a' \
-H 'x-cellosign-request-id: ant-123-abcd' \
-F 'file=@"/Users/antonr/Documents/work/test_data/1-page.docx"' \
-o my.pdf
```

## new API

### docx to pdf

```bash
FILE_PATH="/Users/antonr/Documents/work/test_data/1-page.docx"

# linux
BASE64_DOC=$(base64 -w 0 "$FILE_PATH")
# macos
BASE64_DOC=$(base64 -i "$FILE_PATH" | tr -d '\n')

JSON_PAYLOAD=$(jq -n --arg doc "$BASE64_DOC" --arg type "docx" \
  '{document: $doc, document_type: $type}')

curl -L -m 120 "http://localhost:8022/api/v1/convert_data/" \
  -H "x-cellosign-request-id: testing-testing-123123" \
  -H "Content-Type: application/json" \
  -d "$JSON_PAYLOAD"
```

### xlsx to html

```bash
FILE_PATH="/Users/antonr/Documents/work/test_data/testing.xlsx"

# linux
BASE64_DOC=$(base64 -w 0 "$FILE_PATH")
# macos
BASE64_DOC=$(base64 -i "$FILE_PATH" | tr -d '\n')

JSON_PAYLOAD=$(jq -n --arg doc "$BASE64_DOC" --arg type "xlsx" \
  '{document: $doc, document_type: $type}')

curl -L -m 120 "http://localhost:8022/api/v1/convert_data/" \
  -H "x-cellosign-request-id: testing-testing-123123" \
  -H "Content-Type: application/json" \
  -d "$JSON_PAYLOAD"
```
