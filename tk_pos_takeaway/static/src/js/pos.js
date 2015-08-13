openerp.tk_pos_takeaway = function (instance) {
    module = instance.point_of_sale;
    const EAT_IN = 'eat-in';
    const TAKEAWAY = 'takeaway';
    const DIRECTION = 'direction';
    const REPRESENTATIVE = 'representative';

    module.PosModel = module.PosModel.extend({
        handle_consumer_goods: function (type) {
            var customer_id = false;
            var self = this;
            if (type === EAT_IN) {
                if (self.config.customer_consumer_goods_1
                    && self.config.customer_consumer_goods_1.length === 2) {
                    customer_id = self.config.customer_consumer_goods_1[0];
                }
            } else if (type === TAKEAWAY) {
                if (self.config.customer_consumer_goods_2
                    && self.config.customer_consumer_goods_2.length === 2) {
                    customer_id = self.config.customer_consumer_goods_2[0];
                }
            } else if (type === DIRECTION) {
                if (self.config.customer_consumer_goods_3
                    && self.config.customer_consumer_goods_3.length === 2) {
                    customer_id = self.config.customer_consumer_goods_3[0];
                }
            } else if (type === REPRESENTATIVE) {
                if (self.config.customer_consumer_goods_4
                    && self.config.customer_consumer_goods_4.length === 2) {
                    customer_id = self.config.customer_consumer_goods_4[0];
                }
            }
            var customer = self.db.get_partner_by_id(customer_id);
            if (customer != false && customer != undefined) {
                self.get_order().set_client(customer);
                var currentOrder = self.get('selectedOrder');
                var orderLines = currentOrder.get('orderLines').models;
                self.pricelist_engine.update_products_ui(customer);
                self.pricelist_engine.update_ticket(customer, orderLines);
            }
        }
    });

    var _parent_build_widgets = module.PosWidget.prototype.build_widgets;
    module.PosWidget.prototype.build_widgets = function () {
        _parent_build_widgets.apply(this, arguments);
        this.consumer_goods = new module.ConsumerGoodsWidget(this);
        this.consumer_goods.replace(this.$('.placeholder-ConsumerGoods'));
    };

    module.ConsumerGoodsWidget = module.PosBaseWidget.extend({
        template: 'ConsumerGoodsWidget',
        renderElement: function () {
            var self = this;
            this._super();
            if (self.pos.config.customer_consumer_goods_1) {
                self.el.querySelector('.consumer-good-eat-in')
                    .addEventListener('click', function () {
                        self.pos.handle_consumer_goods(EAT_IN);
                    });
            }
            if (self.pos.config.customer_consumer_goods_2) {
                self.el.querySelector('.consumer-good-takeaway')
                    .addEventListener('click', function () {
                        self.pos.handle_consumer_goods(TAKEAWAY);
                    });
            }
            if (self.pos.config.customer_consumer_goods_3) {
                self.el.querySelector('.consumer-good-direction')
                    .addEventListener('click', function () {
                        self.pos.handle_consumer_goods(DIRECTION);
                    });
            }
            if (self.pos.config.customer_consumer_goods_4) {
                self.el.querySelector('.consumer-good-representative')
                    .addEventListener('click', function () {
                        self.pos.handle_consumer_goods(REPRESENTATIVE);
                    });
            }

        }
    });

};
