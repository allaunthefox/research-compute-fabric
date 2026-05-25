#!/usr/bin/env python3
import bcrypt, sqlite3, sys

pw = sys.argv[1]
db = sys.argv[2]

hashed = bcrypt.hashpw(pw.encode(), bcrypt.gensalt(rounds=8)).decode()
hashed_2a = hashed.replace('$2b$', '$2a$')
print('Hash:', hashed_2a)

c = sqlite3.connect(db)
c.execute("UPDATE users SET pash = ? WHERE username = ?", (hashed_2a, "rootallaun"))
c.commit()
c.close()
print('Updated rootallaun password')
