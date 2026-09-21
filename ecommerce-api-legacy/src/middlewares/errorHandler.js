'use strict';

// Centralized error handler. Never leaks stack traces or internal details.
function errorHandler(err, req, res, next) {
  const status = err.status || 500;
  if (status >= 500) {
    // Structured internal log; no PII/PAN/secrets.
    console.error(
      JSON.stringify({
        level: 'error',
        message: err.message,
        status,
        path: req.originalUrl,
      })
    );
  }
  const clientMessage = status >= 500 ? 'Erro interno' : err.message;
  res.status(status).json({ error: clientMessage, code: status });
}

function notFound(req, res) {
  res.status(404).json({ error: 'Not Found', code: 404 });
}

module.exports = { errorHandler, notFound };
