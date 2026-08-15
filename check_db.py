r"""Diagnóstico: ¿mi máquina conecta a la Supabase del .env?

Uso (PowerShell, raíz del proyecto):
    .\.venv\Scripts\python.exe check_db.py

Si dice OK -> usa Supabase normal, no necesitas SQLite local.
"""
import asyncio

from sqlalchemy import text

from app.core.database import engine, db_url


async def main() -> None:
    print("Probando conexión a:", db_url)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        print("\n✅ Supabase CONECTA. No necesitas la SQLite local:")
        print("   corre la API y el bot sin tocar DATABASE_URL (usa el .env).")
    except Exception as e:  # noqa: BLE001
        print("\n❌ NO conecta:", type(e).__name__, "-", str(e)[:180])
        print("   Causas típicas:")
        print("   1) La contraseña del DATABASE_URL tiene un '@' sin escapar")
        print("      ('jo@quin...' debe ir como 'jo%40quin...').")
        print("   2) El host directo db.<ref>.supabase.co no resuelve desde aquí;")
        print("      Supabase suele requerir el POOLER (aws-0-<region>.pooler.supabase.com:6543).")
        print("   Mientras tanto: usa la SQLite local con setup_local_db.py.")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
