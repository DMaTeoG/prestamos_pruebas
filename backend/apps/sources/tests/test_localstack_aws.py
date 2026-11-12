"""Pruebas unitarias y de integración para la provisión de IaC con LocalStack y Boto3 (Semana 10).

Estructuradas estrictamente bajo el patrón AAA (Arrange, Act, Assert).
"""

from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError
from scripts.init_localstack import provision_s3_bucket, provision_sqs_queues

# ==============================================================================
# Semana 1: Patrón AAA
# Semana 10: Infraestructura como Código (LocalStack AWS + Boto3)
# ==============================================================================


class TestLocalStackAwsProvisioning:
    """Suite de pruebas para validar aprovisionamiento declarativo de S3 y SQS."""

    def test_provision_s3_bucket_creates_when_not_exists_aaa(self):
        """Verifica que un bucket inexistente se crea correctamente siguiendo el patrón AAA."""
        # Arrange: Mock del cliente S3 simulando que el bucket no existe en primera instancia
        mock_s3 = MagicMock()
        mock_s3.head_bucket.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}}, "HeadBucket"
        )
        bucket_name = "test-empresa-documentos-bucket"
        region = "us-east-1"

        # Act: Ejecución de la función de aprovisionamiento declarativo
        result_bucket = provision_s3_bucket(mock_s3, bucket_name, region)

        # Assert: Verificación de llamadas exactas y resultado
        assert result_bucket == bucket_name
        mock_s3.create_bucket.assert_called_once_with(Bucket=bucket_name)

    def test_provision_s3_bucket_idempotent_when_already_exists_aaa(self):
        """Verifica idempotencia: si el bucket existe, no intenta recrearlo."""
        # Arrange: Simulación de bucket existente (head_bucket exitoso)
        mock_s3 = MagicMock()
        mock_s3.head_bucket.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}
        bucket_name = "existing-empresa-bucket"
        region = "us-east-1"

        # Act
        result_bucket = provision_s3_bucket(mock_s3, bucket_name, region)

        # Assert
        assert result_bucket == bucket_name
        mock_s3.create_bucket.assert_not_called()

    @pytest.mark.parametrize(
        "region,expected_config",
        [
            ("us-west-2", {"LocationConstraint": "us-west-2"}),
            ("sa-east-1", {"LocationConstraint": "sa-east-1"}),
            ("eu-west-1", {"LocationConstraint": "eu-west-1"}),
        ],
    )
    def test_provision_s3_bucket_multi_region_parametrized_aaa(self, region, expected_config):
        """Verificación parametrizada (@pytest.mark.parametrize) de regiones S3 no us-east-1."""
        # Arrange
        mock_s3 = MagicMock()
        mock_s3.head_bucket.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}}, "HeadBucket"
        )
        bucket_name = f"regional-bucket-{region}"

        # Act
        provision_s3_bucket(mock_s3, bucket_name, region)

        # Assert
        mock_s3.create_bucket.assert_called_once_with(
            Bucket=bucket_name,
            CreateBucketConfiguration=expected_config,
        )

    def test_provision_sqs_queues_creates_main_and_dlq_aaa(self):
        """Verifica la creación de la cola principal y su respectiva DLQ en SQS."""
        # Arrange
        mock_sqs = MagicMock()
        mock_sqs.create_queue.side_effect = [
            {"QueueUrl": "http://localstack:4566/000000000000/prestamos-evaluacion-dlq"},
            {"QueueUrl": "http://localstack:4566/000000000000/prestamos-evaluacion-queue"},
        ]
        main_queue = "prestamos-evaluacion-queue"
        dlq = "prestamos-evaluacion-dlq"

        # Act
        urls = provision_sqs_queues(mock_sqs, main_queue, dlq)

        # Assert
        assert "main_queue_url" in urls
        assert "dlq_url" in urls
        assert urls["main_queue_url"].endswith(main_queue)
        assert urls["dlq_url"].endswith(dlq)
        assert mock_sqs.create_queue.call_count == 2

