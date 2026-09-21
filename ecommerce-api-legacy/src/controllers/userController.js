'use strict';

class UserController {
  constructor({ userService }) {
    this.userService = userService;
  }

  remove = (req, res, next) => {
    try {
      res.status(200).json(this.userService.deleteUser(Number(req.params.id)));
    } catch (err) {
      next(err);
    }
  };
}

module.exports = UserController;
