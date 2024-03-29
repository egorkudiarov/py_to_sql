import psycopg2
import os

db = os.getenv("DATABASE")
u = os.getenv("LOGIN")
pw = os.getenv("PASSWORD")

class py_to_sql:
    def __init__(self, conn, cur):
        self.conn = conn
        self.cur = cur


    def drop_tables(self):
        self.cur.execute("""
            SELECT table_name
              FROM information_schema.tables
             WHERE table_schema = 'public'
            """)
        tables = self.cur.fetchall() 
        
        for table in tables:
            self.cur.execute("""
                DROP TABLE %s;
                """, table)
        self.conn.commit()


    def init_db(self, drop=False):
        if drop:
            self.drop_tables()
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS users(
                id SERIAL PRIMARY KEY,
                name VARCHAR(64),
                surname VARCHAR(128),
                email VARCHAR(128) UNIQUE
            );
            """)
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS phone_number(
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                number INTEGER NOT NULL UNIQUE
            );
            """)
        self.conn.commit()


    def add_phone_number(self, user_id, phone_number):
        if type(phone_number) != int:
            phone_number = int(''.join(filter(str.isdecimal, phone_number))) 

        self.cur.execute("""
            INSERT INTO phone_number(user_id, number) 
            VALUES (%s, %s);
        """, (user_id, phone_number))
        
        self.conn.commit()
        

    def add_user(self, name, surname, email, *phone_numbers):
        self.cur.execute("""
            INSERT INTO users(name, surname, email) 
            VALUES (%s, %s, %s)
            RETURNING id;
        """, (name, surname, email))
        user_id = self.cur.fetchone()[0]
        
        for phone_number in phone_numbers:
            phone_number = int(''.join(filter(str.isdecimal, phone_number)))
            self.add_phone_number(user_id, phone_number)
        

    def update_user(self, user_id, what_changed, values):
        try:
            len(what_changed) - len(values) == 0
        except ValueError:
            return 'Количество строк и значений не совпдает'
        
        for changed, value in zip(what_changed, values): 
            self.cur.execute("""
                UPDATE users SET %s=%s WHERE id=%s;
            """, (changed, value, user_id))
        
        self.conn.commit()


    def delete_phone_number(self, user_id, phone_number):
        self.cur.execute("""
            DELETE 
            FROM phone_number 
            WHERE number=%s;
            """, (phone_number,))   

        self.conn.commit()


    def delete_user(self, user_id):
        self.cur.execute("""
            DELETE 
            FROM phone_number 
            WHERE user_id=%s;
        """, (user_id,))

        self.cur.execute("""
            DELETE 
            FROM users 
            WHERE id=%s;
        """, (user_id,))

        self.conn.commit()
        

    def find_user(self, name, surname, email, number):
        self.cur.execute("""
            SELECT user_id
            FROM phone_number
            WHERE number = %s;
        """, (number,))
        user_id = self.cur.fetchone()[0]
        
        self.cur.execute("""
            SELECT *
                FROM users
                WHERE id = %s OR name = %s AND surname = %s AND email = %s;
        """, (user_id, name, surname, email))

        return [_[0] for _ in self.cur.fetchall()]


