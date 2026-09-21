'use strict';

class ReportController {
  constructor({ reportService }) {
    this.reportService = reportService;
  }

  financialReport = (req, res, next) => {
    try {
      res.json(this.reportService.financialReport());
    } catch (err) {
      next(err);
    }
  };
}

module.exports = ReportController;
