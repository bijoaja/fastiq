# FAQ (Frequently Asked Questions)

> **Language:** English | [Indonesian](../id/FAQ.md)

**Q: Why are SQLAlchemy Model files not placed inside business modules (e.g., `app/modules/users/models.py`)?**
A: So that Alembic can easily track database models and avoid *circular import* issues when there are *foreign key* relationships across modules. By placing them in `app/models/`, model registration to SQLAlchemy metadata becomes centralized and clean.

**Q: How do I add a new business module?**
A: Simply create a new folder in `app/modules/<module_name>/` containing `router.py`, `service.py`, `repository.py`, and `schemas.py`. Define your new database model in `app/models/<model_name>.py` and register it in `app/models/__init__.py`. Then register the new router in `app/main.py`. You don't need to modify or touch any files in the `app/core/` folder.
