python3 -m venv /tmp/myenv
source /tmp/myenv/bin/activate
pip install -r requirements.txt
./contract-to-openapi.py ../datacontract/personen.yaml  --out ./generated/openapi-spec.yaml