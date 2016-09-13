openerp.tk_account_move_line_search_extension = function (instance) {
    var QWeb = instance.web.qweb
    var _t = instance.web._t;
    var module = instance.account_move_line_search_extension;

    instance.account_move_line_search_extension.ListSearchView.include({
       aml_search_domain: function() {
           if (this.current_amount_min && this.current_amount_max) {
                this.current_amount_min = this.current_amount_min.replace(/[,]/g, '.');
                this.current_amount_max = this.current_amount_max.replace(/[,]/g, '.');
            }
           return this._super();
       },
    });
};