# -*- coding: utf-8 -*-
{
    'name': 'Taktik URL Image Field',
    'version': '0.1',
    'category': 'others',
    'description': """
    Add an image_url widget to allow images to be shown directly via their URLs.
    Add a kanban_image_url method in KanbanRecord to be able to show an image directly
    from its URL.
    """,
    'author': 'Taktik S.A. - Lefever David',
    'website': 'http://www.taktik.be',
    'depends': ['base', 'web'],
    'data': [
    ],
    'qweb': [
        'static/src/xml/tk_image_url_field.xml',
    ],
    'js': [
        'static/src/js/tk_image_url_field.js',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}
