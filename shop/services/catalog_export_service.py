import io
import json
import logging

import pandas as pd
from api_keys.models import AWSConfig
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone

logger = logging.getLogger(__name__)


class CatalogExportService:
    @staticmethod
    def _mask_key(raw_key):
        if not raw_key:
            return "not-set"
        key = str(raw_key)
        if len(key) <= 8:
            return f"{key[:2]}***{key[-2:]}"
        return f"{key[:4]}***{key[-4:]}"

    @classmethod
    def _log_aws_key_context(cls, organization_id):
        active_aws_config = AWSConfig.objects.filter(is_active=True).first()
        env_key = getattr(settings, "AWS_ACCESS_KEY_ID", None)

        if active_aws_config:
            logger.info(
                "[EXCEL_EXPORT] AWS key context org_id=%s source=db_active config_id=%s access_key_id=%s bucket=%s region=%s",
                organization_id,
                active_aws_config.id,
                cls._mask_key(active_aws_config.access_key_id),
                getattr(settings, "AWS_STORAGE_BUCKET_NAME", None),
                getattr(settings, "AWS_S3_REGION_NAME", None),
            )

            if env_key:
                logger.info(
                    "[EXCEL_EXPORT] AWS env fallback currently configured org_id=%s env_access_key_id=%s",
                    organization_id,
                    cls._mask_key(env_key),
                )
            return

        logger.info(
            "[EXCEL_EXPORT] AWS key context org_id=%s source=env_only access_key_id=%s bucket=%s region=%s",
            organization_id,
            cls._mask_key(env_key),
            getattr(settings, "AWS_STORAGE_BUCKET_NAME", None),
            getattr(settings, "AWS_S3_REGION_NAME", None),
        )

    @classmethod
    def export_latest_catalog_to_excel(cls, organization):
        cls._log_aws_key_context(organization.id)
        organization.refresh_from_db(fields=["catalog_file", "catalog_excel_file"])
        assistant = getattr(organization, "assistant", None)
        catalog_file = getattr(organization, "catalog_file", None)
        catalog_source = "organization"

        if not catalog_file and assistant:
            catalog_file = assistant.catalog_file
            catalog_source = "assistant_fallback"

        if not catalog_file:
            logger.info(
                f"[EXCEL_EXPORT] No catalog file source found for org_id={organization.id}"
            )
            return None

        logger.info(
            f"[EXCEL_EXPORT] Catalog source for org_id={organization.id}: {catalog_source}"
        )

        try:
            with catalog_file.open("rb") as catalog_stream:
                catalog_data = json.load(catalog_stream)
        except Exception as exc:
            logger.exception(
                "[EXCEL_EXPORT] Failed to read catalog JSON for org_id=%s source=%s file=%s error=%s",
                organization.id,
                catalog_source,
                getattr(catalog_file, "name", None),
                str(exc),
            )
            return None

        if isinstance(catalog_data, dict):
            catalog_data = [catalog_data]
        if not isinstance(catalog_data, list):
            return None

        dataframe = pd.DataFrame(catalog_data)
        if dataframe.empty:
            return None

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            dataframe.to_excel(writer, index=False, sheet_name="Catalog")

        output.seek(0)

        filename = f"catalog_{organization.id}.xlsx"

        organization_excel_file = getattr(organization, "catalog_excel_file", None)

        if organization_excel_file is not None:
            if organization.catalog_excel_file:
                organization.catalog_excel_file.delete(save=False)

            organization.catalog_excel_file.save(
                filename,
                ContentFile(output.getvalue()),
                save=True,
            )
            file_url = organization.catalog_excel_file.url
            logger.info(
                f"[EXCEL_EXPORT] Excel saved to Organization field for org_id={organization.id}"
            )
        elif assistant:
            if assistant.catalog_excel_file:
                assistant.catalog_excel_file.delete(save=False)

            assistant.catalog_excel_file.save(
                filename,
                ContentFile(output.getvalue()),
                save=True,
            )
            file_url = assistant.catalog_excel_file.url
            logger.info(
                f"[EXCEL_EXPORT] Excel saved to Assistant fallback field for org_id={organization.id}"
            )
        else:
            return None

        logger.info(f"✅ Catalog Excel exported for Organization ID: {organization.id}")
        logger.info(f"   📁 Filename: {filename}")
        logger.info(f"   🔗 URL: {file_url}")
        cache_buster = int(timezone.now().timestamp())
        separator = "&" if "?" in file_url else "?"
        return f"{file_url}{separator}v={cache_buster}"
