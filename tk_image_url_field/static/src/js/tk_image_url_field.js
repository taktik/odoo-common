openerp.tk_image_url_field = function (instance) {
    var QWeb = instance.web.qweb;
    var _t = instance.web._t;

    /**
     * FieldImageURL extend FieldChar.
     * In edit mode, add possibility to enter the URL of an image in the field (like a char field).
     * In normal mode, show the image.
     * @type {*|Object|void}
     */
    instance.web.form.FieldImageURL = instance.web.form.FieldChar.extend({
        template: 'FieldImageURL',
        widget_class: 'oe_form_field_image_url',
        placeholder: "/web/static/src/img/placeholder.png",
        init: function (field_manager, node) {
            this._super(field_manager, node);
        },
        render_value: function () {
            var self = this;
            if (!this.get("effective_readonly")) {
                this._super();
            } else {
                var url;
                if (this.get('value')) {
                    url = this.get('value');
                } else {
                    url = this.placeholder;
                }
                var $img = $(QWeb.render("FieldImageURL-img", { widget: this, url: url }));
                this.$el.find('> img').remove();
                this.$el.append($img);
                $img.load(function () {
                    if (!self.options.size)
                        return;
                    $img.css("max-width", "" + self.options.size[0] + "px");
                    $img.css("max-height", "" + self.options.size[1] + "px");
                });
                $img.on('error', function () {
                    $img.attr('src', self.placeholder);
                    instance.webclient.notification.warn(_t("Image"), _t("Could not display the selected image."));
                });
            }
        },
    });

    instance.web.form.widgets.add('image_url', 'instance.web.form.FieldImageURL');

}