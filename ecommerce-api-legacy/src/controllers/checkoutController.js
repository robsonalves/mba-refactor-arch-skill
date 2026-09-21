'use strict';

// Thin controller: maps external payload -> domain, calls service, builds response.
class CheckoutController {
  constructor({ checkoutService }) {
    this.checkoutService = checkoutService;
  }

  create = (req, res, next) => {
    try {
      const result = this.checkoutService.checkout({
        name: req.body.usr,
        email: req.body.eml,
        password: req.body.pwd,
        courseId: req.body.c_id,
        card: req.body.card,
      });
      res.status(200).json(result);
    } catch (err) {
      next(err);
    }
  };
}

module.exports = CheckoutController;
