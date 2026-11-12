#!/usr/bin/env python3
"""Script de aprovisionamiento declarativo de servicios AWS en LocalStack con Boto3 (Semana 10 - IaC).

Crea de forma automatizada los recursos cloud locales necesarios:
- Bucket S3 para documentos financieros de empresas: `prestamos-documentos-bucket`
- Cola SQS principal para solicitudes de scoring asíncronas: `prestamos-evaluacion-queue`
- Cola SQS de mensajes fallidos (Dead-Letter Queue): `prestamos-evaluacion-dlq`
"""

import os
import sys
import argparse
import boto3
from botocore.exceptions import ClientError


# Nombres de recursos estándar
S3_BUCKET_NAME = os.getenv("S3_DOCS_BUCKET", "prestamos-documentos-bucket")
SQS_QUEUE_NAME = os.getenv("SQS_EVALUATION_QUEUE", "prestamos-evaluacion-queue")
SQS_DLQ_NAME = os.getenv("SQS_EVALUATION_DLQ", "prestamos-evaluacion-dlq")


def get_aws_clients(endpoint_url: str, region: str):
    """Crea clientes boto3 configurados para LocalStack o AWS."""
    session = boto3.session.Session(
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
        region_name=region,
    )
    s3_client = session.client("s3", endpoint_url=endpoint_url)
    sqs_client = session.client("sqs", endpoint_url=endpoint_url)
    return s3_client, sqs_client


def provision_s3_bucket(s3_client, bucket_name: str, region: str) -> str:
    """Crea de forma idempotente el bucket S3 para almacenamiento de documentos."""
    print(f"[IaC-LocalStack] Verificando existencia de bucket S3: '{bucket_name}'...")
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"[IaC-LocalStack] El bucket S3 '{bucket_name}' ya existe.")
    except ClientError:
        print(f"[IaC-LocalStack] Creando bucket S3: '{bucket_name}' en región '{region}'...")
        if region == "us-east-1":
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": region},
            )
        print(f"[IaC-LocalStack] Bucket S3 '{bucket_name}' aprovisionado exitosamente.")
    return bucket_name


def provision_sqs_queues(sqs_client, queue_name: str, dlq_name: str) -> dict:
    """Crea colas SQS principal y Dead Letter Queue (DLQ)."""
    # 1. Crear DLQ primero
    print(f"[IaC-LocalStack] Aprovisionando SQS DLQ: '{dlq_name}'...")
    dlq_res = sqs_client.create_queue(
        QueueName=dlq_name,
        Attributes={
            "MessageRetentionPeriod": "1209600"  # 14 días
        },
    )
    dlq_url = dlq_res["QueueUrl"]
    print(f"[IaC-LocalStack] DLQ disponible en: {dlq_url}")

    # 2. Crear cola principal
    print(f"[IaC-LocalStack] Aprovisionando SQS Principal: '{queue_name}'...")
    queue_res = sqs_client.create_queue(
        QueueName=queue_name,
        Attributes={
            "VisibilityTimeout": "60",
            "MessageRetentionPeriod": "86400",  # 1 día
        },
    )
    queue_url = queue_res["QueueUrl"]
    print(f"[IaC-LocalStack] Cola principal disponible en: {queue_url}")

    return {"main_queue_url": queue_url, "dlq_url": dlq_url}


def main():
    parser = argparse.ArgumentParser(description="Aprovisionamiento IaC en LocalStack con Boto3")
    parser.add_argument(
        "--endpoint-url",
        default=os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566"),
        help="URL del endpoint de LocalStack (default: http://localhost:4566)",
    )
    parser.add_argument(
        "--region",
        default=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
        help="Región AWS (default: us-east-1)",
    )
    args = parser.parse_args()

    print("=================================================================")
    print(f"=== [IaC] Inicializando Servicios AWS en LocalStack ({args.endpoint_url}) ===")
    print("=================================================================")

    try:
        s3_client, sqs_client = get_aws_clients(args.endpoint_url, args.region)
        bucket = provision_s3_bucket(s3_client, S3_BUCKET_NAME, args.region)
        queues = provision_sqs_queues(sqs_client, SQS_QUEUE_NAME, SQS_DLQ_NAME)

        print("\n✅ [IaC] Aprovisionamiento LocalStack completado con éxito:")
        print(f" - S3 Bucket: {bucket}")
        print(f" - SQS Cola Principal: {queues['main_queue_url']}")
        print(f" - SQS Dead Letter Queue: {queues['dlq_url']}")
        print("=================================================================\n")
        return 0
    except Exception as exc:
        print(f"❌ [IaC-LocalStack][ERROR] Falló el aprovisionamiento: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

