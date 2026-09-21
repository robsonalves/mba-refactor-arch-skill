'use strict';

// Domain/HTTP error carrying a status code, handled centrally by the middleware.
class HttpError extends Error {
  constructor(status, message) {
    super(message);
    this.name = 'HttpError';
    this.status = status;
  }
}

module.exports = HttpError;
