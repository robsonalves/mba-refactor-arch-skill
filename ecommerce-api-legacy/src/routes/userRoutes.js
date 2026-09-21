'use strict';

const { Router } = require('express');
const { deleteUserRules } = require('../middlewares/validate');

function userRoutes(userController) {
  const router = Router();
  router.delete('/users/:id', deleteUserRules, userController.remove);
  return router;
}

module.exports = userRoutes;
