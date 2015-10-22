openerp.tk_pos_block_ean_amount = function(instance){

    var QWeb = instance.web.qweb,
    _t = instance.web._t;
    var module = instance.point_of_sale;

    module.PaymentScreenWidget.include({
        validate_order: function(options) {
            var self = this;
            options = options || {};

            var currentOrder = this.pos.get('selectedOrder');

            if(this.pos.config.amount_limit && currentOrder.selected_paymentline.amount && this.pos.config.amount_limit < currentOrder.selected_paymentline.amount){
                self.pos_widget.screen_selector.show_popup('error',{
                    message: _t('Amount must be less than ' + this.pos.config.amount_limit),
                    comment: _t('Please insert a correct amount in the field')
                });
                return;
            }
            // else
            return this._super(options);
        }
    });

};