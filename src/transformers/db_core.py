import psycopg

from config.settings import DATABASE_URL

def upsert_user(user_id: str, user_email: str | None):  
    """Insert or update user info based on primary key of user_id
    
    Args:
        user_id (str): "sub" user ID from cred
        user_email (str | None): optional email from cred
    """    
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO users (id, email) VALUES (%s, %s) "
                        "ON CONFLICT (id) DO UPDATE "
                        "SET email = EXCLUDED.email, updated_at = NOW()", (user_id, user_email))