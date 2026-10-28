# FAQ (Frequently Asked Questions)

> **Bahasa:** Indonesia | [English](../en/FAQ.md)

**T: Mengapa file SQLAlchemy Model tidak diletakkan di dalam modul bisnis (misalnya di `app/modules/users/models.py`)?**
J: Agar Alembic dapat melacak model database dengan mudah dan menghindari isu *circular imports* saat terdapat relasi *foreign key* antar model yang berbeda modul. Dengan meletakkannya di `app/models/`, pendaftaran model ke metadata SQLAlchemy menjadi tersentralisasi dan rapi.

**T: Bagaimana cara menambahkan modul bisnis baru?**
J: Anda hanya perlu membuat folder baru di `app/modules/<nama_modul>/` yang berisi `router.py`, `service.py`, `repository.py`, dan `schemas.py`. Definisikan model database baru Anda di `app/models/<nama_model>.py` dan daftarkan di `app/models/__init__.py`. Kemudian daftarkan router baru tersebut di `app/main.py`. Anda tidak perlu mengubah atau menyentuh berkas di folder `app/core/`.
