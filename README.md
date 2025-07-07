# Duff Beer Inc. ETL Pipeline

Este repositorio contiene la solución completa para la prueba técnica de Duff Beer Inc., que incluye:

- Infraestructura como código (Terraform) para S3, IAM, Glue y API Gateway
- Script PySpark para AWS Glue (`transform.py`)
- Ejecución de ETL: CSV → Parquet particionado
- Consulta en Athena
- API REST en API Gateway + Lambda para exponer datos
- Pre-commit, tests y entorno Python modular

---

##  Contenido

```plaintext
sdet-base/
├─ infra/terraform/       # Terraform para S3, IAM, Glue Job y API Gateway
│   ├─ main.tf
│   ├─ variables.tf
│   ├─ outputs.tf
│   └─ api/               # Módulo Terraform para Lambda + API GW
├─ glue-scripts/
│   └─ transform.py       # ETL PySpark para Glue
├─ lambda/
│   ├─ handler.py         # Lambda Python para API
│   └─ build.sh           # Script de empaquetado
├─ data/
│   └─ orders.csv         # CSV de ejemplo
├─ src/                   # Código Python del CLI / librerías
├─ tests/                 # Tests con pytest
├─ .pre-commit-config.yaml# Hooks para lint, fmt, seguridad
├─ .gitignore
├─ setup.py               # Configuración del paquete Python
└─ README.md              # Este fichero


---

##  Uso completo (end-to-end)

Estos pasos cubren desde clonar el repo hasta desplegar infra, ejecutar ETL y probar la API REST.

```bash
# 1. Clonar y entrar en el proyecto
git clone https://github.com/cloud-architect-ia/sdet-base.git
cd sdet-base

# 2. Preparar entorno Python
python -m venv .venv
# Linux / Mac
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. Configurar credenciales AWS
cat > .env <<EOF
AWS_ACCESS_KEY_ID=TU_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=TU_SECRET_ACCESS_KEY
AWS_DEFAULT_REGION=us-east-1
EOF

# 4. Desplegar infra con Terraform
cd infra/terraform
terraform init
terraform apply -auto-approve

# Se mostrarán estos outputs:
#   glue_job_name
#   input_bucket
#   output_bucket
#   orders_api_invoke_url

# 5. Empaquetar y desplegar Lambda de la API
cd ../../lambda
./build.sh
cd ../infra/terraform/api
terraform init
terraform apply -auto-approve

# 6. Subir ETL y datos a S3
cd ../
INPUT_BUCKET=$(terraform output -raw input_bucket)
OUTPUT_BUCKET=$(terraform output -raw output_bucket)
aws s3 cp ../../glue-scripts/transform.py s3://$INPUT_BUCKET/scripts/transform.py
aws s3 cp ../../data/orders.csv      s3://$INPUT_BUCKET/orders.csv

# 7. Ejecutar Glue Job
cd ../
JOB_NAME=$(terraform output -raw glue_job_name)
aws glue start-job-run \
  --job-name "$JOB_NAME" \
  --arguments '{"--INPUT":"s3://'"$INPUT_BUCKET"'/orders.csv","--OUTPUT":"s3://'"$OUTPUT_BUCKET"'/parquet/","--TempDir":"s3://'"$INPUT_BUCKET"'/temp/"}'

# 8. Verificar Parquet en S3
aws s3 ls s3://$OUTPUT_BUCKET/parquet/status=created/
aws s3 ls s3://$OUTPUT_BUCKET/parquet/status=delivered/

# 9. Consulta en Athena
#   - Configura ubicación de resultados en s3://$OUTPUT_BUCKET/athena-results/
#   - Ejecuta en Athena:
#
#     CREATE DATABASE IF NOT EXISTS sdet_demo;
#     CREATE EXTERNAL TABLE IF NOT EXISTS sdet_demo.orders_parquet (
#       client_id INT, client_name STRING, order_id INT,
#       product_id INT, product_description STRING,
#       product_price DOUBLE, product_ccf INT,
#       product_volume DOUBLE, point_of_sale_channel STRING
#     )
#     PARTITIONED BY (status STRING)
#     STORED AS PARQUET
#     LOCATION 's3://'"$OUTPUT_BUCKET"'/parquet/';
#
#     MSCK REPAIR TABLE sdet_demo.orders_parquet;
#     SELECT * FROM sdet_demo.orders_parquet LIMIT 10;

# 10. Probar API REST
API_URL=$(terraform output -raw orders_api_invoke_url)
curl "$API_URL/orders/1001"


###  Evidencias (cd ../../Doc)

- **Buckets S3**: orders.csv, transform.py y parquet/status=*
- **Glue Job**: estado SUCCEEDED (CloudWatch Logs)
- **Athena**: `SELECT * … LIMIT 10` muestra datos particionados
- **API REST**: `GET /orders/1001` devuelve JSON con órdenes
