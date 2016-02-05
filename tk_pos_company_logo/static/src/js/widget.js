openerp.tk_pos_company_logo = function (instance) {

    module = instance.point_of_sale;

    var _initialize_ = module.PosModel.prototype.initialize;
    module.PosModel.prototype.initialize = function(session, attributes){
        self = this;
        // Add the load of the field res.company.street
        // that is the address of the company
        // Add the load of attribute values
        for (var i = 0 ; i < this.models.length; i++){
            if (this.models[i].model == 'res.company'){
                if (this.models[i].fields.indexOf('logo') == -1) {
                    this.models[i].fields.push('logo');
                }
            }
        }

        return _initialize_.call(this, session, attributes);
    };

    module.PosWidget = module.PosWidget.extend({
        build_widgets: function () {
            this._super();
            $('.pos-logo').attr("src", 'data:image/png;base64,' + this.pos.company.logo);
        },
    });

};
