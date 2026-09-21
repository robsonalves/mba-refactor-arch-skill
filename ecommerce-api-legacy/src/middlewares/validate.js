'use strict';

const { body, param, validationResult } = require('express-validator');

// Boundary validation: returns a structured 400 instead of relying on the client.
function runValidation(req, res, next) {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ error: 'Bad Request', details: errors.array() });
  }
  next();
}

const checkoutRules = [
  body('usr').isString().trim().notEmpty(),
  body('eml').isEmail(),
  body('pwd').isString().notEmpty(),
  body('c_id').isInt({ min: 1 }).toInt(),
  body('card').isString().isLength({ min: 12, max: 19 }).matches(/^[0-9]+$/),
  runValidation,
];

const deleteUserRules = [param('id').isInt({ min: 1 }).toInt(), runValidation];

module.exports = { checkoutRules, deleteUserRules };
