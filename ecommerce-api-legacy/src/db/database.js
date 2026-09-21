'use strict';

const Database = require('better-sqlite3');

// Single place that owns the connection and the schema/seed (DDL).
function createDatabase(dbPath) {
  const db = new Database(dbPath);
  db.pragma('foreign_keys = ON');
  initSchema(db);
  seed(db);
  return db;
}

function initSchema(db) {
  db.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY,
      name TEXT NOT NULL,
      email TEXT NOT NULL,
      pass TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS courses (
      id INTEGER PRIMARY KEY,
      title TEXT NOT NULL,
      price REAL NOT NULL,
      active INTEGER NOT NULL
    );
    CREATE TABLE IF NOT EXISTS enrollments (
      id INTEGER PRIMARY KEY,
      user_id INTEGER NOT NULL,
      course_id INTEGER NOT NULL,
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
      FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS payments (
      id INTEGER PRIMARY KEY,
      enrollment_id INTEGER NOT NULL,
      amount REAL NOT NULL,
      status TEXT NOT NULL,
      FOREIGN KEY (enrollment_id) REFERENCES enrollments(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS audit_logs (
      id INTEGER PRIMARY KEY,
      action TEXT NOT NULL,
      created_at DATETIME NOT NULL
    );
  `);
}

function seed(db) {
  const userCount = db.prepare('SELECT COUNT(*) AS c FROM users').get().c;
  if (userCount > 0) return;

  const seedTx = db.transaction(() => {
    db.prepare('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)').run(
      'Leonan',
      'leonan@fullcycle.com.br',
      // Seed placeholder hash; real password never stored in plaintext.
      'seed-disabled-login'
    );
    const insertCourse = db.prepare(
      'INSERT INTO courses (title, price, active) VALUES (?, ?, ?)'
    );
    insertCourse.run('Clean Architecture', 997.0, 1);
    insertCourse.run('Docker', 497.0, 1);
    db.prepare('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)').run(1, 1);
    db.prepare(
      'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)'
    ).run(1, 997.0, 'PAID');
  });
  seedTx();
}

module.exports = { createDatabase };
