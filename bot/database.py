import aiosqlite
from datetime import datetime

DB_PATH = "salon.db"


async def init_db():
    """Создаёт таблицу записей при первом запуске."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                username    TEXT,
                full_name   TEXT,
                service     TEXT NOT NULL,
                master      TEXT NOT NULL,
                date        TEXT NOT NULL,
                time        TEXT NOT NULL,
                created_at  TEXT NOT NULL
            )
        """)
        await db.commit()


async def add_booking(
    user_id: int,
    username: str | None,
    full_name: str,
    service: str,
    master: str,
    date: str,
    time: str,
) -> int:
    """Сохраняет запись. Возвращает id новой строки."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO bookings (user_id, username, full_name, service, master, date, time, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, username, full_name, service, master, date, time,
             datetime.now().strftime("%Y-%m-%d %H:%M")),
        )
        await db.commit()
        return cursor.lastrowid


async def get_user_bookings(user_id: int) -> list[dict]:
    """Возвращает все активные записи пользователя."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM bookings WHERE user_id = ? ORDER BY date, time",
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_booking_by_id(booking_id: int) -> dict | None:
    """Возвращает запись по id или None если не найдена."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM bookings WHERE id = ?", (booking_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def delete_booking(booking_id: int, user_id: int) -> bool:
    """Удаляет запись. Проверяет, что она принадлежит этому пользователю."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM bookings WHERE id = ? AND user_id = ?",
            (booking_id, user_id),
        )
        await db.commit()
        # rowcount > 0 означает, что запись была найдена и удалена
        return cursor.rowcount > 0
