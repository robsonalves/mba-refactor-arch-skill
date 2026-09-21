'use strict';

// Only layer that talks to the DB for users. All queries parameterized.
class UserRepository {
  constructor(db) {
    this.db = db;
  }

  findByEmail(email) {
    return this.db.prepare('SELECT id FROM users WHERE email = ?').get(email);
  }

  create(name, email, passwordHash) {
    const info = this.db
      .prepare('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)')
      .run(name, email, passwordHash);
    return info.lastInsertRowid;
  }

  findById(id) {
    return this.db.prepare('SELECT id, name, email FROM users WHERE id = ?').get(id);
  }

  deleteById(id) {
    return this.db.prepare('DELETE FROM users WHERE id = ?').run(id);
  }
}

module.exports = UserRepository;
