import os.path as osp
common = {
            'toolbar_size': 24,
            'app_path': osp.dirname(osp.dirname(osp.abspath(__file__))),
        }

feeds_path = osp.join(common['app_path'], "feeds", 'feeds')
icon_path = osp.join(common['app_path'], "windows", 'icons')
