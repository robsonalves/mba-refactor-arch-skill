'use strict';

require('dotenv').config();

// All configuration and secrets come from the environment. Nothing hardcoded.
const config = {
  port: parseInt(process.env.PORT || '3000', 10),
  jsonBodyLimit: process.env.JSON_BODY_LIMIT || '100kb',
  corsOrigins: (process.env.CORS_ORIGINS || '')
    .split(',')
    .map((origin) => origin.trim())
    .filter(Boolean),
  bcryptRounds: parseInt(process.env.BCRYPT_ROUNDS || '10', 10),
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
  dbPath: process.env.DB_PATH || ':memory:',
};

module.exports = config;
