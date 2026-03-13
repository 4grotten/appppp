import io
import json
import logging

import pandas as pd
from django.core.files.base import ContentFile
from django.utils import timezone

logger = logging.getLogger(__name__)


class CatalogExportService:
    @classmethod
    def export_latest_catalog_to_excel(cls, organization):
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
