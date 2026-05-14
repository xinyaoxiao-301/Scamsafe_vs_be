"""
scam_news.py - Database operations for scam news articles and tips
Uses psycopg2 with connection pooling, wrapped in asyncio.to_thread for async compatibility.
"""

import os
import asyncio
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional

# Global connection pool (synchronous)
_pool: Optional[pool.SimpleConnectionPool] = None


def _init_sync_pool() -> None:
    """Initialize the psycopg2 connection pool (synchronous)."""
    global _pool
    if _pool is None:
        database_url = "postgresql://neondb_owner:npg_0TCw8FVNpWmd@ep-blue-snow-anun3pw7-pooler.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
        if not database_url:
            raise EnvironmentError("DATABASE_URL environment variable not set")
        # Parse DATABASE_URL (postgresql://user:pass@host:port/db)
        # Use psycopg2's connection pool
        _pool = pool.SimpleConnectionPool(
            1, 20, dsn=database_url, cursor_factory=RealDictCursor
        )


async def init_db_pool() -> None:
    """Initialize the connection pool asynchronously (runs sync init in thread)."""
    await asyncio.to_thread(_init_sync_pool)


async def close_db_pool() -> None:
    """Close all connections in the pool."""
    global _pool
    if _pool:
        await asyncio.to_thread(_pool.closeall)
        _pool = None


async def get_news_list(limit: int = 10, language: str = "en") -> List[Dict[str, Any]]:
    """
    Fetch a list of scam news articles ordered by rank.
    Returns a list of dicts with keys: article_id, rank, title, published, source, url.

    For non-English languages, title is taken from scam_news_translations with a
    fallback to the English base row when no translation exists.
    """
    if _pool is None:
        await init_db_pool()

    def _fetch():
        conn = _pool.getconn()
        try:
            with conn.cursor() as cur:
                if language == "en":
                    cur.execute("""
                        SELECT article_id, rank, title, published, source, url
                        FROM scam_news
                        ORDER BY rank ASC
                        LIMIT %s
                    """, (limit,))
                else:
                    # COALESCE: use translation if available, otherwise fall back to English
                    cur.execute("""
                        SELECT
                            n.article_id,
                            n.rank,
                            COALESCE(t.title, n.title) AS title,
                            n.published,
                            n.source,
                            n.url
                        FROM scam_news n
                        LEFT JOIN scam_news_translations t
                            ON t.article_id = n.article_id
                            AND t.language_code = %s
                        ORDER BY n.rank ASC
                        LIMIT %s
                    """, (language, limit))
                return [dict(row) for row in cur.fetchall()]
        finally:
            _pool.putconn(conn)

    return await asyncio.to_thread(_fetch)


async def get_article_with_tips(article_id: int, language: str = "en") -> Optional[Dict[str, Any]]:
    """
    Fetch a single article by ID with its associated prevention tips.
    Returns dict with keys: article_id, rank, title, published, source, url, article_content, tips (list of strings).
    Returns None if article not found.

    For non-English languages, title and article_content are taken from
    scam_news_translations, and tip_text from scam_tips_translations, each with
    an English fallback when no translation row exists.
    """
    if _pool is None:
        await init_db_pool()

    def _fetch():
        conn = _pool.getconn()
        try:
            with conn.cursor() as cur:
                if language == "en":
                    cur.execute("""
                        SELECT article_id, rank, title, published, source, url, article_content
                        FROM scam_news
                        WHERE article_id = %s
                    """, (article_id,))
                else:
                    cur.execute("""
                        SELECT
                            n.article_id,
                            n.rank,
                            COALESCE(t.title, n.title) AS title,
                            n.published,
                            n.source,
                            n.url,
                            COALESCE(t.article_content, n.article_content) AS article_content
                        FROM scam_news n
                        LEFT JOIN scam_news_translations t
                            ON t.article_id = n.article_id
                            AND t.language_code = %s
                        WHERE n.article_id = %s
                    """, (language, article_id))

                article = cur.fetchone()
                if not article:
                    return None
                article_dict = dict(article)

                # Fetch associated tips with translation fallback
                if language == "en":
                    cur.execute("""
                        SELECT tip_text
                        FROM scam_tips
                        WHERE article_id = %s
                        ORDER BY tip_id
                    """, (article_id,))
                    tips = [row['tip_text'] for row in cur.fetchall()]
                else:
                    cur.execute("""
                        SELECT COALESCE(tt.tip_text, st.tip_text) AS tip_text
                        FROM scam_tips st
                        LEFT JOIN scam_tips_translations tt
                            ON tt.tip_id = st.tip_id
                            AND tt.language_code = %s
                        WHERE st.article_id = %s
                        ORDER BY st.tip_id
                    """, (language, article_id))
                    tips = [row['tip_text'] for row in cur.fetchall()]

                article_dict['tips'] = tips
                return article_dict
        finally:
            _pool.putconn(conn)

    return await asyncio.to_thread(_fetch)