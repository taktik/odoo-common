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

    /*
    Add kanban_image_url method in KanbanRecord to be able to show an image
    directly from its URL (from a image_url field for instance).
    Usage in the kanban view, for a product with a field image_url containing the URL of an image:
    <img t-att-src="kanban_image_url('product.product', 'image_url', record.id.value)" class="oe_kanban_image"/>
     */
    instance.web_kanban.KanbanRecord = instance.web_kanban.KanbanRecord.extend({
        kanban_image_url: function (model, field, id, cache, options) {
            options = options || {};
            var url;
            if (this.record[field] && this.record[field].value) {
                url = this.record[field].value;
            } else if (this.record[field] && !this.record[field].value) {
                url = "/web/static/src/img/placeholder.png";
            }
            return url;
        }
    });

    instance.web.form.widgets.add('image_url', 'instance.web.form.FieldImageURL');

}