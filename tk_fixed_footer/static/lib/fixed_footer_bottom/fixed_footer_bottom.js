
;(function ($, window, undefined) {
	'use strict';

	var name = 'stickyTableFooter',
		id = 0,
		defaults = {
			fixedOffset: 0,
			leftOffset: 0,
			marginTop: 0,
			objDocument: document,
			objFoot: 'tfoot',
			objWindow: window,
			scrollableArea: window
		};

	function isOverflowed(element){
    	return element.context.scrollWidth > element.context.clientWidth;
	};

	function Plugin (el, options) {
		// To avoid scope issues, use 'base' instead of 'this'
		// to reference this class from internal events and functions.
		var base = this;

		// Access to jQuery and DOM versions of element
		base.$el = $(el);
		base.el = el;
		base.id = id++;

		// Listen for destroyed, call teardown
		base.$el.bind('destroyed',
			$.proxy(base.teardown, base));

		// Cache DOM refs for performance reasons
		base.$clonedFooter = null;
		base.$originalFooter = null;

		// Keep track of state
		base.isSticky = false;
		base.hasBeenSticky = false;
		base.leftOffset = null;
		base.topOffset = null;

		base.init = function () {
			base.setOptions(options);

			base.$el.each(function () {
				var $this = $(this);

				// remove padding on <table> to fix issue #7
				$this.css('padding', 0);

				base.$originalFooter = $('tfoot:first', this);
				base.$clonedFooter = base.$originalFooter.clone();
				$this.trigger('clonedFooter.' + name, [base.$clonedFooter]);

				base.$clonedFooter.addClass('tableFloatingFooter');
				base.$clonedFooter.css('display', 'none');

				base.$originalFooter.addClass('tableFloatingFooterOriginal');
				base.$originalFooter.after(base.$clonedFooter);

				base.$printStyle = $('<style type="text/css" media="print">' +
					'.tableFloatingFooter{}' +
					'.tableFloatingFooterOriginal{bottom:0px;position:absolute !important;}' +
					'</style>');
				base.$foot.append(base.$printStyle);
			});

			base.updateWidth();
			base.toggleFooter();
			base.bind();
		};

		base.destroy = function (){
			base.$el.unbind('destroyed', base.teardown);
			base.teardown();
		};

		base.teardown = function(){
			if (base.isSticky) {
				base.$originalFooter.css('position', 'static');
			}
			$.removeData(base.el, 'plugin_' + name);
			base.unbind();

			base.$clonedFooter.remove();
			base.$originalFooter.removeClass('tableFloatingFooterOriginal');
			base.$originalFooter.css('visibility', 'visible');
			base.$printStyle.remove();

			base.el = null;
			base.$el = null;
		};

		base.bind = function(){
			base.$scrollableArea.on('scroll.' + name, base.toggleFooter);
			if (!base.isWindowScrolling) {
				base.$window.on('scroll.' + name + base.id, base.setPositionValues);
				base.$window.on('resize.' + name + base.id, base.toggleFooter);
                base.$window.on('resize.' + name + base.id, base.updateWidth);
			}
			base.$scrollableArea.on('resize.' + name, base.toggleFooter);
			base.$scrollableArea.on('resize.' + name, base.updateWidth);
		};

		base.unbind = function(){
			// unbind window events by specifying handle so we don't remove too much
			base.$scrollableArea.off('.' + name, base.toggleFooter);
			if (!base.isWindowScrolling) {
				base.$window.off('.' + name + base.id, base.setPositionValues);
				base.$window.off('.' + name + base.id, base.toggleFooter);
			}
			base.$scrollableArea.off('.' + name, base.updateWidth);
		};

		base.toggleFooter = function () {
			if (base.$el) {
				base.$el.each(function () {
					var $this = $(this),
						newLeft,
						newTopOffset = base.isWindowScrolling ? (
									isNaN(base.options.fixedOffset) ?
									base.options.fixedOffset.outerHeight() :
									base.options.fixedOffset
								) :
								base.$scrollableArea.offset().top + (!isNaN(base.options.fixedOffset) ? base.options.fixedOffset : 0),
						offset = $this.offset(),

						scrollTop = base.$scrollableArea.scrollTop(),
						scrollLeft = base.$scrollableArea.scrollLeft(),

						scrolledPastTop = base.isWindowScrolling ?
								scrollTop > offset.top :
								newTopOffset > offset.top,
						notScrolledPastBottom = (base.isWindowScrolling ? scrollTop : 0) <
								(offset.top + $this.height() - base.$clonedFooter.height() - (base.isWindowScrolling ? 0 : newTopOffset));

					if (scrolledPastTop && notScrolledPastBottom) {
                        newLeft = 0;
						base.$originalFooter.css({
							'position': 'absolute',
							'margin-top': base.options.marginTop,
							'z-index': 3 // #18: opacity bug
						});
						base.leftOffset = newLeft;
						base.topOffset = scrollTop;
						base.$clonedFooter.css('display', '');
						if (!base.isSticky) {
							base.isSticky = true;
							// make sure the width is correct: the user might have resized the browser while in static mode
							base.updateWidth();
							$this.trigger('enabledStickiness.' + name);
						}
						base.setPositionValues();
					} else if (base.isSticky) {
						base.$originalFooter.css('position', 'absolute');
						base.$clonedFooter.css('display', '');
						base.isSticky = false;
						base.resetWidth($('td,th', base.$clonedFooter), $('td,th', base.$originalFooter));
						$this.trigger('disabledStickiness.' + name);
					}
				});
			}
		};

		base.setPositionValues = function () {
			//var scrollBottom = base.$window.scrollTop() + base.$window.height();
			//var winScrollLeft = base.$window.scrollLeft();
			var winScrollTop = base.$window.scrollTop(),
				winScrollLeft = base.$window.scrollLeft();
			if (!base.isSticky ||
					winScrollTop < 0 || winScrollTop + base.$window.height() > base.$document.height() ||
					winScrollLeft < 0 || winScrollLeft + base.$window.width() > base.$document.width()) {
				return;
			}

            //var overFlowed = isOverflowed(base.$scrollableArea);
			//var margin = 0;
			//if(overFlowed){
			//	margin = 15;
			//}

			base.$originalFooter.css({
				'bottom': 0 - base.topOffset,
				'margin-bottom': 0,
			});
            base.$clonedFooter.css({
				'margin-bottom': 0,
			});
		};

		base.updateWidth = function () {
			if (!base.isSticky) {
				return;
			}
			// Copy cell widths from clone
			if (!base.$originalFooterCells) {
				base.$originalFooterCells = $('th,td', base.$originalFooter);
			}
			if (!base.$clonedFooterCells) {
				base.$clonedFooterCells = $('th,td', base.$clonedFooter);
			}
			var cellWidths = base.getWidth(base.$clonedFooterCells);
			base.setWidth(cellWidths, base.$clonedFooterCells, base.$originalFooterCells);

			// Copy row width from whole table
			base.$originalFooter.css('width', base.$clonedFooter.width());
		};

		base.getWidth = function ($clonedFooter) {
			var widths = [];
			$clonedFooter.each(function (index) {
				var width, $this = $(this);

				if ($this.css('box-sizing') === 'border-box') {
					var boundingClientRect = $this[0].getBoundingClientRect();
					if(boundingClientRect.width) {
						width = boundingClientRect.width; // #39: border-box bug
					} else {
						width = boundingClientRect.right - boundingClientRect.left; // ie8 bug: getBoundingClientRect() does not have a width property
					}
				} else {
					var $origTh = $('th', base.$originalFooter);
					if ($origTh.css('border-collapse') === 'collapse') {
						if (window.getComputedStyle) {
							width = parseFloat(window.getComputedStyle(this, null).width);
						} else {
							// ie8 only
							var leftPadding = parseFloat($this.css('padding-left'));
							var rightPadding = parseFloat($this.css('padding-right'));
							// Needs more investigation - this is assuming constant border around this cell and it's neighbours.
							var border = parseFloat($this.css('border-width'));
							width = $this.outerWidth() - leftPadding - rightPadding - border;
						}
					} else {
						width = $this.width();
					}
				}

				widths[index] = width;
			});
			return widths;
		};

		base.setWidth = function (widths, $clonedFooter, $origFooter) {
			$clonedFooter.each(function (index) {
				var width = widths[index];
				$origFooter.eq(index).css({
					'min-width': width,
					'max-width': width
				});
			});
		};

		base.resetWidth = function ($clonedFooter, $origFooter) {
			$clonedFooter.each(function (index) {
				var $this = $(this);
				$origFooter.eq(index).css({
					'min-width': $this.css('min-width'),
					'max-width': $this.css('max-width')
				});
			});
		};

		base.setOptions = function (options) {
			base.options = $.extend({}, defaults, options);
			base.$window = $(base.options.objWindow);
			base.$foot = $(base.options.objFoot);
			base.$document = $(base.options.objDocument);
			base.$scrollableArea = $(base.options.scrollableArea);
			base.isWindowScrolling = base.$scrollableArea[0] === base.$window[0];
		};

		base.updateOptions = function (options) {
			base.setOptions(options);
			// scrollableArea might have changed
			base.unbind();
			base.bind();
			base.updateWidth();
			base.toggleFooter();
		};

		// Run initializer
		base.init();
	}

	// A plugin wrapper around the constructor,
	// preventing against multiple instantiations
	$.fn[name] = function ( options ) {
		return this.each(function () {
			var instance = $.data(this, 'plugin_' + name);
			if (instance) {
				if (typeof options === 'string') {
					instance[options].apply(instance);
				} else {
					instance.updateOptions(options);
				}
			} else if(options !== 'destroy') {
				$.data(this, 'plugin_' + name, new Plugin( this, options ));
			}
		});
	};

})(jQuery, window);
