openerp.tk_pos_drawer = function(instance){

    var QWeb = instance.web.qweb,
    _t = instance.web._t;
    var module = instance.point_of_sale;

    module.PaymentScreenWidget.include({

        before_print_hook: function(xml_receipt) {

        },

        before_openCashDrawer_hook: function(currentOrder) {
            return true;
        },

        validate_order: function(options) {

            var self = this;
            options = options || {};

            var currentOrder = this.pos.get('selectedOrder');

            if(currentOrder.get('orderLines').models.length === 0){
                this.pos_widget.screen_selector.show_popup('error',{
                    'message': _t('Empty Order'),
                    'comment': _t('There must be at least one product in your order before it can be validated'),
                });
                return;
            }

            var plines = currentOrder.get('paymentLines').models;
            for (var i = 0; i < plines.length; i++) {
                if (plines[i].get_type() === 'bank' && plines[i].get_amount() < 0) {
                    this.pos_widget.screen_selector.show_popup('error',{
                        'message': _t('Negative Bank Payment'),
                        'comment': _t('You cannot have a negative amount in a Bank payment. Use a cash payment method to return money to the customer.'),
                    });
                    return;
                }
            }

            if(!this.is_paid()){
                return;
            }

            // The exact amount must be paid if there is no cash payment method defined.
            if (Math.abs(currentOrder.getTotalTaxIncluded() - currentOrder.getPaidTotal()) > 0.00001) {
                var cash = false;
                for (var i = 0; i < this.pos.cashregisters.length; i++) {
                    cash = cash || (this.pos.cashregisters[i].journal.type === 'cash');
                }
                if (!cash) {
                    this.pos_widget.screen_selector.show_popup('error',{
                        message: _t('Cannot return change without a cash payment method'),
                        comment: _t('There is no cash payment method available in this point of sale to handle the change.\n\n Please pay the exact amount or add a cash payment method in the point of sale configuration'),
                    });
                    return;
                }
            }

            //var journalTypeCash = false;
            //var journalTypeOther = false;
            //
            //for (var i = 0; i < currentOrder.get('paymentLines').length; i++) {
            //    if(currentOrder.get('paymentLines').models[i].name === 'Cash (EUR)'){
            //        journalTypeCash = true;
            //    }else{
            //        journalTypeOther = true;
            //    }
            //}
            //
            //
            //
            //if(journalTypeOther && !journalTypeCash){
            //    if (Math.abs(currentOrder.getPaidTotal() - currentOrder.getTotalTaxIncluded()) <= 0.00001) {
            //        openCashDrawer = false;
            //    }
            //}

            var openCashDrawer = true;
            openCashDrawer = this.before_openCashDrawer_hook(currentOrder);

            if (this.pos.config.iface_cashdrawer && openCashDrawer) {
                    this.pos.proxy.open_cashbox();
            }

            if(options.invoice){
                // deactivate the validation button while we try to send the order
                this.pos_widget.action_bar.set_button_disabled('validation',true);
                this.pos_widget.action_bar.set_button_disabled('invoice',true);

                var invoiced = this.pos.push_and_invoice_order(currentOrder);

                invoiced.fail(function(error){
                    if(error === 'error-no-client'){
                        self.pos_widget.screen_selector.show_popup('error',{
                            message: _t('An anonymous order cannot be invoiced'),
                            comment: _t('Please select a client for this order. This can be done by clicking the order tab'),
                        });
                    }else{
                        self.pos_widget.screen_selector.show_popup('error',{
                            message: _t('The order could not be sent'),
                            comment: _t('Check your internet connection and try again.'),
                        });
                    }
                    self.pos_widget.action_bar.set_button_disabled('validation',false);
                    self.pos_widget.action_bar.set_button_disabled('invoice',false);
                });

                invoiced.done(function(){
                    self.pos_widget.action_bar.set_button_disabled('validation',false);
                    self.pos_widget.action_bar.set_button_disabled('invoice',false);
                    self.pos.get('selectedOrder').destroy();
                });

            }else{

                this.pos.push_order(currentOrder)
                if(this.pos.config.iface_print_via_proxy){
                    var receipt = currentOrder.export_for_printing();
                    var xml_receipt = QWeb.render('XmlReceipt',{
                        receipt: receipt, widget: self,
                    });
                    this.before_print_hook(xml_receipt);
                    this.pos.proxy.print_receipt(xml_receipt);
                    this.pos.get('selectedOrder').destroy();    //finish order and go back to scan screen
                }else{
                    this.pos_widget.screen_selector.set_current_screen(this.next_screen);
                }

                //this.pos.push_order(currentOrder)
                //if(this.pos.config.iface_print_via_proxy){
                //    var receipt = currentOrder.export_for_printing();
                //    this.pos.proxy.print_receipt(QWeb.render('XmlReceipt',{
                //        receipt: receipt, widget: self,
                //    }));
                //    this.pos.get('selectedOrder').destroy();    //finish order and go back to scan screen
                //}else{
                //    this.pos_widget.screen_selector.set_current_screen(this.next_screen);
                //}

                //instance.web.Model('pos.order').call('save_xml_receipt', [12], {}).then(function(){
                //
                //    }).fail(function (error, event) {
                //
                //    });

            }

            // hide onscreen (iOS) keyboard
            setTimeout(function(){
                document.activeElement.blur();
                $("input").blur();
            },250);
        }
    });
};
