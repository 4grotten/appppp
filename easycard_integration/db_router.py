"""Database router for EasyCard integration.

Routes all easycard_integration models to the 'easycard' database.
This database is READ-ONLY from Apofiz perspective.
"""


class EasyCardRouter:
    """Database router for EasyCard models.

    All models in easycard_integration app are routed to 'easycard' database.
    Migrations are disabled (managed = False in models).
    """

    app_label = "easycard_integration"
    db_name = "easycard"

    def db_for_read(self, model, **hints):
        """Route read operations to easycard database."""
        if model._meta.app_label == self.app_label:
            return self.db_name
        return None

    def db_for_write(self, model, **hints):
        """Route write operations to easycard database.

        Note: Models should be read-only, but we route writes
        to the same database for consistency.
        """
        if model._meta.app_label == self.app_label:
            return self.db_name
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations between EasyCard models."""
        if (
            obj1._meta.app_label == self.app_label
            or obj2._meta.app_label == self.app_label
        ):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Prevent migrations for EasyCard models.

        EasyCard database schema is managed by the EasyCard server.
        """
        if app_label == self.app_label:
            return False
        if db == self.db_name:
            return False
        return None
