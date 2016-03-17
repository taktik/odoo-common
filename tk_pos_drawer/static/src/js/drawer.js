openerp.tk_pos_drawer = function(instance){

    var QWeb = instance.web.qweb,
    _t = instance.web._t;
    var module = instance.tk_pos_validate_order_hook;

    module.PaymentScreenWidget.include({

        before_openCashDrawer_hook: function(currentOrder) {
            var open = true;
            var journalTypeCash = false;
            var journalTypeOther = false;

            for (var i = 0; i < currentOrder.get('paymentLines').length; i++) {
                if(currentOrder.get('paymentLines').models[i].name === 'Cash (EUR)'){
                    journalTypeCash = true;
                }else{
                    journalTypeOther = true;
                }
            }

            if(journalTypeOther && !journalTypeCash){
                if (Math.abs(currentOrder.getPaidTotal() - currentOrder.getTotalTaxIncluded()) <= 0.00001) {
                    open = false;
                }
            }

            return open;
        },

    });
};
